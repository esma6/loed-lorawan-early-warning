"""Probability-calibration analysis for the submitted LoED classifiers.

Produces chronological-test and pooled out-of-fold LOGO predictions, Brier
scores, equal-width/equal-frequency ECE values, and reliability diagrams.
No held-out labels are used to alter model probabilities.
"""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except Exception:
    HAS_XGB = False


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "results_reproduced" / "LoED_full_strict_forecasting.csv"
OUTPUT = ROOT / "results_probability_calibration"
OUTPUT.mkdir(exist_ok=True)

THRESHOLDS = (0.10, 0.20)
N_BINS = 10
RANDOM_STATE = 42


def prepare_data():
    data = pd.read_csv(INPUT, parse_dates=["window_start", "next_window_start"])
    data = data.sort_values(["gateway", "window_start"]).copy()
    grouped = data.groupby("gateway", sort=False)
    data["prev_crc_success_rate"] = grouped["crc_success_rate"].shift(1)
    data["prev_delta"] = data["crc_success_rate"] - data["prev_crc_success_rate"]
    data["rolling_crc_mean_3"] = grouped["crc_success_rate"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    data["rolling_crc_std_3"] = grouped["crc_success_rate"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=2).std()
    )
    data["rolling_crc_mean_6"] = grouped["crc_success_rate"].transform(
        lambda s: s.shift(1).rolling(6, min_periods=1).mean()
    )
    data["rolling_crc_std_6"] = grouped["crc_success_rate"].transform(
        lambda s: s.shift(1).rolling(6, min_periods=2).std()
    )
    data["rolling_rssi_mean_3"] = grouped["rssi_mean"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    data["rolling_snr_mean_3"] = grouped["snr_mean"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    data = data.dropna(subset=["prev_crc_success_rate", "prev_delta"]).copy()
    data["date"] = data["window_start"].dt.date.astype(str)
    excluded = {
        "next_crc_success_rate", "next_packet_count", "next_window_start",
        "gap_minutes", "poor_next", "drop_event", "window_start", "date",
    }
    features = [c for c in data.columns if c not in excluded]
    numeric = [c for c in features if c != "gateway"]
    return data, features, numeric


def preprocess(numeric, scale):
    num_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        num_steps.append(("scaler", StandardScaler()))
    return ColumnTransformer([
        ("num", Pipeline(num_steps), numeric),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), ["gateway"]),
    ])


def models(numeric, y):
    result = {
        "LogisticRegression": Pipeline([
            ("preprocess", preprocess(numeric, True)),
            ("model", LogisticRegression(max_iter=5000, solver="liblinear",
                                          class_weight="balanced",
                                          random_state=RANDOM_STATE)),
        ]),
        "RandomForest": Pipeline([
            ("preprocess", preprocess(numeric, False)),
            ("model", RandomForestClassifier(
                n_estimators=300, max_depth=8, min_samples_leaf=8,
                class_weight="balanced", random_state=RANDOM_STATE,
                n_jobs=-1)),
        ]),
    }
    if HAS_XGB:
        pos = int(np.sum(y == 1))
        neg = int(np.sum(y == 0))
        result["XGBoost"] = Pipeline([
            ("preprocess", preprocess(numeric, False)),
            ("model", XGBClassifier(
                n_estimators=300, max_depth=3, learning_rate=0.03,
                subsample=0.9, colsample_bytree=0.9,
                scale_pos_weight=neg / max(pos, 1), eval_metric="logloss",
                random_state=RANDOM_STATE, n_jobs=-1)),
        ])
    return result


def calibration_bins(y, p, strategy):
    frame = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    if strategy == "equal_width":
        edges = np.linspace(0, 1, N_BINS + 1)
        frame["bin"] = pd.cut(frame.p, edges, include_lowest=True,
                              labels=False)
    else:
        frame["bin"] = pd.qcut(frame.p, N_BINS, duplicates="drop",
                               labels=False)
    table = frame.groupby("bin", observed=True).agg(
        count=("y", "size"), mean_predicted=("p", "mean"),
        observed_rate=("y", "mean"), min_predicted=("p", "min"),
        max_predicted=("p", "max"),
    ).reset_index()
    table["abs_gap"] = abs(table.mean_predicted - table.observed_rate)
    table["weight"] = table["count"] / len(frame)
    return table


def summarize(split, threshold, model, y, p):
    width = calibration_bins(y, p, "equal_width")
    quantile = calibration_bins(y, p, "equal_frequency")
    row = {
        "split_type": split, "threshold": threshold, "model": model,
        "n": len(y), "positive_count": int(np.sum(y)),
        "prevalence": float(np.mean(y)), "mean_predicted": float(np.mean(p)),
        "calibration_in_large": float(np.mean(p) - np.mean(y)),
        "brier_score": brier_score_loss(y, p),
        "brier_reference": brier_score_loss(y, np.repeat(np.mean(y), len(y))),
        "log_loss": log_loss(y, p, labels=[0, 1]),
        "ece_equal_width": float((width.abs_gap * width.weight).sum()),
        "ece_equal_frequency": float((quantile.abs_gap * quantile.weight).sum()),
    }
    row["brier_skill_score"] = 1 - row["brier_score"] / row["brier_reference"]
    tables = []
    for strategy, table in (("equal_width", width), ("equal_frequency", quantile)):
        table.insert(0, "model", model)
        table.insert(0, "threshold", threshold)
        table.insert(0, "split_type", split)
        table.insert(3, "strategy", strategy)
        tables.append(table)
    return row, pd.concat(tables, ignore_index=True)


def plot_reliability(bins, split, threshold):
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    subset = bins[(bins.split_type == split) &
                  (bins.threshold == threshold) &
                  (bins.strategy == "equal_frequency")]
    for model, group in subset.groupby("model"):
        ax.plot(group.mean_predicted, group.observed_rate, marker="o",
                linewidth=1.7, label=model)
    ax.plot([0, 1], [0, 1], "--", color="black", linewidth=1,
            label="Perfect calibration")
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="Mean predicted probability",
           ylabel="Observed event rate",
           title=f"Reliability diagram: {split}, drop >= {threshold:.2f}")
    ax.grid(alpha=.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUTPUT / f"reliability_{split.lower()}_{threshold:.2f}.png", dpi=180)
    plt.close(fig)


def main():
    data, features, numeric = prepare_data()
    dates = sorted(data.date.unique())
    cutoff = int(len(dates) * 0.70)
    train_dates, test_dates = set(dates[:cutoff]), set(dates[cutoff:])
    summaries, all_bins, predictions = [], [], []

    for threshold in THRESHOLDS:
        data["target"] = ((data.crc_success_rate - data.next_crc_success_rate)
                          >= threshold).astype(int)
        train = data[data.date.isin(train_dates)]
        test = data[data.date.isin(test_dates)]
        for name, model in models(numeric, train.target.to_numpy()).items():
            print(f"TIME threshold={threshold:.2f} model={name}", flush=True)
            model.fit(train[features], train.target)
            p = model.predict_proba(test[features])[:, 1]
            row, bins = summarize("Time", threshold, name, test.target, p)
            summaries.append(row); all_bins.append(bins)
            predictions.append(pd.DataFrame({
                "split_type": "Time", "threshold": threshold, "model": name,
                "gateway": test.gateway.to_numpy(), "date": test.date.to_numpy(),
                "y_true": test.target.to_numpy(), "y_probability": p,
            }))

        logo_parts = {}
        for gateway in sorted(data.gateway.unique()):
            train = data[data.gateway != gateway]
            test = data[data.gateway == gateway]
            if train.target.nunique() < 2 or test.target.nunique() < 2:
                continue
            for name, model in models(numeric, train.target.to_numpy()).items():
                print(f"LOGO threshold={threshold:.2f} gateway={gateway} model={name}",
                      flush=True)
                model.fit(train[features], train.target)
                p = model.predict_proba(test[features])[:, 1]
                part = pd.DataFrame({
                    "split_type": "LOGO", "threshold": threshold, "model": name,
                    "gateway": test.gateway.to_numpy(), "date": test.date.to_numpy(),
                    "y_true": test.target.to_numpy(), "y_probability": p,
                })
                logo_parts.setdefault(name, []).append(part)
        for name, parts in logo_parts.items():
            pooled = pd.concat(parts, ignore_index=True)
            row, bins = summarize("LOGO", threshold, name, pooled.y_true,
                                  pooled.y_probability)
            row["valid_gateway_count"] = pooled.gateway.nunique()
            summaries.append(row); all_bins.append(bins); predictions.append(pooled)

    summary = pd.DataFrame(summaries)
    bins = pd.concat(all_bins, ignore_index=True)
    preds = pd.concat(predictions, ignore_index=True)
    summary.to_csv(OUTPUT / "calibration_summary.csv", index=False)
    bins.to_csv(OUTPUT / "calibration_bins.csv", index=False)
    preds.to_csv(OUTPUT / "calibration_predictions.csv", index=False)
    for split in ("Time", "LOGO"):
        for threshold in THRESHOLDS:
            plot_reliability(bins, split, threshold)
    print("\nCALIBRATION SUMMARY")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
