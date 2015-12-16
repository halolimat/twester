#!/usr/bin/env python

################################################################################
# File name: stream_tweets.py                                                  #
# Description: This module uses tweepy to stream from twitter                  #
#------------------------------------------------------------------------------#
# Author: Hussein S. Al-Olimat                                                 #
# Email: hussein@knoesis.org                                                   #
#------------------------------------------------------------------------------#
# Date-last-modified: Dec 13, 2015                                             #
# Python-version: 2.7                                                          #
################################################################################
# This file is part of twester: a python-based program that study the          #
# of a topic on twitter and recommend hashtags for dynamically filtering the   #
# twitter streams.                                                             #
#------------------------------------------------------------------------------#
# twester is a free program: you can redistribute it and/or modify it under    #
# the terms of the GNU General Public License as published by the Free         #
# Software Foundation, either version 3 of the License, or (at your option)    #
# any later version.                                                           #
#------------------------------------------------------------------------------#
# twester is distributed in the hope that it will be useful, but WITHOUT ANY   #
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS    #
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more       #
# details. You should have received a copy of the GNU General Public License   #
# along with twester.  If not, see <http://www.gnu.org/licenses/>.             #
################################################################################


import sys
import time
import json
import tweepy
import db_operations


def getTweets(hashtag):

    # Twitter streams a Max of 57 tweets per second [Fact]
    #---------------------------------------------------------------------------

    reload(sys)
    sys.setdefaultencoding('utf8')

    consumer_key=''
    consumer_secret=''
    access_key=''
    access_secret=''

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)

    class CustomStreamListener(tweepy.StreamListener):
        def on_data(self, data):

            item = json.loads(data)

            if 'text' in data:
                item["hashtags"] = hashtag
                db_operations.insert_tweet(item)
            else:
                pass # Do nothing

        def on_error(self, status_code):
            print >> sys.stderr, 'Encountered error with status code:', status_code
            # sleep for 16 minutes
            print "sleeping for 16 minutes"
            time.sleep(960)

            return True # Don't kill the stream

        def on_timeout(self):
            print >> sys.stderr, 'Timeout...'
            return True # Don't kill the stream

    try:
        sapi = tweepy.streaming.Stream(auth, CustomStreamListener())

        sapi.filter(languages=["en"], track=[hashtag])
    except:
        print "tweepy error" #Don't do anythin
        raise

if __name__ == "__main__":
    getTweets('Trump2016')
