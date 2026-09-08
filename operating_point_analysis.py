"""Leakage-controlled alarm-budget and fixed-recall analysis for LR."""

from pathlib import Path
import numpy as np
import pandas as pd

from crc_ablation_revision import candidate_columns, make_lr, prepare_event_data

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "results_reproduced" / "LoED_full_strict_forecasting.csv"
OUTPUT = ROOT / "results_operating_points"
OUTPUT.mkdir(exist_ok=True)
THRESHOLDS = (0.10, 0.20)
BUDGETS = (0.05, 0.10)
TARGET_RECALLS = (0.80,)


def label(data, threshold):
    return ((data.crc_success_rate - data.next_crc_success_rate)
            >= threshold - 1e-12).astype(int)


def budget_rows(y, score, threshold, split, gateway=""):
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    order = np.argsort(-score, kind="mergesort")
    rows = []
    for budget in BUDGETS:
        count = max(1, int(np.ceil(len(y) * budget)))
        selected = order[:count]
        caught = int(y[selected].sum())
        precision = caught / count
        recall = caught / y.sum()
        rows.append({"split": split, "threshold": threshold, "gateway": gateway,
                     "budget": budget, "n": len(y), "events": int(y.sum()),
                     "alerts": count, "precision": precision, "recall": recall,
                     "lift": recall / budget})
    return rows


def recall_rows(y, score, threshold, split, gateway=""):
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    order = np.argsort(-score, kind="mergesort")
    cumulative = np.cumsum(y[order])
    rows = []
    for target in TARGET_RECALLS:
        needed = int(np.searchsorted(cumulative, np.ceil(target * y.sum()), side="left") + 1)
        caught = int(cumulative[needed - 1])
        rate = needed / len(y)
        rows.append({"split": split, "threshold": threshold, "gateway": gateway,
                     "target_recall": target, "n": len(y), "events": int(y.sum()),
                     "alerts": needed, "alert_rate": rate,
                     "precision": caught / needed, "recall": caught / y.sum(),
                     "lift": (caught / needed) / (y.mean())})
    return rows


def main():
    data = prepare_event_data(INPUT)
    features = candidate_columns(data)
    budget = []
    recall = []
    for threshold in THRESHOLDS:
        frame = data.copy()
        frame["target"] = label(frame, threshold)
        dates = sorted(frame.date.unique())
        cut = int(0.70 * len(dates))
        train = frame[frame.date.isin(dates[:cut])]
        test = frame[frame.date.isin(dates[cut:])]
        model = make_lr(features).fit(train[features], train.target)
        score = model.predict_proba(test[features])[:, 1]
        budget.extend(budget_rows(test.target, score, threshold, "Time"))
        recall.extend(recall_rows(test.target, score, threshold, "Time"))

        for gateway in sorted(frame.gateway.unique()):
            train = frame[frame.gateway != gateway]
            test = frame[frame.gateway == gateway]
            if test.target.nunique() < 2:
                continue
            model = make_lr(features).fit(train[features], train.target)
            score = model.predict_proba(test[features])[:, 1]
            budget.extend(budget_rows(test.target, score, threshold, "LOGO", gateway))
            recall.extend(recall_rows(test.target, score, threshold, "LOGO", gateway))

    budget = pd.DataFrame(budget)
    recall = pd.DataFrame(recall)
    budget.to_csv(OUTPUT / "alarm_budget_detailed.csv", index=False)
    recall.to_csv(OUTPUT / "fixed_recall_detailed.csv", index=False)
    budget.groupby(["split", "threshold", "budget"], as_index=False).mean(
        numeric_only=True).to_csv(OUTPUT / "alarm_budget_summary.csv", index=False)
    recall.groupby(["split", "threshold", "target_recall"], as_index=False).mean(
        numeric_only=True).to_csv(OUTPUT / "fixed_recall_summary.csv", index=False)


if __name__ == "__main__":
    main()
