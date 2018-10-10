import datetime
import gym
import threading
import time
import logging
from gym_malware.envs import malware_env
from multiprocessing import Pool, Process, Value, Lock
import multiprocessing
import os
import argparse
import numpy
import copy

lock = Lock()
counter = Value("i", 0)

TEST_NAME = 'malware-test-v0'
test_process = locals()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

process_path = "process_log.txt"
history_path = "history_log.txt"


def test(id, scores, env):
    global lock, counter
    # with open(path, 'a+') as f:
    #     f.write("run process {} ....\n".format(id))
    # logger.info("run process {} ....\n".format(id))
    start = datetime.datetime.now()
    R = 0
    try:
        for step in range(60):
            action = env.action_space.sample()
            observation, reward, done, info = env.step(action)
            R += reward
            if done:
                step += 1
                with lock:
                    counter.value += step
                end = datetime.datetime.now()
                process_time = end - start
                if R > 0:
                    R = 10
                scores[id] = float(R)
                logger.info(
                    "Process {} runs {} with {} steps  reward = {}   socres = {} .\n".format(id, process_time, step, R,
                                                                                             scores[id]))
                with open(process_path, 'a+') as f:
                    f.write("Process {} runs {} with {} steps.\n".format(id, process_time, step))

                with open(history_path, 'a+') as f:
                    k = []
                    v = []
                    for temp_k, temp_v in env.history.items():
                        k=temp_k
                        v=temp_v

                    if v['evaded']:
                        f.write("{}:{}->success\n".format(id, k))
                        f.write("actions are: {}\n\n".format(v['actions']))
                    else:
                        f.write("{}:{}->fail\n".format(id, k))
                        f.write("actions are: {}\n\n".format(v['actions']))
                break
    except Exception as e:
        logger.info(e)

def delete(path):
    ls = os.listdir(path)
    for i in ls:
        c_path = os.path.join(path, i)
        os.remove(c_path)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--number', type=int, default=100)
    args = parser.parse_args()

    scores = multiprocessing.Array('f', numpy.zeros(args.number))

    delete("Sample/original")
    delete("Sample/modification")

    os.remove("history_log.txt")
    os.remove("process_log.txt")
    env = gym.make(TEST_NAME)

    start = datetime.datetime.now()
    with open(process_path, 'a+') as f:
        f.write("start time is {} \n".format(start))

    for i in range(args.number):
        env.reset()
        env_temp = copy.copy(env)
        env = copy.copy(env_temp)
        test_process['Process' + str(i)] = Process(target=test, args=(i, scores, env_temp))
        test_process.get('Process' + str(i)).start()

    print('Wait all processed end.\n')
    with open(process_path, 'a+') as f:
        f.write('Wait all processed end.\n')
    #
    for i in range(args.number):
        test_process.get('Process' + str(i)).join()
        # print('Process {} exit.\n'.format(i))
        # with open(process_path, 'a+') as f:
        #     f.write('Process {} exit.\n'.format(i))

    print('Process end.')
    with open(process_path, 'a+') as f:
        end = datetime.datetime.now()
        f.write("end time is {} \n".format(end))
        f.write("total time is {} \n".format(end-start))

    #
    # print("counter= {}".format(counter.value))
