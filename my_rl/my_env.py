from my_rl.envs.utils.pefeatures import GeneralFileInfo
from my_rl.envs.utils import interface

# Action space: -1,0,1,2,3,4,5,6,7,8,9


# 暂时不用任何gym的东西
class MyEnv:
    def __init__(self):
        self.reset()

    def step(self, action_index):
        if action_index == -1:
            self.done = True
        else:
            self.state[action_index] = 1
            self.count += 1
            if self.count == self.max_count:  #全部指标都被选择了
                self.done = True

        # reward 默认为0
        reward = 0
        if self.done == True:
            reward = interface.get_success_rate(action_index)

        return self.state, self.done, reward

    def reset(self):
        # 暂时提取my_rl.envs.utils.pefeatures中GeneralFileInfo的9个指标
        features_length = GeneralFileInfo().dim
        # print(features_length)

        self.state = [0 for _ in range(features_length)]
        self.max_count = features_length  # 最大特征数
        self.count = 0  # 当前已经选取的特征数
        self.done = False
        return self.state

    def render(self):
        print("This is me: {}".format(self.observation_space))
