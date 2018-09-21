import datetime
import gym
import threading
import time
import logging
from gym_malware import sha256_holdout, MAXTURNS
from gym_malware.envs.controls import manipulate2 as manipulate
from gym_malware.envs.utils import pefeatures, interface
from multiprocessing import Pool, Process
import os

TEST_NAME = 'malware-test-v0'
test_process = locals()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

path = "time2.txt"


def test(id):
    with open(path, 'a+') as f:
        f.write("run process {} ....\n".format(id))
    logger.info("run process {} ....\n".format(id))
    start = datetime.datetime.now()
    env = gym.make(TEST_NAME)
    _ = env.reset()
    R = 0
    for step in range(60):
        action = env.action_space.sample()
        observation, reward, done, info = env.step(action)
        R += reward
        # if done:
        #     # logger.info("thread %s: step = %s  reward = %s" % (self.threadID, step, R))
        #     # print("thread %s: step = %s  reward = %s" % (self.threadID, step, R))
        #     break
    end = datetime.datetime.now()
    time = end - start
    logger.info("Process {} runs {}.\n".format(id, time))
    with open(path, 'a+') as f:
        f.write("Process {} runs {}.\n".format(id, time))


if __name__ == '__main__':
    print('Parent process %s.' % os.getpid())
    time = datetime.datetime.now()
    with open(path, 'a+') as f:
        f.write("多线程测试: start time is {} \n".format(time))

    for i in range(100):
        test_process['Process' + str(i)] = Process(target=test, args=(i,))
        test_process.get('Process' + str(i)).start()
    for i in range(100):
        test_process.get('Process' + str(i)).join()

    print('Process end.')
    time = datetime.datetime.now()
    with open(path, 'a+') as f:
        f.write("多线程测试: end time is {} \n".format(time))

    # print('Parent process %s.' % os.getpid())
    # p = Pool()
    # for i in range(4):
    #     p.apply_async(test, args=(i,))
    # print('Waiting for all subprocesses done...')
    # p.close()  # no process will be added to the pool
    # p.join()
    # time.sleep(100)
    # print('Parent process %s.' % os.getpid())
    # p1 = Process(target=test, args=(1,))
    # p2 = Process(target=test, args=(2,))
    # p1.start()
    # p2.start()
    # p1.join()
    # p2.join()
    # print('Process end.')

# class myThread(threading.Thread):
#     def __init__(self, threadID):
#         threading.Thread.__init__(self)
#         self.threadID = threadID
#         self.env = gym.make(TEST_NAME)
#         self.start()
#
#     def run(self):
#         with open(path, 'a+') as f:
#             f.write("线程 {}: start time is {} \n".format(self.threadID,datetime.datetime.now()))
#         R = 0
#         _ = self.env.reset()
#         for step in range(60):
#             action = self.env.action_space.sample()
#             observation, reward, done, info = self.env.step(action)
#             R += reward
#             # if done:
#             #     # logger.info("thread %s: step = %s  reward = %s" % (self.threadID, step, R))
#             #     # print("thread %s: step = %s  reward = %s" % (self.threadID, step, R))
#             #     break
#         with open(path, 'a+') as f:
#             f.write("线程 {}: end time is {} \n".format(self.threadID,datetime.datetime.now()))
#
# time = datetime.datetime.now()
# logger.info("start: {}".format(time))
# with open(path, 'a+') as f:
#     f.write("多线程测试: start time is {} \n".format(time))
#
# for i in range(100):
#     test_thread['thread' + str(i)] = myThread(i)
# for i in range(100):
#     test_thread.get('thread' + str(i)).join()
#
# time = datetime.datetime.now()
# logger.info("end: {}".format(time))
# with open(path, 'a+') as f:
#     f.write("多线程测试: end time is {} \n".format(time))
