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
app.config['SLACKBOT_ID'] = environ.get('SLACKBOT_ID')
app.config['SLACK_VERIFICATION_TOKEN'] = environ.get('SLACK_VERIFICATION_TOKEN')
app.config['SCREENSHARE_CHANNEL'] = environ.get('SCREENSHARE_CHANNEL')
app.config['SCREENSHARE_URL'] = environ.get('SCREENSHARE_URL')
app.config['ADAM_ID'] = environ.get('ADAM_ID')
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
    event = event_data["event"]

    if event.get("subtype") is None and event["user"] != app.config['SLACKBOT_ID']:

        channel = event["channel"]
        event_timestamp = event["event_ts"]

        text = [phrase for phrase in event.get('text', '').split(f"<@{app.config['SLACKBOT_ID']}>") if phrase]
        announcement = text[-1].strip(' ,!.?;:') if len(text) > 0 else ''

        key = f"{channel}:{hashlib.md5(bytes(announcement, 'utf-8')).hexdigest()}"

        if (datetime.now().timestamp() - float(event_timestamp) < 90 and
           not REDIS_STORE.exists(key)):
            REDIS_STORE.setex(key, app.config['REDIS_EXPIRES'], "")
            message = f"Victory! Victory! {announcement}! <!here|here>!  :tada:"
            CLIENT.api_call("chat.postMessage", channel=channel, text=message, as_user=True)
            threading.Thread(target=temporarily_post_to_screenshare).start()

    return jsonify({"status":"ok"})


def temporarily_post_to_screenshare():
    # in screenshare, for a minute
    response = CLIENT.api_call("chat.postMessage", channel=app.config['SCREENSHARE_CHANNEL'], text=app.config['SCREENSHARE_URL'], as_user=True)
    if response["ok"]:
        time.sleep(app.config['SCREENSHARE_DURATION'])
        CLIENT.api_call("chat.delete", channel=app.config['SCREENSHARE_CHANNEL'], ts=response["ts"])


@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    team_id = event_data["team_id"]
    event = event_data["event"]

    event_timestamp = event["event_ts"]
    user = event["user"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    message_timestamp = event["item"]["ts"]
    message_user = event.get("item_user", "")

    key = f"{channel}:{message_timestamp}:{hashlib.md5(bytes(emoji, 'utf-8')).hexdigest()}"

    if (emoji in ['tada', 'confetti_ball', 'clap', 'raised_hands'] and
        datetime.now().timestamp() - float(event_timestamp) < 90 and
        float(event_timestamp) - float(message_timestamp) < 90 and
        not REDIS_STORE.exists(key)):
            REDIS_STORE.set(key, "")
            if message_user == app.config['SLACKBOT_ID'] and user == app.config['ADAM_ID']:
                text = ":heart: :cooladam: :heart:"
            else:
                text = f":{emoji}:"
            CLIENT.api_call("chat.postMessage", channel=channel, text=text, thread_ts=message_timestamp, as_user=True)

    return jsonify({"status":"ok"})
