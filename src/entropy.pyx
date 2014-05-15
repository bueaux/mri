from libc.string cimport memset

cdef extern from "math.h":
    double log(double)

DEF NUM_SYMBOLS = 256
DEF _BLOCK_LEN = 512
BLOCK_LEN = float(_BLOCK_LEN)

cpdef double log_lookup_table[_BLOCK_LEN+1]

def init(base = 2.0):
    global log_lookup_table
    cdef int i = 1
    cdef float p_i

    log_lookup_table[0] = 0
    log_lookup_table[_BLOCK_LEN] = 0

    while i < _BLOCK_LEN:
        p_i = float(i)/_BLOCK_LEN
        log_lookup_table[i] = -(log(p_i))*p_i/log(base)
        i += 1

def entropy512(data, length_ = 512, index = 0, retsel = 0):
    """Calculate entropy of block of data

    index is the index into the data.
    retsel selects the type of return value.
        1 - return frequency of '\x00'
        2 - return all frequencies
        3 - return frequencies of \x00 and reljmp opcodes (e8,e9,eb)
        other - just return entropy.
    """
    cdef:
        int freqs[NUM_SYMBOLS], length
        unsigned char *data_ = data
        int i, x
        double H = 0

    length = length_
    if length > 512:
        raise Exception("Length must be 512 or less.")
    elif length == 0:
        return

    # Initialise array
    memset(freqs, 0, sizeof(freqs))

    data_ += index
    # Collect frequencies
    for i in range(length):
        freqs[data_[0]] += 1
        data_ += 1

    # Add up entropy
    for i in range(NUM_SYMBOLS):
        f = freqs[i]
        if f != 0:
            H += log_lookup_table[f]

    if retsel == 1:
        return H, freqs[0]
    elif retsel == 2:
        return H, [ freqs[i] for i in range(NUM_SYMBOLS) ]
    elif retsel == 3:
        return H, freqs[0], (freqs[0xeb] + freqs[0xe8] + freqs[0xe9])
    return H

def count_char(data, c, length = None):
    cdef:
        int N = 0
        char *data_ = data

    c = ord(c)

    if length is None:
        length = len(data)
    elif length > len(data):
        raise IndexError("Data_ length less than specified length")

    for i in range(length):
        if data_[0] == c:
            N += 1 
        data_ += 1

    return N

def count_dword_in_range(data, int rmin, int rmax, length = None):
    cdef:
        char *data_ = data
        int N = 0

    if length is None:
        length = len(data)
    elif length > len(data):
        raise IndexError("Data_ length less than specified length")

    for i in range(length-3):
        if rmin <= (<int *>data_)[0] < rmax:
            N += 1
        data_ += 1

    return N

def offset_of_dwords_in_range(data, unsigned int rmin, unsigned int rmax, length = None):
    cdef:
        char *data_ = data
        int N = 0
        unsigned int x

    dwords = []

    if length is None:
        length = len(data)
    elif length > len(data):
        raise IndexError("Data_ length less than specified length")

    for i in range(length-3):
        x = (<unsigned int *>data_)[0]
        if rmin <= x < rmax:
            dwords.append((i,x))
        data_ += 1

    return dwords

def offset_of_qwords_in_range(data, unsigned long long rmin, unsigned long long rmax, length = None):
    cdef:
        char *data_ = data
        int N = 0
        unsigned long long x

    qwords = []

    if length is None:
        length = len(data)
    elif length > len(data):
        raise IndexError("Data_ length less than specified length")

    for i in range(length-7):
        x = (<unsigned long long *>data_)[0]
        if rmin <= x < rmax:
            qwords.append((i,x))
        data_ += 1

    return qwords

def scale_down128(values):
    DEF OUTSCALE = 128
    cdef:
        unsigned int intg, frac, length, index
        double bin, count, x, weight
        double output[OUTSCALE], *outptr = output

    length = len(values)
    if length < OUTSCALE:
        return values

    # Reducing the range of values to a fixed width by accurately averaging
    # despite the possibility that multiple of the the shorter length doesn't evenly 
    # fit into the larger one.
    #
    # This is similar to integer line drawing algorithm
    # in that we track an integral part and a fractional part
    # of a ratio.

    intg = width_intg = length/OUTSCALE
    frac = width_frac = length%OUTSCALE
    
    bin = 0.0
    count = 0.0
    index = 0
    for n in range(OUTSCALE):
        while intg:
            bin += values[index]
            index += 1
            count += 1
            intg -= 1

        intg += width_intg
        frac += width_frac
        if frac > OUTSCALE:
            frac -= OUTSCALE
            intg += 1

        # If there is a fractional component, we calculate it's contribution
        # to the average.
        if frac:
            x = values[index]
            index += 1

            weight = float(frac)/OUTSCALE
            bin += weight*x
            count += weight
            outptr[0] = bin/count
            bin = (1-weight)*x
            intg -= 1
            count = 1-weight
        else:
            outptr[0] = bin/count
            count = 0.0
            bin = 0.0
        outptr += 1

    return [ x for x in output ]

# def rel_jmps(data, int rmin, int rmax, int offset):
#     cdef:
#         char *data_ = data
#         int N = 0
#         unsigned int jmps[BLOCK_LEN]
#         unsigned char x

#     dwords = []

#     memset(jmps, 0, sizeof(jmps))
#     if length is None:
#         length = len(data)
#     elif length > len(data):
#         raise IndexError("Data_ length less than specified length")

#     for i in range(length-4):
#         x = (<int *>data_)[0]
#         if x == 0xeb: # short rel jmp
#             jmps[i] += 1
#         elif data[0] == 0xe8:


#         if rmin <= x < rmax:
#             dwords.append((i,x))
#         data_ += 1

#     return dwords