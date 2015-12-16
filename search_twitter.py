#!/usr/bin/env python

################################################################################
# File name: search_twitter.py                                                 #
# Description: This module uses tweepy to search twitter                       #
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


import re
import sys
import time
import json
import tweepy
import db_operations
from collections import defaultdict

def get_recentX_tweets(keyword, max_tweets):

    reload(sys)
    sys.setdefaultencoding('utf8')

    consumer_key=''
    consumer_secret=''
    access_key=''
    access_secret=''

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)

    query = keyword

    # above omitted for brevity
    c = tweepy.Cursor(api.search, q=query,
            include_entities=True, lang='en').items()

    tweets = []

    counter = 0

    # Returns the most recent n tweets
    while counter < max_tweets:
        try:
            tweet = c.next()

            counter+=1

            tweets.append(tweet.text.lower())

        #retry in case reached limit
        except tweepy.TweepError as e:
            print "<<<<<"
            print e.message
            print ">>>>>"
            print "sleeping"
            time.sleep(60 * 15)
            continue

        except StopIteration:
            print "stop iteration"
            return tweets # do nothing.. just give whatever I got
        except:
            print "something else.. terminating!"
            return tweets # do nothing.. just give whatever I got

    return tweets

if __name__ == "__main__":
    print get_recentX_tweets('hillary clinton', 10)
