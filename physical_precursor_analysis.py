"""Descriptive analysis of gateway-observable precursors to CRC degradation.

This analysis identifies associations, not physical causes. Comparisons are
standardized within gateway to reduce confounding by gateway-specific levels.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

import probability_calibration_analysis as base

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results_physical_precursors"
OUTPUT.mkdir(exist_ok=True)

FEATURES = [
    "crc_success_rate", "prev_delta", "rssi_mean", "rolling_rssi_mean_3",
    "snr_mean", "rolling_snr_mean_3", "packet_count", "size_mean",
    "spreading_factor_mean", "frequency_nunique",
]


def robust_gateway_z(data, column):
    grouped = data.groupby("gateway")[column]
    median = grouped.transform("median")
    q75 = grouped.transform(lambda x: x.quantile(.75))
    q25 = grouped.transform(lambda x: x.quantile(.25))
    scale = (q75 - q25).replace(0, np.nan)
    return (data[column] - median) / scale


def cliffs_delta_from_u(u, n1, n0):
    return 2 * u / (n1 * n0) - 1


def main():
    data, _, _ = base.prepare_data()
    for feature in FEATURES:
        data[f"z_{feature}"] = robust_gateway_z(data, feature)

    rows = []
    gateway_rows = []
    for threshold in base.THRESHOLDS:
        data["event"] = ((data.crc_success_rate - data.next_crc_success_rate)
                         >= threshold - 1e-12).astype(int)
        for feature in FEATURES:
            z = f"z_{feature}"
            valid = data[["gateway", "event", feature, z]].dropna()
            event = valid[valid.event == 1]
            no_event = valid[valid.event == 0]
            u, p = mannwhitneyu(event[z], no_event[z], alternative="two-sided")
            rows.append({
                "threshold": threshold, "feature": feature,
                "event_n": len(event), "non_event_n": len(no_event),
                "event_raw_median": event[feature].median(),
                "non_event_raw_median": no_event[feature].median(),
                "event_gateway_standardized_median": event[z].median(),
                "non_event_gateway_standardized_median": no_event[z].median(),
                "cliffs_delta": cliffs_delta_from_u(u, len(event), len(no_event)),
                "mann_whitney_p": p,
            })
            for gateway, group in valid.groupby("gateway"):
                if group.event.nunique() < 2:
                    continue
                e = group[group.event == 1][z]
                n = group[group.event == 0][z]
                gu, gp = mannwhitneyu(e, n, alternative="two-sided")
                gateway_rows.append({
                    "threshold": threshold, "gateway": gateway,
                    "feature": feature, "event_n": len(e), "non_event_n": len(n),
                    "cliffs_delta": cliffs_delta_from_u(gu, len(e), len(n)),
                    "p_value": gp,
                })

    summary = pd.DataFrame(rows)
    by_gateway = pd.DataFrame(gateway_rows)
    summary.to_csv(OUTPUT / "physical_precursor_summary.csv", index=False)
    by_gateway.to_csv(OUTPUT / "physical_precursor_by_gateway.csv", index=False)

    labels = {
        "crc_success_rate": "Current CRC", "prev_delta": "Previous CRC change",
        "rssi_mean": "Current RSSI", "rolling_rssi_mean_3": "Lagged RSSI (3)",
        "snr_mean": "Current SNR", "rolling_snr_mean_3": "Lagged SNR (3)",
        "packet_count": "Packet count", "size_mean": "Packet size",
        "spreading_factor_mean": "Spreading factor",
        "frequency_nunique": "Frequency diversity",
    }
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharex=True,
                             constrained_layout=True)
    for ax, threshold in zip(axes, base.THRESHOLDS):
        sub = summary[summary.threshold == threshold].sort_values("cliffs_delta")
        colors = ["#d95f02" if value < 0 else "#1b9e77"
                  for value in sub.cliffs_delta]
        ax.barh([labels[x] for x in sub.feature], sub.cliffs_delta, color=colors)
        ax.axvline(0, color="black", linewidth=.8)
        ax.set_xlim(-.55, .55)
        ax.set_title(f"Drop threshold = {threshold:.2f}")
        ax.set_xlabel("Within-gateway Cliff's delta\n(event minus non-event)")
        ax.grid(axis="x", alpha=.25)
    fig.savefig(OUTPUT / "physical_precursor_effects.png", dpi=220)
    plt.close(fig)

    consistency = by_gateway.groupby(["threshold", "feature"], as_index=False).agg(
        gateways=("gateway", "nunique"),
        median_gateway_delta=("cliffs_delta", "median"),
        positive_gateway_fraction=("cliffs_delta", lambda x: np.mean(x > 0)),
    )
    consistency.to_csv(OUTPUT / "physical_precursor_gateway_consistency.csv",
                       index=False)
    print(summary[["threshold", "feature", "cliffs_delta",
                   "event_raw_median", "non_event_raw_median"]].to_string(index=False))


if __name__ == "__main__":
    main()
