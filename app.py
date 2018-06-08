from os import environ

from flask import Flask, render_template, request, jsonify, abort
from werkzeug.security import safe_str_cmp

import error_handling

import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')
app.config['LOG_LEVEL'] = environ.get('LOG_LEVEL', 'WARNING')
app.config['SLACKBOT_TOKEN'] = environ.get('SLACKBOT_TOKEN')
app.config['SLACK_VERIFICATION_TOKEN'] = environ.get('SLACK_VERIFICATION_TOKEN')

# register error handlers
error_handling.init_app(app)

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


@app.route('/events', methods=['POST'])
def incoming():
    data = request.get_json()
    if token_valid(data.get('token')):
        if data.get('type') == 'url_verification':
            return jsonify({'challenge': data.get('challenge')})
        pass
    abort(403)


def token_valid(token):
    return safe_str_cmp(app.config['SLACK_VERIFICATION_TOKEN'], token)

