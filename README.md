
# chrombpnet-workflow

This repo contains a Krews workflow for running ChromBPNet on ATAC-seq and DNase-seq datasets. It currently supports human data aligned to the hg38 genome. It consists of the following steps:
1. *Training*: trains a bias and ChromBPNet model given filtered BAMs
2. *Prediction*: predicts bias-corrected signal profiles at input regions
3. *Shap*: computes base-resolution importance scores for predicting profiles and counts

The *Shap* step consists of three substeps. It first splits input regions into equally-sized smaller files for performance, computes shap scores on those, then merges the output.

The *Training* step can be skipped if a pre-trained model is available.

Input is a list of BAM files and a BED file containing regions on which to run predictions and shap score analysis. Output is a bias model, a ChromBPNet model, a predicted profile bigWig, a counts importance score bigWig, and a profile importance score bigWig. The bigWigs will only contain values in kilobase-sized windows around the input regions.

See the `sample-configs` directory for example configurations. To run, do `scripts/run-workflow.sh --on google --config /path/to/config.conf`.
