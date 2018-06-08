from os import environ
from flask import Flask, render_template, request
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter

import error_handling

import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')
app.config['LOG_LEVEL'] = environ.get('LOG_LEVEL', 'WARNING')
app.config['SLACKBOT_TOKEN'] = environ.get('SLACKBOT_TOKEN')
app.config['SLACK_VERIFICATION_TOKEN'] = environ.get('SLACK_VERIFICATION_TOKEN')

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
    # If the incoming message contains "hi", then respond with a "Hello" message
    if message.get("subtype") is None and "hi" in message.get('text'):
        channel = message["channel"]
        message = "Hello <@%s>! :tada:" % message["user"]
        CLIENT.api_call("chat.postMessage", channel=channel, text=message)


@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    team_id = event_data["team_id"]
    event = event_data["event"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    if emoji in ['tada', 'confetti_ball']:
        text = ":%s:" % emoji
        CLIENT.api_call("chat.postMessage", channel=channel, text=text)
