import datetime
import re
import os
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


def get_altibase_status(worker_store):
    try:
        path_to_status_sql = os.path.join(os.getcwd(), "queries", "altibase_instance_status.sql")
        conn_str = " ".join([worker_store.conn_str, "-f", path_to_status_sql])

        exec_str_format = '{bin_status_path} {conn_str}'
        exec_str = exec_str_format.format(
            bin_status_path=config_helper.path_join(worker_store.bin_dir, worker_store.bin_isql),
            conn_str=conn_str
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
            lines = [line.decode() for line in stdout.splitlines()]
            while i < len(lines) and not lines[i].startswith("iSQL>"):
                i += 1
            if i + 3 < len(lines):
                columns = lines[i + 1].split()
                datarow = lines[i + 3].split()

                print("")
                print(columns)
                print(datarow)

                for column, data in zip(columns, datarow):
                    if column == "STARTUP_TIME_SEC":
                        result.append("Startup time @{}".format(utils.from_epoch_to_datetime(data)))
                    elif column == "WORKING_TIME_SEC":
                        result.append("Started working {}.".format(utils.seconds_ago_to_slang(int(data))))
                    elif column == "STARTUP_PHASE":
                        result.append("Startup Phase: {}".format(data))
                    else:
                        result.append("{}: {}".format(column, data))

            return False, result
    except Exception as e:
        ex = "Exception: {} @get_altibase_status: {}".format(worker_store.worker_name, e)
        print(ex)
        return True, ex
