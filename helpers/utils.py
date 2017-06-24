import datetime
import maya


def time_to_str(a_time):
    return a_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def from_timestamp_to_datetime(s):
    return datetime.datetime.fromtimestamp(int(s) / 1000)


def from_epoch_to_datetime(s):
    return datetime.datetime.fromtimestamp(int(s), datetime.timezone.utc)


def seconds_ago_to_slang(seconds):
    now = maya.now()
    return now.add(seconds=(seconds * -1)).slang_time()


def datetime_to_slang(d):
    # d is utc
    maya_date = maya.MayaDT.from_datetime(d)
    return maya_date.slang_time()


def seconds_since_last_notification(time_last_notification):
    return 0 if not time_last_notification else (
        datetime.datetime.now() - time_last_notification).total_seconds()


def should_send_error_message(worker_store):
    long_enough = (seconds_since_last_notification(worker_store.time_last_notification) >
                   int(worker_store.seconds_error_msg_flood_protection))
    return not worker_store.time_last_notification or long_enough


def command_without_hostname(hostname, command):
    # !botname hostname-command --> command
    return command.split(hostname)[1][1:]


def should_send_resources_message(resource_store, resource_type):
    if resource_type == "memusage":
        long_enough = (seconds_since_last_notification(resource_store.mem_time_last_notification) >
                       int(resource_store.seconds_error_msg_flood_protection))
        return not resource_store.mem_time_last_notification or long_enough
    elif resource_type == "cpuusage":
        long_enough = (seconds_since_last_notification(resource_store.cpu_time_last_notification) >
                       int(resource_store.seconds_error_msg_flood_protection))
        return not resource_store.cpu_time_last_notification or long_enough
    elif resource_type == "diskusage":
        long_enough = (seconds_since_last_notification(resource_store.disk_time_last_notification) >
                       int(resource_store.seconds_error_msg_flood_protection))
        return not resource_store.disk_time_last_notification or long_enough
    return False


# https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/tools/devappserver2/admin/admin_request_handler.py
def byte_size_format(value):
    byte_count = int(value)
    if byte_count == 1:
        return '1 Byte'
    elif byte_count < 1024:
        return '%d Bytes' % byte_count
    elif byte_count < 1024 ** 2:
        return '%.1f KiB (%d Bytes)' % (byte_count / 1024.0, byte_count)
    elif byte_count < 1024 ** 3:
        return '%.1f MiB (%d Bytes)' % (byte_count / 1024.0 ** 2, byte_count)
    else:
        return '%.1f GiB (%d Bytes)' % (byte_count / 1024.0 ** 3, byte_count)
