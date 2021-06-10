victorybot
==========

This is a Slack bot for cheering on the victorious. It is also an
example of how to do development against a service to which your
application subscribes -- that is, a service that sends POST requests
to your app.

There is a wide variety of APIs and approaches for interacting with
Slack. This program uses one of the more recent,
[Bolt](https://slack.dev/bolt-python/concepts). The basic instructions
for setting up the bot can be found
[here](https://api.slack.com/start/building/bolt-python).

Development
-----------

This program uses [Poetry](https://python-poetry.org/) for Python
package management. Because deployment targets typically do not know
about `poetry.lock`, we need to produce `requirements.txt` with

    poetry export -o requirements.txt

You can run the application locally, after running `poetry install`,
with `poetry run python3 app.py`. However, since it requires Redis for
caching, we run the application in containers; after setting
`SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` in the environment, run

    docker-compose up

You then expose the application to the outside world using
[ngrok](https://ngrok.com/download). In another terminal, run

    ngrok http 3000

You can then put the URL ngrok provides into the Event Subscriptions
page of your bot's configuration, appending the path `/slack/events`.

There is a somewhat arbitrary line between services required on the
host (Poetry, ngrok) and those required in the containers (Redis); you
could equally well run Redis locally and skip the Docker
arrangement.

At the moment, you need to stop and rebuild the app container after a
code change:

    docker-compose up --build

(Even locally, this code doesn't live-reload like Flask does.)

Until this is automated, keep it clean with

    poetry run flake8 --ignore=E129,W504 app.py

Deployment
----------

This program has in previous incarnations been deployed at Heroku, but
is now being deployed to [fly.io](https://fly.io/). At Fly, you'll
need to set at least `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, and
`VICTORY_BOT_ID` with `flyctl secrets set <KEY>=<value>`. You probably
want to set `VICTORY_REACTIONS`, a comma-separated list of reaction
names. You may additionally want to set `SCREENSHARE_CHANNEL` and
`SCREENSHARE_URL`.
