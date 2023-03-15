#!/usr/bin/env python3

import sys
import os
import tempfile

from joblib import Parallel, delayed

def convert(a, b):
    return os.system(f"bigWigToBedGraph {a} {b}")

def sort_and_merge(output, *args):
    with tempfile.NamedTemporaryFile('rt') as f:
        os.system(f"cat {' '.join(args)} | sort -k1,1 -k2,2n > {f.name}")
        found = set()
        for line in f:
            key = tuple(line.split()[:2])
            if key in found: continue
            found.add(key)
            output.write(line)
    output.flush()

def main(argc, argv):

    if argc < 3:
        print("usage: bigwigmerge output.bigwig input1.bigwig [input2.bigwig ...]", file = sys.stderr)
        return 1

    bedGraphs = [ tempfile.NamedTemporaryFile() for _ in argv[2:] ]
    Parallel(n_jobs = -1)(delayed(convert)(x, bedGraphs[i].name) for i, x in enumerate(argv[2:]))

    with tempfile.NamedTemporaryFile('wt') as f:
        sort_and_merge(f, *[ x.name for x in bedGraphs ])
        return os.system(f"bedGraphToBigWig {f.name} /usr/local/genome/hg38.chrom.sizes {argv[1]}")

if __name__ == "__main__":
    sys.exit(main(len(sys.argv), sys.argv))
