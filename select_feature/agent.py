from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from chainer import cuda
import numpy as np
from future import standard_library
standard_library.install_aliases()

import chainer

from chainerrl.agents import double_dqn

class DoubleDQN(double_dqn.DoubleDQN):
    def act(self, state):
        with chainer.using_config('train', False):
            with chainer.no_backprop_mode():
                action_value = self.model(
                    self.batch_states([np.array(state)], self.xp, self.phi))
                q = float(action_value.max.data)
                action = cuda.to_cpu(action_value.greedy_actions.data)[0]

        # Update stats
        self.average_q *= self.average_q_decay
        self.average_q += (1 - self.average_q_decay) * q

        # self.logger.debug('t:%s q:%s action_value:%s', self.t, q, action_value)
        return action

    def step_and_train(self, state, action, reward, next_state, next_action, is_state_terminal):
        self.t += 1

        self.last_state = state
        self.last_action = action
        # Update the target network
        if self.t % self.target_update_interval == 0:
            self.sync_target_network()

        if self.last_state is not None:
            assert self.last_action is not None
            # Add a transition to the replay buffer
            self.replay_buffer.append(
                state=self.last_state,
                action=self.last_action,
                reward=reward,
                next_state=next_state,
                next_action=next_action,
                is_state_terminal=is_state_terminal)

        self.replay_updater.update_if_necessary(self.t)

        if is_state_terminal:
            self.stop_episode()

        # self.logger.debug('t:%s r:%s a:%s', self.t, reward, action)

    def act_without_train(self, state):

        with chainer.using_config('train', False):
            with chainer.no_backprop_mode():
                action_value = self.model(
                    self.batch_states([np.array(state)], self.xp, self.phi))
                action_value.load_state(state)
                q = float(action_value.max.data)
                # print("q is {}".format(q))
                greedy_action = cuda.to_cpu(action_value.greedy_actions.data)[
                    0]
                # greedy_action = action_value.greedy_actions()
                # print(chainer.Variable(action_value.q_values.data.argmax(axis=1).astype(np.int32)))
                # print("greedy action is {}".format(greedy_action))

        self.average_q *= self.average_q_decay
        self.average_q += (1 - self.average_q_decay) * q

        action = self.explorer.select_action(
            self.t, lambda: greedy_action, action_value=action_value)

        return action