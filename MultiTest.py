import datetime
import gym
import threading
import time
import logging
from gym_malware import sha256_holdout, MAXTURNS
from gym_malware.envs.controls import manipulate2 as manipulate
from gym_malware.envs.utils import pefeatures, interface


class myThread(threading.Thread):
    def __init__(self, env, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.env = env

    def run(self):
        R = 0
        observation = self.env.reset()
        for step in range(100):
            action = self.env.action_space.sample()
            observation, reward, done, info = self.env.step(action)
            # logger.info("thread %s: action %s  observation %s" % (self.threadID, action, observation))
            R += reward
            if done:
                logger.info("thread %s: step = %s  reward = %s" % (self.threadID, step, R))
                # print("thread %s: step = %s  reward = %s" % (self.threadID, step, R))
                break


# def test(env, ID):
#     for i in range(3):
#         # action = env
#         observation, reward, done, info = env.step(action)


logger = logging.getLogger()
logger.setLevel(logging.INFO)

TEST_NAME = 'malware-test-v0'
env_test = gym.make(TEST_NAME)
start_time = datetime.datetime.now()
for i in range(100):
    R = 0
    test_state = env_test.reset()
    for step in range(100):
        action = env_test.action_space.sample()
        observation, reward, done, info = env_test.step(action)
        # logger.info("thread %s: action %s  observation %s" % (self.threadID, action, observation))
        R += reward
        if done:
            logger.info("thread %s: step = %s  reward = %s" % (i, step, R))
            # print("thread %s: step = %s  reward = %s" % (self.threadID, step, R))
            break
end_time = datetime.datetime.now()
print("total time is %s " % (end_time - start_time))
with open("time.txt", 'a+') as f:
    f.write("one: total time is %s " % (end_time - start_time))


TEST_NAME = 'malware-test-v0'
test_env = locals()
test_thread = locals()
start_time = datetime.datetime.now()
for x in range (10):
    for i in range(10):
        test_env['env' + str(i)] = gym.make(TEST_NAME)
        test_thread['thread' + str(i)] = myThread(test_env.get('env' + str(i)), i)
        test_thread.get('thread' + str(i)).start()
    for i in range(10):
        test_thread.get('thread' + str(i)).join()
    logger.info("%s  ends"%x)
end_time = datetime.datetime.now()
print("total time is %s " % (end_time - start_time))
with open("time.txt", 'a+') as f:
    f.write("(multi: total time is %s " % (end_time - start_time))



# # 创建新线程
# thread1 = myThread(1, "Thread-1", 1)
# thread2 = myThread(2, "Thread-2", 2)
#
# # 开启新线程
# thread1.start()
# thread2.start()
# thread1.join()
# thread2.join()
# print("退出主线程")
