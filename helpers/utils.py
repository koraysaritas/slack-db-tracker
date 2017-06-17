import datetime


def time_to_str(a_time):
    return a_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def from_timestamp_to_datetime(s):
    return datetime.datetime.fromtimestamp(int(s) / 1000)


def format_error_message(worker_name, time_last_error, last_error):
    header = "{worker_name}@{time}".format(worker_name=worker_name,
                                           time=time_to_str(time_last_error))
    return "\n".join([header, last_error])


def seconds_since_last_notification(worker_store):
    return 0 if not worker_store.time_last_notification else (
        datetime.datetime.now() - worker_store.time_last_notification).total_seconds()


def should_send_error_message(worker_store):
    long_enough = (seconds_since_last_notification(worker_store) > int(worker_store.seconds_error_msg_flood_protection))
    return not worker_store.time_last_notification or long_enough


def command_without_hostname(hostname, command):
    # !botname hostname-command --> command
    return command.split(hostname)[1][1:]
