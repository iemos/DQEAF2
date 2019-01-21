from select_feature.utils.pefeatures import GeneralFileInfo
from select_feature.utils import interface

import numpy as np

import random

# Action space: -1,0,1,2,3,4,5,6,7,8

ACTION_SIZE = 10
STATE_SIZE = 9


# 暂时不用任何gym的东西
class MyEnv:
    def __init__(self):
        self.reset()
        self.state_size = STATE_SIZE
        self.action_size = ACTION_SIZE

    def random_action(self):
        while True:
            action = random.randint(0, 9)
            if action == 9 or self.state[action] == 0:
                break
        return action

    def step(self, action_index):
        if action_index == 9:
            self.done = True
        else:
            self.state[action_index] = 1
            self.count += 1
            if self.count == self.max_count:  # 全部指标都被选择了
                self.done = True

        # reward 默认为0
        reward = 0
        if self.done == True:
            # reward = random.random()
            reward = interface.get_success_rate(self.state)

        return np.array(self.state), self.done, reward

    def reset(self):
        # 暂时提取my_rl.envs.utils.pefeatures中GeneralFileInfo的9个指标
        features_length = GeneralFileInfo().dim
        # print(features_length)

        self.state = [0 for _ in range(features_length)]
        self.max_count = features_length  # 最大特征数
        self.count = 0  # 当前已经选取的特征数
        self.done = False
        return np.array(self.state)

    def render(self):
        print("This is me: {}".format(self.state))
