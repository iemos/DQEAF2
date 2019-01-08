#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 09:13:03 2018

@author: JiaoXiaojun
"""
import numpy as np
import pandas as pd
from keras import optimizers
from keras.layers import Dense
from keras.layers import Dropout
from keras.models import Sequential
from keras.utils import np_utils

np.random.seed(1000)


def GenerateData(num):
    data = []
    label = []
    t = np.random.random(size=num) * 2 * np.pi - np.pi
    x = np.cos(t)
    y = np.sin(t)
    for i in range(0, num):
        len = np.sqrt(np.random.random()) * 10
        dx = x[i] * len
        dy = y[i] * len
        if len < 8:
            label.append(1)
        else:
            label.append(0)
        data.append([dx, dy])
    return (data, label)


num = 40000
train = int(num * 0.7)
(x_train, y_train) = GenerateData(num)
x_train_norm = np.array(x_train[:train])
x_test_norm = np.array(x_train[train:])
x_train_norm = x_train_norm / 10
x_test_norm = x_test_norm / 10
y_trains = np.array(y_train[:train])
y_tests = np.array(y_train[train:])

y_trainsOneHot = np_utils.to_categorical(y_trains)
y_testsOneHot = np_utils.to_categorical(y_tests)
print(x_test_norm.shape)
print(y_testsOneHot.shape)

model = Sequential()
model.add(Dense(units=100, input_dim=2, kernel_initializer='normal', activation='relu'))
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
print(scores)

# model.save("models/MYKerasDemo_model.h5")  # 把训练好的模型保存下来
# model=load_model("/Volumes/Data/dp/MYKerasDemo_model.h5")#加载训练好的模型后续直接用于训练数据集
# predict = model.predict_classes(x_test_norm)
# # 模型训练好了，进行实际预测部署
# predict_classes = predict.reshape(-1)
#
# pd.crosstab(y_tests, predict_classes, rownames=['label'], colnames=['predict'])
# df = pd.DataFrame({'label': y_tests, 'predict': predict_classes})
# dx = (df[df.label != df.predict].index)[:]  # 把原始的数据其标签和实际预测不同的给标记出来
#
# print("{}/{}".format(len(dx), df.__len__()))
# for i in dx[:20]:
#     print(y_tests[i], predict_classes[i])
