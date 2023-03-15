#!/usr/bin/env python3

import sys
import os
import tempfile

from joblib import Parallel, delayed

def convert(a, b):
    with tempfile.NamedTemporaryFile() as f:
        return os.system(f"bigWigToBedGraph {a} {f.name}") + os.system(f"sort -k1,1 -k2,2n {f.name} > {b}")

def main(argc, argv):

    if argc < 3:
        print("usage: bigwigmerge output.bigwig input1.bigwig [input2.bigwig ...]", file = sys.stderr)
        return 1

    bedGraphs = [ tempfile.NamedTemporaryFile() for _ in argv[2:] ]
    Parallel(n_jobs = -1)(delayed(convert)(x, bedGraphs[i].name) for i, x in enumerate(argv[2:]))

    with tempfile.NamedTemporaryFile('wt') as f:
        os.system("""
            bedtools unionbedg
                -i %s
                -filler NA -header
            | awk 'BEGIN {OFS="\\t"} {sum=0; count=0; for(i=4;i<=NF;i++){if($i!="NA"){sum+=$i;count++}}; if(count>0){$4=sum/count; print}}'
            | cut -f1-4 > %s
        """.replace("\n", " ") % (' '.join([ x.name for x in bedGraphs ]), f.name))
        for x in bedGraphs:
            x.close()
        return os.system(f"bedGraphToBigWig {f.name} /usr/local/genome/hg38.chrom.sizes {argv[1]}")

if __name__ == "__main__":
    sys.exit(main(len(sys.argv), sys.argv))
