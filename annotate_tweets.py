#!/usr/bin/env python

################################################################################
# File name: annotate_tweets.py                                                #
# Description: This module annotate tweets using spotlight and YQL             #
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
import json
import string
import urllib
import urllib2
import pymongo
import datetime
from functools import partial
from pymongo import MongoClient
from bson.json_util import dumps

wiki_urls = []

def spotlight(text):
    try:

        url='http://localhost:2222/rest/annotate'

        params = {
            'support': 20,
            'confidence': 0.2,
            'text': text
        }

        req = urllib2.Request(url, urllib.urlencode(params),
                headers = {'Accept' : 'application/json'})
        response = urllib2.urlopen(req)

        return json.load(response)
    except:
        print "something wrong with spotlight"
        raise


def yql(text):

    # to clean the text------------------------
    regex = re.compile('[^a-zA-Z ]')
    text = regex.sub('', text)
    text = re.sub(' +',' ', text)
    text = text.replace(" ", "%20")
    #------------------------------------------

    url = '''https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20c
    ontentanalysis.analyze%20where%20text%3D%22'''+text+'''%22&format=json&
    callback='''

    url = url.replace(" ","%20")

    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)

        responeJSON = json.loads(response.read())

        if responeJSON['query']['count'] > 0:
            return responeJSON
        else:
            print "not result"
    except:
        print "yql exception"
        return None

def alchemy(text):

    api_key = ''

    # to clean the text------------------------
    regex = re.compile('[^a-zA-Z ]')
    text = regex.sub('', text)
    text = re.sub(' +',' ', text)
    text = text.replace(" ", "%20")
    #------------------------------------------

    url = '''
    http://gateway-a.watsonplatform.net/calls/text/TextGetRankedTaxonomy?
    apikey='''+api_key+'''&outputMode=json&text=%22'''+text+'''%22
    '''

    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)

        responeJSON = json.loads(response.read())

        return responeJSON

    except:
        raise


def annotate_return_entities(tweets):

    global wiki_urls

    for tweet in tweets:
        yql_annotations = yql(tweet)
        spotlight_annotations = spotlight(tweets)

        if yql_annotations is not None:
            get_yql_entities(yql_annotations)

        get_spotlight_entities(spotlight_annotations)

    wiki_urls = list(set(wiki_urls))

    return wiki_urls


def get_spotlight_entities(spotlight_annotations):

    global wiki_urls

    try:
        if 'Resources' in spotlight_annotations:
            for x in spotlight_annotations['Resources']:

                uri = x['@URI'].replace('http://dbpedia.org/resource/', '')
                wiki_urls.append(uri)

    except:
        #NOTE: non ASCII characters are causing an error here
        raise
        #pass


def get_yql_entities(yql_annotations):

    global wiki_urls

    results = yql_annotations['query']['results']

    if results['entities'] is not None:

        if isinstance(results['entities']['entity'], list):
            for entity in results['entities']['entity']:
                '''if 'types' in entity:
                    print entity['types']['type']'''

                if 'wiki_url' in entity:
                    wiki_url = entity['wiki_url']
                    wiki_url = wiki_url.replace('http://en.wikipedia.com/wiki/','')
                    wiki_urls.append(wiki_url)


        else:
            entity = results['entities']['entity']

            '''
            # Ignore for now
            if 'types' in entity:
                print entity['types']['type']
            '''

            if 'wiki_url' in entity:
                wiki_url = entity['wiki_url']
                wiki_url = wiki_url.replace('http://en.wikipedia.com/wiki/','')
                wiki_urls.append(wiki_url)
                #print wiki_url


if __name__ == "__main__":
    print annotate_return_entities(
        ['''Anti-immigration protests explode in Berlin with calls
        for Merkel resignation. USA Barak Obama''',
        'Bill Clinton and Donald Trump were running',
        'Donald Trump invited Bill clinton to have dinner later tonight',
        'Donald Trump'])
