from my_rl.envs.utils.pefeatures import GeneralFileInfo
from my_rl.envs.utils import interface


# 暂时不用任何gym的东西
class MyEnv:
    def __init__(self):
        self.reset()

    def step(self, action_index):
        # 根据action_index来改变observation_space
        reward = interface.get_success_rate(action_index)
        done = True
        return self.observation_space, reward, done, {}

    def reset(self):
        # 暂时提取my_rl.envs.utils.pefeatures中GeneralFileInfo的9个指标
        features_length = GeneralFileInfo().dim

        self.observation_space = [0 for _ in range(features_length)]
        return self.observation_space

    def render(self):
        print("This is me: {}".format(self.observation_space))
