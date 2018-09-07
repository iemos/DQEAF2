from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

import visdom
from chainerrl.experiments import StepHook


class TrainingScoresHook(StepHook):
    def __init__(self, title, outdir, figsize=(600, 400)):
        self.outdir = outdir
        self.textwindow = None
        self.opts = dict(
            showlegend=True,
            width=figsize[0],
            height=figsize[1],
            title=title
        )

        self.vis = visdom.Visdom(port=8888)
        assert self.vis.check_connection(), "Fail to connect to Visdom backend!"

    def text(self, content):
        if self.textwindow is None:
            self.textwindow = self.vis.text(content, opts=self.opts)
        else:
            self.vis.text(content, win=self.textwindow)

    def __call__(self, env, agent, step):
        if step % 100 == 0:
            with open(os.path.join(self.outdir, 'scores.txt'), 'r') as f:
                lines = f.readlines()  # 把全部数据文件读到一个列表lines中
                content = []
                for line in lines:  # 把lines中的数据逐行读取出来
                    list = line.strip('\n').split(
                        '\t')  # 处理逐行数据：strip表示把头尾的'\n'去掉，split表示以空格来分割行数据，然后把处理后的行数据返回到list列表中
                    content.append(list[3])
                self.text("<br/>".join(content))


if __name__ == '__main__':
    with open(os.path.join('scores.txt'), 'r') as f:
        lines = f.readlines()  # 把全部数据文件读到一个列表lines中

        for line in lines:  # 把lines中的数据逐行读取出来
            list = line.strip('\n').split(
                '\t')  # 处理逐行数据：strip表示把头尾的'\n'去掉，split表示以空格来分割行数据，然后把处理后的行数据返回到list列表中
            try:
                content = []
                for index, v in enumerate(list):
                    if index == 4 or index == 6 or index == 7:
                        continue
                    elif index > 7:
                        content.append(v if v.isdigit() else '%.4f' % float(v))
                    else:
                        content.append(v if v.isdigit() else '%.2f' % float(v))

                print("{}\\\\".format("&".join(content)))
            except:
                pass
