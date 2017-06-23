import datetime
import numpy as np
from psutil import virtual_memory, cpu_percent, disk_usage

from helpers import utils


def mem_percents_logspaced(start_percent=None, end_percent=90, bins_count=30):
    if not start_percent:
        start_percent = virtual_memory().percent + 1
    logspaced = np.logspace(np.log10(start_percent), np.log10(end_percent), bins_count)
    return logspaced


def disk_percents_logspaced(start_percent=None, end_percent=90, bins_count=30):
    if not start_percent:
        start_percent = virtual_memory().percent
    logspaced = np.logspace(np.log10(start_percent), np.log10(end_percent), bins_count)
    return logspaced


def current_mem_percent(resource_store):
    resource_store.mem_time_last_run = datetime.datetime.now()
    return virtual_memory().percent


def next_threshold(percents_logspaced, current):
    greater_values = percents_logspaced[np.where(percents_logspaced > current)]
    try:
        return round(greater_values[0], 2)
    except:
        return current


def str_current_mem_usage(resource_store):
    msg = "\n".join(["{hostname} @{time_last_measure}".format(hostname=resource_store.hostname,
                                                              time_last_measure=utils.time_to_str(
                                                                  resource_store.mem_time_last_run)),
                     "".join(["Current memory usage: %", str(resource_store.mem_last_percent)]),
                     "".join(["Next notification threshold: %", str(resource_store.mem_threshold_next_percent)]),
                     "---------------------------------------------"
                     ])
    return msg
