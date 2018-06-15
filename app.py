from ast import literal_eval
from datetime import datetime
from os import environ
from flask import Flask, render_template, request, jsonify
from flask_redis import FlaskRedis
import hashlib
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
import time
import threading

import error_handling

import logging

app = Flask(__name__)
# required
app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')
app.config['REDIS_URL'] = environ.get('REDIS_URL')
app.config['SLACKBOT_TOKEN'] = environ.get('SLACKBOT_TOKEN')
app.config['SLACK_VERIFICATION_TOKEN'] = environ.get('SLACK_VERIFICATION_TOKEN')
app.config['SCREENSHARE_CHANNEL'] = environ.get('SCREENSHARE_CHANNEL')
app.config['SCREENSHARE_URL'] = environ.get('SCREENSHARE_URL')
# optional
app.config['SCREENSHARE_DURATION'] = literal_eval(environ.get('SCREENSHARE_DURATION', '60'))
app.config['REDIS_EXPIRES'] = literal_eval(environ.get('REDIS_KEY_FORMAT', '300'))
app.config['LOG_LEVEL'] = environ.get('LOG_LEVEL', 'WARNING')

# register error handlers
error_handling.init_app(app)

# register redis
REDIS_STORE = FlaskRedis(app)

# register Slack Event Adapter
slack_events_adapter = SlackEventAdapter(app.config['SLACK_VERIFICATION_TOKEN'], "/events", app)
CLIENT = SlackClient(app.config['SLACKBOT_TOKEN'])

###
### UTILS ###
###

@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))


###
### ROUTES
###

@app.route('/', methods=['GET'])
def index():
    # http://1lineart.kulaone.com/
    return render_template('generic.html', context={'heading': "victorybot",
                                                    'message': "ᕦ(ò_óˇ)ᕤ"})


@slack_events_adapter.on("app_mention")
def handle_message(event_data):
    message = event_data["event"]
    if message.get("subtype") is None:
        channel = message["channel"]
        announcement = message.get('text').split('>', 1)[1].strip(' ,!.?;:')
        key = f"{channel}:{hashlib.md5(bytes(announcement, 'utf-8')).hexdigest()}"
        if not REDIS_STORE.exists(key):
            REDIS_STORE.setex(key, app.config['REDIS_EXPIRES'], "")
            message = f"Victory! Victory! {announcement}! <!here|here>!  :tada:"
            CLIENT.api_call("chat.postMessage", channel=channel, text=message)
            threading.Thread(target=temporarily_post_to_screenshare).start()
    return jsonify({"status":"ok"})


def temporarily_post_to_screenshare():
    # in screenshare, for a minute
    response = CLIENT.api_call("chat.postMessage", channel=app.config['SCREENSHARE_CHANNEL'], text=app.config['SCREENSHARE_URL'])
    if response["ok"]:
        time.sleep(app.config['SCREENSHARE_DURATION'])
        CLIENT.api_call("chat.delete", channel=app.config['SCREENSHARE_CHANNEL'], ts=response["ts"])


@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    team_id = event_data["team_id"]
    event = event_data["event"]

    event_timestamp = event["event_ts"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    message_ts = event["item"]["ts"]

    key = f"{channel}:{event_timestamp}:{hashlib.md5(bytes(emoji, 'utf-8')).hexdigest()}"

    if (emoji in ['tada', 'confetti_ball', 'clap', 'raised_hands'] and
        datetime.now().timestamp() - float(event_timestamp) < 120 and
        float(event_timestamp) - float(message_ts) < 120 and
        not REDIS_STORE.exists(key)):
            REDIS_STORE.setex(key, app.config['REDIS_EXPIRES'], "")
            text = f":{emoji}:"
            # if item.get('type') == 'message' and item.get('thread_ts'):
            #     CLIENT.api_call("chat.postMessage", channel=channel, text=text, thread_ts=event_data["ts"])
            CLIENT.api_call("chat.postMessage", channel=channel, text=text)

    return jsonify({"status":"ok"})

