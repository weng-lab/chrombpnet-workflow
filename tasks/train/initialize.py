#!/usr/bin/env python3

import os
import sys

def run(command, condition, message):
    if condition: return 0
    print(message, file = sys.stderr)
    return os.system(command)

def main():
    return sum([
        run(
            f"twoBitToFa /usr/local/genome/hg38.2bit {sys.argv[1]}/hg38.fa",
            os.path.exists(f"{sys.argv[1]}/hg38.fa"),
            "building hg38 FASTA"
        ),
        run(
            f"zcat /usr/local/genome/GRCh38-Anchors.bed.gz > {sys.argv[1]}/GRCh38-Anchors.bed",
            os.path.exists(f"{sys.argv[1]}/GRCh38-Anchors.bed"),
            "building anchors"
        ),
        run(f"head -24 /usr/local/genome/hg38.chrom.sizes > {sys.argv[1]}/hg38.minimal.chrom.sizes", False, "filtering chromosomes"),
        run(f"cp {sys.argv[1]}/hg38.minimal.chrom.sizes {sys.argv[1]}/hg38.chrom.sizes", False, "saving chromosomes")
    ])

if __name__ == "__main__":
    sys.exit(main())
