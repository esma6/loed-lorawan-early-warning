"""Compare submitted LR with explicit six-window sequence LR and GRU models."""

from pathlib import Path
import random
import warnings

warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

import probability_calibration_analysis as base

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results_temporal_models"
OUTPUT.mkdir(exist_ok=True)
SEED = 42
SEQ_LEN = 6
EPOCHS = 12
CORE = ["crc_success_rate", "rssi_mean", "snr_mean", "packet_count",
        "size_mean", "spreading_factor_mean", "frequency_nunique", "prev_delta"]


class GRUClassifier(nn.Module):
    def __init__(self, features):
        super().__init__()
        self.gru = nn.GRU(features, 16, batch_first=True)
        self.output = nn.Linear(16, 1)

    def forward(self, x):
        _, hidden = self.gru(x)
        return self.output(hidden[-1]).squeeze(1)


def seed_all():
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    torch.set_num_threads(max(1, min(4, torch.get_num_threads())))


def make_sequences(data):
    data = data.sort_values(["gateway", "window_start"]).copy()
    pieces = []
    for gateway, group in data.groupby("gateway", sort=False):
        group = group.sort_values("window_start").copy()
        valid = pd.Series(True, index=group.index)
        for lag in range(1, SEQ_LEN):
            expected = group.window_start - pd.Timedelta(minutes=5 * lag)
            valid &= group.window_start.shift(lag).eq(expected)
            for feature in CORE:
                group[f"{feature}_lag{lag}"] = group[feature].shift(lag)
        pieces.append(group[valid])
    result = pd.concat(pieces).sort_values(["window_start", "gateway"]).copy()
    flat_cols = []
    for lag in reversed(range(SEQ_LEN)):
        flat_cols.extend([f"{f}_lag{lag}" if lag else f for f in CORE])
    return result, flat_cols


def metrics(y, p):
    return {"n": len(y), "events": int(np.sum(y)),
            "prevalence": float(np.mean(y)),
            "ROC_AUC": roc_auc_score(y, p),
            "PR_AUC": average_precision_score(y, p)}


def fit_sequence_lr(train, test, columns):
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x_train = scaler.fit_transform(imputer.fit_transform(train[columns]))
    x_test = scaler.transform(imputer.transform(test[columns]))
    model = LogisticRegression(max_iter=5000, solver="liblinear",
                               class_weight="balanced", random_state=SEED)
    model.fit(x_train, train.target)
    return model.predict_proba(x_test)[:, 1]


def fit_gru(train, test, columns):
    fit_dates = sorted(train.date.unique())
    val_cut = max(1, int(len(fit_dates) * .85))
    train_mask = train.date.isin(set(fit_dates[:val_cut])).to_numpy()
    val_mask = ~train_mask
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x_fit = scaler.fit_transform(imputer.fit_transform(train.loc[train_mask, columns]))
    x_val = scaler.transform(imputer.transform(train.loc[val_mask, columns]))
    x_test = scaler.transform(imputer.transform(test[columns]))
    x_fit = x_fit.reshape(-1, SEQ_LEN, len(CORE))
    x_val = x_val.reshape(-1, SEQ_LEN, len(CORE))
    x_test = x_test.reshape(-1, SEQ_LEN, len(CORE))
    y_fit = train.loc[train_mask, "target"].to_numpy(dtype=np.float32)
    y_val = train.loc[val_mask, "target"].to_numpy(dtype=np.float32)
    device = torch.device("cpu")
    model = GRUClassifier(len(CORE)).to(device)
    positives = max(float(y_fit.sum()), 1.0)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(
        [(len(y_fit) - positives) / positives], dtype=torch.float32))
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loader = DataLoader(TensorDataset(torch.tensor(x_fit, dtype=torch.float32),
                                      torch.tensor(y_fit)), batch_size=1024,
                        shuffle=True, generator=torch.Generator().manual_seed(SEED))
    best_state, best_loss, stale = None, np.inf, 0
    xv = torch.tensor(x_val, dtype=torch.float32)
    yv = torch.tensor(y_val, dtype=torch.float32)
    for _ in range(EPOCHS):
        model.train()
        for xb, yb in loader:
            optimizer.zero_grad(); loss = loss_fn(model(xb), yb)
            loss.backward(); optimizer.step()
        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(xv), yv))
        if val_loss < best_loss - 1e-4:
            best_loss = val_loss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
            if stale >= 3:
                break
    model.load_state_dict(best_state)
    model.eval()
    probabilities = []
    with torch.no_grad():
        for start in range(0, len(x_test), 4096):
            logits = model(torch.tensor(x_test[start:start+4096], dtype=torch.float32))
            probabilities.append(torch.sigmoid(logits).numpy())
    return np.concatenate(probabilities)


def submitted_lr(train, test, features, numeric):
    model = base.models(numeric, train.target.to_numpy())["LogisticRegression"]
    model.fit(train[features], train.target)
    return model.predict_proba(test[features])[:, 1]


def main():
    seed_all()
    raw, submitted_features, numeric = base.prepare_data()
    data, sequence_columns = make_sequences(raw)
    dates = sorted(data.date.unique())
    cutoff = int(len(dates) * .70)
    train_dates, test_dates = set(dates[:cutoff]), set(dates[cutoff:])
    rows = []
    for threshold in base.THRESHOLDS:
        data["target"] = ((data.crc_success_rate - data.next_crc_success_rate)
                          >= threshold - 1e-12).astype(int)
        train = data[data.date.isin(train_dates)]
        test = data[data.date.isin(test_dates)]
        for name, function, columns in [
            ("Submitted LR", lambda a,b: submitted_lr(a,b,submitted_features,numeric), None),
            ("Sequence LR", lambda a,b: fit_sequence_lr(a,b,sequence_columns), None),
            ("GRU", lambda a,b: fit_gru(a,b,sequence_columns), None),
        ]:
            print(f"TIME threshold={threshold:.2f} model={name}", flush=True)
            p = function(train, test)
            row = {"split_type": "Time", "threshold": threshold, "model": name}
            row.update(metrics(test.target.to_numpy(), p)); rows.append(row)
        for gateway in sorted(data.gateway.unique()):
            train = data[data.gateway != gateway]
            test = data[data.gateway == gateway]
            if test.target.nunique() < 2:
                continue
            for name, function in [
                ("Submitted LR", lambda a,b: submitted_lr(a,b,submitted_features,numeric)),
                ("Sequence LR", lambda a,b: fit_sequence_lr(a,b,sequence_columns)),
                ("GRU", lambda a,b: fit_gru(a,b,sequence_columns)),
            ]:
                print(f"LOGO threshold={threshold:.2f} gateway={gateway} model={name}",
                      flush=True)
                p = function(train, test)
                row = {"split_type": "LOGO", "threshold": threshold,
                       "model": name, "test_gateway": gateway}
                row.update(metrics(test.target.to_numpy(), p)); rows.append(row)
    detailed = pd.DataFrame(rows)
    detailed.to_csv(OUTPUT / "temporal_model_detailed.csv", index=False)
    logo = detailed[detailed.split_type == "LOGO"]
    summary = logo.groupby(["threshold", "model"], as_index=False).agg(
        valid_gateways=("test_gateway", "nunique"), ROC_AUC_mean=("ROC_AUC", "mean"),
        ROC_AUC_sd=("ROC_AUC", "std"), PR_AUC_mean=("PR_AUC", "mean"),
        PR_AUC_sd=("PR_AUC", "std"))
    summary.to_csv(OUTPUT / "temporal_model_logo_summary.csv", index=False)
    time = detailed[detailed.split_type == "Time"]
    time.to_csv(OUTPUT / "temporal_model_time_summary.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), constrained_layout=True)
    for ax, threshold in zip(axes, base.THRESHOLDS):
        t = time[time.threshold == threshold].set_index("model")["PR_AUC"]
        l = summary[summary.threshold == threshold].set_index("model")["PR_AUC_mean"]
        order = ["Submitted LR", "Sequence LR", "GRU"]
        x = np.arange(len(order)); width = .36
        ax.bar(x-width/2, t.reindex(order), width, label="Time")
        ax.bar(x+width/2, l.reindex(order), width, label="LOGO mean")
        ax.set_xticks(x, order, rotation=15); ax.set_ylim(0, .7)
        ax.set_ylabel("PR-AUC"); ax.set_title(f"Drop threshold = {threshold:.2f}")
        ax.grid(axis="y", alpha=.25); ax.legend()
    fig.savefig(OUTPUT / "temporal_model_comparison.png", dpi=220)
    plt.close(fig)
    print("\nTIME\n", time.to_string(index=False))
    print("\nLOGO\n", summary.to_string(index=False))


if __name__ == "__main__":
    main()
