import os
import re
import subprocess

from helpers import config_helper
from helpers import utils


def get_altibase_status(worker_store):
    try:
        path_to_status_sql = os.path.join(os.getcwd(), "queries", "altibase_instance_status.sql")
        conn_str = " ".join([worker_store.conn_str, "-f", path_to_status_sql])

        exec_str_format = '{bin_status_path} {conn_str}'
        exec_str = exec_str_format.format(
            bin_status_path=config_helper.path_join(worker_store.bin_dir, worker_store.bin_isql),
            conn_str=conn_str
        )
        if worker_store.verbose:
            print("\n" + exec_str)

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

                if worker_store.verbose:
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
