#!/usr/bin/env python3

import os
import sys
import copy
from chrombpnet.data import DefaultDataFile, get_default_data_path
from argparse import Namespace

import chrombpnet.helpers.generate_reports.make_html_bias as make_html_bias
import chrombpnet.helpers.generate_reports.make_html as make_html

def bias_modisco(file_prefix, bias_profile_scores, modisco_results_profile_scores, bias_counts_scores, modisco_results_counts_scores, output_dir):
	meme_file=get_default_data_path(DefaultDataFile.motifs_meme)
	
	modisco_command = "modisco motifs -i {} -n 50000 -o {} -w 500".format((bias_profile_scores),modisco_results_profile_scores)
	os.system(modisco_command)
	modisco_command = "modisco report -i {} -o {} -m {}".format((modisco_results_profile_scores),os.path.join(output_dir,"bias-evaluation/modisco_profile/"),meme_file)
	os.system(modisco_command)
	modisco_command = "modisco motifs -i {} -n 50000 -o {} -w 500".format((bias_counts_scores),modisco_results_counts_scores)
	os.system(modisco_command)
	modisco_command = "modisco report -i {} -o {} -m {}".format((modisco_results_counts_scores),os.path.join(output_dir,"bias-evaluation/modisco_counts/"),meme_file)
	os.system(modisco_command)

	args_copy = Namespace(file_prefix=file_prefix, output_dir=output_dir)
	args_copy.input_dir = args_copy.output_dir
	args_copy.command = "train"
	return make_html_bias.main(args_copy)

def modisco(file_prefix, no_bias_profile_scores, modisco_results_profile_scores, output_dir):
    meme_file=get_default_data_path(DefaultDataFile.motifs_meme)
	
    modisco_command = "modisco motifs -i {} -n 50000 -o {} -w 500".format(no_bias_profile_scores,modisco_results_profile_scores)
    os.system(modisco_command)
    modisco_command = "modisco report -i {} -o {} -m {}".format(modisco_results_profile_scores,os.path.join(output_dir,"model-evaluation/modisco_profile/"),meme_file)
    os.system(modisco_command)
	
    args_copy = Namespace(file_prefix=file_prefix, output_dir=output_dir)
    args_copy.input_dir = args_copy.output_dir
    args_copy.command = "train"
    make_html.main(args_copy)

if __name__ == "__main__":
	sys.exit(bias_modisco(*sys.argv[2:]) if sys.argv[1] == "bias" else modisco(*sys.argv[2:]))
