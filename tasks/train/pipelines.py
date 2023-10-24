import chrombpnet.parsers as parsers
import os
from chrombpnet.data import DefaultDataFile, get_default_data_path
from chrombpnet.data import print_meme_motif_file
import chrombpnet.pipelines as pipelines
import copy
import pandas as pd
import logging
logging.getLogger('matplotlib.font_manager').disabled = True

# invoke pipeline modules based on command

def main():
	args = parsers.read_parser()
	
	if args.cmd == "pipeline" or args.cmd == "train":
		os.makedirs(os.path.join(args.output_dir,"logs"), exist_ok=False)
		os.makedirs(os.path.join(args.output_dir,"auxiliary"), exist_ok=False)
		os.makedirs(os.path.join(args.output_dir,"models"), exist_ok=False)
		os.makedirs(os.path.join(args.output_dir,"evaluation"), exist_ok=False)

		pipelines.chrombpnet_train_pipeline(args)
	
	elif args.cmd == "qc":
		os.makedirs(os.path.join(args.output_dir,"auxiliary"), exist_ok=False)
		os.makedirs(os.path.join(args.output_dir,"evaluation"), exist_ok=False)
		
		pipelines.chrombpnet_qc(args)
		
	elif args.cmd == "bias":
		if args.cmd_bias == "pipeline" or args.cmd_bias == "train":
			os.makedirs(os.path.join(args.output_dir,"logs"), exist_ok=False)
			os.makedirs(os.path.join(args.output_dir,"auxiliary"), exist_ok=False)
			os.makedirs(os.path.join(args.output_dir,"models"), exist_ok=False)
			os.makedirs(os.path.join(args.output_dir,"evaluation"), exist_ok=False)

			pipelines.train_bias_pipeline(args)
		
		elif args.cmd_bias == "qc":
			os.makedirs(os.path.join(args.output_dir,"auxiliary"), exist_ok=False)
			os.makedirs(os.path.join(args.output_dir,"evaluation"), exist_ok=False)
			
			pipelines.bias_model_qc(args)
			
		else:
			print("Command not found")

			
	
	elif args.cmd == "pred_bw":
	
		assert (args.bias_model is None) + (args.chrombpnet_model is None) + (args.chrombpnet_model_nb is None) < 3, "No input model provided!"
		import chrombpnet.evaluation.make_bigwigs.predict_to_bigwig as predict_to_bigwig

		predict_to_bigwig.main(args)

	elif args.cmd == "contribs_bw":
	
		import chrombpnet.evaluation.interpret.interpret as interpret
		interpret.main(args)
		import chrombpnet.evaluation.make_bigwigs.importance_hdf5_to_bigwig as importance_hdf5_to_bigwig
		if "counts" in  args.profile_or_counts:
			args_copy = copy.deepcopy(args)
			args_copy.hdf5 = args_copy.output_prefix + ".counts_scores.h5"
			args_copy.output_prefix = args.output_prefix + ".counts_scores"
			
			importance_hdf5_to_bigwig.main(args_copy)
		if "profile" in  args.profile_or_counts:
			args_copy = copy.deepcopy(args)
			args_copy.hdf5 = args_copy.output_prefix + ".profile_scores.h5"
			args_copy.output_prefix = args.output_prefix + ".profile_scores"
	
			importance_hdf5_to_bigwig.main(args_copy)
			
	elif args.cmd == "footprints":
	
		import chrombpnet.evaluation.marginal_footprints.marginal_footprinting as marginal_footprinting
		marginal_footprinting.main(args)

	elif args.cmd == "snp_score":
	
		import chrombpnet.evaluation.variant_effect_prediction.snp_scoring as snp_scoring
		snp_scoring.main(args)
		
	elif args.cmd == "modisco_motifs":
		import chrombpnet
		chrombpnet_src_dir = os.path.dirname(chrombpnet.__file__)
		meme_file=get_default_data_path(DefaultDataFile.motifs_meme)
	
		modisco_command = "modisco motifs -i {} -n 50000 -o {} -w 500".format(args.h5py,args.output_prefix+"_modisco.h5")
		os.system(modisco_command)
		modisco_command = "modisco report -i {} -o {} -m {}".format(args.output_prefix+"_modisco.h5",args.output_prefix+"_reports",meme_file)
		os.system(modisco_command)
		
		import chrombpnet.evaluation.modisco.convert_html_to_pdf as convert_html_to_pdf
		convert_html_to_pdf.main(args.output_prefix+"_reports/motifs.html",args.output_prefix+"_reports/motifs.pdf")

	elif args.cmd == "prep":
	
		if args.cmd_prep == "nonpeaks":

			assert(args.inputlen%2==0) # input length should be a multiple of 2
	
			os.makedirs(args.output_prefix+"_auxiliary/", exist_ok=False)
	
			from chrombpnet.helpers.make_gc_matched_negatives.get_genomewide_gc_buckets.get_genomewide_gc_bins import get_genomewide_gc
			get_genomewide_gc(args.genome,args.output_prefix+"_auxiliary/genomewide_gc.bed",args.inputlen, args.stride)
	
			# get gc content in peaks
			import chrombpnet.helpers.make_gc_matched_negatives.get_gc_content as get_gc_content
			args_copy = copy.deepcopy(args)
			args_copy.input_bed = args_copy.peaks
			args_copy.output_prefix = args.output_prefix+"_auxiliary/foreground.gc"
			get_gc_content.main(args_copy)
	
			# prepare candidate negatives
	
			exclude_bed = pd.read_csv(args.peaks, sep="\t", header=None)
			os.system("bedtools slop -i {peaks} -g {chrom_sizes} -b {flank_size} > {output}".format(peaks=args.peaks,
												chrom_sizes=args.chrom_sizes,
												flank_size=args.inputlen//2,
												output=args.output_prefix+"_auxiliary/peaks_slop.bed"))
			exclude_bed = pd.read_csv(args.output_prefix+"_auxiliary/peaks_slop.bed", sep="\t", header=None, usecols=[0,1,2])
	
			if args.blacklist_regions:
				os.system("bedtools slop -i {blacklist} -g {chrom_sizes} -b {flank_size} > {output}".format(blacklist=args.blacklist_regions,
												chrom_sizes=args.chrom_sizes,
												flank_size=args.inputlen//2,
												output=args.output_prefix+"_auxiliary/blacklist_slop.bed"))
										
				exclude_bed = pd.concat([exclude_bed,pd.read_csv(args.output_prefix+"_auxiliary/blacklist_slop.bed",sep="\t",header=None, usecols=[0,1,2])])

			exclude_bed.to_csv(args.output_prefix+"_auxiliary/exclude_unmerged.bed", sep="\t", header=False, index=False)
			os.system("bedtools sort -i {inputb} | bedtools merge -i stdin > {output}".format(inputb=args.output_prefix+"_auxiliary/exclude_unmerged.bed",
																					output=args.output_prefix+"_auxiliary/exclude.bed"))			
	
	

			bedtools_command = "bedtools intersect -v -a {genomewide_gc} -b {exclude_bed}  > {candidate_bed}".format(
															genomewide_gc=args.output_prefix+"_auxiliary/genomewide_gc.bed",
															exclude_bed=args.output_prefix+"_auxiliary/exclude.bed",
															candidate_bed=args.output_prefix+"_auxiliary/candidates.bed")
			os.system(bedtools_command)
													
			# get final negatives
			import chrombpnet.helpers.make_gc_matched_negatives.get_gc_matched_negatives as get_gc_matched_negatives
			args_copy = copy.deepcopy(args)
			args_copy.candidate_negatives = args.output_prefix+"_auxiliary/candidates.bed"
			args_copy.foreground_gc_bed = args.output_prefix+"_auxiliary/foreground.gc.bed"
			args_copy.output_prefix = 	args.output_prefix+"_auxiliary/negatives"
	
			get_gc_matched_negatives.main(args_copy)
	
			negatives = pd.read_csv(args.output_prefix+"_auxiliary/negatives.bed", sep="\t", header=None)
			negatives[3]="."
			negatives[4]="."
			negatives[5]="."
			negatives[6]="."
			negatives[7]="."
			negatives[8]="."
			negatives[9]=args.inputlen//2
			negatives.to_csv(args.output_prefix+"_negatives.bed", sep="\t", header=False, index=False)

		elif args.cmd_prep == "splits":
			import chrombpnet.helpers.make_chr_splits.splits as splits
			splits.main(args)
			
		else:
			print("Command not found")
		
	else:
		print("Command not found")


if __name__=="__main_-":
	main()

    
        
(base) root@dceaf77f5e59:/scratch/chrombpnet/chrombpnet# cat pipelines.py 
import pandas as pd
import os
import json
import copy
from chrombpnet.data import DefaultDataFile, get_default_data_path
from chrombpnet.data import print_meme_motif_file
import numpy as np

def chrombpnet_train_pipeline(args):

	if args.file_prefix:
		fpx = args.file_prefix+"_"
	else:
		fpx = ""
		
	# Shift bam and convert to bigwig
	import chrombpnet.helpers.preprocessing.reads_to_bigwig as reads_to_bigwig	
	args.output_prefix = os.path.join(args.output_dir,"auxiliary/{}data".format(fpx))
	args.plus_shift = None
	args.minus_shift = None
	reads_to_bigwig.main(args)
	
	# QC bigwig
	import chrombpnet.helpers.preprocessing.analysis.build_pwm_from_bigwig as build_pwm_from_bigwig	
	args.bigwig = os.path.join(args.output_dir,"auxiliary/{}data_unstranded.bw".format(fpx))
	args.output_prefix = os.path.join(args.output_dir,"evaluation/{}bw_shift_qc".format(fpx))
	folds = json.load(open(args.chr_fold_path))
	assert(len(folds["valid"]) > 0) # validation list of chromosomes is empty
	args.chr = folds["valid"][0]
	args.pwm_width=24
	build_pwm_from_bigwig.main(args)
	
	# make predictions with input bias model in peaks
	import chrombpnet.training.predict as predict
	args_copy = copy.deepcopy(args)
	args_copy.output_prefix = os.path.join(args_copy.output_dir,"evaluation/bias")
	args_copy.model_h5 = args.bias_model_path
	args_copy.nonpeaks = "None"
	predict.main(args_copy)
	
	# QC bias model performance in peaks
	bias_metrics = json.load(open(os.path.join(args_copy.output_dir,"evaluation/bias_metrics.json")))
	print("Bias model pearsonr performance in peaks is: {}".format(str(np.round(bias_metrics["counts_metrics"]["peaks"]["pearsonr"],2))))
	assert(bias_metrics["counts_metrics"]["peaks"]["pearsonr"] > -0.5) # bias model has negative correlation in peaks - AT rich bias model. Increase bias threshold and retrain bias model. Or use a different bias model with higher bias threshold. 

	# fetch hyperparameters for training
	import chrombpnet.helpers.hyperparameters.find_chrombpnet_hyperparams as find_chrombpnet_hyperparams
	args_copy = copy.deepcopy(args)
	args_copy.output_prefix = os.path.join(args.output_dir,"auxiliary/{}".format(fpx))
	find_chrombpnet_hyperparams.main(args_copy)
	
	# separating models from logs
	os.rename(os.path.join(args.output_dir,"auxiliary/{}bias_model_scaled.h5".format(fpx)),os.path.join(args.output_dir,"models/{}bias_model_scaled.h5".format(fpx)))
	os.rename(os.path.join(args.output_dir,"auxiliary/{}chrombpnet_model_params.tsv".format(fpx)),os.path.join(args.output_dir,"logs/{}chrombpnet_model_params.tsv".format(fpx)))
	os.rename(os.path.join(args.output_dir,"auxiliary/{}chrombpnet_data_params.tsv".format(fpx)),os.path.join(args.output_dir,"logs/{}chrombpnet_data_params.tsv".format(fpx)))

	params = open(os.path.join(args.output_dir,"logs/{}chrombpnet_model_params.tsv".format(fpx))).read()
	params = params.replace(os.path.join(args.output_dir,"auxiliary/{}bias_model_scaled.h5".format(fpx)),os.path.join(args.output_dir,"models/{}bias_model_scaled.h5".format(fpx)))
	with open(os.path.join(args.output_dir,"logs/{}chrombpnet_model_params.tsv".format(fpx)),"w") as f:
		f.write(params)
		
	# get model architecture path and train chromBPNet model
	import chrombpnet.training.models.chrombpnet_with_bias_model as chrombpnet_with_bias_model
	import chrombpnet.training.train as train
	args_copy = copy.deepcopy(args)
	if args_copy.architecture_from_file is None:
		args_copy.architecture_from_file = 	chrombpnet_with_bias_model.__file__
	args_copy.peaks = os.path.join(args.output_dir,"auxiliary/{}filtered.peaks.bed".format(fpx))
	args_copy.nonpeaks = os.path.join(args.output_dir,"auxiliary/{}filtered.nonpeaks.bed".format(fpx))
	args_copy.output_prefix = os.path.join(args.output_dir,"models/{}chrombpnet".format(fpx))
	args_copy.params = os.path.join(args.output_dir,"logs/{}chrombpnet_model_params.tsv".format(fpx))
	train.main(args_copy)
	
	# separating models from logs
	os.rename(os.path.join(args.output_dir,"models/{}chrombpnet.log".format(fpx)),os.path.join(args.output_dir,"logs/{}chrombpnet.log".format(fpx)))
	os.rename(os.path.join(args.output_dir,"models/{}chrombpnet.log.batch".format(fpx)),os.path.join(args.output_dir,"logs/{}chrombpnet.log.batch".format(fpx)))
	#os.rename(os.path.join(args.output_dir,"models/{}chrombpnet.params.json".format(fpx)),os.path.join(args.output_dir,"logs/{}chrombpnet.params.json".format(fpx)))
	os.rename(os.path.join(args.output_dir,"models/{}chrombpnet.args.json").format(fpx),os.path.join(args.output_dir,"logs/{}chrombpnet.args.json".format(fpx)))

	if args.cmd == "train":
		import chrombpnet.helpers.generate_reports.make_html as make_html
		args_copy = copy.deepcopy(args)
		args_copy.input_dir = args_copy.output_dir
		args_copy.command = args.cmd
		make_html.main(args_copy)
		print("Finished training! Exiting!")
		return
		
	# make predictions with trained chrombpnet model
	args_copy = copy.deepcopy(args)
	args_copy.output_prefix = os.path.join(args.output_dir,"evaluation/{}chrombpnet".format(fpx))
	args_copy.model_h5 = os.path.join(args.output_dir,"models/{}chrombpnet.h5".format(fpx))
	args_copy.nonpeaks = "None"
	predict.main(args_copy)
	
	# marginal footprinting with model
	import chrombpnet.evaluation.marginal_footprints.marginal_footprinting as marginal_footprinting
	if args.data_type == "ATAC":
		bias_motifs = [["tn5_1","GCACAGTACAGAGCTG"],["tn5_2","GTGCACAGTTCTAGAGTGTGCAG"],["tn5_3","CCTCTACACTGTGCAGAA"],["tn5_4","GCACAGTTCTAGACTGTGCAG"],["tn5_5","CTGCACAGTGTAGAGTTGTGC"]]

	elif args.data_type == "DNASE":
		bias_motifs = [["dnase_1","TTTACAAGTCCA"],["dnase_2","TTTACAAGTCCA"]]
	else:
		print("unknown data type: "+args.data_type)
	df = pd.DataFrame(bias_motifs)
	df.to_csv(os.path.join(args_copy.output_dir,"auxiliary/motif_to_pwm.tsv"),sep="\t",header=False,index=False)
	
	args_copy = copy.deepcopy(args)
	args_copy.model_h5 = os.path.join(args.output_dir,"models/{}chrombpnet_nobias.h5".format(fpx))
	args_copy.regions = args.nonpeaks
	args_copy.output_prefix = os.path.join(args.output_dir,"evaluation/{}chrombpnet_nobias".format(fpx))
	args_copy.motifs_to_pwm = os.path.join(args_copy.output_dir,"auxiliary/motif_to_pwm.tsv")
	args_copy.ylim = None
	marginal_footprinting.main(args_copy)
	
	# separating models from logs
	os.rename(os.path.join(args.output_dir,"evaluation/{}chrombpnet_nobias_footprints.h5".format(fpx)),os.path.join(args.output_dir,"auxiliary/{}chrombpnet_nobias_footprints.h5".format(fpx)))

	# get contributions scores with model
	args_copy = copy.deepcopy(args)
	import chrombpnet.evaluation.interpret.interpret as interpret
	peaks = pd.read_csv(os.path.join(args.peaks),sep="\t",header=None)
	if peaks.shape[0] > 30000:
		sub_peaks = peaks.sample(30000, random_state=1234)
	else:
		sub_peaks = peaks
	sub_peaks.to_csv(os.path.join(args_copy.output_dir,"auxiliary/{}30K_subsample_peaks.bed".format(fpx)),sep="\t", header=False, index=False)
	os.makedirs(os.path.join(args.output_dir,"auxiliary/interpret_subsample/"), exist_ok=False)

	#args_copy.profile_or_counts = ["counts", "profile"]
	args_copy.profile_or_counts = ["profile"]	
	args_copy.regions = os.path.join(args_copy.output_dir,"auxiliary/{}30K_subsample_peaks.bed".format(fpx))	
	args_copy.model_h5 = os.path.join(args.output_dir,"models/{}chrombpnet_nobias.h5".format(fpx))
	args_copy.output_prefix = os.path.join(args.output_dir,"auxiliary/interpret_subsample/{}chrombpnet_nobias".format(fpx))
	args_copy.debug_chr = None
	interpret.main(args_copy)
	
def chrombpnet_qc(args):

	if args.file_prefix:
		fpx = args.file_prefix+"_"
	else:
		fpx = ""
	
	def load_model_wrapper(model_hdf5):
		# read .h5 model
		from tensorflow.keras.utils import get_custom_objects
		from tensorflow.keras.models import load_model
		import tensorflow as tf
		import chrombpnet.training.utils.losses as losses
		custom_objects={"multinomial_nll":losses.multinomial_nll, "tf": tf}    
		get_custom_objects().update(custom_objects)    
		model=load_model(model_hdf5)
		model.summary()
		return model
    
	chrombpnet_md = load_model_wrapper(model_hdf5=args.chrombpnet_model)
	args.inputlen = int(chrombpnet_md.input_shape[1])
	args.outputlen = int(chrombpnet_md.output_shape[0][1])
	
	# make predictions with trained chrombpnet model
	import chrombpnet.training.predict as predict
	args_copy = copy.deepcopy(args)
	args_copy.output_prefix = os.path.join(args.output_dir,"evaluation/{}chrombpnet".format(fpx))
	args_copy.model_h5 = args.chrombpnet_model
	args_copy.nonpeaks = "None"
	predict.main(args_copy)
	
	# marginal footprinting with model
	import chrombpnet.evaluation.marginal_footprints.marginal_footprinting as marginal_footprinting
	if args.data_type == "ATAC":
		bias_motifs = [["tn5_1","GCACAGTACAGAGCTG"],["tn5_2","GTGCACAGTTCTAGAGTGTGCAG"],["tn5_3","CCTCTACACTGTGCAGAA"],["tn5_4","GCACAGTTCTAGACTGTGCAG"],["tn5_5","CTGCACAGTGTAGAGTTGTGC"]]

	elif args.data_type == "DNASE":
		bias_motifs = [["dnase_1","TTTACAAGTCCA"],["dnase_2","TTTACAAGTCCA"]]
	else:
		print("unknown data type: "+args.data_type)
	df = pd.DataFrame(bias_motifs)
	df.to_csv(os.path.join(args_copy.output_dir,"auxiliary/motif_to_pwm.tsv"),sep="\t",header=False,index=False)
	
	args_copy = copy.deepcopy(args)
	args_copy.model_h5 = args.chrombpnet_model_nb
	args_copy.regions = args.nonpeaks
	args_copy.output_prefix = os.path.join(args.output_dir,"evaluation/{}chrombpnet_nobias".format(fpx))
	args_copy.motifs_to_pwm = os.path.join(args_copy.output_dir,"auxiliary/motif_to_pwm.tsv")
	args_copy.ylim = None
	marginal_footprinting.main(args_copy)
	
	# separating models from logs
	os.rename(os.path.join(args.output_dir,"evaluation/{}chrombpnet_nobias_footprints.h5".format(fpx)),os.path.join(args.output_dir,"auxiliary/{}chrombpnet_nobias_footprints.h5".format(fpx)))

	# get contributions scores with model
	args_copy = copy.deepcopy(args)
	import chrombpnet.evaluation.interpret.interpret as interpret
	peaks = pd.read_csv(os.path.join(args.peaks),sep="\t",header=None)
	if peaks.shape[0] > 30000:
		sub_peaks = peaks.sample(30000, random_state=1234)
	else:
		sub_peaks = peaks
	sub_peaks.to_csv(os.path.join(args_copy.output_dir,"auxiliary/{}30K_subsample_peaks.bed".format(fpx)),sep="\t", header=False, index=False)
	os.makedirs(os.path.join(args.output_dir,"auxiliary/interpret_subsample/"), exist_ok=False)

	#args_copy.profile_or_counts = ["counts", "profile"]
	args_copy.profile_or_counts = ["profile"]
	args_copy.regions = os.path.join(args_copy.output_dir,"auxiliary/{}30K_subsample_peaks.bed".format(fpx))	
	args_copy.model_h5 = args.chrombpnet_model_nb
	args_copy.output_prefix = os.path.join(args.output_dir,"auxiliary/interpret_subsample/{}chrombpnet_nobias".format(fpx))
	args_copy.debug_chr = None
	interpret.main(args_copy)
	
def train_bias_pipeline(args):

	if args.file_prefix:
		fpx = args.file_prefix+"_"
	else:
		fpx = ""
		
	# Shift bam and convert to bigwig
	import chrombpnet.helpers.preprocessing.reads_to_bigwig as reads_to_bigwig	
	args.output_prefix = os.path.join(args.output_dir,"auxiliary/{}data".format(fpx))
	args.plus_shift = None
	args.minus_shift = None
	reads_to_bigwig.main(args)
	
	# QC bigwig
	import chrombpnet.helpers.preprocessing.analysis.build_pwm_from_bigwig as build_pwm_from_bigwig	
	args.bigwig = os.path.join(args.output_dir,"auxiliary/{}data_unstranded.bw".format(fpx))
	args.output_prefix = os.path.join(args.output_dir,"evaluation/{}bw_shift_qc".format(fpx))
	folds = json.load(open(args.chr_fold_path))
	assert(len(folds["valid"]) > 0) # validation list of chromosomes is empty
	args.chr = folds["valid"][0]
	args.pwm_width=24
	build_pwm_from_bigwig.main(args)
	

	# fetch hyperparameters for training
	import chrombpnet.helpers.hyperparameters.find_bias_hyperparams as find_bias_hyperparams
	args_copy = copy.deepcopy(args)
	args_copy.output_prefix = os.path.join(args.output_dir,"auxiliary/{}".format(fpx))
	find_bias_hyperparams.main(args_copy)
	
	# separating models from logs
	os.rename(os.path.join(args.output_dir,"auxiliary/{}bias_model_params.tsv".format(fpx)),os.path.join(args.output_dir,"logs/{}bias_model_params.tsv".format(fpx)))
	os.rename(os.path.join(args.output_dir,"auxiliary/{}bias_data_params.tsv".format(fpx)),os.path.join(args.output_dir,"logs/{}bias_data_params.tsv".format(fpx)))
		
	# get model architecture path and train chromBPNet model
	import chrombpnet.training.models.bpnet_model as bpnet_model
	import chrombpnet.training.train as train
	args_copy = copy.deepcopy(args)
	if args_copy.architecture_from_file is None:
		args_copy.architecture_from_file = 	bpnet_model.__file__
	args_copy.peaks = "None"
	args_copy.nonpeaks = os.path.join(args_copy.output_dir,"auxiliary/{}filtered.bias_nonpeaks.bed".format(fpx))
	args_copy.output_prefix = os.path.join(args_copy.output_dir,"models/{}bias".format(fpx))
	args_copy.params = os.path.join(args_copy.output_dir,"logs/{}bias_model_params.tsv".format(fpx))
	train.main(args_copy)
	
	# separating models from logs
	os.rename(os.path.join(args.output_dir,"models/{}bias.args.json".format(fpx)),os.path.join(args.output_dir,"logs/{}bias.args.json".format(fpx)))
	os.rename(os.path.join(args.output_dir,"models/{}bias.log".format(fpx)),os.path.join(args.output_dir,"logs/{}bias.log".format(fpx)))
	os.rename(os.path.join(args.output_dir,"models/{}bias.log.batch".format(fpx)),os.path.join(args.output_dir,"logs/{}bias.log.batch".format(fpx)))
#	os.rename(os.path.join(args.output_dir,"models/{}bias.#".format(fpx)),os.path.join(args.output_dir,"logs/{}bias.params.json".format(fpx)))

	if args.cmd_bias == "train":
		import chrombpnet.helpers.generate_reports.make_html_bias as make_html_bias
		args_copy = copy.deepcopy(args)
		args_copy.input_dir = args_copy.output_dir
		args_copy.command = args_copy.cmd_bias
		make_html_bias.main(args_copy) 
		print("Finished training! Exiting!")
		return
		
	# make predictions with trained bias model 
	import chrombpnet.training.predict as predict
	args_copy = copy.deepcopy(args)
	args_copy.output_prefix = os.path.join(args_copy.output_dir,"evaluation/{}bias".format(fpx))
	args_copy.model_h5 = os.path.join(args.output_dir,"models/{}bias.h5".format(fpx))
	predict.main(args_copy)

	# get contributions scores with model
	import chrombpnet.evaluation.interpret.interpret as interpret
	peaks = pd.read_csv(os.path.join(args.peaks),sep="\t",header=None)
	if peaks.shape[0] > 30000:
		sub_peaks = peaks.sample(30000, random_state=1234)
	else:
		sub_peaks = peaks
	sub_peaks.to_csv(os.path.join(args_copy.output_dir,"auxiliary/{}30K_subsample_peaks.bed".format(fpx)),sep="\t", header=False, index=False)
	os.makedirs(os.path.join(args.output_dir,"auxiliary/interpret_subsample/"), exist_ok=False)

	args_copy = copy.deepcopy(args)
	args_copy.profile_or_counts = ["counts", "profile"]
	args_copy.regions = os.path.join(args_copy.output_dir,"auxiliary/{}30K_subsample_peaks.bed".format(fpx))	
	args_copy.model_h5 = os.path.join(args.output_dir,"models/{}bias.h5".format(fpx))
	args_copy.output_prefix = os.path.join(args.output_dir,"auxiliary/interpret_subsample/{}bias".format(fpx))
	args_copy.debug_chr = None
	interpret.main(args_copy)

def bias_model_qc(args):

	if args.file_prefix:
		fpx = args.file_prefix+"_"
	else:
		fpx = ""
	
	def load_model_wrapper(model_hdf5):
		# read .h5 model
		from tensorflow.keras.utils import get_custom_objects
		from tensorflow.keras.models import load_model
		import tensorflow as tf
		import chrombpnet.training.utils.losses as losses
		custom_objects={"multinomial_nll":losses.multinomial_nll, "tf": tf}    
		get_custom_objects().update(custom_objects)    
		model=load_model(model_hdf5)
		model.summary()
		return model
    
	bias_md = load_model_wrapper(model_hdf5=args.bias_model)
	args.inputlen = int(bias_md.input_shape[1])
	args.outputlen = int(bias_md.output_shape[0][1])
	
	# make predictions with trained bias model 
	import chrombpnet.training.predict as predict
	args_copy = copy.deepcopy(args)
	args_copy.output_prefix = os.path.join(args_copy.output_dir,"evaluation/{}bias".format(fpx))
	args_copy.model_h5 = args.bias_model
	predict.main(args_copy)

	# get contributions scores with model
	import chrombpnet.evaluation.interpret.interpret as interpret
	peaks = pd.read_csv(os.path.join(args.peaks),sep="\t",header=None)
	if peaks.shape[0] > 30000:
		sub_peaks = peaks.sample(30000, random_state=1234)
	else:
		sub_peaks = peaks
	sub_peaks.to_csv(os.path.join(args_copy.output_dir,"auxiliary/{}30K_subsample_peaks.bed".format(fpx)),sep="\t", header=False, index=False)
	os.makedirs(os.path.join(args.output_dir,"auxiliary/interpret_subsample/"), exist_ok=False)

	args_copy = copy.deepcopy(args)
	args_copy.profile_or_counts = ["counts", "profile"]
	args_copy.regions = os.path.join(args_copy.output_dir,"auxiliary/{}30K_subsample_peaks.bed".format(fpx))	
	args_copy.model_h5 = args.bias_model
	args_copy.output_prefix = os.path.join(args.output_dir,"auxiliary/interpret_subsample/{}bias".format(fpx))
	args_copy.debug_chr = None
	interpret.main(args_copy)
	
	import chrombpnet
	chrombpnet_src_dir = os.path.dirname(chrombpnet.__file__)
	meme_file=get_default_data_path(DefaultDataFile.motifs_meme)
	
	# modisco-lite pipeline
	
	modisco_command = "modisco motifs -i {} -n 50000 -o {} -w 500".format(os.path.join(args.output_dir,"auxiliary/interpret_subsample/{}bias.profile_scores.h5".format(fpx)),os.path.join(args.output_dir,"auxiliary/interpret_subsample/{}modisco_results_profile_scores.h5".format(fpx)))
	os.system(modisco_command)
	modisco_command = "modisco report -i {} -o {} -m {}".format(os.path.join(args.output_dir,"auxiliary/interpret_subsample/{}modisco_results_profile_scores.h5".format(fpx)),os.path.join(args.output_dir,"evaluation/modisco_profile/"),meme_file)
	os.system(modisco_command)
	modisco_command = "modisco motifs -i {} -n 50000 -o {} -w 500".format(os.path.join(args.output_dir,"auxiliary/interpret_subsample/{}bias.counts_scores.h5".format(fpx)),os.path.join(args.output_dir,"auxiliary/interpret_subsample/{}modisco_results_counts_scores.h5".format(fpx)))
	os.system(modisco_command)
	modisco_command = "modisco report -i {} -o {} -m {}".format(os.path.join(args.output_dir,"auxiliary/interpret_subsample/{}modisco_results_counts_scores.h5".format(fpx)),os.path.join(args.output_dir,"evaluation/modisco_counts/"),meme_file)
	os.system(modisco_command)
	
	import chrombpnet.evaluation.modisco.convert_html_to_pdf as convert_html_to_pdf
	convert_html_to_pdf.main(os.path.join(args.output_dir,"evaluation/modisco_counts/motifs.html"),os.path.join(args.output_dir,"evaluation/{}bias_counts.pdf".format(fpx)))
	convert_html_to_pdf.main(os.path.join(args.output_dir,"evaluation/modisco_profile/motifs.html"),os.path.join(args.output_dir,"evaluation/{}bias_profile.pdf".format(fpx)))

	import chrombpnet.helpers.generate_reports.make_html_bias as make_html_bias
	args_copy = copy.deepcopy(args)
	args_copy.input_dir = args_copy.output_dir
	args_copy.command = args_copy.cmd_bias
	make_html_bias.main(args_copy)
