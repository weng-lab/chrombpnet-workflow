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
import itertools
import subprocess
from hmmlearn import hmm
from scipy.signal import convolve

EX_USAGE = 64
EX_NOINPUT = 66

def value_vector(bed, bigWig, expansion_size=500):
    with open(bed, 'r') as f:
        regions = [ (x.split()[0], int(x.split()[1]), int(x.split()[2])) for x in f ]
    regions = [ (x[0], int((x[1] + x[2]) / 2) - expansion_size, int((x[1] + x[2]) / 2) + expansion_size) for x in regions ]
    print(f"reading values for {len(regions)} regions")
    with pyBigWig.open(bigWig) as bw:
        values = []
        for i, (chromosome, start, end) in enumerate(regions):
            if i % 10000 == 0: print(f"working with region {i + 1} of {len(regions)}", file = sys.stderr)
            values.extend(bw.values(chromosome, start, end))
    return regions, numpy.nan_to_num(numpy.array(values), 0)

def z_threshold(x, d):
    s = numpy.std(x)
    m = numpy.mean(x)
    return m + s * 1.96 * d

def ghmm(data):
    model = hmm.MultinomialHMM(n_components=3, init_params='', params='ste')
    model.transmat_ = [[0.99639193, 0.0021334, 0.00147468], [0.1726586, 0.80259281, 0.0247486 ], [0.0842804, 0.01653451, 0.89918509]]
    model.emissionprob_ = [
        [9.98800471e-01, 7.71665149e-04, 4.27864194e-04],
        [5.97874631e-01, 4.01552650e-01, 5.72718809e-04],
        [4.56654445e-01, 1.57082808e-02, 5.27637275e-01]
    ]
    model.startprob_ = [1, 0, 0]
    model.fit(data)
    return model

def replace_single_zeros(arr):
    # Find indices of zeros surrounded by 1s or -1s
    zero_indices = np.where(arr == 0)[0]
    valid_indices = []
    for idx in zero_indices:
        if (idx > 0 and arr[idx - 1] in [1, -1]) and \
           (idx < len(arr) - 1 and arr[idx + 1] in [1, -1]):
            valid_indices.append(idx)

    # Update the zeros with corresponding neighboring numbers
    for idx in valid_indices:
        if arr[idx - 1] == 1:
            arr[idx] = 1
        elif arr[idx - 1] == -1:
            arr[idx] = -1

    return arr

def find_changes(arr):
    # Compute differences between adjacent elements
    diff = np.diff(arr)

    # Find indices where the differences are nonzero
    change_indices = np.nonzero(diff)[0] + 1

    # Create list of tuples containing the value and the index where it changes
    changes = [(arr[i], i) for i in change_indices if i < len(arr)]

    return changes

def find_runs(values):
    change_indexes = find_changes(replace_single_zeros(values))
    change_indexes.append((0, 1000))
    stretches = [[], [], []]
    for i, x in enumerate(change_indexes):
        if i == len(change_indexes) - 1: break
        if change_indexes[i + 1][1] - x[1] > 4:
            stretches[x[0]].append(( x[1], change_indexes[i + 1][1]))
    return stretches

def region_coordinates(x, model, states=None):
    if states is None: states = model.predict(x)
    state_runs = find_runs(states)[1:]
    zero_emission_runs = find_runs([ 0 if xx[0] == 1 else 1 for xx in x ])[0] if model is not None else find_runs(x)[0]
    return [ multirange_diff(x, zero_emission_runs) for x in state_runs ]

def range_diff(r1, r2):
    s1, e1 = r1
    s2, e2 = r2
    endpoints = sorted((s1, s2, e1, e2))
    result = []
    if endpoints[0] == s1:
        result.append((endpoints[0], endpoints[1]))
    if endpoints[3] == e1:
        result.append((endpoints[2], endpoints[3]))
    return result

def multirange_diff(r1_list, r2_list):
    for r2 in r2_list:
        r1_list = list(itertools.chain(*[range_diff(r1, r2) for r1 in r1_list]))
    return r1_list

def argument_parser():
    parser = argparse.ArgumentParser(description='use an HMM to identify important motifs from a ChromBPNet importance score bigWig')
    parser.add_argument('--bigwig', required=True, help='profile or count importance score bigWig')
    parser.add_argument("--bed", help='regions in which to find important motifs; if not passed, all consecutive regions with signal in the bigWig will be used')
    parser.add_argument("--positive-output", required=True, help='path to output positive importance region bigBed')
    parser.add_argument("--negative-output", required=True, help='path to output negative importance region bigBed')
    parser.add_argument("--gaussian-kernel-mode", action="store_true", help='if set, use Gaussian kernel smoothing rather than HMM to call regions')
    parser.add_argument("--gaussian-kernel-minimum", help='if provided, minimum curve value to be called significant by the Gaussian kernel method')
    return parser

def gaussian_kernel(size, sigma):
    x = np.arange(-size // 2 + 1, size // 2 + 1)
    kernel = np.exp(-x**2 / (2 * sigma**2))
    return kernel / np.sum(kernel)

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
    
    # make sure input bed exists; if it does not, generate one using regions in the bigWig that have signal
    temporary_bed = None
    if args.bed is None or not os.path.exists(args.bed):
        temporary_bed = tempfile.NamedTemporaryFile()
        args.bed = temporary_bed.name
        command = [
            sys.executable,
            os.path.join(os.path.dirname(os.path.realpath(__file__)), 'find-regions-with-signal.py'),
            args.bigwig,
            args.bed
        ]
        if subprocess.run(command).returncode != 0:
            print(f"unable to identify consecutive regions with signal in {args.bigwig}; check that it is appropriately formatted", file = sys.stderr)
            return EX_NOINPUT
        
    # get values at input regions
    print("loading signal values...", file = sys.stderr)
    regions, values = value_vector(args.bed, args.bigwig)

    # use Gaussian kernel to make predictions if requested
    if args.gaussian_kernel_mode:
        kernel_size = 50  # Adjust as needed
        sigma = 6.0  # Adjust as needed
        gaussian_kernel_values = gaussian_kernel(kernel_size, sigma)

        print("smoothing array...", file = sys.stderr)
        padded_array = np.pad(values, (kernel_size // 2, kernel_size // 2), mode='edge')
        smoothed_array = convolve(padded_array, gaussian_kernel_values, mode='valid')

        print(f"calling significant regions across {len(smoothed_array)} base pairs...", file = sys.stderr)
        cmin = 3 if args.gaussian_kernel_minimum is None else float(args.gaussian_kernel_minimum)
        calls = [ (1 * (-1 if x < 0 else 1)) if abs(x) > abs(smoothed_array[i] + cmin) else 0 for i, x in enumerate(values) ]
        important_regions = [ region_coordinates(calls[1000*i:1000*(i+1)], None, calls[1000*i:1000*(i+1)]) for i in range(len(regions)) ]

    else:
        
        # get thresholds
        v_log = numpy.log(numpy.abs(values)) * numpy.sign(values)
        v_log_abs = numpy.log(numpy.abs(values[values != 0]))
        pos_threshold = z_threshold(v_log[v_log > 0], -1)
        neg_threshold = z_threshold(v_log[v_log < 0], 1)
        all_threshold = -z_threshold(v_log_abs, 1)
        print(f"positive threshold: {pos_threshold}\nnegative threshold: {neg_threshold}\ncomplete threshold: {all_threshold}")

        # make HMM input
        v_thresholded = numpy.copy(v_log)
        v_thresholded = numpy.where(
            numpy.logical_and(v_thresholded > -all_threshold, v_thresholded < 0), 1, # set all positive contributors to 1
            np.where(
                np.logical_and(v_thresholded < all_threshold, v_thresholded > 0), -1, # set all negative contributors to -1
                0 # set all remaining to 0
            )
        )
        print(f"there are {len(v_thresholded[v_thresholded == -1])} negative regulating bases and {len(v_thresholded[v_thresholded == 1])} positive regulating bases")
        tvalues = numpy.array([ [ 0, 1, 0 ], [ 1, 0, 0 ], [ 0, 0, 1 ] ])
        prediction_input = numpy.array(tvalues)[numpy.nan_to_num(v_thresholded, 0) + 1]

        # get the important regions
        model = ghmm(prediction_input[:10000000])
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
    
    # close the temporary BED file if it was generated
    if temporary_bed is not None:
        temporary_bed.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
