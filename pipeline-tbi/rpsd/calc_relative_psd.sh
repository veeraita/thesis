#!/bin/bash

OUTPUT_DIR=/scratch/nbe/tbi-meg/veera/processed

echo "OUTPUT_DIR set as $OUTPUT_DIR"

ml purge
module load teflon
ml anaconda3
conda init bash >/dev/null 2>&1
source ~/.bashrc
conda activate mne


cd $OUTPUT_DIR


dirnames=(*/)
for d in "${dirnames[@]}"
do
  sub=${d%?}
  if [ -n "$sub" ]
  then
    echo "${sub}"
    python /scratch/nbe/tbi-meg/veera/pipeline/rpsd/relative_psd.py ${sub} ${OUTPUT_DIR}
  fi
done

