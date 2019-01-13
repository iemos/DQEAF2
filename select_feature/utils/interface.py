import glob
import os
import sys
import csv

import numpy as np
from keras import optimizers
from keras.layers import Dense
from keras.layers import Dropout
from keras.models import Sequential
from keras.utils import np_utils

from select_feature.utils.pefeatures import PEFeatureExtractor

module_path = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))

MALWARE_SAMPLE_PATH = os.path.join(module_path, 'samples/malware')
BENIGN_SAMPLE_PATH = os.path.join(module_path, 'samples/benign')

feature_extractor = PEFeatureExtractor()


# 获取文件二进制数据
def fetch_file(filename, benign=False):
    root = MALWARE_SAMPLE_PATH if not benign else BENIGN_SAMPLE_PATH
    location = os.path.join(root, filename)
    with open(location, 'rb') as infile:
        bytez = infile.read()
    return bytez


# 在sample_path目录中读取样本，放入list返回
def get_available_sha256(sample_path):
    filelist = []
    for fp in glob.glob(os.path.join(sample_path, '*')):
        fn = os.path.split(fp)[-1]
        filelist.append(fn)
    assert len(filelist) > 0, "no files found in {} with sha256 names".format(sample_path)
    return filelist


def delete_file(sample_path, sha256):
    location = os.path.join(sample_path, sha256)
    os.remove(location)


# 生成label数据
def generate_label():
    data = []
    label = []

    malware_files = get_available_sha256(MALWARE_SAMPLE_PATH)
    for file in malware_files:
        bytez = fetch_file(file)
        features = feature_extractor.extract(bytez)
        data.append(features)
        label.append(1)

    benign_files = get_available_sha256(BENIGN_SAMPLE_PATH)
    for file in benign_files:
        bytez = fetch_file(file, benign=True)
        features = feature_extractor.extract(bytez)
        data.append(features)
        label.append(0)

    return data, label


# 根据label得到准确率
def get_success_rate(state):
    # print("start get SR\nstate:{}".format(state))
    data, label = load_data("data.csv", "label.txt")

    count = len(state)
    for i in reversed(range(len(state))):
        if state[i] == 0:
            count -= 1
            if count == 0:
                continue
            for index in range(len(data)):
                # print("current data is {}\ni = {}".format(data[index],i))
                del data[index][i]

    num = len(label)
    part = 0.9  # 取多少作为训练集
    first = int(num * part / 2)
    second = int(num / 2)
    third = int(num / 2 + first)
    # print("first:{}, second:{},third:{}\n".format(first,second,third))

    # 划分训练集
    x_train_norm = np.array(data[:first] + data[second:third])
    x_test_norm = np.array(data[first:second] + data[third:])

    # print(x_test_norm)

    y_trains = np.array(label[:first] + label[second:third])
    y_tests = np.array(label[first:second] + label[third:])

    # print(len(x_train_norm))
    # print(len(x_test_norm))
    # print(len(y_trains))
    # print(len(y_tests))

    y_trainsOneHot = np_utils.to_categorical(y_trains, 2)
    y_testsOneHot = np_utils.to_categorical(y_tests, 2)
    # print(x_test_norm.shape)
    # print(y_testsOneHot.shape)

    model = Sequential()
    model.add(Dense(units=100, input_dim=len(data[0]), kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(units=400, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(units=200, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(units=2, activation='softmax'))
    # model.add(Dense(units=2))
    # model.add(Softmax(axis=1))
    # print(model.summary())
    # 优化器的选择：SGD,RMSprop,Adagrad,Adadelta,Adam,Adamax,Nadam(Nesterov版的Adam),TFOptimizer
    adam = optimizers.Adam(lr=1e-3, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
    # decay——每次参数更新后的学习率衰减值
    # amsgrad——是否应用此算法的AMSGrad变种
    model.compile(loss='binary_crossentropy', optimizer=adam, metrics=['accuracy', 'mae', 'acc'])

    train_history = model.fit(x_train_norm, y_trainsOneHot, batch_size=100, epochs=10, verbose=2, validation_split=0.2)

    scores = model.evaluate(x_test_norm, y_testsOneHot, verbose=1)
    return scores[1]


def save_data(data, label, data_path, label_path):
    if os.path.exists(data_path):
        os.remove(data_path)
    if os.path.exists(label_path):
        os.remove(label_path)

    with open(data_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for i in range(len(data)):
            if data[i]:
                writer.writerow(data[i])
            else:
                label[i] = -1

    with open(label_path, 'w') as f:
        for i in label:
            if i != -1:
                f.write(str(i) + "\n")


def load_data(data_path, label_path):
    data = []
    label = []

    with open(data_path) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            for i in range(len(row)):
                if row[i] == 'True':
                    row[i] = True
                elif row[i] == 'False':
                    row[i] = False
                else:
                    row[i] = int(row[i])
            data.append(row)

    with open(label_path, 'r') as f:
        x = f.readlines()
        for i in x:
            i = i.strip('\n')
            if (i == '1'):
                i = 1
            else:
                i = 0
            label.append(i)
    return data, label


if __name__ == '__main__':

    for i in reversed(range(6)):
        print(i)
    # 生成数据集
    # data, label = generate_label()
    # save_data(data, label, "data.csv", "label.txt")

    # data, label = load_data("data.csv", "label.txt")

    # score = get_success_rate([1, 0, 0, 0, 1, 1, 1, 1, 1])

    # a = []
    # b = [1,2,3]
    # c = [4,5,6]
    # d = [7,8,9]
    # e = [0,1,1]
    # a.append(b)
    # a.append(c)
    # a.append(d)
    #
    # for i in e:
    #     if i == 0:
    #         for index in range(len(a)):
    #             del a[index][i]
    # print(a)
