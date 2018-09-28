import requests

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
        return positives/total

if __name__ == '__main__':
    vt = VirusTotal()
    print(vt.get_score('42405f0b77d4b4f6c3ebf0948006c8b549203801dc80f99c84cfa160d2e714c6-1538103628'))
