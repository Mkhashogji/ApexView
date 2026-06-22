#!/usr/bin/env bash
# Runs the granularity diagnostic suite inside the f1-api container environment.
# Primary session: 2025 China (Shanghai) Q3 — mixed circuit, heavy braking at T14.
# Contrast session: 2025 Monaco Q3 — street circuit, low speed.
set -u
cd "$(dirname "$0")"
mkdir -p results

PRIMARY_YEAR=2025; PRIMARY_GP=China;  PRIMARY_CID=shanghai
CONTRAST_YEAR=2025; CONTRAST_GP=Monaco; CONTRAST_CID=monaco

echo "##### PRIMARY: ${PRIMARY_YEAR} ${PRIMARY_GP} (${PRIMARY_CID}) #####"
python 01_sample_intervals.py    $PRIMARY_YEAR $PRIMARY_GP
python 02_spatial_resolution.py  $PRIMARY_YEAR $PRIMARY_GP
python 03_derivative_noise.py    $PRIMARY_YEAR $PRIMARY_GP $PRIMARY_CID
python 04_channel_character.py   $PRIMARY_YEAR $PRIMARY_GP
python 05_corner_scale.py        $PRIMARY_YEAR $PRIMARY_GP $PRIMARY_CID
python 06_alignment_interaction.py $PRIMARY_YEAR $PRIMARY_GP

echo; echo "##### CONTRAST: ${CONTRAST_YEAR} ${CONTRAST_GP} (${CONTRAST_CID}) #####"
python 02_spatial_resolution.py  $CONTRAST_YEAR $CONTRAST_GP
python 05_corner_scale.py        $CONTRAST_YEAR $CONTRAST_GP $CONTRAST_CID
python 06_alignment_interaction.py $CONTRAST_YEAR $CONTRAST_GP
