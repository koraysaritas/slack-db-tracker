class Store:
    def __init__(self, config):
        self.version = config["app"]["version"]
        self.hostname = config["app"]["hostname"]
        self.arr_supported_databases = config["app"]["hostname"]
        self.verbose = False


class WorkerStore(Store):
    def __init__(self, config, worker_name):
        Store.__init__(self, config)
        self.is_active = config[worker_name]["is-active"]
        self.worker_name = worker_name
        self.bin_dir = config[worker_name]["bin-dir"]
        self.bin_isql = config[worker_name]["bin-isql"]
        self.bin_status = config[worker_name]["bin-status"]
        self.conn_str = config[worker_name]["conn-str"]
        self.seconds_sleep_after_status_check = config[worker_name]["seconds-sleep-after-status-check"]
        self.seconds_error_msg_flood_protection = config[worker_name]["seconds-error-msg-flood-protection"]
        self.dict_parser_isql = config[worker_name]["parser"]["isql"]
        self.time_last_status_check = None
        self.has_error = False
        self.time_last_error = None
        self.time_last_notification = None


class SlackStore(Store):
    def __init__(self, config):
        Store.__init__(self, config)
        self.dict_slack_userid_username = {}
        self.dict_slack_username_userid = {}
        self.dict_slack_channels = {}
        self.slack_client = None
        self.slack_token = config["slack"]["token"]
        self.slack_url_webhook = config["slack"]["webhook-url"]
        self.request_header = {'Content-Type': 'application/json'}
        self.slack_channel_name = config["slack"]["channel-name"]
        self.slack_send_help_msg = config["slack"]["send-help-msg"]
        self.slack_bot_name = config["slack"]["bot-name"]
        self.mention_format = "<@{member_id}>"
        self.slack_mention_bot = None
        self.format_bot_cmd_start = "!{bot_name}"
        self.bot_cmd_start = self.format_bot_cmd_start.format(bot_name=self.slack_bot_name)
        self.format_bot_cmd = "!{bot_name} {hostname_and_command}"
        self.dict_commands = {"-".join([self.hostname, command]): worker_name
                              for command, worker_name in dict(config["slack"]["commands"]).items()}
        self.dict_commands_raw = config["slack"]["commands"]
        self.seconds_sleep_after_slack_poll = int(config["slack"]["seconds-sleep-after-slack-poll"])


class ResourceStore(Store):
    def __init__(self, config):
        Store.__init__(self, config)
        self.seconds_sleep_after_run = int(config["resource"]["seconds-sleep-after-run"])
        self.seconds_error_msg_flood_protection = config["resource"]["seconds-error-msg-flood-protection"]
        self.notify_memory_usage = config["resource"]["notify-memory-usage"]
        self.notify_cpu_usage = config["resource"]["notify-cpu-usage"]
        self.notify_disk_usage = config["resource"]["notify-disk-usage"]
        self.mem_percents_logspaced = None
        self.mem_last_percent = None
        self.mem_threshold_next_percent = None
        self.mem_time_last_notification = None
        self.mem_time_last_run = None
        self.cpu_last_percent = None
        self.cpu_percents_ring_buffer = None
        self.cpu_time_last_notification = None
        self.cpu_time_last_run = None
        self.disk_percents_logspaced = None
        self.disk_last_percent = None
        self.disk_threshold_next_percent = None
        self.disk_time_last_notification = None
        self.disk_time_last_run = None

