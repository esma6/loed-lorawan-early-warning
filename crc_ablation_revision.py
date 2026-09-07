"""Reviewer-requested CRC-dependence ablations for the LoED JTIT paper.

This script reads the already reproduced strict current-next table and writes
only to ``results_crc_ablation``. It never extracts or deletes raw data.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_DIR = Path(__file__).resolve().parent
INPUT_CSV = PROJECT_DIR / "results_reproduced" / "LoED_full_strict_forecasting.csv"
RESULT_DIR = PROJECT_DIR / "results_crc_ablation"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DROP_THRESHOLDS = (0.10, 0.20)
RANDOM_STATE = 42


def prepare_event_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path, low_memory=False)
    data["window_start"] = pd.to_datetime(data["window_start"], utc=True)
    data["date"] = pd.to_datetime(data["date"]).dt.date
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
    return data.dropna(subset=["prev_crc_success_rate", "prev_delta"]).copy()


def candidate_columns(data: pd.DataFrame) -> list[str]:
    excluded = {
        "next_crc_success_rate",
        "next_packet_count",
        "next_window_start",
        "gap_minutes",
        "poor_next",
        "drop_event",
        "window_start",
        "date",
    }
    return [column for column in data.columns if column not in excluded]


def build_feature_sets(all_features: list[str]) -> dict[str, list[str]]:
    crc_history = {
        "prev_crc_success_rate",
        "prev_delta",
        "rolling_crc_mean_3",
        "rolling_crc_std_3",
        "rolling_crc_mean_6",
        "rolling_crc_std_6",
    }
    current_and_rolling = {
        "crc_success_rate",
        "rolling_crc_mean_3",
        "rolling_crc_std_3",
        "rolling_crc_mean_6",
        "rolling_crc_std_6",
    }
    radio_current = {
        "rssi_mean", "rssi_std", "rssi_min", "rssi_max",
        "snr_mean", "snr_std", "snr_min", "snr_max",
    }
    radio_delayed = {"rolling_rssi_mean_3", "rolling_snr_mean_3"}

    def keep(names: set[str], include_gateway: bool = False) -> list[str]:
        selected = [column for column in all_features if column in names]
        if include_gateway and "gateway" in all_features:
            selected.append("gateway")
        return selected

    return {
        "full_features": list(all_features),
        "current_crc_only": keep({"crc_success_rate"}),
        "without_current_crc": [c for c in all_features if c != "crc_success_rate"],
        "without_current_rolling_crc": [
            c for c in all_features if c not in current_and_rolling
        ],
        "without_all_crc": [
            c for c in all_features if c not in crc_history | {"crc_success_rate"}
        ],
        "current_radio_only": keep(radio_current),
        "delayed_radio_only": keep(radio_delayed),
    }


def make_lr(feature_columns: list[str]) -> Pipeline:
    categorical = [c for c in feature_columns if c == "gateway"]
    numeric = [c for c in feature_columns if c not in categorical]
    transformers = []
    if numeric:
        transformers.append((
            "num",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]),
            numeric,
        ))
    if categorical:
        transformers.append((
            "cat",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]),
            categorical,
        ))
    return Pipeline([
        ("preprocess", ColumnTransformer(transformers=transformers)),
        ("model", LogisticRegression(
            max_iter=5000,
            solver="liblinear",
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )),
    ])


def metrics(y_true, y_pred, y_score) -> dict[str, float | int]:
    binary = len(np.unique(y_true)) == 2
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "BalancedAcc": balanced_accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1": f1_score(y_true, y_pred, zero_division=0),
        "ROC_AUC": roc_auc_score(y_true, y_score) if binary else np.nan,
        "PR_AUC": average_precision_score(y_true, y_score) if binary else np.nan,
        "PositiveRate": float(np.mean(y_true)),
        "PositiveCount": int(np.sum(y_true == 1)),
        "NegativeCount": int(np.sum(y_true == 0)),
        "valid_binary_test": int(binary),
    }


def fit_score(train, test, features, threshold):
    y_train = train["drop_event"].astype(int)
    y_test = test["drop_event"].astype(int)
    if y_train.nunique() < 2:
        return None
    model = make_lr(features)
    model.fit(train[features], y_train)
    prediction = model.predict(test[features])
    score = model.predict_proba(test[features])[:, 1]
    result = metrics(y_test, prediction, score)
    result["threshold"] = threshold
    result["train_samples"] = len(train)
    result["test_samples"] = len(test)
    result["feature_count"] = len(features)
    return result


def main():
    base = prepare_event_data(INPUT_CSV)
    all_features = candidate_columns(base)
    feature_sets = build_feature_sets(all_features)
    feature_manifest = pd.DataFrame([
        {"feature_setting": name, "feature": feature}
        for name, features in feature_sets.items()
        for feature in features
    ])
    feature_manifest.to_csv(RESULT_DIR / "crc_ablation_feature_manifest.csv", index=False)

    time_rows = []
    logo_rows = []

    for threshold in DROP_THRESHOLDS:
        event_data = base.copy()
        event_data["drop_event"] = (
            event_data["crc_success_rate"] - event_data["next_crc_success_rate"]
            >= threshold
        ).astype(int)

        dates = sorted(event_data["date"].unique())
        split_index = int(len(dates) * 0.70)
        train_dates, test_dates = dates[:split_index], dates[split_index:]
        time_train = event_data[event_data["date"].isin(train_dates)]
        time_test = event_data[event_data["date"].isin(test_dates)]

        for setting, features in feature_sets.items():
            print(f"TIME threshold={threshold:.2f} setting={setting}", flush=True)
            result = fit_score(time_train, time_test, features, threshold)
            if result:
                result.update({"feature_setting": setting, "split_type": "time_based"})
                time_rows.append(result)

        for gateway in sorted(event_data["gateway"].unique()):
            logo_train = event_data[event_data["gateway"] != gateway]
            logo_test = event_data[event_data["gateway"] == gateway]
            if len(logo_train) < 100 or len(logo_test) < 20:
                continue
            for setting, features in feature_sets.items():
                print(
                    f"LOGO threshold={threshold:.2f} gateway={gateway} setting={setting}",
                    flush=True,
                )
                result = fit_score(logo_train, logo_test, features, threshold)
                if result:
                    result.update({
                        "feature_setting": setting,
                        "split_type": "leave_one_gateway_out",
                        "test_gateway": gateway,
                    })
                    logo_rows.append(result)

    time_results = pd.DataFrame(time_rows)
    logo_details = pd.DataFrame(logo_rows)
    logo_binary = logo_details[logo_details["valid_binary_test"] == 1]
    metric_columns = [
        "Accuracy", "BalancedAcc", "Precision", "Recall", "F1",
        "ROC_AUC", "PR_AUC", "PositiveRate", "PositiveCount",
        "train_samples", "test_samples", "feature_count",
    ]
    logo_summary = (
        logo_binary.groupby(["threshold", "feature_setting"])[metric_columns]
        .agg(["mean", "std", "count"])
    )
    logo_summary.columns = [f"{metric}_{stat}" for metric, stat in logo_summary.columns]
    logo_summary = logo_summary.reset_index()

    time_results.to_csv(RESULT_DIR / "crc_ablation_time_results.csv", index=False)
    logo_details.to_csv(RESULT_DIR / "crc_ablation_logo_detailed.csv", index=False)
    logo_summary.to_csv(RESULT_DIR / "crc_ablation_logo_summary.csv", index=False)

    compact_time = time_results[[
        "threshold", "feature_setting", "feature_count", "Recall", "ROC_AUC", "PR_AUC"
    ]].sort_values(["threshold", "PR_AUC"], ascending=[True, False])
    compact_logo = logo_summary[[
        "threshold", "feature_setting", "feature_count_mean",
        "Recall_mean", "Recall_std", "ROC_AUC_mean", "ROC_AUC_std",
        "PR_AUC_mean", "PR_AUC_std", "PR_AUC_count",
    ]].sort_values(["threshold", "PR_AUC_mean"], ascending=[True, False])
    compact_time.to_csv(RESULT_DIR / "crc_ablation_time_compact.csv", index=False)
    compact_logo.to_csv(RESULT_DIR / "crc_ablation_logo_compact.csv", index=False)

    print("\nTIME RESULTS")
    print(compact_time.to_string(index=False))
    print("\nLOGO RESULTS (binary-test gateways, unweighted fold mean)")
    print(compact_logo.to_string(index=False))
    print(f"\nSaved to: {RESULT_DIR}")


if __name__ == "__main__":
    main()
