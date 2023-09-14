import math

def roundToBase(value, base):
    if base == 0:
        return value
    vb = value / base
    if (vb > 0):
        vb = math.ceil(vb)
    else:
        vb = math.floor(vb)
    return vb * base
