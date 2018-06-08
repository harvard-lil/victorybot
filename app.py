from os import environ
from ast import literal_eval
import requests
from functools import wraps
from datetime import datetime, timedelta

from flask import Flask, request, redirect, session, abort, url_for, render_template
import error_handling

import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')
app.config['LOG_LEVEL'] = environ.get('LOG_LEVEL', 'WARNING')

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

@app.route('/', defaults={'path': ''}, methods=['GET'])
def index(path):
    # http://1lineart.kulaone.com/
    return render_template('generic.html', context={'heading': "victorybot",
                                                    'message': "ᕦ(ò_óˇ)ᕤ"})



