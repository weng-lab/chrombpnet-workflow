#!/usr/bin/env python3

import os
import sys
import tempfile
import argparse

from zscores import ActiveRegions
from combinedbams import CombinedBAMs

EX_USAGE = 64
EX_NOINPUT = 66

def cargs():
    parser = argparse.ArgumentParser(description='train a human ChromBPNet model using V4 anchors')
    parser.add_argument('--bams', nargs='+', help='input BAMs')
    parser.add_argument('--bias_output_directory', help='bias model output directory')
    parser.add_argument('--model_output_directory', help='model output directory')
    parser.add_argument('--bias_model', nargs='?', help='(optional) path to existing bias model')
    return parser.parse_args()

def main():

    # check arguments
    try:
        args = cargs()
    except argparse.ArgumentError as error:
        # Print a usage message
        print(f"error: {error}")
        parser.print_usage()
        return EX_USAGE
    
    # make sure input files exist
    for input_file in args.bams:
        if not os.path.exists(input_file):
            print(f"{input_file} does not exist", file = sys.stderr)
            return EX_NOINPUT
    
    # make sure sequence is initialized
    initialized = os.system("initialize.py")
    if initialized != 0:
        print("unable to initialize hg38 genome sequence", file = sys.stderr)
        return initialized

    # convert input BED files to narrowPeak
    chromosomes = " ".join([ f"chr{i}" for i in range(1, 23) ] + [ "chrX", "chrY" ])
    with CombinedBAMs(args.bams, chromosomes) as filtered_bam:
        with ActiveRegions(filtered_bam.name, "/usr/local/genome/GRCh38-Anchors.bed") as peaks:
            with tempfile.NamedTemporaryFile() as nonpeaks:

                # convert BEDs to narrowPeak
                with tempfile.TemporaryDirectory() as d:
                    bed_conversion = sum([
                        os.system(f"bed3-to-narrowpeak.py {peaks.name} {peaks.name}.narrowPeak && mv {peaks.name}.narrowPeak {peaks.name}"),
                        os.system(f"chrombpnet prep nonpeaks -g /usr/local/genome/hg38.fa -p {peaks.name} -c  /usr/local/genome/hg38.chrom.sizes -fl /usr/local/genome/fold.json -o {d}"),
                        os.system(f"mv {d}_auxiliary/negatives.bed {nonpeaks.name}"),
                        os.system(f"bed3-to-narrowpeak.py {nonpeaks.name} {nonpeaks.name}.narrowPeak && mv {nonpeaks.name}.narrowPeak {nonpeaks.name}")
                    ])
                if bed_conversion != 0:
                    print("unable to convert BED files to narrowPeak", file = sys.stderr)
                    return bed_conversion

                # train the bias model
                bias_model = args.bias_model if args.bias_model is not None else os.path.join(args.bias_output_directory, "models", "bias.h5")
                if not os.path.exists(bias_model):
                    bias_training = os.system(f"""
                        chrombpnet bias pipeline
                            -ibam {filtered_bam.name}
                            -d \"ATAC\"
                            -g /usr/local/genome/hg38.fa
                            -c /usr/local/genome/hg38.chrom.sizes
                            -p {peaks.name}
                            -n {nonpeaks.name}
                            -fl /usr/local/genome/fold.json
                            -b 1000
                            -o {args.bias_output_directory}
                        """.replace("\n", " "))
                    if bias_training != 0:
                        print("unable to train bias model", file = sys.stderr)
                        return bias_training
                
                # train the model
                return os.system(f"""
                    chrombpnet pipeline
                        -ibam {filtered_bam.name}
                        -d \"ATAC\"
                        -g /usr/local/genome/hg38.fa
                        -c /usr/local/genome/hg38.chrom.sizes
                        -p {peaks.name}
                        -n {nonpeaks.name}
                        -fl /usr/local/genome/fold.json
                        -b {bias_model}
                        -o {args.model_output_directory}
                    """.replace("\n", " "))

if __name__ == "__main__":
    sys.exit(main())
