#!/usr/bin/env python

################################################################################
# File name: tf.py                                                             #
# Description: This module return all terms frequences in a given wikipage     #
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
import os
import xml
import nltk
import string
import urllib2
import collections
from collections import Counter
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem.porter import PorterStemmer


stemmer = PorterStemmer()
cachedStopWords = stopwords.words("english")


def tf(word, blob):
    return blob.words.count(word) / len(blob.words)

def n_containing(word, bloblist):
    return sum(1 for blob in bloblist if word in blob)

def idf(word, bloblist):
    return math.log(len(bloblist) / (1 + n_containing(word, bloblist)))

def tfidf(word, blob, bloblist):
    return tf(word, blob) * idf(word, bloblist)


#-------------------------------------------------------------------------------
# nltk -------------------------------------------------------------------------

def stem_tokens(tokens, stemmer):
    stemmed = []
    for item in tokens:
        stemmed.append(stemmer.stem(item))
    return stemmed


def tokenize(text):
    tokens = nltk.word_tokenize(text)
    stems = stem_tokens(tokens, stemmer)
    return stems

#-------------------------------------------------------------------------------

# Removes all html tags from text
def remove_tags(text):
    return ''.join(xml.etree.ElementTree.fromstring(text).itertext())


def get_frequencies_wikipage(wikipage):
    url = 'https://en.wikipedia.org/wiki/'+wikipage

    req = urllib2.Request(url)
    response = urllib2.urlopen(req)

    text = remove_tags(response.read())
    regex = re.compile('[^a-zA-Z]')
    text = regex.sub(' ', text)

    text = ' '.join([word for word in text.split() if word not in cachedStopWords])

    text = text.split(" ")

    str_list = filter(None, text)

    y = [s for s in str_list if len(s) > 3]

    return collections.Counter(y)


if __name__ == "__main__":

    wikipage = 'United_States_presidential_election,_2016'

    print get_frequencies_wikipage(wikipage)
