"""Confidence intervals and paired tests for the LoED JTIT revision.

Time-based uncertainty uses a date-cluster bootstrap so correlated windows from
the same collection date remain together. LOGO uncertainty and comparisons use
held-out gateways as the sampling/pairing unit. P-values are Holm-adjusted
within each metric, threshold, split, and comparison family.
"""

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from crc_ablation_revision import (
    build_feature_sets,
    candidate_columns,
    make_lr,
    prepare_event_data,
)


PROJECT_DIR = Path(__file__).resolve().parent
STRICT_CSV = PROJECT_DIR / "results_reproduced" / "LoED_full_strict_forecasting.csv"
ORIGINAL_RESULTS = PROJECT_DIR / "results_reproduced"
ABLATION_RESULTS = PROJECT_DIR / "results_crc_ablation"
RESULT_DIR = PROJECT_DIR / "results_statistical_validation"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLDS = (0.10, 0.20)
METRICS = ("PR_AUC", "ROC_AUC")
N_TIME_BOOTSTRAP = 2000
N_LOGO_BOOTSTRAP = 10000
N_TIME_PERMUTATIONS = 1999
SEED = 42


def preprocess(features, scale):
    categorical = [c for c in features if c == "gateway"]
    numeric = [c for c in features if c not in categorical]
    transformers = []
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        numeric_steps.append(("scaler", StandardScaler()))
    if numeric:
        transformers.append(("num", Pipeline(numeric_steps), numeric))
    if categorical:
        transformers.append((
            "cat",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]),
            categorical,
        ))
    return ColumnTransformer(transformers)


def model_set(features, y_train):
    negatives = int((y_train == 0).sum())
    positives = int((y_train == 1).sum())
    scale_pos_weight = negatives / positives
    return {
        "LR": make_lr(features),
        "RF": Pipeline([
            ("preprocess", preprocess(features, scale=False)),
            ("model", RandomForestClassifier(
                n_estimators=300,
                max_depth=8,
                min_samples_leaf=8,
                class_weight="balanced",
                random_state=SEED,
                n_jobs=-1,
            )),
        ]),
        "XGBoost": Pipeline([
            ("preprocess", preprocess(features, scale=False)),
            ("model", XGBClassifier(
                n_estimators=300,
                max_depth=3,
                learning_rate=0.03,
                subsample=0.9,
                colsample_bytree=0.9,
                scale_pos_weight=scale_pos_weight,
                eval_metric="logloss",
                random_state=SEED,
                n_jobs=-1,
            )),
        ]),
    }


def metric_value(y, score, metric):
    if len(np.unique(y)) < 2:
        return np.nan
    if metric == "PR_AUC":
        return average_precision_score(y, score)
    return roc_auc_score(y, score)


def date_cluster_bootstrap(predictions, metric, rng):
    dates = predictions["date"].drop_duplicates().to_numpy()
    groups = {
        date: predictions.index[predictions["date"] == date].to_numpy()
        for date in dates
    }
    estimates = {model: [] for model in ("LR", "RF", "XGBoost")}
    differences = {"LR-RF": [], "LR-XGBoost": []}
    for _ in range(N_TIME_BOOTSTRAP):
        sampled_dates = rng.choice(dates, size=len(dates), replace=True)
        indices = np.concatenate([groups[date] for date in sampled_dates])
        y = predictions.loc[indices, "y_true"].to_numpy()
        values = {}
        for model in estimates:
            value = metric_value(y, predictions.loc[indices, model].to_numpy(), metric)
            estimates[model].append(value)
            values[model] = value
        differences["LR-RF"].append(values["LR"] - values["RF"])
        differences["LR-XGBoost"].append(values["LR"] - values["XGBoost"])
    return estimates, differences


def interval(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return tuple(np.quantile(values, [0.025, 0.975]))


def paired_date_cluster_permutation_pvalue(
    predictions, left, right, metric, rng, n_permutations=N_TIME_PERMUTATIONS
):
    """Two-sided paired randomization test with collection date as the swap unit.

    Under the null hypothesis that the two fitted models are exchangeable, all
    scores belonging to a collection date are swapped as one block.  The global
    PR-AUC or ROC-AUC is recomputed after every randomization.  This preserves
    within-date dependence without treating bootstrap confidence limits as a
    null-hypothesis test.
    """
    y = predictions["y_true"].to_numpy()
    left_score = predictions[left].to_numpy()
    right_score = predictions[right].to_numpy()
    date_codes, unique_dates = pd.factorize(predictions["date"], sort=False)
    observed = abs(
        metric_value(y, left_score, metric) - metric_value(y, right_score, metric)
    )
    exceedances = 0
    for _ in range(n_permutations):
        swap_by_date = rng.integers(0, 2, len(unique_dates), dtype=np.int8).astype(bool)
        swap = swap_by_date[date_codes]
        perm_left = np.where(swap, right_score, left_score)
        perm_right = np.where(swap, left_score, right_score)
        permuted = abs(
            metric_value(y, perm_left, metric) - metric_value(y, perm_right, metric)
        )
        exceedances += permuted >= observed - 1e-15
    return (exceedances + 1) / (n_permutations + 1)


def exact_sign_flip_pvalue(differences):
    differences = np.asarray(differences, dtype=float)
    differences = differences[np.isfinite(differences)]
    differences = differences[differences != 0]
    if len(differences) == 0:
        return 1.0
    observed = abs(differences.mean())
    permuted = []
    for signs in product((-1.0, 1.0), repeat=len(differences)):
        permuted.append(abs(np.mean(differences * np.asarray(signs))))
    return float(np.mean(np.asarray(permuted) >= observed - 1e-15))


def gateway_bootstrap(values, rng):
    values = np.asarray(values, dtype=float)
    samples = rng.choice(values, size=(N_LOGO_BOOTSTRAP, len(values)), replace=True)
    return samples.mean(axis=1)


def holm_adjust(frame, group_columns):
    frame = frame.copy()
    frame["p_holm"] = np.nan
    for _, indexes in frame.groupby(group_columns, dropna=False).groups.items():
        indexes = list(indexes)
        ordered = sorted(indexes, key=lambda i: frame.loc[i, "p_raw"])
        running = 0.0
        m = len(ordered)
        for rank, index in enumerate(ordered):
            adjusted = min(1.0, (m - rank) * frame.loc[index, "p_raw"])
            running = max(running, adjusted)
            frame.loc[index, "p_holm"] = running
    return frame


def run_time_validation(base, features):
    rng = np.random.default_rng(SEED)
    prediction_frames = []
    ci_rows = []
    comparison_rows = []
    for threshold in THRESHOLDS:
        data = base.copy()
        data["drop_event"] = (
            data["crc_success_rate"] - data["next_crc_success_rate"] >= threshold - 1e-12
        ).astype(int)
        dates = sorted(data["date"].unique())
        split = int(len(dates) * 0.70)
        train = data[data["date"].isin(dates[:split])]
        test = data[data["date"].isin(dates[split:])].copy()
        predictions = test[["date", "gateway"]].reset_index(drop=True)
        predictions["y_true"] = test["drop_event"].to_numpy()
        for name, model in model_set(features, train["drop_event"]).items():
            print(f"TIME FIT threshold={threshold:.2f} model={name}", flush=True)
            model.fit(train[features], train["drop_event"])
            predictions[name] = model.predict_proba(test[features])[:, 1]
        predictions["threshold"] = threshold
        prediction_frames.append(predictions)

        for metric in METRICS:
            estimates, differences = date_cluster_bootstrap(predictions, metric, rng)
            for model, boot in estimates.items():
                low, high = interval(boot)
                ci_rows.append({
                    "split_type": "time_based",
                    "threshold": threshold,
                    "metric": metric,
                    "model": model,
                    "estimate": metric_value(
                        predictions["y_true"].to_numpy(), predictions[model].to_numpy(), metric
                    ),
                    "ci_low": low,
                    "ci_high": high,
                    "resampling_unit": "collection_date",
                    "clusters": predictions["date"].nunique(),
                    "bootstrap_replicates": N_TIME_BOOTSTRAP,
                })
            for comparison, boot_diff in differences.items():
                low, high = interval(boot_diff)
                left, right = comparison.split("-")
                comparison_rows.append({
                    "split_type": "time_based",
                    "family": "model_comparison",
                    "threshold": threshold,
                    "metric": metric,
                    "comparison": comparison,
                    "difference": metric_value(
                        predictions["y_true"], predictions[left], metric
                    ) - metric_value(predictions["y_true"], predictions[right], metric),
                    "ci_low": low,
                    "ci_high": high,
                    "p_raw": paired_date_cluster_permutation_pvalue(
                        predictions, left, right, metric, rng
                    ),
                    "test": "paired date-cluster score-swap permutation",
                    "pairs": predictions["date"].nunique(),
                })
    return pd.concat(prediction_frames, ignore_index=True), pd.DataFrame(ci_rows), pd.DataFrame(comparison_rows)


def logo_intervals_and_tests(rng):
    original = pd.read_csv(ORIGINAL_RESULTS / "gateway_split_detailed_results.csv")
    original = original[original["valid_binary_test"] == 1].copy()
    name_map = {
        "LogisticRegression_gateway": "LR",
        "RandomForest_gateway": "RF",
        "XGBoost_gateway": "XGBoost",
    }
    original = original[original["model"].isin(name_map)].copy()
    original["model"] = original["model"].map(name_map)

    ci_rows = []
    comparison_rows = []
    for (threshold, metric, model), group in original.melt(
        id_vars=["threshold", "test_gateway", "model"],
        value_vars=list(METRICS), var_name="metric", value_name="value",
    ).groupby(["threshold", "metric", "model"]):
        boot = gateway_bootstrap(group["value"].dropna(), rng)
        low, high = interval(boot)
        ci_rows.append({
            "split_type": "leave_one_gateway_out",
            "threshold": threshold,
            "metric": metric,
            "model": model,
            "estimate": group["value"].mean(),
            "ci_low": low,
            "ci_high": high,
            "resampling_unit": "held_out_gateway",
            "clusters": group["value"].notna().sum(),
            "bootstrap_replicates": N_LOGO_BOOTSTRAP,
        })

    for threshold in THRESHOLDS:
        for metric in METRICS:
            wide = original[original["threshold"] == threshold].pivot(
                index="test_gateway", columns="model", values=metric
            ).dropna()
            for left, right in (("LR", "RF"), ("LR", "XGBoost")):
                diff = wide[left] - wide[right]
                boot = gateway_bootstrap(diff.to_numpy(), rng)
                low, high = interval(boot)
                comparison_rows.append({
                    "split_type": "leave_one_gateway_out",
                    "family": "model_comparison",
                    "threshold": threshold,
                    "metric": metric,
                    "comparison": f"{left}-{right}",
                    "difference": diff.mean(),
                    "ci_low": low,
                    "ci_high": high,
                    "p_raw": exact_sign_flip_pvalue(diff),
                    "test": "exact paired gateway sign-flip",
                    "pairs": len(diff),
                })
    return pd.DataFrame(ci_rows), pd.DataFrame(comparison_rows)


def ablation_logo_tests(rng):
    data = pd.read_csv(ABLATION_RESULTS / "crc_ablation_logo_detailed.csv")
    data = data[data["valid_binary_test"] == 1]
    comparisons = (
        "without_current_crc",
        "without_current_rolling_crc",
        "without_all_crc",
        "current_crc_only",
        "current_radio_only",
        "delayed_radio_only",
    )
    rows = []
    for threshold in THRESHOLDS:
        for metric in METRICS:
            subset = data[data["threshold"] == threshold]
            wide = subset.pivot(index="test_gateway", columns="feature_setting", values=metric)
            for variant in comparisons:
                paired = wide[["full_features", variant]].dropna()
                diff = paired["full_features"] - paired[variant]
                boot = gateway_bootstrap(diff.to_numpy(), rng)
                low, high = interval(boot)
                rows.append({
                    "split_type": "leave_one_gateway_out",
                    "family": "crc_ablation",
                    "threshold": threshold,
                    "metric": metric,
                    "comparison": f"full_features-{variant}",
                    "difference": diff.mean(),
                    "ci_low": low,
                    "ci_high": high,
                    "p_raw": exact_sign_flip_pvalue(diff),
                    "test": "exact paired gateway sign-flip",
                    "pairs": len(diff),
                })
    return pd.DataFrame(rows)


def main():
    rng = np.random.default_rng(SEED)
    base = prepare_event_data(STRICT_CSV)
    features = candidate_columns(base)
    predictions, time_ci, time_tests = run_time_validation(base, features)
    logo_ci, logo_tests = logo_intervals_and_tests(rng)
    ablation_tests = ablation_logo_tests(rng)

    all_ci = pd.concat([time_ci, logo_ci], ignore_index=True)
    all_tests = pd.concat([time_tests, logo_tests, ablation_tests], ignore_index=True)
    all_tests = holm_adjust(
        all_tests,
        ["split_type", "family", "threshold", "metric"],
    )
    all_tests["significant_holm_0_05"] = all_tests["p_holm"] < 0.05

    predictions.to_csv(RESULT_DIR / "time_model_predictions.csv", index=False)
    all_ci.to_csv(RESULT_DIR / "model_metric_confidence_intervals.csv", index=False)
    all_tests.to_csv(RESULT_DIR / "paired_statistical_tests.csv", index=False)
    print("\nCONFIDENCE INTERVALS")
    print(all_ci.to_string(index=False))
    print("\nPAIRED TESTS")
    print(all_tests.to_string(index=False))
    print(f"\nSaved to: {RESULT_DIR}")


if __name__ == "__main__":
    main()
