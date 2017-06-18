import time

from slackclient import SlackClient

from helpers import slack_helper
from helpers import voltdb_helper
from helpers.store import SlackStore
from helpers.store import WorkerStore


# export PATH=$PATH:$HOME/voltdb/voltdb-ent-7.0/bin
# sudo bash -c "echo never > /sys/kernel/mm/transparent_hugepage/enabled"
# sudo bash -c "echo never > /sys/kernel/mm/transparent_hugepage/defrag"
# sudo /home/volt/voltdb/voltdb-ent-7.0/bin/voltdb init
# sudo /home/volt/voltdb/voltdb-ent-7.0/bin/voltdb start
# sudo /home/volt/voltdb/voltdb-ent-7.0/bin/voltdb stop

def run(config, worker_name):
    slack_store = SlackStore(config)
    worker_store = WorkerStore(config, worker_name)

    slack_store.slack_client = SlackClient(slack_store.slack_token)
    slack_helper.join_channel(slack_store, slack_store.slack_channel_name)

    while True:
        try:
            error, result = voltdb_helper.get_voltdb_status(worker_store)
            if error:
                slack_helper.process_error(slack_store, worker_store, result)
            else:
                print("")
                msg = ""
                for m in result:
                    msg += m + "\n"
                print(msg)
                if worker_store.has_error:
                    slack_helper.send_message(slack_store, msg, worker_name)
                    worker_store.time_last_notification = None
                worker_store.has_error = False
                worker_store.time_last_error = None
                worker_store.last_error = None
        except Exception as e:
            ex = "Exception: {} @run: {}".format(worker_name, e)
            print(ex)
        finally:
            time.sleep(worker_store.seconds_sleep_after_status_check)
