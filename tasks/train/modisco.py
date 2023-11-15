#!/usr/bin/env python3

import os
import sys
from chrombpnet.data import DefaultDataFile, get_default_data_path
from argparse import Namespace

import chrombpnet.helpers.generate_reports.make_html_bias as make_html_bias
import chrombpnet.helpers.generate_reports.make_html as make_html

def bias_modisco(file_prefix, bias_profile_scores, modisco_results_profile_scores, bias_counts_scores, modisco_results_counts_scores, output_dir, data_type, log, bias_metrics):
    meme_file=get_default_data_path(DefaultDataFile.motifs_meme)
    
    os.system(f"mkdir -p {os.path.join(output_dir, 'bias-evaluation', 'modisco_profile')}")
    os.system(f"mkdir -p {os.path.join(output_dir, 'bias-evaluation', 'modisco_counts')}")
    modisco_command = "modisco motifs -i {} -n 50000 -o {} -w 500".format((bias_profile_scores),modisco_results_profile_scores)
    os.system(modisco_command)
    modisco_command = "modisco report -i {} -o {} -m {}".format((modisco_results_profile_scores),os.path.join(output_dir,"bias-evaluation","modisco_profile"),meme_file)
    os.system(modisco_command)
    modisco_command = "modisco motifs -i {} -n 50000 -o {} -w 500".format((bias_counts_scores),modisco_results_counts_scores)
    os.system(modisco_command)
    modisco_command = "modisco report -i {} -o {} -m {}".format((modisco_results_counts_scores),os.path.join(output_dir,"bias-evaluation", "modisco_counts"),meme_file)
    os.system(modisco_command)

    os.system(f"mkdir -p {output_dir}/evaluation")
    os.system(f"cp {bias_metrics} {output_dir}/evaluation")
    os.system(f"cp -r {output_dir}/model-evaluation/modisco_profile {output_dir}/evaluation/modisco_profile")
    os.system(f"cp -r {output_dir}/model-evaluation/modisco_counts {output_dir}/evaluation/modisco_counts")
    os.system(f"mkdir -p {output_dir}/logs")
    os.system(f"cp {log} {output_dir}/logs")

    args_copy = Namespace(file_prefix=file_prefix, output_dir=output_dir, data_type=data_type)
    args_copy.input_dir = args_copy.output_dir
    args_copy.command = "train"
    return make_html_bias.main(args_copy)

def modisco(file_prefix, no_bias_profile_scores, modisco_results_profile_scores, output_dir, data_type, biasMetrics, log, metrics, maxBiasResponse):
    meme_file=get_default_data_path(DefaultDataFile.motifs_meme)
    
    os.system(f"mkdir -p {os.path.join(output_dir, 'model-evaluation', 'modisco_profile')}")
    modisco_command = "modisco motifs -i {} -n 50000 -o {} -w 500".format(no_bias_profile_scores,modisco_results_profile_scores)
    os.system(modisco_command)
    modisco_command = "modisco report -i {} -o {} -m {}".format(modisco_results_profile_scores,os.path.join(output_dir,"model-evaluation", "modisco_profile"),meme_file)
    os.system(modisco_command)
    
    os.system(f"mkdir -p {output_dir}/evaluation")
    os.system(f"cp {biasMetrics} {metrics} {maxBiasResponse} {output_dir}/evaluation")
    os.system(f"cp -r {output_dir}/model-evaluation/modisco_profile {output_dir}/evaluation/modisco_profile")
    os.system(f"mkdir -p {output_dir}/logs")
    os.system(f"cp {log} {output_dir}/logs")

    args_copy = Namespace(file_prefix=file_prefix, output_dir=output_dir, data_type=data_type)
    args_copy.input_dir = args_copy.output_dir
    args_copy.command = "train"
    make_html.main(args_copy)

if __name__ == "__main__":
    sys.exit(bias_modisco(*sys.argv[2:]) if sys.argv[1] == "bias" else modisco(*sys.argv[2:]))
