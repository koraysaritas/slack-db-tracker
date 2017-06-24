import collections
import datetime
from copy import copy

from numpy import logspace, log10, where
from psutil import virtual_memory, cpu_percent, disk_partitions, disk_usage

from helpers import slack_helper
from helpers import utils


def mem_percents_logspaced(start_percent=None, end_percent=90, bins_count=30):
    if not start_percent:
        start_percent = virtual_memory().percent + 1
    logspaced = logspace(log10(start_percent), log10(end_percent), bins_count)
    return logspaced


def disk_percents_logspaced(start_percent=None, end_percent=90, bins_count=30):
    if not start_percent:
        start_percent = virtual_memory().percent
    logspaced = logspace(log10(start_percent), log10(end_percent), bins_count)
    return logspaced


def current_mem_percent(resource_store):
    resource_store.mem_time_last_run = datetime.datetime.now()
    return virtual_memory().percent


def current_cpu_percent(resource_store):
    resource_store.cpu_time_last_run_local = datetime.datetime.now()
    resource_store.cpu_time_last_run_utc = datetime.datetime.now().utcnow()
    return cpu_percent(interval=1, percpu=True)


def current_disk_percent(resource_store, filter_by_threshold=False):
    # physical devices only
    dfkh = [(dp.device, dp.mountpoint, disk_usage(dp.mountpoint).percent) for dp in disk_partitions(all=False)]
    if filter_by_threshold:
        dfkh = [df for df in dfkh if df[2] > resource_store.disk_usage_percent_threshold]
    return dfkh if len(dfkh) > 0 else None


def cpu_save_current_usage(resource_store, current_cpu_usage, cpu_time_last_run_utc):
    try:
        for t in range(resource_store.logical_cpu_count):
            resource_store.cpu_circular_buffer[t].append((current_cpu_usage[t], cpu_time_last_run_utc))
    except Exception as e:
        ex = "Exception @cpu_save_current_usage: %s" % e
        print(ex)


def process_cpu_ring_buffer(resource_store):
    should_notify_cpu_usage = False
    cpu_gone_wild = []  # (logical_cpu_id, copy_of_ring_buffer)

    for t in range(resource_store.logical_cpu_count):
        num_above_threshold = sum(prcnt >= resource_store.cpu_usage_percent_threshold
                                  for prcnt, _ in resource_store.cpu_circular_buffer[t])

        if num_above_threshold >= resource_store.cpu_notification_threshold_count:
            should_notify_cpu_usage = True
            cpu_gone_wild.append((t, copy(resource_store.cpu_circular_buffer[t])))

    return should_notify_cpu_usage, cpu_gone_wild


def get_cpu_ring_buffer_snapshot(resource_store):
    # (logical_cpu_id, copy_of_ring_buffer)
    snapshot = [(t, copy(resource_store.cpu_circular_buffer[t]))
                for t in range(resource_store.logical_cpu_count)]
    return snapshot


def to_friendly_cpu_notification_message(resource_store, id_and_buff):
    try:
        msg = []
        header = "\n".join(["{} @{}".format(resource_store.hostname, utils.time_to_str(datetime.datetime.now())),
                            "CPU usage threshold percent: %{}".format(str(resource_store.cpu_usage_percent_threshold)),
                            "Num. occurrences to trigger a notification: {}".format(
                                str(resource_store.cpu_notification_threshold_count))
                            ])
        msg.extend(["~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"])
        for cpu_id, ring_buffer in id_and_buff:
            msg.extend(["{} Core #{}\t%{}\t@{}".format(resource_store.hostname,
                                                       "%#02d" % (cpu_id + 1),
                                                       "%#04.1f" % percent,
                                                       utils.datetime_to_slang(timestamp))
                        for percent, timestamp in ring_buffer])
            msg.extend(["~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"])

        msg = "\n".join([header,
                         "\n".join(m for m in msg)])
        return msg
    except Exception as e:
        ex = "Sorry, I've failed @to_friendly_cpu_notification_message\n{}".format(e)
        print(ex)
        return ex


def next_threshold(percents_logspaced, current):
    greater_values = percents_logspaced[where(percents_logspaced > current)]
    try:
        return round(greater_values[0], 2)
    except:
        return current


def to_friendly_mem_notification_message(resource_store):
    msg = "\n".join(["{hostname} @{time_last_measure}".format(hostname=resource_store.hostname,
                                                              time_last_measure=utils.time_to_str(
                                                                  resource_store.mem_time_last_run)),
                     "".join(["Current memory usage: %", str(resource_store.mem_last_percent)]),
                     "".join(["Next notification threshold: %", str(resource_store.mem_threshold_next_percent)])
                     ])
    return msg


def to_friendly_disk_notification_message(resource_store, dfkh):
    try:
        msg = []
        header = "\n".join(["{} @{}".format(resource_store.hostname, utils.time_to_str(datetime.datetime.now())),
                            "Disk usage threshold percent: %{}".format(
                                str(resource_store.disk_usage_percent_threshold)),
                            ])
        msg.extend(["~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"])
        for device, mountpoint, disk_percent in dfkh:
            msg.extend(["{}\nDevice: {}\nMount Point: {}\nUsed: %{}".format(resource_store.hostname,
                                                                            device,
                                                                            mountpoint,
                                                                            "%#04.1f" % disk_percent)])
            msg.extend(["~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"])

        msg = "\n".join([header,
                         "\n".join(m for m in msg)])
        return msg
    except Exception as e:
        ex = "Sorry, I've failed @to_friendly_disk_notification_message\n{}".format(e)
        print(ex)
        return ex


def send_friendly_message(slack_store, friendly_message, userid):
    if userid:
        slack_helper.send_message_to_user(slack_store, friendly_message, "resource", userid)
    else:
        slack_helper.send_message(slack_store, friendly_message, "resource")
