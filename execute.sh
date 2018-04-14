#!/bin/sh

#SBATCH --qos=tenenbaum
#SBATCH --time=1000
#SBATCH --mem=100G
#SBATCH --job-name=ec
cd /om/user/mnye/ec
source activate ../ec_conda
$@ 
