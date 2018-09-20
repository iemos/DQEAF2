import datetime
import gym
import threading
import time
import logging
from gym_malware import sha256_holdout, MAXTURNS
from gym_malware.envs.controls import manipulate2 as manipulate
from gym_malware.envs.utils import pefeatures, interface


logger = logging.getLogger()
logger.setLevel(logging.INFO)


time = datetime.datetime.now()
logger.info("start: {}".format(time))
with open("time.txt", 'a+') as f:
    f.write("单线程测试: start time is %s " % time)

TEST_NAME = 'malware-test-v0'
env_test = gym.make(TEST_NAME)
for i in range(100):
    R = 0
    test_state = env_test.reset()
    for step in range(60):
        action = env_test.action_space.sample()
        observation, reward, done, info = env_test.step(action)
        R += reward
        # if done:
        #     # logger.info("thread %s: step = %s  reward = %s" % (i, step, R))
        #     # print("thread %s: step = %s  reward = %s" % (self.threadID, step, R))
        #     break

time = datetime.datetime.now()
logger.info("end: {}".format(time))
with open("time.txt", 'a+') as f:
    f.write("单线程测试: end time is %s " % time)

