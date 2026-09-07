# Gateway-Level Early Warning of LoRaWAN Link Degradation

This repository contains the manuscript, analysis code and compact result
artifacts for **“Gateway-Level Early Warning of LoRaWAN Link Degradation Using
LoED Measurements.”** It is organized to support independent reproduction of
the chronological, leave-one-gateway-out (LOGO), ablation, calibration,
temporal-resolution, precursor, sequence-model and offline replay analyses.

## Authors

- Esma Fazilet Karagülle — Department of Computer Engineering, Atatürk University — [ORCID](https://orcid.org/0009-0002-7225-9970)
- Faruk Baturalp Günay — Assistant Professor, Department of Computer Engineering, Atatürk University — [ORCID](https://orcid.org/0000-0001-5472-3608) — baturalp@atauni.edu.tr
- Esra Odabaş Yıldırım — Assistant Professor, Department of Software Engineering, Atatürk University — [ORCID](https://orcid.org/0000-0002-0936-1342) — esra.odabas@atauni.edu.tr

## Repository structure

```text
.
├── data/                         # Dataset acquisition instructions
├── manuscript/                   # JTIT LaTeX source, figures and compiled PDF
├── results/                      # Compact reported tables and figures
├── loed_experiments.py           # Core preprocessing and model evaluation
├── crc_ablation_revision.py      # CRC and radio-feature ablations
├── statistical_validation.py     # Clustered uncertainty and paired tests
├── window_duration_experiments.py# 1/5/10/15-minute sensitivity
├── probability_calibration_analysis.py
├── lr_temporal_recalibration.py
├── gateway_results_artifacts.py
├── streaming_replay_experiment.py
├── physical_precursor_analysis.py
├── temporal_sequence_models.py
├── requirements.txt
└── CITATION.cff
```

## Data

The raw LoED archive is not duplicated in Git. Download it from
[Zenodo](https://doi.org/10.5281/zenodo.4121430) and place it at
`data/LoED_LoRaWAN_at_edge_dataset.zip`. Further provenance information is in
[`data/README.md`](data/README.md).

## Environment

The verified run used Python 3.12 on Windows. Create an isolated environment:

```bash
python -m venv .venv
```

Activate it and install the pinned dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

PyTorch installation may vary by platform; consult the official PyTorch
installation instructions if the pinned wheel is unavailable for your system.

## Reproduction workflow

Run commands from the repository root. Randomized estimators use fixed seeds.

```bash
python loed_experiments.py
python crc_ablation_revision.py
python statistical_validation.py
python crc_ablation_time_statistics.py
python window_duration_experiments.py
python probability_calibration_analysis.py
python lr_temporal_recalibration.py
python gateway_results_artifacts.py
python streaming_replay_experiment.py
python physical_precursor_analysis.py
python temporal_sequence_models.py
```

The first command performs raw-data processing and creates the shared
`results_reproduced/LoED_full_strict_forecasting.csv` input used by subsequent
analyses. The window-duration script additionally reads the extracted daily
files. Run times depend on CPU, memory and storage performance; the raw-data and
sequence-model stages are the most computationally intensive.

## Evaluation design

- **Chronological evaluation:** early dates are used for training and later
  dates for testing, preserving temporal order.
- **LOGO evaluation:** one gateway is held out at a time to quantify transfer
  to unseen gateways.
- **Uncertainty:** dates or gateways are treated as independent clusters;
  paired tests are adjusted using Holm correction.
- **Outcome:** a warning is positive when the next gateway-window exhibits a
  CRC success-rate decrease of at least 10% or 20%.

The code distinguishes ranking performance from probability calibration and
does not interpret gateway-observable associations as physical causes.

## Verified reference run

The reference run processed 188 daily files, 11,263,001 packet rows, 112,214
five-minute gateway-windows, 110,157 aligned current-next pairs and nine
gateways. Logistic Regression achieved chronological PR-AUC values of 0.562
and 0.360 for the 10% and 20% degradation thresholds. The paper reports the
full uncertainty, LOGO, ablation and sensitivity results.

## Manuscript

The journal-formatted source and compiled article are in `manuscript/`.
Compile with XeLaTeX from that directory:

```bash
xelatex -interaction=nonstopmode -halt-on-error JTIT_LoED_LoRaWAN_revision.tex
xelatex -interaction=nonstopmode -halt-on-error JTIT_LoED_LoRaWAN_revision.tex
```

## Citation

Citation metadata are provided in [`CITATION.cff`](CITATION.cff). Until the
article receives final bibliographic metadata, cite the title, authors and this
repository URL together with an access date.

## Reproducibility scope

The repository supports computational reproduction from the public LoED data.
The offline replay measures scoring on an evaluation computer and is not a
prospective deployment benchmark on gateway hardware. Exact timing values can
therefore vary across machines even when predictive metrics agree.

## License

No reuse license is asserted in this initial research release. The dataset
retains its original license and terms. Users may inspect and reproduce the
materials; broader redistribution or derivative use requires permission from
the relevant rights holders until a project license is added.
