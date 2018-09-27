import requests

API_KEY = '54a104603aad46c9bc02917b952e273846d8748ddd6247e09f845bfb16d8ed10'
SANDBOX_TYPE = 'win7_sp1_enx86_office2013'

class ThreatBook(object):

    def __init__(self, api_key):
        self.api_key = api_key
        self.sandbox_type = SANDBOX_TYPE

    def __repr__(self):
        return "<ThreatBook proxy>"

    # 提交文件并分析
    # {
    #     "msg": "OK",
    #     "response_code": 0,
    #     "sha256": "3b7e88dea3d358744345f9a18cfb06edf858b5a6c72a91e7ddf92202cc244a02",
    #     "permalink": "https://s.threatbook.cn/report/file/3b7e88dea3d358744345f9a18cfb06edf858b5a6c72a91e7ddf92202cc244a02/?sign=history&env=win7_sp1_enx86_office2013"
    # }
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
    def get_summary(self, sha256):
        url = 'https://s.threatbook.cn/api/v2/file/report/summary'
        params = {
            'apikey': self.api_key,
            'sandbox_type': self.sandbox_type,
            'sha256': sha256
        }
        response = requests.get(url, params=params)
        print(response.json())

    # 获取文件的多引擎检测报告
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
    def get_multiengines(self, sha256):
        url = 'https://s.threatbook.cn/api/v2/file/report/multiengines'
        params = {
            'apikey': self.api_key,
            'sandbox_type': self.sandbox_type,
            'sha256': sha256
        }
        response = requests.get(url, params=params)
        print(response.json())

if __name__ == "__main__":
    file_name = 'win32.pe.samples'

    tb = ThreatBook(API_KEY)
    result_dict = tb.upload(file_name)
    sha256 = result_dict['sha256']
    tb.get_summary(sha256)
