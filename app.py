import os
from datetime import datetime
import redis
import hashlib
import threading
import time

from slack_bolt import App

# required environment variables
app = App(
    token=os.environ.get('SLACK_BOT_TOKEN'),
    signing_secret=os.environ.get('SLACK_SIGNING_SECRET')
)
try:
    redis_url = os.environ['FLY_REDIS_CACHE_URL']
except KeyError:
    redis_url = os.environ['REDIS_URL']
cache = redis.from_url(redis_url)

me = os.environ.get('VICTORY_BOT_ID')

# optional environment variables
reactions = os.environ.get('VICTORY_REACTIONS', 'test_tube,top').split(',')
expires = int(os.environ.get('CACHE_EXPIRES', '90'))


@app.event('reaction_added')
def respond_to_reaction(body, say):
    event = body['event']

    reaction = event['reaction']
    event_ts = float(event['event_ts'])
    message_timestamp = event['item']['ts']
    channel = event['item']['channel']
    digest = hashlib.md5(bytes(reaction, 'utf-8')).hexdigest()

    key = f'{channel}:{message_timestamp}:{digest}'

    now = datetime.now().timestamp()
    in_time = now - event_ts < 90 and event_ts - float(message_timestamp) < 90
    if reaction in reactions and in_time and not cache.exists(key):
        cache.set(key, "")
        message = f':{reaction}:'
        try:
            boss = os.environ['VICTORY_BOSS_ID']
            reaction = os.environ['VICTORY_BOSS_REACTION']
            message_user = event.get('item_user', '')
            user = event['user']
            if message_user == me and user == boss:
                message = f':heart: :{reaction}: :heart:'
        except KeyError:
            pass
        say(message, thread_ts=message_timestamp)


@app.event('app_mention')
def handle_message(body, say):
    event = body['event']

    if event.get('subtype') is None and event['user'] != me:
        channel = event['channel']
        event_ts = float(event['event_ts'])

        text = [phrase for
                phrase in event.get('text', '').split(f'<@{me}>')
                if phrase]
        announcement = text[-1].strip(' ,!.?;:') if len(text) > 0 else ''

        digest = hashlib.md5(bytes(announcement, 'utf-8')).hexdigest()
        key = f'{channel}:{digest}'

        now = datetime.now().timestamp()
        if now - event_ts < 90 and not cache.exists(key):
            cache.setex(key, expires, '')
            message = f'Victory! Victory! {announcement}! <!here|here>! :tada:'
            say(message)
            threading.Thread(target=temporarily_post_to_screenshare).start()


def temporarily_post_to_screenshare():
    channel = os.environ.get('SCREENSHARE_CHANNEL')
    url = os.environ.get('SCREENSHARE_URL')
    if channel and url:
        response = app.client.chat_postMessage(
            channel=channel,
            text=url,
            as_user=True)
        if response['ok']:
            time.sleep(int(os.environ.get('SCREENSHARE_DURATION', '60')))
            app.client.chat_delete(
                channel=channel,
                ts=response['ts'])


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
