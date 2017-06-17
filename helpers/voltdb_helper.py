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


def get_voltdb_overview(worker_store):
    try:
        c1 = 'echo "exec @SystemInformation OVERVIEW;"'
        # c2 = 'sqlcmd' # requires: export PATH=$PATH:$HOME/voltdb/voltdb-ent-7.0/bin
        c2 = config_helper.get_isql_path(worker_store.bin_dir, worker_store.bin_isql)
        print(" | ".join([c1, c2]))

        p1 = subprocess.Popen(c1, shell=True, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(c2, stdin=p1.stdout, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p2.communicate()

        if p2.returncode != 0:
            err = re.sub(' +', ' ', stderr.decode("utf-8"))
            return True, err
        else:
            result = ["{0}: {1}".format("Hostname", worker_store.hostname)]

            for line in stdout.splitlines():
                if line and len(line) > 0:
                    for key, value in worker_store.dict_parser_isql.items():
                        column_name, regex = value
                        m = re.match(regex, str(line))
                        if m:
                            g = m.groups()[0]
                            if key == "StartTime":
                                g = utils.time_to_str(utils.from_timestamp_to_datetime(g))
                            elif key == "Uptime":
                                g = g.strip()
                            msg = "{0}: {1}".format(column_name, g)
                            result.append(msg)
            return False, result
    except Exception as e:
        ex = "Exception: {} @get_voltdb_overview: {}".format(worker_store.worker_name, e)
        print(ex)
        return True, ex
