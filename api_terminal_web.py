#!/usr/bin/env python

################################################################################
# File name: api_terminal_web.py                                               #
# Description: This module implements a simple webapp to use use the data      #
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
import time
import base64
import datetime
import operator
import collections
import networkx as nx
from json import dumps
from bson import ObjectId
from bottle import response
from dateutil import parser
from json import JSONEncoder
from bson import Binary, Code
from tabulate import tabulate
from datetime import timedelta
import matplotlib.pyplot as plt
from pymongo import MongoClient
from collections import Counter
from bson.json_util import dumps
from multiprocessing import Process
from collections import defaultdict
from collections import OrderedDict
from gevent import monkey; monkey.patch_all()
from bottle import Bottle, run, response, post, get, request, static_file


import similaritites
import db_operations
import stream_tweets
import search_twitter
import wikipage_entities
import annotate_tweets


#-------------------------------------------------------------------------------
last_time = datetime.datetime.utcnow()# - timedelta(minutes=20)
hashtag_freq = defaultdict(int)

app = Bottle()
#-------------------------------------------------------------------------------

@app.get('/twester')
def twester():

    sessions = []

    html = '''<select name="state" id="mySelect" onchange="myFunction()"
                style="width: 200px;height: 40px;">'''

    html += '<option value="">Select one</option>'

    for session in db_operations.get_sessions():
        html += ('<option value="'+session['_id']+'">'
                    +session['_id']+'</option>\n')

    html += '</select>'

    html += '''
        <p id="demo"></p>

        <script type="text/javascript"
                src="//cdn.jsdelivr.net/jquery/1/jquery.min.js"></script>

        <script>
            function myFunction() {
                var x = document.getElementById("mySelect").value;

                $.get( '/get_data/'+x+'', function(newRowCount){
                        $('#demo').html( newRowCount );
                    });
            }
        </script>
    '''

    return html


@app.post('/get_data/<vars>', method='GET')
def get_data(vars):

    main_hashtag = vars[:-4].lower()

    result = db_operations.get_sessions_data(vars)

    html = '''
        <head>
        <style>
        div.scroll {
            height: 50%;
            float:left;
            table-layout: auto;

            overflow-x: hidden;
            overflow-y: scroll;

	        font-size:11px;
            font-family: verdana,arial,sans-serif;

        	color:#333333;

            border-width: 1px;
        	border-color: #666666;
        	border-collapse: collapse;
        }

        table, td, th {
            border: 1px solid black;
        }

        </style>
        </head>
    '''

    # For graph
    edgelist = []

    cosine_similarities = dict()
    # outputs data in tables as is
    for x in result[0]:
        if x not in ["_id",'coochashtags1', 'coochashtags2', 'coochashtags3',
                        'coochashtags4']:

            label = x

            #renaming dict key- to make it more user friendly
            if 'coochashtags5' in x:
                label = 'Main#Cooccurences'
            elif 'wikipage_hashtags' in x:
                label = 'Wiki-based Scores'


            html += ('<div class="scroll"><table><caption><h2>'+
                        label+'</h2></caption>')

            tmp_1 = collections.OrderedDict(sorted(result[0][x].items(),
                        key=operator.itemgetter(1), reverse=True))

            for y in tmp_1:
                if (x in "wikipage_hashtags" and
                    y not in "hashtag-taxonomies" and
                    y not in "hashtag-cooc"):

                    html += '<tr><th colspan="2">'+y+'</th></tr>'

                    tmp_2 = collections.OrderedDict(
                                sorted(result[0][x][y].items(),
                                key=operator.itemgetter(1), reverse=True))

                    for z in tmp_2:
                        if not z.isdigit():
                            html += ('<tr><td>'+z+'</td><td>'+
                                        str(result[0][x][y][z])+'</td></tr>')

                            if 'cosine_sim' in y :
                                cosine_similarities[z] = result[0][x][y][z]

                elif y not in "hashtag-taxonomies" and y not in "hashtag-cooc":
                    if not y.isdigit():
                        html += ('<tr><td>'+y+'</td><td>'+
                                    str(result[0][x][y])+'</td></tr>')

                        # Start building edges for the graph
                        edgelist.append((main_hashtag, y, result[0][x][y]))

            html += '</table></div>'

    # ~~~~~~~~~~ taxonomies ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # change hashtag-taxonomies => to => Cooccured Hashtags Taxonomies

    hashtag_taxonomies_scores = dict()

    max = 0

    if 'wikipage_hashtags' in result[0]:
        if 'hashtag-taxonomies' in result[0]['wikipage_hashtags']:

            # Used to biase the taxonomies
            event_theme = get_event_theme()
            hastag_vector = {}

            taxonomies = result[0]['wikipage_hashtags']['hashtag-taxonomies']

            for hashtag in taxonomies:

                hashtag_tax_score = 0

                for taxonomy in taxonomies[hashtag]:
                    #NOTE: this taxonomy level-1 is given based on the chosen theme
                    # this can be made as a drop-down list to make the user choose

                    if 'label' in taxonomy:
                        if "law, govt and politics" in taxonomy['label']:
                            hashtag_tax_score += float(taxonomy['score'])


                hashtag_taxonomies_scores[hashtag] = hashtag_tax_score

            # create html table from data --------------------------------------

            hashtag_taxonomies_scores_sorted = collections.OrderedDict(
                sorted(hashtag_taxonomies_scores.items(),
                key=operator.itemgetter(1), reverse=True))


            html += '''<div class="scroll"><table><caption>
                            <h2>Co-Hashtags Taxonomies</h2></caption>'''

            for hashtag in hashtag_taxonomies_scores_sorted:
                html += ('<tr><td>'+hashtag+'</td><td>'+
                        str(hashtag_taxonomies_scores_sorted[hashtag])+
                        '</td></tr>')


        html += '</table></div>'

    # ~~~~~~~~~~ taxonomies ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # ~~~~~~~~~~ cooc-hashtags ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Output the cooccurrences of a hashtag, the frequency and the score of each
    #   of each hashtag in the set of hashtags

    # Change hashtag-cooc => to => Co-Hashtags-Cooccurences

    hashtag_cooc_dict = dict()

    if 'wikipage_hashtags' in result[0]:
        if 'hashtag-cooc' in result[0]['wikipage_hashtags']:

            html += '''<div class="scroll"><table><caption>
                        <h2>Co-Hashtags-Cooccurences</h2></caption>'''

            for hashtag in result[0]['wikipage_hashtags']['hashtag-cooc']:


                hashtag_cooc_dict[hashtag] = 0

                html += '<tr><th colspan="3">'+hashtag+'</th></tr>'

                counter=collections.Counter(
                    result[0]['wikipage_hashtags']['hashtag-cooc'][hashtag])

                counter = collections.OrderedDict(
                            sorted(counter.items(),
                            key=operator.itemgetter(1), reverse=True))

                #NOTE: this for fixing the cosine similarity
                sum_cooccurences = 0

                for hash in counter:
                    if hash not in hashtag:
                        sum_cooccurences += counter[hash]


                for hash in counter:
                    if hash not in hashtag:
                        html += ('<tr><td>'+hash+'</td><td>'+
                                    str(counter[hash])+
                                    '</td><td>'+
                                    str(counter[hash]/float(sum_cooccurences))+
                                    '</td></tr>')

                        # This is for the evaluration part
                        if main_hashtag in hash:
                            hashtag_cooc_dict[hashtag] = (counter[hash]/
                                                        float(sum_cooccurences))



                        if counter[hash] > 1:
                            edgelist.append((hashtag, hash, counter[hash]))

            html += '</table></div>'

    # ~~~~~~~~~~ cooc-hashtags ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Normalize data and multiply score by cosine similarity

    cooc_result = dict()

    if cosine_similarities is not None:
        for x in cosine_similarities.keys():
            if x in cosine_similarities and x in hashtag_cooc_dict:
                cooc_result[x] = cosine_similarities[x] * hashtag_cooc_dict[x]


        # normalize
        min = sys.maxint
        max = 0
        for x in cooc_result.keys():
            if cooc_result[x] < min:
                min = cooc_result[x]
            if cooc_result[x] > max:
                max = cooc_result[x]

        for x in cooc_result.keys():
            cooc_result[x] = (cooc_result[x]-min)/(max-min)

        cooc_result_normalized = normalize_data(cooc_result)
        hashtag_taxonomies_scores_normalized = (
                normalize_data(hashtag_taxonomies_scores) )

        final_ranking = dict()

        for x in cooc_result_normalized:
            final_ranking[x] = cooc_result_normalized[x] * (
                                    hashtag_taxonomies_scores_normalized[x])


        final_ranking = collections.OrderedDict(sorted(final_ranking.items(),
                            key=operator.itemgetter(1), reverse=True))


        #------------------------------

        if final_ranking:

            html += '''<div class="scroll"><table><caption>
                            <h2>Recommended-Hashtags</h2></caption>'''

            for x in final_ranking:
                html += '<tr><td>'+x+'</td><td>'+str(final_ranking[x])+'</td></tr>'

            html += '</table></div>'

    # Graph --------------------------------------------------------------------
    if edgelist:

        # Creates a directed graph of the cooccurrences of the cooccured hashtag
        create_graph(edgelist)

        with open("directed.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())

        html += ('<img src="data:image/png;base64,'+encoded_string+
                    '" alt="Red dot" />')


    return html


def normalize_data(dict):
    # normalize
    min = sys.maxint
    max = 0
    for x in dict.keys():
        if dict[x] < min:
            min = dict[x]
        if dict[x] > max:
            max = dict[x]

    for x in dict.keys():
        max_minus_min = max-min

        if not max_minus_min == 0:
            dict[x] = (dict[x]-min)/(max-min)

        # when there is only one item
        else:
            dict[x] = 1

    return dict

def create_graph(edgelist):

    G = nx.DiGraph()

    G.add_weighted_edges_from(edgelist)

    # Graph layout
    pos = nx.spring_layout(G)

    # Remove nodes with out-degree = 1------------------------------------------

    outdeg = nx.degree(G)

    while 1 in outdeg.values():

        to_remove = [n for n in outdeg if outdeg[n] == 1]

        G.remove_nodes_from(to_remove)

        # Remove edges also checking the two values of the tuple
        edgelist = [x for x in edgelist if x[0] not in to_remove]
        edgelist = [x for x in edgelist if x[1] not in to_remove]

        outdeg = nx.degree(G)
    #---------------------------------------------------------------------------

    # Node size ================================================================

    d = nx.degree(G)

    nx.draw_networkx_nodes(G, pos, nodelist=d.keys(),
                node_size=[v * 100 for v in d.values()])

    #===========================================================================

    nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'), node_size=1)

    edge_labels=dict([((u,v,),d['weight']) for u,v,d in G.edges(data=True)])

    nx.draw_networkx_edges(G,pos,width=0.5,alpha=0.2)

    nx.draw_networkx_edge_labels(G,pos,edge_labels=edge_labels)

    labels = {}

    for node in G.nodes():
        labels[node] = node

    nx.draw_networkx_labels(G,pos,labels,font_size=8)

    if not len(G) == 1:

        from networkx.algorithms import approximation as apxm

        print apxm.min_edge_dominating_set(G)
        print apxm.max_clique(G)
        print apxm.maximum_independent_set(G)
        print apxm.min_maximal_matching(G)

        print nx.degree_centrality(G)


    plt.savefig("directed.png") # save as png

    # clean old graph
    plt.clf()


def get_event_theme():

    politics = ["law, govt and politics","immigration","government",
    "courts and judiciary","embassies and consulates","executive branch",
    "government agencies","government contracting and procurement",
    "heads of state","legislative","parliament","state and local government",
    "espionage and intelligence","secret service","surveillance","terrorism",
    "commentary","armed forces","air force","army","marines","navy","veterans",
    "law enforcement","coast guard","fire department","highway patrol","police",
    "legal issues","civil law","civl rights","criminal law","death penalty",
    "human rights","international law","legislation","politics",
    "domestic policy","elections","foreign policy","lobbying",
    "political parties"]

    theme = politics

    return theme


#get_data('Trump2016-005')

#-------------------------------------------------------------------------------
run(app, host='0.0.0.0', port=8081, server='gevent')
