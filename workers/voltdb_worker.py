from helpers import utils
import time
import datetime
import re
import json
import requests
from helpers import slack_helper
from slackclient import SlackClient
from helpers.store import WorkerStore
from helpers.store import SlackStore


def run(config, worker_name):
    slack_store = SlackStore(config)
    worker_store = WorkerStore(config, worker_name)

    slack_store.slack_client = SlackClient(slack_store.slack_token)
    slack_helper.join_channel(slack_store, slack_store.slack_channel_name)
