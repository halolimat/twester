#!/usr/bin/env python

################################################################################
# File name: api_terminal.py                                                   #
# Description: This module executes the background processing of the program   #
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
import csv
import ast
import sys
import json
import math
import time
import thread
import datetime
import operator
import send_email
import collections
from json import dumps
from bson import ObjectId
from dateutil import parser
from json import JSONEncoder
from bson import Binary, Code
from tabulate import tabulate
from datetime import timedelta
from pymongo import MongoClient
from collections import Counter
from bson.json_util import dumps
from collections import defaultdict
from collections import OrderedDict


import tf
import similaritites
import db_operations
import stream_tweets
import search_twitter
import annotate_tweets
import wikipage_entities

#===============================================================================

last_time = datetime.datetime.utcnow()# - timedelta(minutes=20)
hashtag_freq = defaultdict(int)

#===============================================================================

# Global CoocHashtags
coochashtags = dict()

execute = True
counter = 0
#===============================================================================

def increment_global_counter():
    global counter
    counter += 1

    if counter == 6:
        counter = 0

def get_global_counter():
    global counter
    return counter

#===============================================================================

def set_coochashtags(value):
    global coochashtags
    coochashtags = value
    #print "Inside set_coochashtags, coochashtags is now:", coochashtags

def get_coochashtags():
    global coochashtags
    return coochashtags
#===============================================================================

# Start of main functions
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

def findCoocHashtags(vars_dict, sessionID):

    global last_time
    global execute

    now_time = datetime.datetime.utcnow()

    result = db_operations.get_tweets(last_time, now_time)

    last_time = now_time

    for tweet in result:

        hashtagsInTweet = re.findall(r"#(\w+)", tweet['text'].lower())

        # To remove duplicate hashtags in same tweet
        hashtagsInTweet = list(set(hashtagsInTweet))

        if len(hashtagsInTweet) > 0:
            if vars_dict['hashtag'].lower() in hashtagsInTweet:
                hashtagsInTweet.remove(vars_dict['hashtag'].lower())
                for x in hashtagsInTweet:
                    hashtag_freq[x] = hashtag_freq[x] + 1

    # sort dict
    sorted_dict = collections.OrderedDict(sorted(hashtag_freq.items(),
                    key=operator.itemgetter(1), reverse=True))

    #print sorted_dict

    # Update the global coochashtags
    set_coochashtags(sorted_dict)

    # This will allow us to call wikihashtag method every 5 times ==============
    increment_global_counter()

    # inserts cooc hashtags
    db_operations.insert_cooc_hashtags(sessionID, sorted_dict,
                                            get_global_counter())

    print get_global_counter()

    # Start wikipage recommendation process every 5 runs of this function
    if get_global_counter() == 5:

        execute = False

        findWikiHashtags(vars_dict['wikipage'], sessionID)

    #===========================================================================

def findWikiHashtags(wikipage, sessionID):

    # get wikipedia concepts ranks:
    #   gets the current wiki innerlinks and rank them
    _wikipage_entities = rank_wiki_entities(wikipage)

    # Get the list of cooc hashtags from the global variable
    coochashtags = get_coochashtags()

    # will contain the hashtag name and the score based on jaccard similarity
    recommended_hashtags_jaccard = defaultdict(float)

    # cosine scores
    recommended_hashtags_cosine = defaultdict(float)

    # The cooccurences of the coocurrences of the main hashtag
    recommended_hashtags_coocs = defaultdict(list)

    # Taxonomies of searched tweets
    recommended_hashtags_taxonomies = defaultdict(list)

    # 1- search twitter for each hashtag ---------------------------------------
    entities = []

    max_tweets = 20

    #TODO: this should be a thredhold instead
    # only the top x hashtags
    number_of_hashtags = 10

    for hashtag in coochashtags.keys():
        if number_of_hashtags >= 0:

            # TYPE: List
            hashtag_tweets = search_twitter.get_recentX_tweets(hashtag, max_tweets)

            # This will allow me to find other hashtags that did not coocuured
            # directly with my main hashtag (AND) find taxonomies of each tweet
            for tweet in hashtag_tweets:

                # This will get all hashtags++++++++++++++++++++++++++++++++++++

                hashtagsInTweet = re.findall(r"#(\w+)", tweet.lower())

                # To remove duplicate hashtags in same tweet
                hashtagsInTweet = list(set(hashtagsInTweet))

                for haTag in hashtagsInTweet:
                    recommended_hashtags_coocs[hashtag].append(haTag)

                #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

                if 'taxonomy' in annotate_tweets.alchemy(tweet):
                    for label in annotate_tweets.alchemy(tweet)['taxonomy']:
                        recommended_hashtags_taxonomies[hashtag].append(label)


            # Annotate tweets and get all entities
            # TYPE: List
            entities = annotate_tweets.annotate_return_entities(hashtag_tweets)

            # entity and Frequency in a hashtag tweets
            hashtag_all_entities = dict(Counter(entities))

            # Jaccard Similarity - section 3.3.1: without scores
            sim = similaritites.jaccard_similarity(
                    Counter(hashtag_all_entities.keys()),
                    Counter(_wikipage_entities.keys()))

            recommended_hashtags_jaccard[hashtag] = sim

            # Cosine Similarity - section 3.3.2: with scores

            #1: unify the two sets of entities from wikipage and tweets
            combined_entities = list(
                                set(entities).union(_wikipage_entities.keys()))

            #===================================================================

            # As in Pavan Paper
            hashtag_h = []

            for x in combined_entities:
                if x in entities:
                    hashtag_h.append(hashtag_all_entities[x])
                else:
                    hashtag_h.append(0)

            #===================================================================

            # As in Pavan Paper
            event_e = []

            for x in combined_entities:
                if x in _wikipage_entities.keys():
                    event_e.append(_wikipage_entities[x])
                else:
                    event_e.append(0)

            #===================================================================

            sim = similaritites.cosine_similarity(
                    Counter(hashtag_h), Counter(event_e))

            recommended_hashtags_cosine[hashtag] = sim

            #-------
            print number_of_hashtags

            number_of_hashtags -= 1

            #===================================================================
            #===================================================================
            #===================================================================

        else:
            break

    recommended_hashtags = {
        'jaccard_sim': recommended_hashtags_jaccard,
        'cosine_sim': recommended_hashtags_cosine,
        'hashtag-cooc': recommended_hashtags_coocs,
        'hashtag-taxonomies': recommended_hashtags_taxonomies
    }

    db_operations.insert_wikipage_recommended_hashtags(sessionID,
                    recommended_hashtags)


#NOTE: This implements section 3.2 in the paper
def rank_wiki_entities(wikipage):

    print wikipage

    # gets the current wiki innerlinks
    _wikipage_entities = wikipage_entities.get_current_wiki_links(wikipage)

    entities_rank = defaultdict(float)

    # 1- Rank Entities based on backlins
    # 2- Rank based on outt link overlap
    # 3- Mentions in the page - TF

    for entity in _wikipage_entities:
        # Edge based------------------------------------
        innerLink_outLinks = wikipage_entities.get_current_wiki_links(entity)

        if innerLink_outLinks is not None:

            if wikipage in innerLink_outLinks:
                entities_rank[entity] = entities_rank[entity] + 2.0

            else:
                entities_rank[entity] = entities_rank[entity] + 1.0


            # Concept overlap - using jaccard
            entities_rank[entity] = entities_rank[entity] + (
                similaritites.jaccard_similarity(
                    Counter(_wikipage_entities),
                    Counter(innerLink_outLinks)))


    # 3- TF +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    entity_mentions = defaultdict(int)


    frequencies = tf.get_frequencies_wikipage(wikipage)


    for x in frequencies.keys():
        for entity in _wikipage_entities:
            if x in entity:
                # This will make sure to get only one value or the other of an
                # entity of two terms
                if entity_mentions[entity] < frequencies[x]:
                    entity_mentions[entity] = frequencies[x]


    # sort dict
    entity_mentions = collections.OrderedDict(
        sorted(entity_mentions.items(),
                key=operator.itemgetter(1), reverse=True))

    # normalize between zero and one
    max_value = entity_mentions.values()[0]
    min_value = entity_mentions.values()[-1]

    for entity in entity_mentions.keys():

        # Normalize score
        score = (
                    (entity_mentions[entity] - min_value)/ (
                        float(max_value - min_value)
                    )
                )

        if entity in entities_rank.keys():
            entities_rank[entity] = entities_rank[entity] + score

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    entities_rank = collections.OrderedDict(sorted(entities_rank.items(),
                        key=operator.itemgetter(1), reverse=True))


    return entities_rank

#-------------------------------------------------------------------------------

if __name__ == "__main__":

    #sessionID = 'Trump2016-020'
    #wikipage = 'Donald_Trump_presidential_campaign,_2016'

    sessionID = 'Bernie2016-002'
    wikipage = 'Bernie_Sanders_presidential_campaign,_2016'
    #wikipage = 'United_States_presidential_election,_2016'

    # get hashtag from sessionID
    hashtag = sessionID[:-4]

    vars_dict = {"wikipage": wikipage, 'hashtag': hashtag}

    thread.start_new_thread(stream_tweets.getTweets, (vars_dict['hashtag'],))

    # Find the cooc hashtags every 6 minutes and save to DB
    while execute:

        time.sleep(6*60)

        try:
            findCoocHashtags(vars_dict, sessionID)
        except Exception as e:
            send_email.send("streamer error", str(e))
