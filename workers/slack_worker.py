import datetime
import time

from slackclient import SlackClient

from helpers import config_helper
from helpers import slack_helper
from helpers import utils
from helpers import voltdb_helper
from helpers import timesten_helper
from helpers import altibase_helper
from helpers.store import SlackStore
from helpers.store import WorkerStore


def run(config, worker_name, verbose, queue_resource):
    slack_store = SlackStore(config)
    slack_store.verbose = verbose

    maybe_workers = config_helper.get_supported_databases(config)
    dict_workers = {worker_name: WorkerStore(config, worker_name)
                    for worker_name in maybe_workers
                    if config_helper.is_worker_active(config, worker_name)}

    slack_store.slack_client = SlackClient(slack_store.slack_token)
    slack_helper.join_channel(slack_store, slack_store.slack_channel_name)

    while True:
        try:
            if slack_store.slack_client.rtm_connect():
                print("{} connected to the {}. Polling messages. . .".format(worker_name,
                                                                             slack_store.slack_channel_name))
                while True:
                    try:
                        # read slack
                        userid, channel_name, has_my_hostname, target_hostname, maybe_command = parse_slack_output(
                            slack_store,
                            slack_store.slack_client.rtm_read())

                        # if there is a message to bot or bot's name mentioned
                        if channel_name and userid:
                            if slack_store.verbose:
                                print("Channel: {}, HasMyHostname: {} Maybe Command: {}".format(channel_name,
                                                                                                has_my_hostname,
                                                                                                maybe_command))

                            # message contains a db command
                            yes_handle, worker_store = should_handle_command(slack_store, dict_workers, userid,
                                                                             channel_name, has_my_hostname,
                                                                             maybe_command)
                            if yes_handle:
                                slack_helper.send_wait_message(slack_store, "slack", userid)
                                handle_command(slack_store, worker_store, userid, maybe_command, channel_name)

                            # the message is a command but some other worker needs to process it
                            yes_request = False
                            if not yes_handle:
                                yes_request, queue_message = should_request_command(config, slack_store,
                                                                                    has_my_hostname, maybe_command)
                                if yes_request:
                                    slack_helper.send_wait_message(slack_store, "slack", userid)
                                    queue_put_request(slack_store, queue_resource, queue_message, userid)

                            # send user a friendly message about available commands
                            if not any([yes_handle, yes_request]) \
                                    and not is_valid_command(slack_store, maybe_command) \
                                    and slack_store.slack_send_help_msg:
                                message = "{mention_text} not sure what you mean.\nCommands:\n" + \
                                          slack_helper.get_avail_command_str(slack_store)
                                slack_helper.send_message_to_user(slack_store, message, "slack", userid)
                    except Exception as e:
                        ex = "Exception: {} @slack_client.rtm_read: {}".format(worker_name, e)
                        print(ex)
                        slack_store.slack_client.rtm_connect()
                    finally:
                        time.sleep(slack_store.seconds_sleep_after_slack_poll)
            else:
                print("Connection failed. Invalid Slack token or bot ID?")
        except Exception as e:
            ex = "Exception: {} @run: {}".format(worker_name, e)
            print(ex)
        finally:
            time.sleep(slack_store.seconds_sleep_after_slack_poll)


def parse_slack_output(slack_store, slack_rtm_output):
    output_list = slack_rtm_output
    has_my_hostname = False
    target_hostname = None
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output:
                if slack_store.verbose:
                    print("text: " + output['text'])
                # return text after the @ mention, whitespace removed
                as_mention = ""
                has_bot = slack_store.slack_mention_bot in output['text']
                has_my_hostname = slack_store.hostname in output['text']
                target_hostname = parse_target_hostname(output['text'])
                if has_bot:
                    as_mention = slack_store.slack_mention_bot
                if not has_bot and slack_store.bot_cmd_start in output['text']:
                    has_bot = True
                    as_mention = slack_store.bot_cmd_start
                if not has_bot and slack_store.slack_bot_name in output['text']:
                    has_bot = True
                    as_mention = slack_store.slack_bot_name
                if has_bot and "bot_id" not in output:
                    userid = ""
                    try:
                        userid = output["user"]
                    except Exception as e:
                        ex = "Exception @parse_slack_output: %s" % e
                        print(ex)
                    return userid, output['channel'], has_my_hostname, target_hostname, \
                           output['text'].split(as_mention)[
                               1].strip().lower()
    return None, None, None, None, None


def parse_target_hostname(output_text):
    try:
        # !kerata omsdev1-altibase-status
        hostname_command = (output_text.split())[1]  # omsdev1-altibase-status
        maybe_hostname = hostname_command.split('-')[0]  # omsdev1
        return maybe_hostname
    except Exception as e:
        return None


def is_valid_command(slack_store, maybe_command):
    return maybe_command and maybe_command in slack_store.dict_commands


def should_handle_command(slack_store, dict_workers, userid, channel_name, has_my_hostname, maybe_command):
    if maybe_command in slack_store.dict_commands:
        command_worker_name = slack_store.dict_commands[maybe_command]
        if has_my_hostname and command_worker_name in dict_workers:
            if dict_workers[command_worker_name].is_active:
                return True, dict_workers[command_worker_name]
        else:
            pass  # worker config does not exist in the current instance
    return False, None


def handle_command(slack_store, worker_store, userid, command, channel_name):
    cmd_parsed = utils.command_without_hostname(slack_store.hostname, command)

    helper_func = None
    if cmd_parsed == "voltdb-status":
        helper_func = voltdb_helper.get_voltdb_status
    elif cmd_parsed == "timesten-status":
        helper_func = timesten_helper.get_timesten_status
    elif cmd_parsed == "altibase-status":
        helper_func = altibase_helper.get_altibase_status
    if helper_func:
        do_func(helper_func, slack_store, worker_store, userid, command, channel_name)


def do_func(func, slack_store, worker_store, userid, command, channel_name):
    error, result = func(worker_store)
    if error:
        msg = slack_helper.format_error_message(slack_store.hostname,
                                                worker_store.worker_name,
                                                datetime.datetime.now(),
                                                result)
        if slack_store.verbose:
            print(msg)
        slack_helper.send_message(slack_store, msg, worker_store.worker_name)
    else:
        msg = ""
        for m in result:
            msg += m + "\n"

        if slack_store.verbose:
            print("\n" + msg)
        slack_helper.send_message(slack_store, msg, worker_store.worker_name)


def should_request_command(config, slack_store, has_my_hostname, queue_message):
    if has_my_hostname and queue_message in slack_store.dict_commands:
        maybe_resource = slack_store.dict_commands[queue_message]
        queue_message = utils.command_without_hostname(slack_store.hostname, queue_message)
        if maybe_resource == "resource" and config_helper.is_resource_notification_active(config, queue_message):
            return True, queue_message
    return False, None


def queue_put_request(slack_store, queue_resource, queue_message, userid):
    queue_resource.put((queue_message, userid))
