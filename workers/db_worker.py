import time

from slackclient import SlackClient

from helpers import slack_helper
from helpers import voltdb_helper
from helpers import timesten_helper
from helpers import altibase_helper
from helpers.store import SlackStore
from helpers.store import WorkerStore


# VOLTDB
# export PATH=$PATH:$HOME/voltdb/voltdb-ent-7.0/bin
# sudo bash -c "echo never > /sys/kernel/mm/transparent_hugepage/enabled"
# sudo bash -c "echo never > /sys/kernel/mm/transparent_hugepage/defrag"
# sudo /home/volt/voltdb/voltdb-ent-7.0/bin/voltdb init
# sudo /home/volt/voltdb/voltdb-ent-7.0/bin/voltdb start
# sudo /home/volt/voltdb/voltdb-ent-7.0/bin/voltdb stop

# TIMESTEN
# ./ttdaemonadmin -stop
# ./ttdaemonadmin -start
# ./ttdaemonadmin -startserver
# ./ttdaemonadmin -stopserver

# ALTIBASE
# export ALTIBASE_HOME=/home/altibase/ALTIBASE_COMMUNITY_EDITION_SERVER
# export ALTIBASE_PORT_NO=20300
# export PATH=${ALTIBASE_HOME}/bin:${PATH}
# export LD_LIBRARY_PATH=${ALTIBASE_HOME}/lib:${LD_LIBRARY_PATH}
# export CLASSPATH=${ALTIBASE_HOME}/lib/Altibase.jar:${CLASSPATH}
# THIS DOES NOT WORK: echo "SELECT * FROM V$INSTANCE;" | ./isql -s 127.0.0.1 -u <USERNAME> -p <PASSWORD>
# ERROR:
# >> [ERR-31031 : Table or view was not found :
# >> 0001 : SELECT * FROM V
# WORKAROUND: ./isql -s 127.0.0.1 -u <USERNAME> -p <PASSWORD> -f altibase_instance_status.sql


def run(config, worker_name, verbose):
    slack_store = SlackStore(config)
    worker_store = WorkerStore(config, worker_name)

    slack_store.verbose = verbose
    worker_store.verbose = verbose

    func_get_db_status = None
    if worker_name == "voltdb":
        func_get_db_status = voltdb_helper.get_voltdb_status
    elif worker_name == "timesten":
        func_get_db_status = timesten_helper.get_timesten_status
    elif worker_name == "altibase":
        func_get_db_status = altibase_helper.get_altibase_status

    if not func_get_db_status:
        raise TypeError("DB status function must be set. Worker: {}".format(worker_name))

    slack_store.slack_client = SlackClient(slack_store.slack_token)
    slack_helper.join_channel(slack_store, slack_store.slack_channel_name)

    while True:
        try:
            error, result = func_get_db_status(worker_store)
            if error:
                slack_helper.process_error(slack_store, worker_store, result)
            else:
                msg = ""
                for m in result:
                    msg += m + "\n"
                if verbose:
                    print("\n" + msg)
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
