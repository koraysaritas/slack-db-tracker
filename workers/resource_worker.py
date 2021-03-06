import time
import datetime
import collections
from multiprocessing import queues

from slackclient import SlackClient
from psutil import cpu_count

from helpers import resource_helper
from helpers import slack_helper
from helpers import utils
from helpers.store import ResourceStore
from helpers.store import SlackStore


def init_stores(slack_store, resource_store):
    slack_store.slack_client = SlackClient(slack_store.slack_token)
    slack_helper.join_channel(slack_store, slack_store.slack_channel_name)

    resource_store.mem_percents_logspaced = resource_helper.mem_percents_logspaced(start_percent=50,
                                                                                   end_percent=90,
                                                                                   bins_count=20)
    resource_store.mem_last_percent = resource_helper.current_mem_percent(resource_store)
    resource_store.mem_threshold_next_percent = resource_helper.next_threshold(resource_store.mem_percents_logspaced,
                                                                               resource_store.mem_last_percent)

    resource_store.logical_cpu_count = cpu_count(logical=True)
    resource_store.cpu_circular_buffer = [collections.deque(maxlen=resource_store.cpu_circular_buffer_maxlen)
                                          for _ in range(resource_store.logical_cpu_count)]

    print("\n".join(["Memory usage thresholds(logscaled):",
                     str(resource_store.mem_percents_logspaced)]))
    print("\nLogical CPU Count: {}".format(resource_store.logical_cpu_count))


def run(config, worker_name, verbose, queue_resource):
    slack_store = SlackStore(config)
    resource_store = ResourceStore(config)

    slack_store.verbose = verbose
    resource_store.verbose = verbose

    init_stores(slack_store, resource_store)

    while True:
        try:
            queue_message = try_get_queue_message(queue_resource)
            if queue_message:
                handle_queue_message(slack_store, resource_store, queue_message)
            if resource_store.notify_memory_usage:
                process_mem_usage(slack_store, resource_store)
            if resource_store.notify_cpu_usage:
                process_cpu_usage(slack_store, resource_store)
            if resource_store.notify_disk_usage:
                process_disk_usage(slack_store, resource_store)
        except Exception as e:
            ex = "Exception: {} @run: {}".format(worker_name, e)
            print(ex)
        finally:
            time.sleep(resource_store.seconds_sleep_after_run)


def try_get_queue_message(queue_resource):
    try:
        queue_message = queue_resource.get_nowait()
        return queue_message
    except queues.Empty:
        pass
    return None


def handle_queue_message(slack_store, resource_store, tpl_queue_message):
    queue_message, userid = tpl_queue_message
    if queue_message == "memusage":
        current_measure = resource_helper.current_mem_percent(resource_store)
        resource_store.mem_last_percent = current_measure
        friendly_message = resource_helper.to_friendly_mem_notification_message(resource_store)
        if resource_store.verbose:
            print(friendly_message)
        resource_helper.send_friendly_message(slack_store, friendly_message, userid)
    elif queue_message == "cpuusage":
        current_cpu_usage = resource_helper.current_cpu_percent(resource_store)
        resource_helper.cpu_save_current_usage(resource_store, current_cpu_usage, resource_store.cpu_time_last_run_utc)
        snapshot = resource_helper.get_cpu_ring_buffer_snapshot(resource_store)
        friendly_message = resource_helper.to_friendly_cpu_notification_message(resource_store, snapshot)
        if resource_store.verbose:
            print(friendly_message)
        resource_helper.send_friendly_message(slack_store, friendly_message, userid)
    elif queue_message == "diskusage":
        dfkh = resource_helper.current_disk_percent(resource_store, filter_by_threshold=False)
        resource_store.disk_time_last_run = datetime.datetime.now()
        friendly_message = resource_helper.to_friendly_disk_notification_message(resource_store, dfkh)
        if resource_store.verbose:
            print(friendly_message)
        resource_helper.send_friendly_message(slack_store, friendly_message, userid)


def process_mem_usage(slack_store, resource_store):
    last_threshold = resource_store.mem_threshold_next_percent
    current_measure = resource_helper.current_mem_percent(resource_store)
    resource_store.mem_time_last_run = datetime.datetime.now()
    resource_store.mem_last_percent = current_measure
    resource_store.mem_threshold_next_percent = resource_helper.next_threshold(resource_store.mem_percents_logspaced,
                                                                               current_measure)
    if current_measure > last_threshold:
        friendly_message = resource_helper.to_friendly_mem_notification_message(resource_store)

        if resource_store.verbose:
            print("\n" + friendly_message)

        if utils.should_send_resources_message(resource_store, "memusage"):
            resource_helper.send_friendly_message(slack_store, friendly_message, userid=None)
            resource_store.mem_time_last_notification = datetime.datetime.now()
        else:
            if resource_store.verbose:
                print("\nmem_time_last_notification: " +
                      utils.time_to_str(resource_store.mem_time_last_notification))
                print("seconds_since_last_notification: " +
                      str(utils.seconds_since_last_notification(resource_store.mem_time_last_notification)))


def process_cpu_usage(slack_store, resource_store):
    current_cpu_usage = resource_helper.current_cpu_percent(resource_store)
    resource_helper.cpu_save_current_usage(resource_store, current_cpu_usage, resource_store.cpu_time_last_run_utc)
    should_notify_cpu_usage, cpu_gone_wild = resource_helper.process_cpu_ring_buffer(resource_store)

    if should_notify_cpu_usage:
        friendly_message = resource_helper.to_friendly_cpu_notification_message(resource_store, cpu_gone_wild)

        if resource_store.verbose:
            print("\n" + friendly_message)

        if utils.should_send_resources_message(resource_store, "cpuusage"):
            resource_helper.send_friendly_message(slack_store, friendly_message, userid=None)
            resource_store.cpu_time_last_notification = datetime.datetime.now()
        else:
            if resource_store.verbose:
                print("\ncpu_time_last_notification: " +
                      utils.time_to_str(resource_store.cpu_time_last_notification))
                print("seconds_since_last_notification: " +
                      str(utils.seconds_since_last_notification(resource_store.cpu_time_last_notification)))


def process_disk_usage(slack_store, resource_store):
    dfkh = resource_helper.current_disk_percent(resource_store, filter_by_threshold=True)
    resource_store.disk_time_last_run = datetime.datetime.now()

    if dfkh:
        friendly_message = resource_helper.to_friendly_disk_notification_message(resource_store, dfkh)

        if resource_store.verbose:
            print("\n" + friendly_message)

        if utils.should_send_resources_message(resource_store, "diskusage"):
            resource_helper.send_friendly_message(slack_store, friendly_message, userid=None)
            resource_store.disk_time_last_notification = datetime.datetime.now()
        else:
            if resource_store.verbose:
                print("\ndisk_time_last_notification: " +
                      utils.time_to_str(resource_store.disk_time_last_notification))
                print("seconds_since_last_notification: " +
                      str(utils.seconds_since_last_notification(resource_store.disk_time_last_notification)))
