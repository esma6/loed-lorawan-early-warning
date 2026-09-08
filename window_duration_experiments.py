"""Reviewer-requested 1/5/10/15-minute LoED window sensitivity study.

Raw daily CSV files are read once. Each duration uses identical cleaning,
minimum packet support, strict next-window alignment, feature engineering,
chronological date split, and leave-one-gateway-out Logistic Regression.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from crc_ablation_revision import make_lr, metrics


PROJECT_DIR = Path(__file__).resolve().parent
LOCAL_EXTRACT_DIR = PROJECT_DIR / "data" / "LoED_full_extracted"
EXISTING_EXTRACT_DIR = Path(r"C:\Users\ETU\Downloads\LoED_full_extracted")
DATA_DIR = LOCAL_EXTRACT_DIR if LOCAL_EXTRACT_DIR.exists() else EXISTING_EXTRACT_DIR
RESULT_DIR = PROJECT_DIR / "results_window_duration"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS = ("1min", "5min", "10min", "15min")
THRESHOLDS = (0.10, 0.20)
MIN_PACKETS = 10

NEEDED_COLUMNS = [
    "time", "gateway", "crc_status", "frequency", "spreading_factor",
    "rssi", "snr", "size",
]


def crc_binary(series):
    numeric = pd.to_numeric(series, errors="coerce")
    result = pd.Series(np.nan, index=series.index)
    result[numeric == 1] = 1
    result[numeric.isin((-1, 0))] = 0
    return result


def aggregate_file(data, window):
    data = data.copy()
    data["window_start"] = data["time"].dt.floor(window)
    group_columns = ["gateway", "window_start"]
    aggregated = data.groupby(group_columns).agg(
        packet_count=("crc_ok", "count"),
        crc_success_rate=("crc_ok", "mean"),
        rssi_mean=("rssi", "mean"),
        rssi_std=("rssi", "std"),
        rssi_min=("rssi", "min"),
        rssi_max=("rssi", "max"),
        snr_mean=("snr", "mean"),
        snr_std=("snr", "std"),
        snr_min=("snr", "min"),
        snr_max=("snr", "max"),
        size_mean=("size", "mean"),
        size_std=("size", "std"),
        spreading_factor_mean=("spreading_factor", "mean"),
        spreading_factor_std=("spreading_factor", "std"),
        frequency_nunique=("frequency", "nunique"),
    ).reset_index()
    sf_counts = (
        data.dropna(subset=["spreading_factor"])
        .groupby(group_columns + ["spreading_factor"])
        .size()
        .unstack(fill_value=0)
    )
    if len(sf_counts):
        ratios = sf_counts.div(sf_counts.sum(axis=1), axis=0)
        ratios.columns = [f"sf_{int(value)}_ratio" for value in ratios.columns]
        aggregated = aggregated.merge(ratios.reset_index(), on=group_columns, how="left")
    return aggregated


def aggregate_all_windows():
    csv_files = sorted(
        path for path in DATA_DIR.rglob("*.csv") if "__MACOSX" not in str(path)
    )
    if len(csv_files) <= 6:
        raise RuntimeError(f"Expected full dataset; found only {len(csv_files)} CSV files")
    parts = {window: [] for window in WINDOWS}
    raw_rows = clean_rows = 0
    for index, path in enumerate(csv_files, 1):
        if index == 1 or index % 20 == 0 or index == len(csv_files):
            print(f"RAW {index}/{len(csv_files)} {path.name}", flush=True)
        data = pd.read_csv(path, low_memory=False)
        raw_rows += len(data)
        data.columns = [str(column).strip().lower() for column in data.columns]
        missing = [column for column in NEEDED_COLUMNS if column not in data.columns]
        if missing:
            raise RuntimeError(f"{path} missing columns: {missing}")
        data = data[NEEDED_COLUMNS].copy()
        data["time"] = pd.to_datetime(data["time"], errors="coerce", utc=True)
        data["gateway"] = data["gateway"].astype(str)
        data["crc_ok"] = crc_binary(data["crc_status"])
        for column in ("frequency", "spreading_factor", "rssi", "snr", "size"):
            data[column] = pd.to_numeric(data[column], errors="coerce")
        data = data.dropna(subset=["time", "gateway", "crc_ok", "rssi", "snr"])
        data["crc_ok"] = data["crc_ok"].astype(int)
        data = data[data["rssi"].between(-160, -20)]
        data = data[data["snr"].between(-40, 30)]
        data.loc[~data["spreading_factor"].between(6, 12), "spreading_factor"] = np.nan
        clean_rows += len(data)
        for window in WINDOWS:
            parts[window].append(aggregate_file(data, window))
    return parts, len(csv_files), raw_rows, clean_rows


def build_strict(parts, window):
    data = pd.concat(parts, ignore_index=True)
    for sf in range(6, 13):
        column = f"sf_{sf}_ratio"
        if column not in data:
            data[column] = 0.0
    ratio_columns = [c for c in data if c.startswith("sf_") and c.endswith("_ratio")]
    data[ratio_columns] = data[ratio_columns].fillna(0.0)
    data = data[data["packet_count"] >= MIN_PACKETS].copy()
    duplicates = data.duplicated(["gateway", "window_start"]).sum()
    data = data.drop_duplicates(["gateway", "window_start"], keep="first")
    data["hour"] = data["window_start"].dt.hour
    data["dayofweek"] = data["window_start"].dt.dayofweek
    data["date"] = data["window_start"].dt.date
    data = data.sort_values(["gateway", "window_start"]).reset_index(drop=True)

    strict = data.copy()
    grouped = strict.groupby("gateway", sort=False)
    strict["next_window_start"] = grouped["window_start"].shift(-1)
    strict["next_crc_success_rate"] = grouped["crc_success_rate"].shift(-1)
    strict["next_packet_count"] = grouped["packet_count"].shift(-1)
    strict["gap_minutes"] = (
        strict["next_window_start"] - strict["window_start"]
    ).dt.total_seconds() / 60
    minutes = pd.Timedelta(window).total_seconds() / 60
    strict = strict[
        strict["gap_minutes"].eq(minutes) & strict["next_crc_success_rate"].notna()
    ].copy()
    return data, strict, int(duplicates)


def feature_engineering(strict):
    data = strict.sort_values(["gateway", "window_start"]).copy()
    grouped = data.groupby("gateway", sort=False)
    data["prev_crc_success_rate"] = grouped["crc_success_rate"].shift(1)
    data["prev_delta"] = data["crc_success_rate"] - data["prev_crc_success_rate"]
    for width in (3, 6):
        data[f"rolling_crc_mean_{width}"] = grouped["crc_success_rate"].transform(
            lambda s, width=width: s.shift(1).rolling(width, min_periods=1).mean()
        )
        data[f"rolling_crc_std_{width}"] = grouped["crc_success_rate"].transform(
            lambda s, width=width: s.shift(1).rolling(width, min_periods=2).std()
        )
    data["rolling_rssi_mean_3"] = grouped["rssi_mean"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    data["rolling_snr_mean_3"] = grouped["snr_mean"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    return data.dropna(subset=["prev_crc_success_rate", "prev_delta"]).copy()


def feature_columns(data):
    excluded = {
        "next_crc_success_rate", "next_packet_count", "next_window_start",
        "gap_minutes", "drop_event", "window_start", "date",
    }
    return [column for column in data if column not in excluded]


def fit_lr(train, test, features, threshold):
    model = make_lr(features)
    model.fit(train[features], train["drop_event"])
    prediction = model.predict(test[features])
    score = model.predict_proba(test[features])[:, 1]
    result = metrics(test["drop_event"].to_numpy(), prediction, score)
    result.update({
        "threshold": threshold,
        "train_samples": len(train),
        "test_samples": len(test),
        "feature_count": len(features),
    })
    return result


def evaluate_duration(event_base, window):
    features = feature_columns(event_base)
    time_rows, logo_rows = [], []
    for threshold in THRESHOLDS:
        data = event_base.copy()
        data["drop_event"] = (
            data["crc_success_rate"] - data["next_crc_success_rate"] >= threshold - 1e-12
        ).astype(int)
        dates = sorted(data["date"].unique())
        split = int(len(dates) * 0.70)
        train = data[data["date"].isin(dates[:split])]
        test = data[data["date"].isin(dates[split:])]
        print(f"TIME window={window} threshold={threshold:.2f}", flush=True)
        row = fit_lr(train, test, features, threshold)
        row.update({
            "window": window,
            "split_type": "time_based",
            "total_samples": len(data),
            "overall_event_rate": data["drop_event"].mean(),
            "test_event_rate": test["drop_event"].mean(),
            "date_count": len(dates),
            "valid_gateway_count": np.nan,
        })
        time_rows.append(row)

        for gateway in sorted(data["gateway"].unique()):
            train = data[data["gateway"] != gateway]
            test = data[data["gateway"] == gateway]
            if len(train) < 100 or len(test) < 20 or train["drop_event"].nunique() < 2:
                continue
            print(
                f"LOGO window={window} threshold={threshold:.2f} gateway={gateway}",
                flush=True,
            )
            row = fit_lr(train, test, features, threshold)
            row.update({
                "window": window,
                "split_type": "leave_one_gateway_out",
                "test_gateway": gateway,
                "total_samples": len(data),
                "overall_event_rate": data["drop_event"].mean(),
                "test_event_rate": test["drop_event"].mean(),
                "date_count": len(dates),
            })
            logo_rows.append(row)
    return time_rows, logo_rows


def main():
    parts, file_count, raw_rows, clean_rows = aggregate_all_windows()
    dataset_rows, time_rows, logo_rows = [], [], []
    for window in WINDOWS:
        print(f"\nBUILD window={window}", flush=True)
        windows, strict, duplicate_count = build_strict(parts[window], window)
        event_base = feature_engineering(strict)
        dataset_rows.append({
            "window": window,
            "daily_csv_files": file_count,
            "raw_packet_rows": raw_rows,
            "clean_packet_rows": clean_rows,
            "gateway_windows": len(windows),
            "strict_pairs": len(strict),
            "event_model_samples": len(event_base),
            "gateways": event_base["gateway"].nunique(),
            "dates": event_base["date"].nunique(),
            "duplicate_gateway_windows_removed": duplicate_count,
        })
        window_token = window.replace("min", "m")
        windows.to_csv(RESULT_DIR / f"window_level_{window_token}.csv", index=False)
        strict.to_csv(RESULT_DIR / f"strict_pairs_{window_token}.csv", index=False)
        duration_time, duration_logo = evaluate_duration(event_base, window)
        time_rows.extend(duration_time)
        logo_rows.extend(duration_logo)

    dataset_summary = pd.DataFrame(dataset_rows)
    time_results = pd.DataFrame(time_rows)
    logo_details = pd.DataFrame(logo_rows)
    binary_logo = logo_details[logo_details["valid_binary_test"] == 1]
    metric_columns = [
        "Accuracy", "BalancedAcc", "Precision", "Recall", "F1",
        "ROC_AUC", "PR_AUC", "PositiveRate", "PositiveCount",
        "test_samples", "test_event_rate",
    ]
    logo_summary = (
        binary_logo.groupby(["window", "threshold"])[metric_columns]
        .agg(["mean", "std", "count"])
    )
    logo_summary.columns = [f"{metric}_{stat}" for metric, stat in logo_summary.columns]
    logo_summary = logo_summary.reset_index()

    dataset_summary.to_csv(RESULT_DIR / "window_dataset_summary.csv", index=False)
    time_results.to_csv(RESULT_DIR / "window_time_results.csv", index=False)
    logo_details.to_csv(RESULT_DIR / "window_logo_detailed.csv", index=False)
    logo_summary.to_csv(RESULT_DIR / "window_logo_summary.csv", index=False)
    print("\nDATASET SUMMARY")
    print(dataset_summary.to_string(index=False))
    print("\nTIME RESULTS")
    print(time_results[[
        "window", "threshold", "total_samples", "overall_event_rate",
        "test_event_rate", "Precision", "Recall", "F1", "ROC_AUC", "PR_AUC",
    ]].to_string(index=False))
    print("\nLOGO SUMMARY")
    print(logo_summary[[
        "window", "threshold", "PR_AUC_mean", "PR_AUC_std", "PR_AUC_count",
        "ROC_AUC_mean", "Recall_mean",
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
