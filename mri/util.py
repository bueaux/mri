from itertools import ifilter, izip
from operator import add

from mri import _entropy

BLOCK_LEN = _entropy.BLOCK_LEN

def generate_hex_ticks(ticks, max):
    mask = 0xfffffff

    # Find the largest bit mask we can use without reducing the number
    # of ticks by much less than a half.
    # Worse case scenario is we get the original mask.
    ticks = map(int, ticks)
    while mask:
        tnew = [ t&(~mask) for t in ticks ]
        if len(set(tnew)) >= 0.45*len(ticks):
            tnew = sorted(list(set(tnew)))
            ticks = range(0,ticks[-1],tnew[1])
            break
        mask >>= 4

    # If there's not enough ticks, double them.
    while len(ticks) < 6:
        half = ticks[1]/2
        ticks = [ [t,t+half] for t in ticks ]
        ticks = reduce(add, ticks)

    # Truncate at the maximum point of the graph.
    return filter(lambda x: x<max, ticks)

def scale_down(values, num):
    if len(values) < num:
        return values

    # Reducing the range of values to a fixed width by accurately averaging
    # despite the possibility that multiple of the the shorter length doesn't evenly 
    # fit into the larger one.
    #
    # This is similar to integer line drawing algorithm using antialiasing
    # in that we track an integral part and a fractional part
    # of a ratio.

    intg = width_intg = len(values)/num
    frac = width_frac = len(values)%num
    
    bin = 0.0
    count = 0.0
    output = []
    values = (v for v in values)
    for n in xrange(num):
        while intg:
            bin += values.next()
            count += 1
            intg -= 1

        intg += width_intg
        frac += width_frac
        if frac > num:
            frac -= num
            intg += 1

        # If there is a fractional component, we calculate it's contribution
        # to the average.
        if frac:
            weight = float(frac)/num
            x = values.next()
            bin += weight*x
            count += weight
            output.append(bin/count)
            bin = (1-weight)*x
            intg -= 1
            count = 1-weight
        else:
            output.append(bin/count)
            count = 0.0
            bin = 0.0

    return output

def filter_zero(axis, data):
    return zip(*ifilter(lambda x: x[1] != 0.0, izip(axis, data)))