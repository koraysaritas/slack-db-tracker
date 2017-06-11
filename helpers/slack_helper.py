import time
import datetime
import re
import json
import requests
from slackclient import SlackClient


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
            ex = "Exception@get_channel_id: {}.".format(e)
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
            print(slack_store.dict_slack_userid_username)
        else:
            raise Exception("Channel ID not found: {}.".format(slack_channel_name))
    except Exception as e:
        ex = "Exception@join_channel: {}".format(e)
        print(ex)
