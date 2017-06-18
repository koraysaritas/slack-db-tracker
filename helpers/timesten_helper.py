import re
import subprocess

from helpers import config_helper


def get_timesten_status(worker_store):
    try:
        exec_str_format = '{bin_status_path} {conn_str}'
        exec_str = exec_str_format.format(
            bin_status_path=config_helper.path_join(worker_store.bin_dir, worker_store.bin_status),
            conn_str=worker_store.conn_str
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
