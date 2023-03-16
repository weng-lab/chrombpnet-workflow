#!/usr/bin/env python3

"""
Some code in this script was generated in part with ChatGPT, OpenAI's large-scale
language-generation model. Upon generating draft code, the author reviewed, edited,
and revised the code to their own liking and takes ultimate responsibility for the
content of this script.
"""

import sys
import os
import pyBigWig
import numpy
import numpy as np
import argparse
import tempfile
from hmmlearn import hmm

EX_USAGE = 64
EX_NOINPUT = 66

def value_vector(bed, bigWig, expansion_size=500):
    with open(bed, 'r') as f:
        regions = [ (x.split()[0], int(x.split()[1]), int(x.split()[2])) for x in f ]
    regions = [ (x[0], int((x[1] + x[2]) / 2) - expansion_size, int((x[1] + x[2]) / 2) + expansion_size) for x in regions ]
    print(f"reading values for {len(regions)} regions")
    with pyBigWig.open(bigWig) as bw:
        values = []
        for chromosome, start, end in regions:
            values.extend(bw.values(chromosome, start, end))
    return regions, numpy.nan_to_num(numpy.array(values), 0)

def z_threshold(x, d):
    s = numpy.std(x)
    m = numpy.mean(x)
    return m + s * 2 * d

def ghmm():
    model = hmm.MultinomialHMM(n_components=3, init_params='', params='')
    model.transmat_ = [[0.99639193, 0.0021334, 0.00147468], [0.1726586, 0.80259281, 0.0247486 ], [0.0842804, 0.01653451, 0.89918509]]
    model.emissionprob_ = [
        [9.98800471e-01, 7.71665149e-04, 4.27864194e-04],
        [5.97874631e-01, 4.01552650e-01, 5.72718809e-04],
        [4.56654445e-01, 1.57082808e-02, 5.27637275e-01]
    ]
    model.startprob_ = [1, 0, 0]
    model.fit(numpy.array([[ 1, 0, 0 ]]))
    return model

def find_changes(arr):
    # Compute differences between adjacent elements
    diff = np.diff(arr)

    # Find indices where the differences are nonzero
    change_indices = np.nonzero(diff)[0] + 1

    # Create list of tuples containing the value and the index where it changes
    changes = [(arr[i], i) for i in change_indices]

    return changes

def region_coordinates(x, model):
    states = model.predict(x)
    change_indexes = find_changes(states)
    change_indexes.append((0, 1000))
    stretches = [[], []]
    for i, x in enumerate(change_indexes):
        if i == len(change_indexes) - 1: break
        if x[0] == 0: continue
        if x[0] >= 1 and change_indexes[i + 1][1] - x[1] > 4:
            stretches[x[0] - 1].append(( x[1], change_indexes[i + 1][1]))
    return stretches

def argument_parser():
    parser = argparse.ArgumentParser(description='use an HMM to identify important motifs from a ChromBPNet importance score bigWig')
    parser.add_argument('--bigwig', required=True, help='profile or count importance score bigWig')
    parser.add_argument("--bed", required=True, help='regions in which to find important motifs')
    parser.add_argument("--positive-output", required=True, help='path to output positive importance region bigBed')
    parser.add_argument("--negative-output", required=True, help='path to output negative importance region bigBed')
    return parser

def main():

    # check arguments
    parser = argument_parser()
    try:
        args = parser.parse_args()
    except argparse.ArgumentError as error:
        # Print a usage message
        print(f"error: {error}")
        parser.print_usage()
        return EX_USAGE

    # make sure input bigWig exists
    if not os.path.exists(args.bigwig):
        print(f"{args.bigwig} does not exist", file = sys.stderr)
        return EX_NOINPUT
    
    # make sure input bed exists
    if not os.path.exists(args.bed):
        print(f"{args.bigwig} does not exist", file = sys.stderr)
        return EX_NOINPUT
    
    # get values at input regions
    regions, values = value_vector(args.bed, args.bigwig)

    # get thresholds
    v_log = numpy.log(numpy.abs(values)) * numpy.sign(values)
    pos_threshold = z_threshold(v_log[v_log > 0], -1)
    neg_threshold = z_threshold(v_log[v_log < 0], 1)
    print(f"positive threshold: {pos_threshold}\nnegative threshold: {neg_threshold}")

    # make HMM input
    v_thresholded = numpy.copy(v_log)
    v_thresholded = numpy.where(
        numpy.logical_and(v_thresholded > neg_threshold, v_thresholded < 0), 1, # set all positive contributors to 1
        np.where(
            np.logical_and(v_thresholded < pos_threshold, v_thresholded > 0), -1, # set all negative contributors to -1
            0 # set all remaining to 0
        )
    )
    print(f"there are {len(v_thresholded[v_thresholded == -1])} negative regulating bases and {len(v_thresholded[v_thresholded == 1])} positive regulating bases")
    tvalues = numpy.array([ [ 0, 1, 0 ], [ 1, 0, 0 ], [ 0, 0, 1 ] ])
    prediction_input = numpy.array(tvalues)[numpy.nan_to_num(v_thresholded, 0) + 1]

    # get the important regions
    model = ghmm()
    important_regions = [ region_coordinates(prediction_input[1000*i:1000*(i+1)], model) for i in range(len(regions)) ]

    # write the negative importance regions
    with tempfile.NamedTemporaryFile('wt') as negative_regions:
        for i, x in enumerate(important_regions):
            for start, end in x[0]:
                negative_regions.write(f"{regions[i][0]}\t{regions[i][1] + start}\t{regions[i][1] + end}\n")
        negative_regions.flush()
        with tempfile.NamedTemporaryFile() as negative_sorted:
            os.system(f"sort -k1,1 -k2,2n {negative_regions.name} > {negative_sorted.name}")
            os.system(f"bedToBigBed {negative_sorted.name} /usr/local/genome/hg38.chrom.sizes {args.negative_output}")
    
    # write the positive importance regions
    with tempfile.NamedTemporaryFile('wt') as positive_regions:
        for i, x in enumerate(important_regions):
            for start, end in x[1]:
                positive_regions.write(f"{regions[i][0]}\t{regions[i][1] + start}\t{regions[i][1] + end}\n")
        positive_regions.flush()
        with tempfile.NamedTemporaryFile() as positive_sorted:
            os.system(f"sort -k1,1 -k2,2n {positive_regions.name} > {positive_sorted.name}")
            os.system(f"bedToBigBed {positive_sorted.name} /usr/local/genome/hg38.chrom.sizes {args.positive_output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
