"""Leakage-safe temporal recalibration of the preferred LR classifier."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss

import probability_calibration_analysis as base


OUTPUT = Path(__file__).resolve().parent / "results_probability_calibration"


def fit_calibrators(y, scores):
    sigmoid = LogisticRegression(solver="lbfgs", random_state=base.RANDOM_STATE)
    sigmoid.fit(scores.reshape(-1, 1), y)
    isotonic = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
    isotonic.fit(scores, y)
    return sigmoid, isotonic


def transform(method, sigmoid, isotonic, scores):
    if method == "uncalibrated":
        return scores
    if method == "sigmoid":
        return sigmoid.predict_proba(scores.reshape(-1, 1))[:, 1]
    return isotonic.predict(scores)


def evaluate(split, threshold, gateway, fit, calibration, test, features, numeric):
    model = base.models(numeric, fit.target.to_numpy())["LogisticRegression"]
    model.fit(fit[features], fit.target)
    calibration_scores = model.predict_proba(calibration[features])[:, 1]
    test_scores = model.predict_proba(test[features])[:, 1]
    sigmoid, isotonic = fit_calibrators(calibration.target.to_numpy(),
                                        calibration_scores)
    rows, bins, predictions = [], [], []
    for method in ("uncalibrated", "sigmoid", "isotonic"):
        p = transform(method, sigmoid, isotonic, test_scores)
        summary, bin_table = base.summarize(split, threshold, method,
                                            test.target.to_numpy(), p)
        summary["test_gateway"] = gateway
        summary["fit_n"] = len(fit)
        summary["calibration_n"] = len(calibration)
        rows.append(summary)
        bin_table = bin_table.rename(columns={"model": "method"})
        bin_table["test_gateway"] = gateway
        bins.append(bin_table)
        predictions.append(pd.DataFrame({
            "split_type": split, "threshold": threshold,
            "test_gateway": gateway, "method": method,
            "y_true": test.target.to_numpy(), "y_probability": p,
        }))
    return rows, bins, predictions


def temporal_parts(frame, fit_fraction=0.80):
    dates = sorted(frame.date.unique())
    cut = max(1, min(len(dates) - 1, int(len(dates) * fit_fraction)))
    fit_dates = set(dates[:cut])
    calibration_dates = set(dates[cut:])
    return frame[frame.date.isin(fit_dates)], frame[frame.date.isin(calibration_dates)]


def main():
    data, features, numeric = base.prepare_data()
    dates = sorted(data.date.unique())
    test_cut = int(len(dates) * 0.70)
    development = data[data.date.isin(set(dates[:test_cut]))].copy()
    chronological_test = data[data.date.isin(set(dates[test_cut:]))].copy()
    all_rows, all_bins, all_predictions = [], [], []

    for threshold in base.THRESHOLDS:
        for frame in (development, chronological_test, data):
            frame["target"] = ((frame.crc_success_rate - frame.next_crc_success_rate)
                               >= threshold).astype(int)
        fit, calibration = temporal_parts(development)
        print(f"TIME recalibration threshold={threshold:.2f}", flush=True)
        rows, bins, preds = evaluate("Time", threshold, "", fit, calibration,
                                    chronological_test, features, numeric)
        all_rows += rows; all_bins += bins; all_predictions += preds

        for gateway in sorted(data.gateway.unique()):
            training_gateways = data[data.gateway != gateway].copy()
            test = data[data.gateway == gateway].copy()
            if test.target.nunique() < 2:
                continue
            fit, calibration = temporal_parts(training_gateways)
            if fit.target.nunique() < 2 or calibration.target.nunique() < 2:
                continue
            print(f"LOGO recalibration threshold={threshold:.2f} gateway={gateway}",
                  flush=True)
            rows, bins, preds = evaluate("LOGO", threshold, gateway, fit,
                                        calibration, test, features, numeric)
            all_rows += rows; all_bins += bins; all_predictions += preds

    detailed = pd.DataFrame(all_rows)
    bins = pd.concat(all_bins, ignore_index=True)
    predictions = pd.concat(all_predictions, ignore_index=True)
    detailed.to_csv(OUTPUT / "lr_recalibration_detailed.csv", index=False)
    bins.to_csv(OUTPUT / "lr_recalibration_bins.csv", index=False)
    predictions.to_csv(OUTPUT / "lr_recalibration_predictions.csv", index=False)

    logo = detailed[detailed.split_type == "LOGO"]
    logo_summary = logo.groupby(["threshold", "model"], as_index=False).agg(
        valid_gateway_count=("test_gateway", "nunique"),
        prevalence_mean=("prevalence", "mean"),
        mean_predicted_mean=("mean_predicted", "mean"),
        brier_score_mean=("brier_score", "mean"),
        brier_score_sd=("brier_score", "std"),
        ece_mean=("ece_equal_frequency", "mean"),
        ece_sd=("ece_equal_frequency", "std"),
        brier_skill_mean=("brier_skill_score", "mean"),
    )
    logo_summary = logo_summary.rename(columns={"model": "method"})
    logo_summary.to_csv(OUTPUT / "lr_recalibration_logo_summary.csv", index=False)

    for split in ("Time", "LOGO"):
        for threshold in base.THRESHOLDS:
            if split == "Time":
                subset = bins[(bins.split_type == split) &
                              (bins.threshold == threshold) &
                              (bins.strategy == "equal_frequency")]
            else:
                pooled = predictions[(predictions.split_type == split) &
                                     (predictions.threshold == threshold)]
                pieces = []
                for method, group in pooled.groupby("method"):
                    table = base.calibration_bins(group.y_true,
                                                  group.y_probability,
                                                  "equal_frequency")
                    table["method"] = method
                    pieces.append(table)
                subset = pd.concat(pieces, ignore_index=True)
            fig, ax = plt.subplots(figsize=(6.4, 5.2))
            for method, group in subset.groupby("method"):
                ax.plot(group.mean_predicted, group.observed_rate,
                        marker="o", linewidth=1.7, label=method)
            ax.plot([0, 1], [0, 1], "--", color="black", linewidth=1,
                    label="Perfect calibration")
            ax.set(xlim=(0, 1), ylim=(0, 1),
                   xlabel="Mean predicted probability",
                   ylabel="Observed event rate",
                   title=f"LR temporal recalibration: {split}, drop >= {threshold:.2f}")
            ax.grid(alpha=.25); ax.legend(); fig.tight_layout()
            fig.savefig(OUTPUT / f"lr_recalibration_{split.lower()}_{threshold:.2f}.png",
                        dpi=180)
            plt.close(fig)

    print("\nTIME")
    print(detailed[detailed.split_type == "Time"].to_string(index=False))
    print("\nLOGO MEAN")
    print(logo_summary.to_string(index=False))


if __name__ == "__main__":
    main()
