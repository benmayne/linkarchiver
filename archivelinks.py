#!/usr/bin/env python3

# Listens to a Twitter timeline and sends tweeted URLs to the Internet Archive.

import os
import requests
import yaml
from twython import Twython, TwythonStreamer, TwythonError

fullpath = os.path.dirname(os.path.realpath(__file__))
CONFIGFILE = os.path.join(fullpath, "config.yaml")

with open(CONFIGFILE, 'r') as c:
    CONFIG = yaml.load(c)

SCREEN_NAME = CONFIG['twitter_bot_name']

def get_twitter_creds():
    twitter_app_key = CONFIG['twitter_app_key']
    twitter_app_secret = CONFIG['twitter_app_secret']
    twitter_oauth_token = CONFIG['twitter_oauth_token']
    twitter_oauth_token_secret = CONFIG['twitter_oauth_token_secret']
    return twitter_app_key, twitter_app_secret, twitter_oauth_token, twitter_oauth_token_secret

def get_stream_instance():
    app_key, app_secret, oauth_token, oauth_token_secret = get_twitter_creds()
    return TwythonStreamer(app_key, app_secret, oauth_token, oauth_token_secret)

def get_twitter_instance():
    app_key, app_secret, oauth_token, oauth_token_secret = get_twitter_creds()
    return Twython(app_key, app_secret, oauth_token, oauth_token_secret)

def check_tweet(data):
    if 'entities' in data:
        url_list = grab_urls(data)
        screen_names = [user['screen_name'] for user in 
                data['entities']['user_mentions']]
        for url in url_list:
            archive_link = send_to_archive(url)
            if SCREEN_NAME in screen_names:
                tweet_reply(
                        archive_link, data['id_str'], 
                        data['user']['screen_name'])
    elif 'event' in data:
        print("Some kind of event! {}".format(data['event']))
        if data['event'] == 'follow' and data['source']['screen_name'] != SCREEN_NAME:
            print("I'm gonna follow {}.".format(data['source']['screen_name']))
            twitter_follow(data['source']['screen_name'])
    else:
        print(data)

def log_failure(status_code, data):
    print("Something's gone terribly wrong: " + str(status_code) + " " + str(data))

def twitter_follow(screen_name):
    twitter = get_twitter_instance()
    try:
        twitter.create_friendship(screen_name = screen_name)
    except TwythonError as err:
        print("Had this error, bud: " + str(err))

def tweet_reply(archive_link, tweet_id, screen_name):
    twitter = get_twitter_instance()
    if archive_link:
        message = "Here's your archived link: " + archive_link
    else:
        message = "Sorry, something went wrong :("
    try:
        twitter.update_status(status = "@" + screen_name + " " + message,
                in_reply_to_status_id = tweet_id)
    except:
        pass

def grab_urls(tweet):
    url_list = ["https://twitter.com/{}/status/{}".format(tweet["user"]["screen_name"], tweet["id"])]
    for url in tweet['entities']['urls']:
        if url['expanded_url']:
            url_list.append(url['expanded_url'])
    return url_list

def send_to_archive(link):
    print("Sending {} to the Internet Archive.".format(link))
    if link:
        try:
            res = requests.get("https://web.archive.org/save/{}".format(link),
                    headers = {'user-agent':'@{} twitter bot'.format(SCREEN_NAME)})
            with open(os.path.join(fullpath,"log.txt"),"a") as f:
                f.write(link + "\n")
            return "https://web.archive.org" + res.headers['Content-Location']
        except:
            pass

def main():
    streamer = get_stream_instance()

    streamer.on_success = check_tweet
    streamer.on_error = log_failure

    streamer.user(replies=all)

if __name__ == '__main__':
    main()
