import datetime
import gym
import threading
import time
import logging
from gym_malware import sha256_holdout, MAXTURNS
from gym_malware.envs.controls import manipulate2 as manipulate
from gym_malware.envs.utils import pefeatures, interface

TEST_NAME = 'malware-test-v0'
test_thread = locals()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class myThread(threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.env = gym.make(TEST_NAME)

    def run(self):
        R = 0
        _ = self.env.reset()
        for step in range(60):
            action = self.env.action_space.sample()
            observation, reward, done, info = self.env.step(action)
            R += reward
            # if done:
            #     # logger.info("thread %s: step = %s  reward = %s" % (self.threadID, step, R))
            #     # print("thread %s: step = %s  reward = %s" % (self.threadID, step, R))
            #     break


time = datetime.datetime.now()
logger.info("start: {}".format(time))
with open("time.txt", 'a+') as f:
    f.write("多线程测试: start time is %s " % time)

for i in range(100):
    test_thread['thread' + str(i)] = myThread(i)
    test_thread.get('thread' + str(i)).start()
for i in range(100):
    test_thread.get('thread' + str(i)).join()

time = datetime.datetime.now()
logger.info("end: {}".format(time))
with open("time.txt", 'a+') as f:
    f.write("多线程测试: end time is %s " % time)
