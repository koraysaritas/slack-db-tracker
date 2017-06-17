import datetime
import re
import subprocess

from helpers import slack_helper
from helpers import utils
from helpers import config_helper


def process_error(slack_store, worker_store):
    try:
        seconds_since_last_notification = utils.seconds_since_last_notification(worker_store)
        print("seconds_since_last_notification: " + str(seconds_since_last_notification))

        if utils.should_send_error_message(worker_store):
            err = utils.format_error_message(worker_store.worker_name, worker_store.time_last_error,
                                             worker_store.last_error)
            slack_helper.send_message(slack_store, err, worker_store.worker_name)
            worker_store.time_last_notification = datetime.datetime.now()
    except Exception as e:
        ex = "Exception: {} @process_error: {}".format(worker_store.worker_name, e)
        print(ex)


def get_timesten_status(worker_store):
    try:
        exec_str_format = '{bin_status_path} {conn_str}'
        exec_str = exec_str_format.format(
            bin_status_path=config_helper.path_join(worker_store.bin_dir, worker_store.bin_status),
            conn_str=worker_store.conn_str
        )
        print(exec_str)

        c1 = exec_str
        p1 = subprocess.Popen(c1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p1.communicate()

        if p1.returncode != 0:
            err = re.sub(' +', ' ', stderr.decode("utf-8"))
            return True, err
        else:
            result = ["{0}: {1}".format("Hostname", worker_store.hostname)]
            i = 0
            for line in stdout.splitlines():
                if line and len(line) > 0:
                    line = line.decode()
                    if "No TimesTen server running" in str(line):
                        result.append(line)
                        return True, result
                    if not line.startswith("--"):
                        result.append(line)
                        i += 1
                        if i >= 4:
                            break
            return False, result
    except Exception as e:
        ex = "Exception: {} @get_timesten_status: {}".format(worker_store.worker_name, e)
        print(ex)
        return True, ex
