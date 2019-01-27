import chainer
import chainer.functions as F
import chainer.links as L
import numpy as np
from chainer import optimizers
from chainerrl import replay_buffer, explorers

from select_feature import action_value as ActionValue
from select_feature import agent as DDQN
from select_feature import env as Env

MAX_EPISODE = 100

net_layers = [64, 32]


# 每一轮逻辑如下
# 1. 初始化环境，定义S和A两个list，用来保存过程中的state和action。进入循环，直到当前这一轮完成（done == True）
# 2. 在每一步里，首先选择一个action，此处先用简单的act()代替
# 3. 接着env接收这个action，返回新的state，done和reward，当done==False时，reward=0，当done==True时，reward为模型的准确率
# 4. 如果done==True，那么应该把当前的S、A和reward送到replay buffer里（replay也应该在此时进行），往replay buffer里添加时，
#    每一对state和action都有一个reward，这个reward应该和env返回的reward（也就是该模型的acc）和count有关。

# 用这个逻辑替代原来的my_train的逻辑，只需要把agent加入即可，agent应该是不需要修改的

def main():
    class QFunction(chainer.Chain):
        def __init__(self, obs_size, n_actions, n_hidden_channels=None):
            super(QFunction, self).__init__()
            if n_hidden_channels is None:
                n_hidden_channels = net_layers
            net = []
            inpdim = obs_size
            for i, n_hid in enumerate(n_hidden_channels):
                net += [('l{}'.format(i), L.Linear(inpdim, n_hid))]
                # net += [('norm{}'.format(i), L.BatchNormalization(n_hid))]
                net += [('_act{}'.format(i), F.relu)]
                net += [('_dropout{}'.format(i), F.dropout)]
                inpdim = n_hid

            net += [('output', L.Linear(inpdim, n_actions))]

            with self.init_scope():
                for n in net:
                    if not n[0].startswith('_'):
                        setattr(self, n[0], n[1])

            self.forward = net

        def __call__(self, x, test=False):
            """
            Args:
                x (ndarray or chainer.Variable): An observation
                test (bool): a flag indicating whether it is in test mode
            """
            for n, f in self.forward:
                if not n.startswith('_'):
                    x = getattr(self, n)(x)
                elif n.startswith('_dropout'):
                    x = f(x, 0.1)
                else:
                    x = f(x)

            return ActionValue.DiscreteActionValue(x)

    def train_agent(env, agent):
        for episode in range(MAX_EPISODE):
            state = env.reset()
            terminal = False
            S = []
            A = []
            count = 0  # 当前选取了的特征数
            while terminal == False:
                # 此处保存的是上一轮的state，即保存的是state和针对该state选择的action
                S.append(state)
                action, q = agent.act_without_train(state)  # 此处action是否合法（即不能重复选取同一个指标）由agent判断。env默认得到的action合法。
                A.append(action)

                print("episode:{}, action:{}, q:{}".format(episode, action, q))

                state, terminal, reward = env.step(action)
                if terminal:
                    print("state:{}\nreward = {}\n".format(state, reward))
                    last_state = None
                    last_action = None
                    is_terminal = False
                    for i in range(len(S)):
                        current_state = S[i]
                        current_action = A[i]
                        if i == len(S) - 1:
                            is_terminal = True
                        agent.step_and_train(last_state, last_action, reward, current_state, current_action,
                                             is_terminal)

                        last_state = current_state
                        last_action = current_action
                else:
                    count += 1

    def create_agent(env):
        state_size = env.state_size
        action_size = env.action_size
        q_func = QFunction(state_size, action_size)

        start_epsilon = 1.0
        end_epsilon = 0.3
        decay_steps = 100
        explorer = explorers.LinearDecayEpsilonGreedy(
            start_epsilon, end_epsilon, decay_steps,
            env.random_action)

        opt = optimizers.Adam()
        opt.setup(q_func)

        rbuf_capacity = 5 * 10 ** 3
        minibatch_size = 16

        steps = 1000
        replay_start_size = 20
        update_interval = 10
        betasteps = (steps - replay_start_size) // update_interval
        rbuf = replay_buffer.PrioritizedReplayBuffer(rbuf_capacity, betasteps=betasteps)

        phi = lambda x: x.astype(np.float32, copy=False)

        agent = DDQN.DoubleDQN(q_func, opt, rbuf, gamma=0.99,
                               explorer=explorer, replay_start_size=replay_start_size,
                               target_update_interval=10,  # target q网络多久和q网络同步
                               update_interval=update_interval,
                               phi=phi, minibatch_size=minibatch_size,
                               target_update_method='hard',
                               soft_update_tau=1e-2,
                               episodic_update=False,
                               episodic_update_len=16)
        return agent

    def train():
        env = Env.MyEnv()
        agent = create_agent(env)
        train_agent(env, agent)

        return env, agent

    train()


if __name__ == '__main__':
    main()
