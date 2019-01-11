import lief

from select_feature.utils import interface

# 本文件用于过滤样本中被lief判定为不是pe文件的文件（有点绕~），并删除
# 从bytez字节parse，该方法只能使用lief 0.7版本
# Mac系统下使用0.8要报错，原因未知
SAMPLE_PATH = interface.MALWARE_SAMPLE_PATH
# SAMPLE_PATH = interface.BENIGN_SAMPLE_PATH

sha_list = interface.get_available_sha256(SAMPLE_PATH)
normal = []
unnormal = []
index = 1
for sha256 in sha_list:
    bytez = interface.fetch_file(sha256, benign=(SAMPLE_PATH == interface.BENIGN_SAMPLE_PATH))
    print("========================{}========================".format(index))
    print("========================{}========================".format(sha256))
    try:
        binary = lief.PE.parse(bytez)
        normal.append(sha256)
    except:
        unnormal.append(sha256)
        interface.delete_file(SAMPLE_PATH, sha256)

    index = index + 1

print('normal:{}, unnormal:{}'.format(len(normal), len(unnormal)))
