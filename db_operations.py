#!/usr/bin/env python

################################################################################
# File name: db_operations.py                                                  #
# Description: This module is used to store and retrieve data to and from DB   #
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


import json
import pymongo
import MySQLdb
import datetime
from pymongo import MongoClient


client = MongoClient('mongodb://semantics:knoesis@localhost:27017/semantic_filtering')

db = client.semantic_filtering


def insert_tweet(item):

    item['created_at'] = datetime.datetime.utcnow()

    db.tweets.insert(item)


def count_tweets():

    return db.tweets.count()


def get_tweets(last_time, now_time):

    tweets_texts =  db.tweets.find(
            {"created_at":{"$gte":last_time,"$lt":now_time}}, {"text": 1})

    return tweets_texts


def insert_cooc_hashtags(eventID, item, counter):

    _item = {'coochashtags'+str(counter): item}

    db.hashtags.update({'_id': eventID}, {'$set' :_item}, upsert=True)


def insert_wikipage_recommended_hashtags(eventID, item):

    _item = {'wikipage_hashtags': item}


    db.hashtags.update({'_id': eventID}, {'$set' :_item}, upsert=True)


def get_sessions():
    sessions =  db.hashtags.find({}, {"_id": 1})

    return sessions


def get_sessions_data(id):

    data = db.hashtags.find({'_id': id})

    return data
