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

EX_USAGE = 64
EX_NOINPUT = 66

def write_bed_file(regions, output_filename):
    with open(output_filename, 'w') as bed_file:
        for i, region in enumerate(regions):
            chrom, start, end = region
            bed_file.write(f"{chrom}\t{start}\t{end}\tregion_{i}\n")

def main(argc, argv):
    
    if argc < 2:
        print("usage: find-regions-with-signal.py input.bigWig output.bed", file = sys.stderr)
        return EX_USAGE

    if not os.path.exists(argv[1]):
        print(f"{argv[1]} does not exist", file = sys.stderr)
        return EX_NOINPUT

    bigwig_file = pyBigWig.open(argv[1])
    regions = []  # List to store regions with signal

    for chrom in bigwig_file.chroms():
        chromosome_regions = []
        
        # Iterate through intervals with signal
        if bigwig_file.intervals(chrom) is None: continue
        for interval in bigwig_file.intervals(chrom):
            start, end, signal = interval
            chromosome_regions.append((chrom, start, end))
        
        # Merge regions for this chromosome and store
        chromosome_regions = sorted(chromosome_regions, key = lambda r: r[1])
        final_regions = [ chromosome_regions[0] ]
        for c, s, e in chromosome_regions[1:]:
            if s == final_regions[-1][-1]:
                final_regions[-1] = (c, final_regions[-1][1], e)
            else: final_regions.append((c, s, e))
        regions += final_regions
        print(f"found {len(final_regions)} regions with signal on {chrom}", file = sys.stderr)

    # Write the regions to the BED file
    write_bed_file(regions, argv[2])

    # Close the bigWig file
    bigwig_file.close()

    return 0

if __name__ == "__main__":
    sys.exit(main(len(sys.argv), sys.argv))
