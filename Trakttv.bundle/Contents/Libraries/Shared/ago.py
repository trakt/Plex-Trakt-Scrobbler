from datetime import datetime
from datetime import timedelta

def delta2dict( delta ):
    """Accepts a delta, returns a dictionary of units"""
    delta = abs( delta )
    return { 
        'year'   : delta.days / 365 ,
        'day'    : delta.days % 365 ,
        'hour'   : delta.seconds / 3600 ,
        'minute' : (delta.seconds / 60) % 60 ,
        'second' : delta.seconds % 60 ,
        'microsecond' : delta.microseconds
    }

def human(dt, precision=2, past_tense='%s ago', future_tense='in %s'):
    """Accept a datetime or timedelta, return a human readable delta string"""
    delta = dt
    if type(dt) is not type(timedelta()):
        delta = datetime.now() - dt
     
    the_tense = past_tense
    if delta < timedelta(0):
        the_tense = future_tense

    d = delta2dict( delta )
    hlist = [] 
    count = 0
    units = ( 'year', 'day', 'hour', 'minute', 'second', 'microsecond' )
    for unit in units:
        if count >= precision: break # met precision
        if d[ unit ] == 0: continue # skip 0's
        s = '' if d[ unit ] == 1 else 's' # handle plurals
        hlist.append( '%s %s%s' % ( d[unit], unit, s ) )
        count += 1
    human_delta = ', '.join( hlist )
    return the_tense % human_delta

