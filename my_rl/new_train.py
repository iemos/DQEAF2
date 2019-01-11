from my_rl import my_env as env

MAX_EPISODE = 100


# 每一轮逻辑如下
# 1. 初始化环境，定义S和A两个list，用来保存过程中的state和action。进入循环，直到当前这一轮完成（done == True）
# 2. 在每一步里，首先选择一个action，此处先用简单的act()代替
# 3. 接着env接收这个action，返回新的state，done和reward，当done==False时，reward=0，当done==True时，reward为模型的准确率
# 4. 如果done==True，那么应该把当前的S、A和reward送到replay buffer里（replay也应该在此时进行），往replay buffer里添加时，
#    每一对state和action都有一个reward，这个reward应该和env返回的reward（也就是该模型的acc）和count有关。

# 用这个逻辑替代原来的my_train的逻辑，只需要把agent加入即可，agent应该是不需要修改的

def act(state):
    return -1

def replay_append(S, A, reward, count):
    pass

def stop_and_replay():
    pass

env = env.MyEnv
for episode in range(MAX_EPISODE):
    state = env.reset()
    done = False
    S = []
    A = []
    count = 0  # 当前选取了的特征数
    while done == False:
        # 此处保存的是上一轮的state，即保存的是state和针对该state选择的action
        S.append(state)
        action = act(state)  #此处action是否合法（即不能重复选取同一个指标）由agent判断。env默认得到的action合法。
        A.append(action)

        state, done, reward = env.step(action)
        if done:
            replay_append(S, A, reward, count)
            stop_and_replay()
        else:
            count += 1
