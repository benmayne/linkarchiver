#!/usr/bin/env python

# Listens to a Twitter timeline and sends tweeted URLs to the Internet Archive.

import os
import requests
import yaml
import urllib
from twython import Twython, TwythonStreamer, TwythonError
import time
import thread as thread
import logging

logging.basicConfig(filename='log.log',level=logging.WARN)

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
    try:
        if 'entities' in data:
            url_list = grab_urls(data)
            for url in url_list:
                thread.start_new_thread(send_to_archive, (url, ))
        elif 'event' in data:
            print("Some kind of event! {}".format(data['event']))
        else:
            print("other: " + str(data))
    except Exception:
        logging.warn(str(data))
        print(Exception)

def log_failure(status_code, data):
    print("Something's gone terribly wrong: " + str(status_code) + " " + str(data))

def grab_urls(tweet):
    url_list = ["https://twitter.com/{}/status/{}".format(tweet["user"]["screen_name"], tweet["id"])]
    for url in tweet['entities']['urls']:
        if url['expanded_url']:
            url_list.append(url['expanded_url'])
    return url_list

def send_to_archive(link):
    print("submitting: " + link)
    if link:
        try:
            requests.get("https://web.archive.org/save/{}".format(link),
                    headers = {'user-agent':'@{} twitter bot'.format(SCREEN_NAME)})
            print("archive.org submitted: " + link)
        except:
            print("ERROR archive.org on: " + link)
        try:
            requests.post(
                "https://archive.fo/submit/",
                data = urllib.urlencode({"submitid":"twitter-{}".format(time.time()), "url":link}),
                headers = {'user-agent':'@{} twitter bot'.format(SCREEN_NAME),
                           'origin': 'https://archive.fo',
                           'content-type': 'application/x-www-form-urlencoded',
                           'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                           'cache-control': 'max-age=0',
                           'dnt': '1'}
            )
            print("archive.fo submitted: " + link)
        except:
            print("ERROR archive.fo on: " + link)

def main():
    streamer = get_stream_instance()

    streamer.on_success = check_tweet
    streamer.on_error = log_failure

    streamer.user(replies=all)

if __name__ == '__main__':
    main()
