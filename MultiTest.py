import datetime
import gym
import threading
import time
import logging
from gym_malware import sha256_holdout, MAXTURNS
from gym_malware.envs.controls import manipulate2 as manipulate
from gym_malware.envs.utils import pefeatures, interface
from multiprocessing import Pool, Process, Value, Lock
import multiprocessing
import os
import argparse

lock = Lock()
counter = Value("i", 0)

TEST_NAME = 'malware-test-v0'
test_process = locals()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

path = "test_log.txt"


def test(id):
    global lock, counter
    with open(path, 'a+') as f:
        f.write("run process {} ....\n".format(id))
    logger.info("run process {} ....\n".format(id))
    start = datetime.datetime.now()
    env = gym.make(TEST_NAME)
    _ = env.reset()
    R = 0
    try:
        for step in range(60):
            with lock:
                counter.value += 1
            action = env.action_space.sample()
            observation, reward, done, info = env.step(action)
            R += reward
            if done:
                break
    except Exception as e:
        logger.info(e)

    end = datetime.datetime.now()
    process_time = end - start
    logger.info("Process {} runs {} with {} steps.\n".format(id, process_time, step))
    with open(path, 'a+') as f:
        f.write("Process {} runs {} with {} steps.\n".format(id, process_time, step))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--number', type=int, default=100)
    args = parser.parse_args()

    count = multiprocessing.Value("d", )
    time = datetime.datetime.now()

    for i in range(args.number):
        test_process['Process' + str(i)] = Process(target=test, args=(i,))
        test_process.get('Process' + str(i)).start()

    print('Wait all processed end.\n')
    with open(path, 'a+') as f:
        f.write('Wait all processed end.\n')

    for i in range(args.number):
        test_process.get('Process' + str(i)).join()
        print('Process {} exit.\n'.format(i))
        with open(path, 'a+') as f:
            f.write('Process {} exit.\n'.format(i))

    print('Process end.')
    time = datetime.datetime.now()
    # with open(path, 'a+') as f:
    #     f.write("多线程测试: end time is {} \n".format(time))
    #     f.write("成功个数为: {} / {} \n".format(counter.value, args.number))

    print("counter= {}".format(counter.value))
