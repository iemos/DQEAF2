import os

import requests
from gym_malware.envs.utils import interface

class ThreatBook(object):
    def __init__(self):
        self.api_key = '54a104603aad46c9bc02917b952e273846d8748ddd6247e09f845bfb16d8ed10'
        self.sandbox_type = 'win7_sp1_enx86_office2013'

    # 提交文件并分析
    def upload(self, file_name):
        url = 'https://s.threatbook.cn/api/v2/file/upload'
        fields = {
            'apikey': self.api_key,
            'sandbox_type': self.sandbox_type
        }
        files = {
            'file': (file_name, open(file_name, 'rb'))
        }
        response = requests.post(url, data=fields, files=files)
        return response.json()

    # 获取文件分析报告
    def get_report(self, sha256):
        url = 'https://s.threatbook.cn/api/v2/file/report'
        params = {
            'apikey': self.api_key,
            'sandbox_type': self.sandbox_type,
            'sha256': sha256
        }
        response = requests.get(url, params=params)
        print(response.json())

    # 获取文件的概要信息
    def get_summary(self, sha256):
        url = 'https://s.threatbook.cn/api/v2/file/report/summary'
        params = {
            'apikey': self.api_key,
            'sandbox_type': self.sandbox_type,
            'sha256': sha256
        }
        response = requests.get(url, params=params)
        return response.json()

    # 获取文件的多引擎检测报告
    def get_multiengines(self, sha256):
        url = 'https://s.threatbook.cn/api/v2/file/report/multiengines'
        params = {
            'apikey': self.api_key,
            'sandbox_type': self.sandbox_type,
            'sha256': sha256
        }
        response = requests.get(url, params=params)
        return response.json()


def main():
    file_name = 'win32.pe.samples'

    tb = ThreatBook()
    result_dict = tb.upload(file_name)
    # {
    #     "msg": "OK",
    #     "response_code": 0,
    #     "sha256": "3b7e88dea3d358744345f9a18cfb06edf858b5a6c72a91e7ddf92202cc244a02",
    #     "permalink": "https://s.threatbook.cn/report/file/3b7e88dea3d358744345f9a18cfb06edf858b5a6c72a91e7ddf92202cc244a02/?sign=history&env=win7_sp1_enx86_office2013"
    # }
    if result_dict['msg'] != 'OK':
        print("upload error!")
        return -1

    sha256 = result_dict['sha256']

    # summary
    summary_dict = tb.get_summary(sha256)

    if summary_dict['msg'] != 'OK':
        print("summary error!")
        return -1

    print('threat_level: {}'.format(summary_dict['data']['summary']['threat_level']))
    print('threat_score: {}'.format(summary_dict['data']['summary']['threat_score']))
    # {
    #     "status_code": 0,
    #     "data": {
    #         "summary": {
    #             "threat_level": "malicious",
    #             "submit_time": "2018-09-27 21:43:04",
    #             "file_name": "Backdoor.Win32.Hupigon.zay",
    #             "file_type": "EXEx86",
    #             "sample_sha256": "3b7e88dea3d358744345f9a18cfb06edf858b5a6c72a91e7ddf92202cc244a02",
    #             "tag": {
    #                 "s": [
    #                     "PE32",
    #                     "语言neutral"
    #                 ],
    #                 "x": [
    #                     "TrojanDropper",
    #                     "Hupigon"
    #                 ]
    #             },
    #             "threat_score": 192,
    #             "sandbox_type": "win7_sp1_enx86_office2013"
    #         }
    #     },
    #     "msg": "OK"
    # }

    # multi
    multi_dict = tb.get_multiengines(sha256)

    if multi_dict['msg'] != 'OK':
        print("multi error!")
        return -1

    engines = multi_dict['data']['multiengines']
    print('ratio: {}/{}'.format(len([key for key in engines if engines[key] == 'safe']), len(engines)))
    # {
    #     "AVG": "safe",
    #     "Antiy": "safe",
    #     "Avast": "safe",
    #     "Avira": "safe",
    #     "Baidu": "safe",
    #     "Baidu-China": "Win32.Trojan.WisdomEyes.151026.9950.9995",
    #     "ClamAV": "safe",
    #     "DrWeb": "safe",
    #     "ESET": "safe",
    #     "GDATA": "safe",
    #     "Huorong": "Backdoor/MSIL.Agent.a",
    #     "IKARUS": "safe",
    #     "JiangMin": "safe",
    #     "K7": "safe",
    #     "Kaiwei": "safe",
    #     "Kaspersky": "Backdoor.MSIL.Agent.yqg",
    #     "Kingsoft": "safe",
    #     "Microsoft": "safe",
    #     "NANO": "safe",
    #     "Panda": "Trj/GdSda.A",
    #     "Qihu360": "safe",
    #     "Rising": "safe",
    #     "Sophos": "safe",
    #     "Tencent": "Msil.Backdoor.Agent.Lneq",
    #     "vbwebshell": "safe"
    # }


# 使用本地引擎统计sample里样本组成情况
def local_engine():
    sha_list = interface.get_available_sha256()
    malware = []
    benign = []
    for sha256 in sha_list:
        bytez = interface.fetch_file(sha256)
        label = interface.get_label_local(bytez)
        if label == 0.0:
            benign.append(sha256)
            interface.delete_file(sha256)
        else:
            malware.append(sha256)

    print('malware:{}, benign:{}'.format(malware.__len__(), benign.__len__()))


# 使用远程引擎统计sample里样本组成情况
def remote_engine(limit=20):
    sha_list = interface.get_available_sha256()
    malware = []
    benign = []
    for sha256 in sha_list:
        file_path = os.path.join(interface.SAMPLE_PATH, sha256)

        limit -= 1
        if limit < 0:
            break

        tb = ThreatBook()
        result_dict = tb.upload(file_path)
        if result_dict['msg'] != 'OK':
            print("upload error!")
            continue

        sha256 = result_dict['sha256']

        # summary
        summary_dict = tb.get_summary(sha256)

        if summary_dict['msg'] != 'OK':
            print(summary_dict)
            continue

        print('threat_level: {}'.format(summary_dict['data']['summary']['threat_level']))
        print('threat_score: {}'.format(summary_dict['data']['summary']['threat_score']))

        # multi
        multi_dict = tb.get_multiengines(sha256)

        if multi_dict['msg'] != 'OK':
            print("multi error!")
            return -1

        engines = multi_dict['data']['multiengines']
        print('ratio: {}/{}'.format(len([key for key in engines if engines[key] == 'safe']), len(engines)))

        # bytez = interface.fetch_file(sha256)
        # label = interface.get_label_local(bytez)
        # if label == 0.0:
        #     benign.append(sha256)
        #     interface.delete_file(sha256)
        # else:
        #     malware.append(sha256)

    print('malware:{}, benign:{}'.format(malware.__len__(), benign.__len__()))

if __name__ == '__main__':
    remote_engine()
