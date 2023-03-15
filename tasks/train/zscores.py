#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
import joblib
import pysam
import math
import tempfile
import multiprocessing

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

def zscores(bam, bed):
    with open(bed, 'r') as f:
        regions = [(line.split()[0], int(line.split()[1]), int(line.strip().split()[2])) for line in f]
    raw_counts = extract_read_counts(bam, regions)
    non_zero = np.log(np.array([ x for x in raw_counts if x > 0 ]))
    mean = np.mean(non_zero)
    std = np.std(non_zero)
    return [ -10 if x == 0 else (math.log(x) - mean) / std for x in raw_counts ]

class ActiveRegions:

    def __init__(self, bam, bed, threshold=1.64):
        z = zscores(bam, bed)
        if not os.path.exists(f"{bam}.bai"): os.system(f"samtools index {bam}")
        self.bed = bed
        self.active_indexes = { i for i, x in enumerate(z) if x > threshold }

    def __enter__(self):
        self.tempfile = tempfile.NamedTemporaryFile('wt')
        with open(self.bed, 'r') as f:
            for i, x in enumerate(f):
                if i in self.active_indexes: self.tempfile.write(x)
        self.tempfile.flush()
        return self.tempfile
    
    def __exit__(self, *args):
        self.tempfile.close()
