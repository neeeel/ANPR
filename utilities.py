import datetime
import pandas as pd
import numpy as np

def bin_time(t):
    ###
    ### takes a timedelta t
    ### put the timedelta t into a bin , basically flooring it to the nearest 15 seconds
    ### so 00:01:27 would return a bin of 00:01:15
    ###
    seconds = t.seconds - t.seconds%15
    return datetime.timedelta(seconds = seconds)

def format_timedelta(td):
    if pd.isnull(td):
        return 0
    minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
    hours, minutes = divmod(minutes, 60)
    return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)

def date_to_time(d):
    if d is None:
        return "00:00:00"
    if pd.isnull(d):
        return "00:00:00"
    try:
        return d.strftime("%H:%M:%S")
    except Exception as e:
        try:
            return d.strftime("%H:%M")
        except Exception as e:
            return "00:00:00"


