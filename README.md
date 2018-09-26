# 使用深度强化学习进行恶意软件检测规避 

**DQEAF**:Deep Q-network anti-malware Engines Attacking Framework

The goal of this project is to improve the author's [original work](https://github.com/endgameinc/gym-malware).  
In his Paper: **Evading Machine Learning Malware Detection**, He builds a framework for attacking static PE anti-malware engines based on reinforcement learning.

## TODO
1. web查毒引擎接口
1. reward重新设计
1. 异步测试

## NOTES
1. Blackjack的RL训练过程就是：观察手上的牌，和庄家的牌，决定是否要继续要牌，action最初始终都是1，最后一步是0，这个和我们的env可能没有太多的相似性