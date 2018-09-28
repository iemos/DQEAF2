import requests
from gym_malware.envs.utils import interface
import os
import time


class VirusTotal(object):
    def __init__(self):
        self.api_key = '086c5f98f3b6350d46593606900533400a07763ef507dac79de648a2b94b1f65'

    def scan(self, file_name):
        url = 'https://www.virustotal.com/vtapi/v2/file/scan'
        params = {'apikey': self.api_key}
        files = {
            'file': (file_name, open(file_name, 'rb'))
        }
        response = requests.post(url, files=files, params=params)
        return response.json()

    def report(self, resource):
        url = 'https://www.virustotal.com/vtapi/v2/file/report'
        params = {'apikey': self.api_key, 'resource': resource}
        response = requests.get(url, params=params)
        return response.json()

    def get_score(self, resource):
        result = self.report(resource)
        total = result["total"]
        positives = result["positives"]
        return total, positives, positives / total


def remote_engine(limit=20):
    sha_list = interface.get_available_sha256()
    malware = []
    benign = []
    crash = []
    for sha256 in sha_list:
        limit -= 1
        if limit < 0:
            break
        # print(sha256)
        file_path = os.path.join(interface.SAMPLE_PATH, sha256)

        vt = VirusTotal()
        result_dict = vt.scan(file_path)

        sha_256 = result_dict['sha256']
        while(1):
            try:
                total, positives, score = vt.get_score(sha_256)
                print('{} -> score: {}, ratio: {}/{}'.format(
                    sha256, score, positives, total))
            except:
                print("detect error and wait 10s")
                time.sleep(10)
            else:
                break;


if __name__ == '__main__':
    # vt = VirusTotal()
    # result_dict = vt.scan('Backdoor.Win32.PcClient.pkk')
    # print((result_dict))
    # scan_id = result_dict['scan_id']
    #
    # total, positives, score = vt.get_score(scan_id)
    # print('score: {}, ratio: {}/{}'.format(
    #      score, positives, total))
    # print(vt.get_score('42405f0b77d4b4f6c3ebf0948006c8b549203801dc80f99c84cfa160d2e714c6-1538103628'))
    remote_engine(10)
