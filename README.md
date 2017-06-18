# Slack DB Tracker
Send database events and notifications into Slack.


##### Supported Databases
- VoltDB
- TimesTen
- Altibase

## Prerequisites

- Git (1.7.x or newer)
- Python 3.5+
- A Slack App and a Bot User
  - https://YOUR-TEAM-HERE.slack.com/apps/manage
- Running instances of Altibase, Oracle TimesTen or VoltDB.


## Installing
You can install from source:

###### Clone from source
    $ git clone https://github.com/koraysaritas/slack-db-tracker

###### Create and activate a new virtual environment
    $ cd slack-db-tracker
    $ python3 -m venv venv
    $ source venv/bin/activate

###### Install project requirements
    $ pip install -r requirements.txt

## Configuration
You need to set up these Slack and database related configs at the config.yaml file:

- ``hostname: '<HOSTNAME-HERE>'``
  - Example: ``hostname: 'omsdev'``
- ``supported-databases: ['altibase', 'timesten', 'voltdb']``
  - You can delete the unused items
  - Example ``supported-databases: ['timesten']``
- ``token: '<SLACK-TOKEN-HERE>'``
  - Example: ``token: 'xoxb-15...'``
- ``webhook-url: '<SLACK-WEBHOOK-URL-HERE>'``
  - Example: ``webhook-url: 'https://hooks.slack.com/services/T32...'``
- ``bot-name: '<SLACK-BOT-NAME-HERE>'``
  - Example: ``bot-name: 'kerata'``
- ``channel-name: '<SLACK-CHANNEL-HERE>'``
  - Example: ``channel-name: 'general'``

Make some or all of the following settings depending on your setup:
###### Altibase
- ``bin-dir: '<ALTIBASE-BIN-DIR-HERE>'``
  - Example: ``bin-dir: '/home/altibase/ALTIBASE_COMMUNITY_EDITION_SERVER/bin/'``
- ``conn-str: '-s <SERVER-NAME-HERE> -u <USER-NAME-HERE> -p <PASSWORD-HERE>'``
  - Example: ``conn-str: '-s 127.0.0.1 -u hodor -p hodor'``

###### TimesTen
- ``bin-dir: '<TIMESTEN-BIN-DIR-HERE>'``
  - Example: ``bin-dir: '~/TimesTen/tt1122/bin/'``
- ``conn-str: '-connStr <TIMESTEN-CONNSTR-HERE>'``
  - Example: ``conn-str: '-connStr "DSN=TT_1122;"'``

###### VoltDB
- ``bin-dir: '<VOLTDB-BIN-DIR-HERE>'``
  - Example: ``bin-dir: '~/voltdb/voltdb-ent-7.0/bin/'``
- ``conn-str: '<VOLTDB-CONNSTR-HERE>'``
  - Example: ``conn-str: '--servers=odin --user=thor --password=loki.sucks'``

## Screenshots

###### Commands-1
![01](https://github.com/koraysaritas/slack-db-tracker/blob/master/screenshots/01_small.png)

###### Commands-2
![03](https://github.com/koraysaritas/slack-db-tracker/blob/master/screenshots/03_small.png)

###### Push notifications
![02](https://github.com/koraysaritas/slack-db-tracker/blob/master/screenshots/02_small.png)
