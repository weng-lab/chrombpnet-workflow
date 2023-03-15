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
            "twoBitToFa /usr/local/genome/hg38.2bit /usr/local/genome/hg38.fa",
            os.path.exists("/usr/local/genome/hg38.fa"),
            "building hg38 FASTA"
        ),
        run(
            "gunzip /usr/local/genome/GRCh38-Anchors.bed.gz",
            os.path.exists("/usr/local/genome/GRCh38-Anchors.bed"),
            "building anchors"
        ),
        run("head -24 /usr/local/genome/hg38.chrom.sizes > /usr/local/genome/hg38.minimal.chrom.sizes", False, "filtering chromosomes"),
        run("mv /usr/local/genome/hg38.minimal.chrom.sizes /usr/local/genome/hg38.chrom.sizes", False, "saving chromosomes")
    ])

if __name__ == "__main__":
    sys.exit(main())
