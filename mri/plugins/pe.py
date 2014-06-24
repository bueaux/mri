import os
import re
import pefile

from functools import partial
from collections import defaultdict

from mri import _entropy
from mri.util import filter_zero
from mri.entropy import BLOCK_LEN, entropy
from mri.entropy import offset_of_dwords_in_range, offset_of_qwords_in_range

def generate_graph_data(filename):
    factor = 2
    graph_data = {}

    _entropy.init(256.0)
    pe = pefile.PE(filename)
    H, Z, P = _get_heuristics(filename, pe)
    R = pointers_to_references(P, pe, factor)
    plots = graph_data['plots'] = []
    graph_data['legend_order'] = [ 'entropy','zeros','ptrs','refs' ]

    xaxis = [ BLOCK_LEN*off for off in xrange(len(H)) ]

    # zeros------------------------------
    zeros = {
        'type': 'plot',
        'label': 'zeros',
        'color': 'g',
        'fill': True,
        'fillalpha': 0.15,
        'data': (xaxis,Z),
    }
    plots.append(zeros)

    # pointers---------------------------
    P = [ float(len(p)) for p in P ]
    P = _condense_pointers(P, factor)

    # Custom axis
    temp_axis = [ BLOCK_LEN*o for o in xrange(0, len(P), factor) ]
    width = (BLOCK_LEN*factor)/2.0
    pointers = {
        'type': 'bar',
        'label': 'ptrs',
        'color': 'crimson',
        'edgecolor': 'crimson',
        'width': width,
        'data': filter_zero(temp_axis, P),
    }
    plots.append(pointers)

    # references--------------------------
    # Custom axis shifted over by half an enlarged block length
    temp_axis = [ (BLOCK_LEN*o + width) for o in xrange(0,len(R),factor) ]
    references = {
        'type': 'bar',
        'label': 'refs',
        'color': 'm',
        'edgecolor': 'm',
        'width': width,
        'data': filter_zero(temp_axis, R),
    }
    plots.append(references)

    #entropy-------------------------------
    entropy = {
        'type': 'plot',
        'label': 'entropy',
        'color': 'b',
        'linewidth': lambda th: 2.0 if not th else 1.3,
        'data': (xaxis,H),
    }
    plots.append(entropy)

    graph_data['xlim'] = (0, xaxis[-1])
    graph_data['ylim'] = (0.0,1.02)
    graph_data['points'] = _get_points(pe)
    graph_data['boundaries'] = _get_boundaries(pe, os.stat(filename).st_size)

    return graph_data

def _get_heuristics(filename, pe, **kwargs):
    fd = open(filename, 'rb')

    start = kwargs.get('start', 0)
    length = kwargs.get('length', 0xffffffff)

    imbase = pe.OPTIONAL_HEADER.ImageBase
    imsize = pe.OPTIONAL_HEADER.SizeOfImage
    image=(imbase, imbase+imsize)

    if pe.FILE_HEADER.Machine in [ 0x8664 ]:
        pe_type = 'pe64'
    elif pe.FILE_HEADER.Machine in [ 0x14c ] :
        pe_type = 'pe32'

    entropy_list = []
    zeros_list = []
    refs_list = []
    ptrs_list = []

    if start:
        fd.seek(start)

    if pe_type == 'pe32':
        offset_of_ptrs_in_range = offset_of_dwords_in_range
    elif pe_type == 'pe64':
        offset_of_ptrs_in_range = offset_of_qwords_in_range
    else:
        offset_of_ptrs_in_range = lambda x,y: []

    offset = start
    blk = int(BLOCK_LEN)
    for data in iter(partial(fd.read, blk), ''):
        H, Z = entropy(data, retsel=1)
        P = offset_of_ptrs_in_range(data, image)
        entropy_list.append(H)
        zeros_list.append(Z/BLOCK_LEN)
        ptrs_list.append(P)
        length -= BLOCK_LEN
        if length <= 0:
            break

    return entropy_list, zeros_list, ptrs_list 

def _get_boundaries(pe, filesize):
    boundaries = []
    rex = re.compile(r'([^\x00]*)\x00*$')

    appended_offset = 0
    nsec = len(pe.sections)
    for n, s in enumerate(sorted(pe.sections, key=lambda s: -s.PointerToRawData)):
        name = s.Name
        m = rex.match(name)
        if m is not None:
            name = m.group(1)
        if name == '':
            name = 'sec_%d' % (nsec-n)

        end = s.PointerToRawData + s.SizeOfRawData
        if end > appended_offset:
            appended_offset = end
        B = {
            'name': name,
            'offset': s.PointerToRawData,
            'end_offset': end,
        }
        boundaries.append(B)

    if appended_offset != filesize:
        B = {
            'name': 'appended',
            'offset': appended_offset,
            'end_offset': filesize,
        }
        boundaries.append(B)

    return boundaries

def _get_points(pe):
    points = []
    eprva = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    try:
        offset = pe.get_offset_from_rva(eprva)
        pt = {
            'name': 'EP',
            'offset': offset,
        }
        points.append(pt)
    except pefile.PEFormatError:
        pass
    return points


def _condense_pointers(pointers, factor=4):
    ptrs = defaultdict(float)
    ptrcounts = []
    m = 0
    offset = 0
    for temp in pointers:
        q = int(offset/BLOCK_LEN/factor)*BLOCK_LEN*factor

        ptrs[q] += temp
        offset += BLOCK_LEN
        if q > m:
            m = int(q)

    for q in xrange(0,m+1,int(BLOCK_LEN)*factor):
        val = 0 if q not in ptrs else float(ptrs[q])
        ptrcounts.append(val/BLOCK_LEN)

    return ptrcounts

def pointers_to_references(pointers, pe, factor=4):
    base = pe.OPTIONAL_HEADER.ImageBase
    refs = defaultdict(int)
    refcounts = []
    m = 0
    for temp in pointers:
        for off, ptr in temp:
            ptr -= base
            try:
                off = pe.get_offset_from_rva(ptr)
            except pefile.PEFormatError:
                # print "Can't convert rva: %x" % ptr
                continue

            q = int(off/BLOCK_LEN/factor)*BLOCK_LEN*factor
            if q > m:
                m = int(q)
            refs[q] += 1

    for q in xrange(0,m+1,int(BLOCK_LEN)*factor):
        val = 0 if q not in refs else refs[q]
        refcounts.append(val/BLOCK_LEN)

    return refcounts
