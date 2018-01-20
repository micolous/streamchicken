#!/usr/bin/env python
"""
twitter_scraper.py - Scrapes twitter for timvideos.us streaming site.

Copyright 2018 Michael Farrell <micolous+git@gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""
from __future__ import print_function
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from datetime import datetime, timedelta
from json import dump
import tweepy
from pytz import timezone, utc

class ScraperException(Exception): pass

def connect_twitter_api(secrets_f):
  """Reads secrets from the secrets file, and returns a Tweepy API object."""
  secrets = ConfigParser()
  secrets.read_file(secrets_f)
  get_secrets = lambda *x: [secrets.get('api', y) for y in x]
  auth = tweepy.OAuthHandler(*get_secrets('consumer_key', 'consumer_secret'))
  auth.set_access_token(*get_secrets('access_token', 'access_token_secret'))
  secrets_f.close()
  api = tweepy.API(auth)
  return api

def build_twitter_json(config_f, secrets_f, output_f):
  api = connect_twitter_api(secrets_f)
  
  # Read in the config
  config = ConfigParser()
  config.read_file(config_f)
  get_config = lambda x: config.get('twitter', x)
  announcements_user_name = get_config('announcements')
  # eg: Australia/Sydney
  local_tz = timezone(get_config('tz'))
  twitter_to_local = lambda x: utc.localize(x).astimezone(local_tz)

  # eg: #lca2018
  search_query = get_config('search')

  # lat,lng,radius, eg for Sydney: '-33.8688,151.2093,50km'
  geocode = get_config('geo')
  
  # max number of recent tweets to get
  rpp = get_config('count')

  # Sanity check to make sure we don't get something like a hashtag search
  # We don't actually pass this to the API...
  if not announcements_user_name.startswith('@'):
    raise ScraperException('twitter->announcements must be a user (starting with @)')
  else:
    announcements_user_name = announcements_user_name[1:]
    
  announcements_user = api.get_user(announcements_user_name)
  announcements_user_status = announcements_user.status
  
  # Get some tweets
  recent_tweets = api.search(search_query, geocode=geocode, rpp=rpp)
  tweets = []
  for tweet in recent_tweets:
    tweets.append({
      'txt': tweet.text,
      'who': tweet.user.screen_name,
      'ico': tweet.user.profile_image_url_https,
      'url': 'https://twitter.com/i/web/status/%s' % tweet.id_str,
      'ts': twitter_to_local(tweet.created_at).isoformat(),
    })
  
  # Show tweets in reverse chronological order
  tweets.sort(key=lambda x: x['ts'])
  tweets.reverse()
  
  output = {
    'ts': local_tz.localize(datetime.now()).isoformat(),
    'announce': {
      'txt': announcements_user_status.text,
      'url': 'https://twitter.com/i/web/status/%s' % announcements_user_status.id_str,
      'ts': twitter_to_local(announcements_user_status.created_at).isoformat(),
    },
    'feed': tweets
  }

  dump(output, output_f)


def main():
  parser = ArgumentParser()
  parser.add_argument('-c', '--config', required=True, type=FileType('rb'),
    help='Full path to twitter_config.ini (configuration file)')
  parser.add_argument('-s', '--secrets', required=True, type=FileType('rb'),
    help='Full path to twitter_secrets.ini')
  parser.add_argument('-o', '--output', required=True, type=FileType('wb'))

  options = parser.parse_args()

  build_twitter_json(options.config, options.secrets, options.output)

if __name__ == '__main__':
  main()
