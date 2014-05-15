from functools import partial

from mri import _entropy

BLOCK_LEN = _entropy.BLOCK_LEN

def entropy(data, **kwargs):
    length = kwargs.get('length', 512)
    index = kwargs.get('index', 0)
    retsel = kwargs.get('retsel', 0)

    return _entropy.entropy512(data, length, index, retsel)

def entropy_file(file_, **kwargs):
    entropy_list = []
    if isinstance(file_, str):
        fd = open(file_, 'rb')
    else:
        fd = file_
    blk = int(BLOCK_LEN)
    for data in iter(partial(fd.read, blk), ''):
        H = entropy(data)
        entropy_list.append(H)

    return entropy_list

def count_dwords_in_range(data, range_):
    return _entropy.count_dword_in_range(data, range_[0], range_[1])

def offset_of_dwords_in_range(data, range_):
    return _entropy.offset_of_dwords_in_range(data, range_[0], range_[1])

def offset_of_qwords_in_range(data, range_):
    return _entropy.offset_of_qwords_in_range(data, range_[0], range_[1])

def entropy_profile(entropy_points):
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    L = len(chars)-1

    return ''.join([ chars[int(e*L)] for e in entropy_points ])