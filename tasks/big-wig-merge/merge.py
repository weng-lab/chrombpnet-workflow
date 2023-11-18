#!/usr/bin/env python3

import sys
import os
import tempfile

from joblib import Parallel, delayed

def convert(a, b):
    with tempfile.NamedTemporaryFile() as f:
        return os.system(f"bigWigToBedGraph {a} {f.name}") + os.system(f"sort -k1,1 -k2,2n {f.name} > {b}")

def main(argc, argv):

    if argc < 4:
        print("usage: bigwigmerge assembly output.bigwig input1.bigwig [input2.bigwig ...]", file = sys.stderr)
        return 1

    bedGraphs = [ tempfile.NamedTemporaryFile() for _ in argv[3:] ]
    Parallel(n_jobs = -1)(delayed(convert)(x, bedGraphs[i].name) for i, x in enumerate(argv[3:]))

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
        if os.path.exists(f"/usr/local/genome/{argv[1]}.chrom.sizes"):
            return os.system(f"bedGraphToBigWig {f.name} /usr/local/genome/{argv[1]}.chrom.sizes {argv[2]}")
        with tempfile.NamedTemporaryFile() as c:
            os.system(f"wget https://hgdownload.soe.ucsc.edu/goldenPath/{argv[1]}/bigZips/{argv[1]}.chrom.sizes -O {c.name}")
            return os.system(f"bedGraphToBigWig {f.name} {c.name} {argv[2]}")

if __name__ == "__main__":
    sys.exit(main(len(sys.argv), sys.argv))
