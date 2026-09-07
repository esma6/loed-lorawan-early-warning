"""Causal offline streaming replay of the calibrated LR warning pipeline.

The replay consumes already aggregated gateway-window rows in timestamp order.
Lag and rolling features are causal. Reported latency covers preprocessing,
imputation, scaling, encoding, LR scoring, and sigmoid calibration; it excludes
raw packet ingestion and five-minute aggregation.
"""

from pathlib import Path
from time import perf_counter_ns
import platform

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

import probability_calibration_analysis as base

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results_streaming_replay"
OUTPUT.mkdir(exist_ok=True)
ALARM_BUDGETS = (0.05, 0.10)


def calibrate(y, scores):
    model = LogisticRegression(solver="lbfgs", random_state=base.RANDOM_STATE)
    model.fit(scores.reshape(-1, 1), y)
    return model


def measures(y, alarm):
    tp = int(np.sum((y == 1) & alarm))
    alerted = int(alarm.sum())
    positives = int(y.sum())
    return {
        "windows": len(y), "events": positives, "alerts": alerted,
        "alert_rate": alerted / len(y),
        "precision": tp / alerted if alerted else np.nan,
        "event_recall": tp / positives if positives else np.nan,
        "lift_over_random": (tp / positives) / (alerted / len(y))
                            if positives and alerted else np.nan,
    }


def main():
    data, features, numeric = base.prepare_data()
    dates = sorted(data.date.unique())
    development_dates = dates[:int(len(dates) * .70)]
    dev_cut = int(len(development_dates) * .80)
    fit_dates = set(development_dates[:dev_cut])
    calibration_dates = set(development_dates[dev_cut:])
    test_dates = set(dates[int(len(dates) * .70):])
    outputs, latency_rows = [], []

    for threshold in base.THRESHOLDS:
        data["target"] = ((data.crc_success_rate - data.next_crc_success_rate)
                          >= threshold).astype(int)
        fit = data[data.date.isin(fit_dates)].copy()
        calibration = data[data.date.isin(calibration_dates)].copy()
        test = data[data.date.isin(test_dates)].sort_values(
            ["window_start", "gateway"]).copy()

        predictor = base.models(numeric, fit.target.to_numpy())["LogisticRegression"]
        predictor.fit(fit[features], fit.target)
        calibration_raw = predictor.predict_proba(calibration[features])[:, 1]
        sigmoid = calibrate(calibration.target.to_numpy(), calibration_raw)
        calibration_probability = sigmoid.predict_proba(
            calibration_raw.reshape(-1, 1))[:, 1]

        budget_thresholds = {
            budget: float(np.quantile(calibration_probability, 1 - budget))
            for budget in ALARM_BUDGETS
        }

        probabilities = np.empty(len(test), dtype=float)
        position = 0
        for timestamp, group in test.groupby("window_start", sort=True):
            start = perf_counter_ns()
            raw = predictor.predict_proba(group[features])[:, 1]
            probability = sigmoid.predict_proba(raw.reshape(-1, 1))[:, 1]
            elapsed = perf_counter_ns() - start
            n = len(group)
            probabilities[position:position+n] = probability
            position += n
            latency_rows.append({
                "threshold": threshold, "window_start": timestamp,
                "gateway_windows": n, "batch_latency_ms": elapsed / 1e6,
                "latency_ms_per_gateway_window": elapsed / 1e6 / n,
            })

        replay = test[["gateway", "window_start", "date", "target"]].copy()
        replay["calibrated_probability"] = probabilities
        for budget, cutoff in budget_thresholds.items():
            replay[f"alarm_budget_{int(budget*100)}"] = probabilities >= cutoff
            row = {"threshold": threshold, "target_alarm_budget": budget,
                   "score_cutoff_from_calibration": cutoff}
            row.update(measures(replay.target.to_numpy(),
                                replay[f"alarm_budget_{int(budget*100)}"].to_numpy()))
            outputs.append(row)
        replay.to_csv(OUTPUT / f"stream_replay_predictions_{threshold:.2f}.csv",
                      index=False)

    latency = pd.DataFrame(latency_rows)
    summary = pd.DataFrame(outputs)
    latency_summary = latency.groupby("threshold", as_index=False).agg(
        timestamp_batches=("window_start", "count"),
        gateway_windows=("gateway_windows", "sum"),
        mean_batch_latency_ms=("batch_latency_ms", "mean"),
        p95_batch_latency_ms=("batch_latency_ms", lambda x: np.quantile(x, .95)),
        p99_batch_latency_ms=("batch_latency_ms", lambda x: np.quantile(x, .99)),
        max_batch_latency_ms=("batch_latency_ms", "max"),
        mean_latency_ms_per_window=("latency_ms_per_gateway_window", "mean"),
        p95_latency_ms_per_window=("latency_ms_per_gateway_window",
                                   lambda x: np.quantile(x, .95)),
    )
    summary.to_csv(OUTPUT / "streaming_alarm_summary.csv", index=False)
    latency.to_csv(OUTPUT / "streaming_latency_detailed.csv", index=False)
    latency_summary.to_csv(OUTPUT / "streaming_latency_summary.csv", index=False)
    (OUTPUT / "runtime_environment.txt").write_text(
        f"platform={platform.platform()}\nprocessor={platform.processor()}\n"
        f"python={platform.python_version()}\n"
        "latency_scope=preprocessing+LR scoring+sigmoid calibration\n"
        "excluded=raw packet ingestion and five-minute aggregation\n",
        encoding="utf-8")
    print("\nALARMS")
    print(summary.to_string(index=False))
    print("\nLATENCY")
    print(latency_summary.to_string(index=False))


if __name__ == "__main__":
    main()
