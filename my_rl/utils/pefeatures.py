import re

import lief  # pip install https://github.com/lief-project/LIEF/releases/download/0.7.0/linux_lief-0.7.0_py3.6.tar.gz
import numpy as np
# FeatureHasher(n_features=10).transform( [ {k:v}, {k:v}])
from sklearn.feature_extraction import FeatureHasher


class FeatureType(object):
    '''Base class from which each feature type may inherit'''

    def __init__(self):
        super().__init__()
        self.dim = 0
        self.dtype = np.float32
        self.name = ''

    def __call__(self, arg):
        raise (NotImplemented)

    def empty(self):
        return np.zeros((self.dim,), dtype=self.dtype)

    def __repr__(self):
        return '{}({})'.format(self.name, self.dim)


class SectionInfo(FeatureType):
    '''Information about section names, sizes and entropy.  Uses hashing trick
    to summarize all this section info into a feature vector.
    '''

    def __init__(self):
        super().__init__()
        # sum of the vector sizes comprising this feature
        self.dim = 5 + 50 + 50 + 50 + 50 + 50
        self.name = 'SectionInfo'

    def __call__(self, binary):
        # general statistics about sections
        general = [len(binary.sections),  # total number of sections
                   # number of sections with nonzero size
                   sum(1 for s in binary.sections if s.size == 0),
                   # number of sections with an empty name
                   sum(1 for s in binary.sections if s.name == ""),
                   sum(1 for s in binary.sections if s.has_characteristic(lief.PE.SECTION_CHARACTERISTICS.MEM_READ)
                       and s.has_characteristic(lief.PE.SECTION_CHARACTERISTICS.MEM_EXECUTE)),  # number of RX
                   sum(1 for s in binary.sections if s.has_characteristic(
                       lief.PE.SECTION_CHARACTERISTICS.MEM_WRITE)),  # number of W
                   ]
        # TODO: print('genaral part ', general)
        # gross characteristics of each section
        section_sizes = [(s.name, len(s.content)) for s in binary.sections]
        section_entropy = [(s.name, s.entropy) for s in binary.sections]
        section_vsize = [(s.name, s.virtual_size) for s in binary.sections]

        # properties of entry point, or if invalid, the first executable section
        try:
            entry = binary.section_from_offset(binary.entrypoint)
        except lief.not_found:
            # bad entry point, let's find the first executable section
            entry = None
            for s in binary.sections:
                if lief.PE.SECTION_CHARACTERISTICS.MEM_EXECUTE in s.characteristics_lists:
                    entry = s
                    break
        if entry is not None:
            entry_name = [entry.name]
            entry_characteristics = [str(c)
                                     for c in entry.characteristics_lists]
            # ['SECTION_CHARACTERISTICS.CNT_CODE', 'SECTION_CHARACTERISTICS.MEM_EXECUTE','SECTION_CHARACTERISTICS.MEM_READ']
        else:
            entry_name = []
            entry_characteristics = []

        # let's dump all this info into a single vector
        res = np.concatenate([
            np.atleast_2d(np.asarray(general, dtype=self.dtype)),  # View inputs as arrays with at least two dimensions.
            FeatureHasher(50, input_type="pair", dtype=self.dtype).transform(
                [section_sizes]).toarray(),
            FeatureHasher(50, input_type="pair", dtype=self.dtype).transform(
                [section_entropy]).toarray(),
            FeatureHasher(50, input_type="pair", dtype=self.dtype).transform(
                [section_vsize]).toarray(),
            FeatureHasher(50, input_type="string", dtype=self.dtype).transform(
                [entry_name]).toarray(),
            FeatureHasher(50, input_type="string", dtype=self.dtype).transform([entry_characteristics]).toarray()
        ], axis=-1).flatten().astype(self.dtype)

        # TODO: print("SectionInfo length: ", res.size)
        # TODO: print('section: ', res)

        return np.concatenate([
            np.atleast_2d(np.asarray(general, dtype=self.dtype)),
            FeatureHasher(50, input_type="pair", dtype=self.dtype).transform(
                [section_sizes]).toarray(),
            FeatureHasher(50, input_type="pair", dtype=self.dtype).transform(
                [section_entropy]).toarray(),
            FeatureHasher(50, input_type="pair", dtype=self.dtype).transform(
                [section_vsize]).toarray(),
            FeatureHasher(50, input_type="string", dtype=self.dtype).transform(
                [entry_name]).toarray(),
            FeatureHasher(50, input_type="string", dtype=self.dtype).transform([entry_characteristics]).toarray()
        ], axis=-1).flatten().astype(self.dtype)


class ImportsInfo(FeatureType):
    '''Information about imported libraries and functions from the 
    import address table.  Note that the total number of imported
    functions is contained in GeneralFileInfo.
    '''

    def __init__(self):
        super().__init__()
        self.dim = 256 + 1024
        self.name = 'ImportsInfo'

    def __call__(self, binary):
        libraries = [l.lower() for l in binary.libraries]
        # we'll create a string like "kernel32.dll:CreateFileMappingA" for each entry
        imports = [lib.name.lower() + ':' +
                   e.name for lib in binary.imports for e in lib.entries]

        # TODO: print('libraries: ', libraries.__len__())
        # TODO: print('imports: ', imports.__len__())

        # two separate elements: libraries (alone) and fully-qualified names of imported functions
        res = np.concatenate([
            FeatureHasher(256, input_type="string", dtype=self.dtype).transform(
                [libraries]).toarray(),
            FeatureHasher(1024, input_type="string", dtype=self.dtype).transform(
                [imports]).toarray()
        ], axis=-1).flatten().astype(self.dtype)

        # TODO: print("ImportsInfo length: ", res.size)
        # TODO: np.set_printoptions(threshold=1e6)
        # TODO: print("imports: ", res)

        return np.concatenate([
            FeatureHasher(256, input_type="string", dtype=self.dtype).transform(
                [libraries]).toarray(),
            FeatureHasher(1024, input_type="string", dtype=self.dtype).transform(
                [imports]).toarray()
        ], axis=-1).flatten().astype(self.dtype)


class ExportsInfo(FeatureType):
    '''Information about exported functions. Note that the total number of exported
    functions is contained in GeneralFileInfo.
    '''

    def __init__(self):
        super().__init__()
        self.dim = 128
        self.name = 'ExportsInfo'

    def __call__(self, binary):
        res = FeatureHasher(128, input_type="string", dtype=self.dtype).transform(
            [binary.exported_functions]).toarray().flatten().astype(self.dtype)
        # TODO: print("ExportsInfo length: ", res.size)

        return FeatureHasher(128, input_type="string", dtype=self.dtype).transform(
            [binary.exported_functions]).toarray().flatten().astype(self.dtype)


class GeneralFileInfo(FeatureType):
    '''General information about the file.'''

    def __init__(self):
        super().__init__()
        self.dim = 9
        self.name = 'GeneralFileInfo'

    def __call__(self, binary):  # 基本信息
        return [
            binary.virtual_size,
            binary.has_debug,
            len(binary.exported_functions),
            len(binary.imported_functions),
            binary.has_relocations,
            binary.has_resources,
            binary.has_signature,
            binary.has_tls,
            len(binary.symbols),
        ]


class HeaderFileInfo(FeatureType):
    '''Machine, architecure, OS, linker and other information extracted from header.'''

    def __init__(self):
        super().__init__()
        self.dim = 62
        self.name = 'HeaderFileInfo'

    def __call__(self, binary):
        return np.concatenate([
            [[binary.header.time_date_stamps]],
            FeatureHasher(10, input_type="string", dtype=self.dtype).transform(
                [[str(binary.header.machine)]]).toarray(),
            FeatureHasher(10, input_type="string", dtype=self.dtype).transform(
                [[str(c) for c in binary.header.characteristics_list]]).toarray(),
            FeatureHasher(10, input_type="string", dtype=self.dtype).transform(
                [[str(binary.optional_header.subsystem)]]).toarray(),
            FeatureHasher(10, input_type="string", dtype=self.dtype).transform(
                [[str(c) for c in binary.optional_header.dll_characteristics_lists]]).toarray(),
            FeatureHasher(10, input_type="string", dtype=self.dtype).transform(
                [[str(binary.optional_header.magic)]]).toarray(),
            [[binary.optional_header.major_image_version]],
            [[binary.optional_header.minor_image_version]],
            [[binary.optional_header.major_linker_version]],
            [[binary.optional_header.minor_linker_version]],
            [[binary.optional_header.major_operating_system_version]],
            [[binary.optional_header.minor_operating_system_version]],
            [[binary.optional_header.major_subsystem_version]],
            [[binary.optional_header.minor_subsystem_version]],
            [[binary.optional_header.sizeof_code]],
            [[binary.optional_header.sizeof_headers]],
            [[binary.optional_header.sizeof_heap_commit]],
        ], axis=-1).flatten().astype(self.dtype)


class StringExtractor(FeatureType):
    ''' Extracts strings from raw byte stream '''

    def __init__(self):
        super().__init__()
        self.dim = 1 + 1 + 1 + 96 + 1 + 1 + 1 + 1
        self.name = 'StringExtractor'
        # all consecutive runs of 0x20 - 0x7f that are 5+ characters
        self._allstrings = re.compile(b'[\x20-\x7f]{5,}')
        # occurances of the string 'C:\'.  Not actually extracting the path
        self._paths = re.compile(b'c:\\\\', re.IGNORECASE)
        # occurances of http:// or https://.  Not actually extracting the URLs
        self._urls = re.compile(b'https?://', re.IGNORECASE)
        # occurances of the string prefix HKEY_.  No actually extracting registry names
        self._registry = re.compile(b'HKEY_')
        # crude evidence of an MZ header (dropper?) somewhere in the byte stream
        self._mz = re.compile(b'MZ')

    def __call__(self, bytez):
        allstrings = self._allstrings.findall(bytez)
        if allstrings:
            # statistics about strings:
            string_lengths = [len(s) for s in allstrings]
            avlength = sum(string_lengths) / len(string_lengths)  # 平均长度
            # map printable characters 0x20 - 0x7f to an int array consisting of 0-95, inclusive
            as_shifted_string = [b - ord(b'\x20')  # ord 返回对应的 ASCII 数值，或者 Unicode 数值
                                 for b in b''.join(allstrings)]
            c = np.bincount(as_shifted_string, minlength=96)  # histogram count
            # distribution of characters in printable strings
            p = c.astype(np.float32) / c.sum()
            wh = np.where(c)[0]
            H = np.sum(-p[wh] * np.log2(p[wh]))  # entropy
        else:
            avlength = 0
            p = np.zeros((96,), dtype=np.float32)
            H = 0

        res = np.concatenate([
            [[len(allstrings)]],  # 满足5+可打印字符串的长度
            [[avlength]],  # 平均长度
            [p.tolist()],  # 96个字符出现频率
            [[H]],  # 96个字符对应的熵值
            [[len(self._paths.findall(bytez))]],
            [[len(self._urls.findall(bytez))]],
            [[len(self._registry.findall(bytez))]],
            [[len(self._mz.findall(bytez))]]
        ], axis=-1).flatten().astype(self.dtype)

        # TODO: print('StringExtractor length: ', res.size)

        return np.concatenate([
            [[len(allstrings)]],
            [[avlength]],
            [p.tolist()],
            [[H]],
            [[len(self._paths.findall(bytez))]],
            [[len(self._urls.findall(bytez))]],
            [[len(self._registry.findall(bytez))]],
            [[len(self._mz.findall(bytez))]]
        ], axis=-1).flatten().astype(self.dtype)


class PEFeatureExtractor(object):
    ''' Extract useful features from a PE file, and return as a vector
        of fixed size. 
    '''

    def __init__(self):

        self.parsed_features = [
            GeneralFileInfo()
            # HeaderFileInfo(),
            # SectionInfo(),
            # ImportsInfo(),
            # ExportsInfo()
        ]
        self.dim = sum(o.dim for o in self.parsed_features)

    def extract(self, bytez):
        # feature vectors that require only raw bytez
        featurevectors = []

        # feature vectors that require a parsed file
        try:
            binary = lief.PE.parse(list(bytez))
        except (lief.bad_format, lief.bad_file, lief.pe_error, lief.parser_error, RuntimeError):
            # some kind of parsing problem, none of these feature extractors will work
            binary = None
            for fe in self.parsed_features:
                featurevectors = fe.empty()
        # except: # everything else (KeyboardInterrupt, SystemExit, ValueError):
        #     raise

        if binary is not None:
            for fe in self.parsed_features:
                try:
                    featurevectors = fe(binary)
                except(KeyboardInterrupt, SystemExit):
                    raise
                except:
                    # some property was invalid or missing
                    featurevectors = fe.empty()

        return featurevectors
        # return np.concatenate(featurevectors)
