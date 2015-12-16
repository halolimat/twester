#!/usr/bin/env python

################################################################################
# File name: wikipage_entities.py                                              #
# Description: This module retrieves all inner-links(entities) in a wikipage   #
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
import urllib2


def extract_links_from_api(url):

    req = urllib2.Request(url)
    response = urllib2.urlopen(req)

    responeJSON = json.loads(response.read())

    return responeJSON


def cleanup_result(inner_links):
    # Cleanup result
    final_wiki_links = []

    for inner_link in inner_links:

        if ('Category:' not in inner_link and
            'File:' not in inner_link and
            'Template:' not in inner_link):

            if "#" in inner_link:
                indexHashtag = inner_link.index("#")
                inner_link = inner_link[:indexHashtag]

            if "|" in inner_link:
                indexHashtag = inner_link.index("|")
                inner_link = inner_link[:indexHashtag]

            final_wiki_links.append(inner_link.replace(" ", "_"))

    return list(set(final_wiki_links))

def get_current_wiki_links(page):

    url = ('''https://en.wikipedia.org/w/api.php?action=query&page='''+
            page+'''&prop=links&action=parse&format=json&''')

    # links with non ascii names
    try:
        result = extract_links_from_api(url)

        result_set = []

        for link in result['parse']['links']:
            result_set.append(link['*'].replace(' ', '_'))

        return cleanup_result(result_set)


    except:
        return None


if __name__ == "__main__":

    page = "United_States_presidential_election,_2016"

    print get_current_wiki_links(page)
