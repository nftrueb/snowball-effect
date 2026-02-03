from . import get_logger

logger = get_logger()

def clamp(value, upper, lower): 
    if value > upper: 
        return upper 
    if value < lower: 
        return lower
    return value

def clamp_upper(value, upper): 
    return upper if value > upper else value 

def clamp_lower(value, lower): 
    return lower if value < lower else value 

def increment_to_limit(value, limit):
    if value is not None: 
        value += 1 
        if value >= limit: 
            value = None 
    return value 

def decrement_to_limit(value, limit=0):
    if value is not None: 
        value -= 1 
        if value <= limit: 
            value = None 
    return value 

def multiply_tuple_by_int(tup, scalar, idx=None): 
    if idx is None: 
        return tuple([value * scalar for value in tup])
    
    if idx >= len(tup) or idx < 0: 
        logger.error(f'Invalid args when multipying tuple by scalar: tuple={tup} scalar={scalar} idx={idx}')
        return tup 
    
    l = list(tuple)
    l[idx] *= scalar 
    return tuple(l)