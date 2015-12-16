#!/usr/bin/env python

################################################################################
# File name: similarities.py                                                   #
# Description: This module measures the jaccard and cosine similarities        #
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


import math
from collections import Counter


# Cosine similarity as in:
# https://en.wikipedia.org/wiki/Cosine_similarity#Definition
def cosine_similarity(c1, c2):
    terms = set(c1).union(c2)
    dotprod = sum(c1.get(k, 0) * c2.get(k, 0) for k in terms)
    magA = math.sqrt(sum(c1.get(k, 0)**2 for k in terms))
    magB = math.sqrt(sum(c2.get(k, 0)**2 for k in terms))

    denominator = (magA * magB)

    if denominator == 0:
        return 0

    else:
        return dotprod / denominator


# Jaccard Similarity as in:
# https://en.wikipedia.org/wiki/Jaccard_index
def jaccard_similarity(c1, c2):
    intersection_cardinality = float(len(set(c1).intersection(c2)))
    union_cardinality = float(len(set(c1).union(c2)))

    return intersection_cardinality/union_cardinality


if __name__ == "__main__":
    dataSetI = Counter(["hussein", "Al-Olimat", "Yes", "Knoesis", "hussein"])
    dataSetII = Counter(["hussein", "Knoesis", "no"])

    print cosine_similarity(dataSetI, dataSetII)
    print jaccard_similarity(dataSetI, dataSetII)
