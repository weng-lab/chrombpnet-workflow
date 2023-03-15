#!/usr/bin/env python3

"""
This script was generated in part with ChatGPT, OpenAI’s large-scale language-generation model.
Upon generating draft code, the author reviewed, edited, and revised the code to their own liking
and takes ultimate responsibility for the content of this script.
"""

import os
import sys
import pandas as pd

EX_USAGE = 64
EX_NOINPUT = 66

def main(argc, argv):

    # check for proper number of arguments
    if argc < 3:
        print("usage: bed3-to-narrowpeak.py input.bed3 output.narrowPeak", file = sys.stderr)
        return EX_USAGE

    # check that input file exists
    if not os.path.exists(argv[1]):
        print(f"{argv[1]} does not exist.", file = sys.stderr)
        return EX_NOINPUT

    # Read the 3-column BED file
    bed = pd.read_csv(argv[1], header=None, sep='\t', usecols=[0, 1, 2], names=["chrom", "start", "end"])
    bed["start"] = bed["start"].astype(int)
    bed["end"] = bed["end"].astype(int)
    
    # Compute the summit as the midpoint of the region
    bed["summit"] = ((bed["end"].astype(int) - bed["start"].astype(int)) / 2).astype(int)

    # Add columns with fixed values for narrowPeak format
    bed["name"] = "."
    bed["score"] = "0"
    bed["strand"] = "."
    bed["signalValue"] = "0"
    bed["pValue"] = "1"
    bed["qValue"] = "1"

    # Reorder columns to match narrowPeak format
    bed = bed[["chrom", "start", "end", "name", "score", "strand", "summit", "signalValue", "pValue", "qValue"]]

    # Write the narrowPeak file
    bed.to_csv(argv[2], sep="\t", header=False, index=False)

    return 0

if __name__ == "__main__":
    sys.exit(main(len(sys.argv), sys.argv))
