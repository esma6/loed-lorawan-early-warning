"""Create manuscript-ready per-gateway LOGO tables and figures."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "results_reproduced" / "gateway_split_detailed_results.csv"
OUTPUT = ROOT / "results_gateway_reporting"
OUTPUT.mkdir(exist_ok=True)

data = pd.read_csv(INPUT)
data = data[data.model.str.contains("LogisticRegression|RandomForest|XGBoost")].copy()
data["model"] = data.model.str.replace("_gateway", "", regex=False).replace({
    "LogisticRegression": "LR", "RandomForest": "RF"})
gateways = sorted(data.test_gateway.unique())
mapping = {g: f"G{i+1}" for i, g in enumerate(gateways)}
data["gateway_id"] = data.test_gateway.map(mapping)

mapping_table = pd.DataFrame({"gateway_id": mapping.values(),
                              "gateway": mapping.keys()})
mapping_table.to_csv(OUTPUT / "gateway_id_mapping.csv", index=False)

lr = data[data.model == "LR"].copy()
compact = lr[["gateway_id", "threshold", "test_positive_count",
              "test_negative_count", "test_positive_rate", "Recall",
              "ROC_AUC", "PR_AUC", "valid_binary_test"]].copy()
compact["test_n"] = compact.test_positive_count + compact.test_negative_count
compact = compact[["gateway_id", "threshold", "test_n", "test_positive_count",
                   "test_positive_rate", "Recall", "ROC_AUC", "PR_AUC",
                   "valid_binary_test"]]
compact.to_csv(OUTPUT / "per_gateway_lr_compact.csv", index=False)

valid = compact[compact.valid_binary_test == 1].copy()
with open(OUTPUT / "per_gateway_lr_table.tex", "w", encoding="utf-8") as f:
    f.write(valid.to_latex(index=False, float_format="%.3f",
                           columns=["gateway_id", "threshold", "test_n",
                                    "test_positive_count", "test_positive_rate",
                                    "Recall", "ROC_AUC", "PR_AUC"],
                           header=["Gateway", "$\\theta$", "$n$", "Events",
                                   "Prevalence", "Recall", "ROC-AUC", "PR-AUC"],
                           escape=False))

models = [m for m in ["LR", "RF", "XGBoost"] if m in data.model.unique()]
fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.7), constrained_layout=True)
for ax, threshold in zip(axes, [0.10, 0.20]):
    sub = data[(data.threshold == threshold) & (data.valid_binary_test == 1)]
    pivot = sub.pivot(index="gateway_id", columns="model", values="PR_AUC")
    pivot = pivot.reindex(columns=models)
    image = ax.imshow(pivot.to_numpy(), vmin=0, vmax=1, cmap="viridis",
                      aspect="auto")
    ax.set_xticks(range(len(models)), models)
    ax.set_yticks(range(len(pivot)), pivot.index)
    ax.set_title(f"Drop threshold = {threshold:.2f}")
    ax.set_xlabel("Model"); ax.set_ylabel("Held-out gateway")
    for i in range(len(pivot)):
        for j in range(len(models)):
            value = pivot.iloc[i, j]
            if pd.notna(value):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                        color="white" if value < .72 else "black", fontsize=8)
fig.colorbar(image, ax=axes, label="PR-AUC", shrink=.86)
fig.savefig(OUTPUT / "gateway_model_pr_auc_heatmap.png", dpi=220)
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
for ax, threshold in zip(axes, [0.10, 0.20]):
    sub = compact[compact.threshold == threshold].sort_values("gateway_id")
    colors = ["#4c78a8" if v else "#bdbdbd" for v in sub.valid_binary_test]
    ax.bar(sub.gateway_id, sub.test_positive_rate * 100, color=colors)
    ax.set_title(f"Drop threshold = {threshold:.2f}")
    ax.set_xlabel("Held-out gateway"); ax.set_ylabel("Event prevalence (%)")
    ax.grid(axis="y", alpha=.25)
fig.savefig(OUTPUT / "gateway_event_prevalence.png", dpi=220)
plt.close(fig)

print(valid.to_string(index=False))

