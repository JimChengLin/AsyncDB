from gzip import compress, decompress
from io import BytesIO
from pickle import dumps, load, loads
from struct import pack, unpack

OP = b'\x00'
ED = b'\x01'


class IndexNode:
    def __init__(self, is_leaf=True, file: BytesIO = None):
        self.ptr = 0
        self.size = 0

        if file is None:
            self.is_leaf = is_leaf
            self.keys = []
            self.ptrs_value = []
            if not is_leaf:
                self.ptrs_child = []
        else:
            self.load(file)

    def __bytes__(self):
        result = dumps(compress(dumps((self.is_leaf, self.keys)))) + b''.join(pack('Q', ptr) for ptr in self.ptrs_value)
        if not self.is_leaf:
            result += b''.join(pack('Q', ptr) for ptr in self.ptrs_child)
        self.size = len(result)
        return result

    def load(self, file: BytesIO):
        self.ptr = file.tell()
        self.is_leaf, self.keys = loads(decompress(load(file)))

        ptr_num = len(self.keys)
        if not self.is_leaf:
            ptr_num += (ptr_num + 1)
        ptrs = unpack('Q' * ptr_num, file.read(8 * ptr_num))

        if self.is_leaf:
            self.ptrs_value = list(ptrs)
        else:
            ptr_num //= 2
            self.ptrs_value = list(ptrs[:ptr_num])
            self.ptrs_child = list(ptrs[ptr_num:])
        self.size = file.tell() - self.ptr

    def dump(self, file: BytesIO):
        self.ptr = file.tell()
        file.write(bytes(self))

    def clone(self):
        result = IndexNode(is_leaf=self.is_leaf)
        result.ptr = self.ptr
        result.size = self.size

        result.keys = self.keys[:]
        result.ptrs_value = self.ptrs_value[:]
        if not result.is_leaf:
            result.ptrs_child = self.ptrs_child[:]
        return result

    def nth_child_ads(self, n: int) -> int:
        assert self.ptr > 0 and self.size > 0 and not self.is_leaf
        # sub_num = val_num + 1
        return self.ptr + self.size - (len(self.keys) + 1 - n) * 8

    def nth_value_ads(self, n: int) -> int:
        assert self.ptr > 0 and self.size > 0
        tail = self.ptr + self.size if self.is_leaf else self.nth_child_ads(0)
        return tail - (len(self.keys) - n) * 8


class ValueNode:
    def __init__(self, key=None, value=None, file: BytesIO = None):
        self.ptr = 0
        self.size = 0

        if file is None:
            self.key = key
            self.value = value
        else:
            self.load(file)

    def __bytes__(self):
        assert self.key is not None
        # 0删除 1正常
        result = ED + dumps((self.key, self.value))
        self.size = len(result)
        return result

    def load(self, file: BytesIO):
        self.ptr = file.tell()
        indicator = file.read(1)
        assert indicator in (OP, ED)
        self.key, self.value = load(file)
        self.size = file.tell() - self.ptr

    def dump(self, file: BytesIO):
        self.ptr = file.tell()
        file.write(bytes(self))
