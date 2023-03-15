#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
import joblib
import pysam
import math
import tempfile
import multiprocessing
import gzip

def count_reads_in_regions(bam_file, regions):
    """Count the number of reads in a BAM file for a list of regions using pysam."""
    bam = pysam.AlignmentFile(bam_file, "rb")
    read_counts = [bam.count(region[0], region[1], region[2]) for region in regions]
    bam.close()
    return read_counts

def extract_read_counts(bam_file, regions, n_jobs=-1):
    """Extract read counts from a BAM file for a list of regions using joblib."""
    batch_size = math.ceil(len(regions) / (n_jobs if n_jobs > 0 else multiprocessing.cpu_count()))
    batches = [regions[i:i + batch_size] for i in range(0, len(regions), batch_size)]
    read_counts = joblib.Parallel(n_jobs=n_jobs)(joblib.delayed(count_reads_in_regions)(bam_file, batch) for batch in batches)
    return sum(read_counts, [])

def zscores(raw_counts):
    non_zero = np.log(np.array([ x for x in raw_counts if x > 0 ]))
    mean = np.mean(non_zero)
    std = np.std(non_zero)
    return [ -10 if x == 0 else (math.log(x) - mean) / std for x in raw_counts ]

def bam_zscores(bam, bed):
    with open(bed, 'r') as f:
        regions = [(line.split()[0], int(line.split()[1]), int(line.strip().split()[2])) for line in f]
    return zscores(extract_read_counts(bam, regions))

def fragment_zscores(fragment, bed):
    with (gzip.open if bed.endswith(".gz") else open)(bed, 'rt') as f:
        region_order = [ tuple(line.split()[:3]) for line in f ]
    region_counts = { k: 0 for k in region_order }
    with tempfile.NamedTemporaryFile('rt') as bed3:
        with tempfile.NamedTemporaryFile('rt') as intersection:
            z = 'z' if bed.endswith(".gz") else ''
            os.system(f"{z}cat {bed} | cut -f1-3 > {bed3.name}")
            os.system(f"bedtools intersect -a {bed3.name} -b {fragment} -wa -wb > {intersection.name}")
            for line in intersection:
                region_counts[tuple(line.split()[:3])] += int(line.split()[-2])
    return zscores([ region_counts[k] for k in region_order ])

def is_bam(path):
    try:
        pysam.AlignmentFile(path)
        return True
    except:
        return False

class ActiveRegions:

    def __init__(self, input_file, bed, threshold=1.64):
        if is_bam(input_file):
            z = bam_zscores(input_file, bed)
            if not os.path.exists(f"{input_file}.bai"): os.system(f"samtools index {input_file}")
        else:
            z = fragment_zscores(input_file, bed)
        self.bed = bed
        self.active_indexes = { i for i, x in enumerate(z) if x > threshold }

    def __enter__(self):
        self.tempfile = tempfile.NamedTemporaryFile('wt')
        with open(self.bed, 'r') as f:
            for i, x in enumerate(f):
                if i in self.active_indexes: self.tempfile.write(x)
        self.tempfile.flush()
        return self.tempfile
    
    def __exit__(self, *_):
        self.tempfile.close()
