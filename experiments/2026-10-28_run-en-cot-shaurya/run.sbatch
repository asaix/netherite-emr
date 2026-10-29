#!/bin/bash
#SBATCH -A research
#SBATCH -p u22
#SBATCH --qos=medium
#SBATCH -c 4
#SBATCH -t 12:00:00
#SBATCH -J en-cot-hindi-n50
#SBATCH -o logs/slurm-%j.out
#SBATCH --mail-type=END,FAIL

cd "$SLURM_SUBMIT_DIR"
for d in short medium long very_long; do
    ~/miniconda3/envs/anlp/bin/python sarvam.py --config config/sarvam.yaml --prompts config/prompt.yaml --general config/general.yaml --input ../../Dataset/$d --output outputs/$d
done
