import glob
import os
import sys

import numpy as np
from keras import optimizers
from keras.layers import Dense
from keras.layers import Dropout
from keras.models import Sequential
from keras.utils import np_utils

from my_rl.envs.utils.pefeatures import PEFeatureExtractor

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
def get_success_rate(action_index):
    # TODO: 根据action_index来调整生成的label
    (x_train, y_train) = generate_label()

    num = len(y_train)
    train = int(num * 0.7)

    # 划分训练集
    x_train_norm = np.array(x_train[:train])
    x_test_norm = np.array(x_train[train:])

    y_trains = np.array(y_train[:train])
    y_tests = np.array(y_train[train:])

    y_trainsOneHot = np_utils.to_categorical(y_trains, 2)
    y_testsOneHot = np_utils.to_categorical(y_tests, 2)
    print(x_test_norm.shape)
    print(y_testsOneHot.shape)

    model = Sequential()
    model.add(Dense(units=100, input_dim=9, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(units=400, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(units=200, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(units=2, activation='softmax'))
    # model.add(Dense(units=2))
    # model.add(Softmax(axis=1))
    print(model.summary())
    # 优化器的选择：SGD,RMSprop,Adagrad,Adadelta,Adam,Adamax,Nadam(Nesterov版的Adam),TFOptimizer
    adam = optimizers.Adam(lr=1e-3, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
    # decay——每次参数更新后的学习率衰减值
    # amsgrad——是否应用此算法的AMSGrad变种
    model.compile(loss='binary_crossentropy', optimizer=adam, metrics=['accuracy', 'mae', 'acc'])

    train_history = model.fit(x_train_norm, y_trainsOneHot, batch_size=100, epochs=10, verbose=2, validation_split=0.2)

    scores = model.evaluate(x_test_norm, y_testsOneHot, verbose=1)

    print(scores[1])

    return scores[1]


if __name__ == '__main__':
    get_success_rate()
