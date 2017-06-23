import time
import datetime
import re
import json
import requests
from slackclient import SlackClient
from . import utils


def send_message_to_user(slack_store, message, worker_name, userid):
    if userid in slack_store.dict_slack_userid_username:
        username = slack_store.dict_slack_userid_username[userid]
        mention_format = slack_store.mention_format
        mention_text = "" if username == "" else mention_format.format(member_id=userid)
        response = message.format(mention_text=mention_text)
        send_message(slack_store, response, worker_name)


def send_message(slack_store, message, worker_name):
    header = slack_store.request_header
    payload = json.dumps({'text': message})

    if slack_store.verbose:
        print('\nRequest to slack from {}.\nMessage: {}'.format(worker_name, message))

    response = requests.post(
        slack_store.slack_url_webhook, data=payload,
        headers=header
    )

    if response.status_code != 200:
        print('\nRequest to slack from {} has an error {}.\nResponse: {}\nMessage: {}\n'.format(
            worker_name, response.status_code, response.text, message))


def send_wait_message(slack_store, worker_name, userid):
    msg = "{mention_text} Ok wait a second."
    send_message_to_user(slack_store, msg, worker_name, userid)


def get_channel_id(slack_store, slack_channel_name):
    if slack_channel_name in slack_store.dict_slack_channels:
        return slack_store.dict_slack_channels[slack_channel_name]
    else:
        slack_store.dict_slack_channels = {}
        chn_id = None
        channel_list = slack_store.slack_client.api_call(
            "channels.list",
            exclude_archived=1
        )
        try:
            for chn in channel_list["channels"]:
                if chn["name"] == slack_channel_name:
                    chn_id = chn["id"]
                slack_store.dict_slack_channels[chn["id"]] = chn["name"]
        except Exception as e:
            ex = "Exception: slack_helper @get_channel_id: {}.".format(e)
            print(ex)
        return chn_id


def join_channel(slack_store, slack_channel_name):
    try:
        channel_id = get_channel_id(slack_store, slack_channel_name)

        if channel_id:
            slack_store.slack_client.api_call(
                "channels.join",
                channel=channel_id
            )
            users_list = slack_store.slack_client.api_call(
                "users.list",
                channel=channel_id
            )
            members = users_list["members"]
            for m in members:
                id = m["id"]
                name = m["name"]
                if name == slack_store.slack_bot_name:
                    slack_store.slack_mention_bot = slack_store.mention_format.format(member_id=id)
                slack_store.dict_slack_userid_username[id] = name
                slack_store.dict_slack_username_userid[name] = id
            if slack_store.verbose:
                print(slack_store.dict_slack_userid_username)
        else:
            raise Exception("Channel ID not found: {}.".format(slack_channel_name))
    except Exception as e:
        ex = "Exception: slack_helper @join_channel: {}".format(e)
        print(ex)


def get_avail_command_str(slack_store):
    c = ""
    for command, worker_name in slack_store.dict_commands.items():
        format_bot_cmd = slack_store.format_bot_cmd
        c += format_bot_cmd.format(bot_name=slack_store.slack_bot_name,
                                   hostname_and_command=command) + "\n"
    return c


def format_error_message(worker_name, time_last_error, last_error):
    header = "{worker_name}@{time}".format(worker_name=worker_name,
                                           time=utils.time_to_str(time_last_error))
    return "\n".join([header, last_error])


def process_error(slack_store, worker_store, error_result):
    try:
        if not worker_store.time_last_error:
            worker_store.time_last_error = datetime.datetime.now()
        worker_store.last_error = "\n".join(error_result) if isinstance(error_result, list) else error_result
        worker_store.has_error = True
        err_msg = format_error_message(worker_store.worker_name,
                                       worker_store.time_last_error,
                                       worker_store.last_error)
        if worker_store.verbose:
            print("\n" + err_msg)

        seconds_since_last_notification = utils.seconds_since_last_notification(worker_store.time_last_notification)
        if worker_store.verbose:
            print("seconds_since_last_notification: " + str(seconds_since_last_notification))

        if utils.should_send_error_message(worker_store):
            send_message(slack_store, err_msg, worker_store.worker_name)
            worker_store.time_last_notification = datetime.datetime.now()
    except Exception as e:
        ex = "Exception: {} @process_error: {}".format(worker_store.worker_name, e)
        print(ex)
