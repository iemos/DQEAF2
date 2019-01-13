from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import *  # NOQA
from future import standard_library
from future.utils import with_metaclass

standard_library.install_aliases()

from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
import warnings

from cached_property import cached_property
import chainer
from chainer import cuda
from chainer import functions as F
import numpy as np

from chainerrl.misc.chainer_compat import matmul_v3


class ActionValue(with_metaclass(ABCMeta, object)):
    """Struct that holds state-fixed Q-functions and its subproducts.

    Every operation it supports is done in a batch manner.
    """

    @abstractproperty
    def greedy_actions(self):
        """Get argmax_a Q(s,a)."""
        raise NotImplementedError()

    @abstractproperty
    def max(self):
        """Evaluate max Q(s,a)."""
        raise NotImplementedError()

    @abstractmethod
    def evaluate_actions(self, actions):
        """Evaluate Q(s,a) with a = given actions."""
        raise NotImplementedError()

    @abstractproperty
    def params(self):
        """Learnable parameters of this action value.

        Returns:
            tuple of chainer.Variable
        """
        raise NotImplementedError()


class DiscreteActionValue(ActionValue):
    """Q-function output for discrete action space.

    Args:
        q_values (ndarray or chainer.Variable):
            Array of Q values whose shape is (batchsize, n_actions)
    """

    def __init__(self, q_values, q_values_formatter=lambda x: x):
        assert isinstance(q_values, chainer.Variable)
        self.xp = cuda.get_array_module(q_values.data)
        self.q_values = q_values
        self.n_actions = q_values.data.shape[1]
        self.q_values_formatter = q_values_formatter

    @cached_property
    def greedy_actions(self):
        data = self.q_values.data.astype(np.int32)
        while True:
            action = np.argmax(data, axis=1)[0]
            if self.state[action] == 1:
                data[0][action] = -1
            else:
                break

        return chainer.Variable(np.array([action]).astype(np.int32))
        # return chainer.Variable(np.array([-1]).astype(np.int32))
        # print(self.q_values.data.argmax(axis=1).astype(np.int32))
        # return chainer.Variable(
        #     self.q_values.data.argmax(axis=1).astype(np.int32))

    @cached_property
    def max(self):
        with chainer.force_backprop_mode():
            return F.select_item(self.q_values, self.greedy_actions)

    def sample_epsilon_greedy_actions(self, epsilon):
        assert self.q_values.data.shape[0] == 1, \
            "This method doesn't support batch computation"
        if np.random.random() < epsilon:
            return chainer.Variable(
                self.xp.asarray([np.random.randint(0, self.n_actions)],
                                dtype=np.int32))
        else:
            return self.greedy_actions

    def evaluate_actions(self, actions):
        return F.select_item(self.q_values, actions)

    def compute_advantage(self, actions):
        return self.evaluate_actions(actions) - self.max

    def compute_double_advantage(self, actions, argmax_actions):
        return (self.evaluate_actions(actions) -
                self.evaluate_actions(argmax_actions))

    def compute_expectation(self, beta):
        return F.sum(F.softmax(beta * self.q_values) * self.q_values, axis=1)

    def load_state(self, state):
        self.state = state

    def __repr__(self):
        return 'DiscreteActionValue greedy_actions:{} q_values:{}'.format(
            self.greedy_actions.data,
            self.q_values_formatter(self.q_values.data))

    @property
    def params(self):
        return (self.q_values,)
