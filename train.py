# coding=UTF-8
# ! /usr/bin/python
import datetime

import argparse
import linecache
import os
import sys
from math import isnan

import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import gym
import numpy as np
from chainer import optimizers
from chainerrl import experiments, explorers, replay_buffer, misc

from gym_malware import sha256_holdout, MAXTURNS
from gym_malware.envs.controls import manipulate2 as manipulate
from gym_malware.envs.utils import pefeatures, interface
from hook.plot_hook import PlotHook
from hook.training_scores_hook import TrainingScoresHook

from keras.models import Sequential, load_model
from keras.layers import Dense, Activation, Flatten, ELU, Dropout, BatchNormalization
from keras.optimizers import RMSprop

# pip install keras-rl
from rl.agents.dqn import DQNAgent
from rl.policy import BoltzmannQPolicy, EpsGreedyQPolicy
from rl.memory import SequentialMemory
from rl.callbacks import Callback, TrainEpisodeLogger, TestLogger

from collections import defaultdict

ACTION_LOOKUP = {i: act for i, act in enumerate(manipulate.ACTION_TABLE.keys())}

net_layers = [256, 64]

LOSS_DECAY = 0.9
Q_DECAY = 0.9

step_average_loss = 0
episode_average_loss = 0
step_average_q = 0
episode_average_q = 0

# 用于快速调用chainerrl的训练方法，参数如下：
# 1、命令行启动visdom
# ➜  ~ source activate new
# (new) ➜  ~ python -m visdom.server -p 8888
# 2、运行train
# python train.py

timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")

step_loss_hook = PlotHook('Step Average Loss ', plot_index=0, xlabel='Training Steps', ylabel='Step Average Loss')
episode_loss_hook = PlotHook('Episode Average Loss ', plot_index=1, xlabel='Training Episodes',
                             ylabel='Episode Average Loss')

step_q_hook = PlotHook('Step Average Q ', plot_index=2, xlabel='Training Steps', ylabel='Step Average Q')
episode_q_hook = PlotHook('Episode Average Q ', plot_index=3, xlabel='Training Episodes',
                          ylabel='Episode Average Q')

test_step_to_success_hook = PlotHook('Step to success (Test) ', plot_index=4, xlabel='Testing Episodes',
                                     ylabel='Step to success (Test)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', type=str, default='models')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--gpu', action='store_true')
    parser.add_argument('--final-exploration-steps', type=int, default=10 ** 4)
    parser.add_argument('--start-epsilon', type=float, default=1.0)
    parser.add_argument('--end-epsilon', type=float, default=0.1)
    parser.add_argument('--load', type=str, default=None)
    parser.add_argument('--steps', type=int, default=1000)
    parser.add_argument('--prioritized-replay', action='store_false')
    parser.add_argument('--episodic-replay', action='store_true')
    parser.add_argument('--replay-start-size', type=int, default=1000)
    parser.add_argument('--target-update-interval', type=int, default=10 ** 2)
    parser.add_argument('--target-update-method', type=str, default='hard')
    parser.add_argument('--soft-update-tau', type=float, default=1e-2)
    parser.add_argument('--update-interval', type=int, default=1)
    parser.add_argument('--eval-n-runs', type=int, default=80)
    parser.add_argument('--eval-interval', type=int, default=1000)
    parser.add_argument('--gamma', type=float, default=0.99)
    parser.add_argument('--minibatch-size', type=int, default=None)
    parser.add_argument('--test-random', action='store_true')
    parser.add_argument('--rounds', type=int, default=1)
    args = parser.parse_args()

    # kerasrl
    def generate_dense_model(input_shape, nb_actions):
        model = Sequential()
        model.add(Flatten(input_shape=input_shape))
        # normalize before compute
        model.add(BatchNormalization())
        model.add(Dropout(0.1))  # drop out the input to make model less sensitive to any 1 feature

        for layer in net_layers:
            model.add(Dense(layer))
            model.add(ELU(alpha=1.0))
            model.add(Dropout(0.1))

        model.add(Dense(nb_actions))
        model.add(Activation('linear'))
        print(model.summary())

        return model

    class Episode_hook(TrainEpisodeLogger):
        def on_episode_end(self, episode, logs):
            metrics = np.array(self.metrics[episode])
            loss = np.nanmean(metrics[:, 0])
            q = np.nanmean(metrics[:, 2])
            if isnan(loss):
                loss = 0
            if isnan(q):
                q = 0
            global episode_average_loss
            global episode_average_q
            episode_average_loss *= LOSS_DECAY
            episode_average_loss += (1 - LOSS_DECAY) * loss
            episode_loss_hook(self.env, self.model, episode, episode_average_loss)

            episode_average_q *= Q_DECAY
            episode_average_q += (1 - Q_DECAY) * q
            episode_q_hook(self.env, self.model, episode, episode_average_q)

            print('episode %s, loss %s, q %s' % (episode, episode_average_loss, episode_average_q))

    class Step_hook(Callback):
        def on_step_end(self, step, logs={}):
            metrics = logs.get('metrics')
            loss = metrics[0]
            q = metrics[2]
            global step_average_loss
            global step_average_q
            if isnan(loss):
                loss = 0
            if isnan(q):
                q = 0
            print('step_average_q is %s' % step_average_q)

            step_average_loss *= LOSS_DECAY
            step_average_loss += (1 - LOSS_DECAY) * loss
            step_loss_hook(self.env, self.model, self.model.step, step_average_loss)

            step_average_q *= Q_DECAY
            step_average_q += (1 - Q_DECAY) * q
            step_q_hook(self.env, self.model, self.model.step, step_average_q)

    class Test_Episode_hook(TestLogger):
        def on_episode_end(self, episode, logs):
            step = logs.get('nb_steps')
            test_step_to_success_hook(self.env, self.model, episode, step)

    def train_keras_dqn_model(args):
        ENV_NAME = 'malware-v0'
        env = gym.make(ENV_NAME)
        env.seed(123)
        nb_actions = env.action_space.n
        window_length = 1  # "experience" consists of where we were, where we are now

        # generate a policy model
        model = generate_dense_model((window_length,) + env.observation_space.shape, nb_actions)

        # configure and compile our graduation_agent
        # BoltzmannQPolicy selects an action stochastically with a probability generated by soft-maxing Q values
        # policy = BoltzmannQPolicy()
        policy = EpsGreedyQPolicy()

        # memory can help a model during training
        # for this, we only consider a single malware sample (window_length=1) for each "experience"
        memory = SequentialMemory(limit=1000, ignore_episode_boundaries=False, window_length=window_length)

        # DQN graduation_agent as described in Mnih (2013) and Mnih (2015).
        # http://arxiv.org/pdf/1312.5602.pdf
        # http://arxiv.org/abs/1509.06461
        agent = DQNAgent(model=model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=16,
                         enable_double_dqn=True, enable_dueling_network=True, dueling_type='avg',
                         target_model_update=1e-2, policy=policy, batch_size=16)

        # keras-rl allows one to use and built-in keras optimizer
        agent.compile(RMSprop(lr=1e-2), metrics=['mae'])

        # play the game. learn something!
        callbacks = [Episode_hook(), Step_hook()]
        agent.fit(env, nb_steps=args.steps, callbacks=callbacks, visualize=False, verbose=2)

        model.save('models/{}.h5'.format(timestamp), overwrite=True)

        history_test = None

        if True:
            # Set up the testing environment
            TEST_NAME = 'malware-test-v0'
            test_env = gym.make(TEST_NAME)

            # evaluate the graduation_agent on a few episodes, drawing randomly from the test samples2
            callbacks = [Test_Episode_hook()]
            agent.test(test_env, nb_episodes=100, callbacks=callbacks, visualize=False)
            history_test = test_env.history

        return env, agent, history_test

    # 动作评估
    def evaluate(action_function):
        success = []
        misclassified = []
        for sha256 in sha256_holdout:
            success_dict = defaultdict(list)
            bytez = interface.fetch_file(sha256)
            label = interface.get_label_local(bytez)
            if label == 0.0:
                misclassified.append(sha256)
                continue  # already misclassified, move along
            for _ in range(MAXTURNS):
                action = action_function(bytez)
                print(action)
                success_dict[sha256].append(action)
                bytez = manipulate.modify_without_breaking(bytez, [action])
                new_label = interface.get_label_local(bytez)
                if new_label == 0.0:
                    success.append(success_dict)
                    break
        return success, misclassified  # evasion accuracy is len(success) / len(sha256_holdout)

    # test
    if not args.test:
        print("training...")

        # 反复多次重新训练模型，避免手工操作
        for _ in range(args.rounds):
            env, agent, history_test = train_keras_dqn_model(args)

            with open(os.path.join(args.outdir, '{}.txt'.format(timestamp)), 'a+') as f:
                f.write(
                    "total_turn/episode->{}({}/{})\n".format(env.total_turn / env.episode, env.total_turn, env.episode))
                f.write("history:\n")

                count = 0
                success_count = 0
                for k, v in history_test.items():
                    count += 1
                    if v['evaded']:
                        success_count += 1
                        f.write("{}:{}->evaded success!\n".format(count, k))
                    else:
                        f.write("{}:{}->\n".format(count, k))

                f.write("success count:{}".format(success_count))
                f.write("{}".format(history_test))

            # 重置outdir到models
            args.outdir = 'models'
    else:
        print("testing...")

        total = len(sha256_holdout)
        # baseline: choose actions at random
        if args.test_random:
            random_action = lambda bytez: np.random.choice(list(manipulate.ACTION_TABLE.keys()))
            random_success, misclassified = evaluate(random_action)
            total = len(sha256_holdout) - len(misclassified)  # don't count misclassified towards success

        # option 1: Boltzmann sampling from Q-function network output
        softmax = lambda x: np.exp(x) / np.sum(np.exp(x))
        boltzmann_action = lambda x: np.argmax(np.random.multinomial(1, softmax(x).flatten()))
        # option 2: maximize the Q value, ignoring stochastic action space
        best_action = lambda x: np.argmax(x)

        fe = pefeatures.PEFeatureExtractor()

        def model_policy(model):
            shp = (1,) + tuple(model.input_shape[1:])

            def f(bytez):
                # first, get features from bytez
                feats = fe.extract2(bytez)
                # feats = get_ob(bytez)
                q_values = model.predict(feats.reshape(shp))[0]
                action_index = best_action(q_values)  # alternative: best_action
                return ACTION_LOOKUP[action_index]

            return f

        model_fold = os.path.join(args.outdir, args.load)
        scores_file = os.path.join(args.outdir, '{}.txt'.format(args.load))

        # compare to keras models with windowlength=1
        dqn = load_model(model_fold)
        # dqn = load_model('models/dqn.h5')
        dqn_success, _ = evaluate(model_policy(dqn))

        # let's compare scores
        if args.test_random:
            random_result = "random:{}({}/{})".format(len(random_success) / total, len(random_success), total)
        else:
            random_result = "random:untested"

        blackbox_result = "blackbox:{}({}/{})".format(len(dqn_success) / total, len(dqn_success), total)
        with open(scores_file, 'a') as f:
            f.write("{}\n".format(random_result))
            f.write("{}\n".format(blackbox_result))


if __name__ == '__main__':
    main()
