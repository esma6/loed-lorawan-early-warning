"""Date-clustered confidence intervals for chronological CRC ablations."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from crc_ablation_revision import (
    build_feature_sets,
    candidate_columns,
    make_lr,
    prepare_event_data,
)
from statistical_validation import holm_adjust


PROJECT_DIR = Path(__file__).resolve().parent
INPUT_CSV = PROJECT_DIR / "results_reproduced" / "LoED_full_strict_forecasting.csv"
RESULT_DIR = PROJECT_DIR / "results_statistical_validation"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
THRESHOLDS = (0.10, 0.20)
METRICS = ("PR_AUC", "ROC_AUC")
N_BOOTSTRAP = 1000
SEED = 2026


def score_metric(y, score, metric):
    return (
        average_precision_score(y, score)
        if metric == "PR_AUC"
        else roc_auc_score(y, score)
    )


def pvalue(values):
    values = np.asarray(values)
    lower = (np.sum(values <= 0) + 1) / (len(values) + 1)
    upper = (np.sum(values >= 0) + 1) / (len(values) + 1)
    return min(1.0, 2 * min(lower, upper))


def main():
    rng = np.random.default_rng(SEED)
    base = prepare_event_data(INPUT_CSV)
    feature_sets = build_feature_sets(candidate_columns(base))
    variants = [name for name in feature_sets if name != "full_features"]
    prediction_frames = []
    ci_rows = []
    test_rows = []

    for threshold in THRESHOLDS:
        data = base.copy()
        data["drop_event"] = (
            data["crc_success_rate"] - data["next_crc_success_rate"] >= threshold
        ).astype(int)
        dates = sorted(data["date"].unique())
        split = int(len(dates) * 0.70)
        train = data[data["date"].isin(dates[:split])]
        test = data[data["date"].isin(dates[split:])].copy()
        predictions = test[["date", "gateway"]].reset_index(drop=True)
        predictions["y_true"] = test["drop_event"].to_numpy()

        for setting, features in feature_sets.items():
            print(f"FIT threshold={threshold:.2f} setting={setting}", flush=True)
            model = make_lr(features)
            model.fit(train[features], train["drop_event"])
            predictions[setting] = model.predict_proba(test[features])[:, 1]
        predictions["threshold"] = threshold
        prediction_frames.append(predictions)

        unique_dates = predictions["date"].drop_duplicates().to_numpy()
        groups = {
            date: predictions.index[predictions["date"] == date].to_numpy()
            for date in unique_dates
        }
        boot = {
            metric: {setting: [] for setting in feature_sets}
            for metric in METRICS
        }
        for _ in range(N_BOOTSTRAP):
            sampled = rng.choice(unique_dates, size=len(unique_dates), replace=True)
            indexes = np.concatenate([groups[date] for date in sampled])
            y = predictions.loc[indexes, "y_true"].to_numpy()
            for metric in METRICS:
                for setting in feature_sets:
                    boot[metric][setting].append(
                        score_metric(y, predictions.loc[indexes, setting], metric)
                    )

        for metric in METRICS:
            for setting in feature_sets:
                values = np.asarray(boot[metric][setting])
                low, high = np.quantile(values, [0.025, 0.975])
                ci_rows.append({
                    "threshold": threshold,
                    "metric": metric,
                    "feature_setting": setting,
                    "estimate": score_metric(
                        predictions["y_true"], predictions[setting], metric
                    ),
                    "ci_low": low,
                    "ci_high": high,
                    "resampling_unit": "collection_date",
                    "clusters": len(unique_dates),
                    "bootstrap_replicates": N_BOOTSTRAP,
                })
            full = np.asarray(boot[metric]["full_features"])
            for variant in variants:
                differences = full - np.asarray(boot[metric][variant])
                low, high = np.quantile(differences, [0.025, 0.975])
                test_rows.append({
                    "split_type": "time_based",
                    "family": "crc_ablation",
                    "threshold": threshold,
                    "metric": metric,
                    "comparison": f"full_features-{variant}",
                    "difference": score_metric(
                        predictions["y_true"], predictions["full_features"], metric
                    ) - score_metric(predictions["y_true"], predictions[variant], metric),
                    "ci_low": low,
                    "ci_high": high,
                    "p_raw": pvalue(differences),
                    "test": "paired date-cluster bootstrap",
                    "pairs": len(unique_dates),
                })

    cis = pd.DataFrame(ci_rows)
    tests = holm_adjust(
        pd.DataFrame(test_rows),
        ["split_type", "family", "threshold", "metric"],
    )
    tests["significant_holm_0_05"] = tests["p_holm"] < 0.05
    pd.concat(prediction_frames, ignore_index=True).to_csv(
        RESULT_DIR / "crc_ablation_time_predictions.csv", index=False
    )
    cis.to_csv(RESULT_DIR / "crc_ablation_time_confidence_intervals.csv", index=False)
    tests.to_csv(RESULT_DIR / "crc_ablation_time_paired_tests.csv", index=False)
    print("\nCRC TIME CONFIDENCE INTERVALS")
    print(cis.to_string(index=False))
    print("\nCRC TIME PAIRED TESTS")
    print(tests.to_string(index=False))


if __name__ == "__main__":
    main()
