from os import environ
from flask import Flask, render_template, request, jsonify
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
import time
import threading

import error_handling

import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')
app.config['LOG_LEVEL'] = environ.get('LOG_LEVEL', 'WARNING')
app.config['SLACKBOT_TOKEN'] = environ.get('SLACKBOT_TOKEN')
app.config['SLACK_VERIFICATION_TOKEN'] = environ.get('SLACK_VERIFICATION_TOKEN')
app.config['SCREENSHARE'] = environ.get('SCREENSHARE')

# register error handlers
error_handling.init_app(app)

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
        message = "Victory! Victory! {}! <!here|here>!  :tada:".format(announcement, message["user"])
        CLIENT.api_call("chat.postMessage", channel=channel, text=message)
        threading.Thread(target=temporarily_post_to_screenshare).start()
    return jsonify({"status":"ok"})


def temporarily_post_to_screenshare():
    # in screenshare, for a minute
    response = CLIENT.api_call("chat.postMessage", channel=app.config['SCREENSHARE'], text="I should be here for only a minute. Then be deleted automatically.")
    if response["ok"]:
        time.sleep(60)
        CLIENT.api_call("chat.delete", channel=app.config['SCREENSHARE'], ts=response["ts"])


@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    team_id = event_data["team_id"]
    event = event_data["event"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    if emoji in ['tada', 'confetti_ball', 'clap', 'raised_hands']:
        text = ":%s:" % emoji
        CLIENT.api_call("chat.postMessage", channel=channel, text=text)
    return jsonify({"status":"ok"})

