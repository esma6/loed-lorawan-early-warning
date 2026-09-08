# ============================================================
# LoED FULL DATASET
# Edge-Level Early Warning of Link Degradation in LoRaWAN IoT
# Sıfırdan tam çalışan kod
# ============================================================

import os
import shutil
import zipfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


# ============================================================
# 1. AYARLAR
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
ZIP_PATH = DATA_DIR / "LoED_LoRaWAN_at_edge_dataset.zip"

# All generated artifacts stay inside this revision project regardless of the
# shell's current working directory. To avoid duplicating the 398 MB archive
# on a nearly full disk, reuse the existing extracted dataset read-only when
# the project-local extraction has not yet been created.
LOCAL_EXTRACT_DIR = DATA_DIR / "LoED_full_extracted"
EXISTING_EXTRACT_DIR = Path(r"C:\Users\ETU\Downloads\LoED_full_extracted")
EXTRACT_DIR = (
    LOCAL_EXTRACT_DIR
    if LOCAL_EXTRACT_DIR.exists() or not EXISTING_EXTRACT_DIR.exists()
    else EXISTING_EXTRACT_DIR
)
RESULT_DIR = PROJECT_DIR / "results_reproduced"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

WINDOW = "5min"
MIN_PACKETS_PER_WINDOW = 10

DROP_THRESHOLDS = [0.10, 0.20]

RANDOM_STATE = 42
# Preserve an existing extraction on reruns. Set this to True manually only
# when the project-local extracted copy is known to be disposable.
RESET_EXTRACT = False


# ============================================================
# 2. XGBOOST VAR MI KONTROL ET
# ============================================================

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
    print("XGBoost bulundu. XGBoost modeli çalıştırılacak.")
except Exception:
    HAS_XGB = False
    print("XGBoost bulunamadı. XGBoost modeli atlanacak.")


# ============================================================
# 3. FULL ZIP DOSYASINI AÇ
# ============================================================

if RESET_EXTRACT and EXTRACT_DIR.exists():
    shutil.rmtree(EXTRACT_DIR)

if not EXTRACT_DIR.exists():
    print("\nDataset açılıyor...")
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(EXTRACT_DIR)

csv_files = sorted([
    p for p in EXTRACT_DIR.rglob("*.csv")
    if "__MACOSX" not in str(p)
])

print("\nCSV file count:", len(csv_files))

print("\nFirst files:")
for f in csv_files[:10]:
    print(" -", f)

print("\nLast files:")
for f in csv_files[-10:]:
    print(" -", f)

if len(csv_files) <= 6:
    raise RuntimeError(
        "CSV sayısı 6 veya daha az çıktı. Büyük ihtimalle SAMPLE dosyası kullanılıyor."
    )


# ============================================================
# 4. CRC STATUS DÖNÜŞÜMÜ
# ============================================================

def map_crc_to_binary_series(s):
    """
    LoED için:
    1  -> geçerli paket
    -1 -> hatalı/geçersiz paket

    Bazı dosyalarda veri string gibi okunursa diye numeric dönüşüm yapılır.
    """

    s_num = pd.to_numeric(s, errors="coerce")

    out = pd.Series(np.nan, index=s.index)
    out[s_num == 1] = 1
    out[s_num == -1] = 0
    out[s_num == 0] = 0

    return out


# ============================================================
# 5. GÜNLÜK CSV DOSYALARINI OKU VE WINDOW-LEVEL VERİ OLUŞTUR
# ============================================================

needed_cols = [
    "time",
    "gateway",
    "crc_status",
    "frequency",
    "spreading_factor",
    "rssi",
    "snr",
    "size",
]

window_parts = []

raw_total_rows = 0
clean_total_rows = 0
skipped_files = []

for i, file_path in enumerate(csv_files, start=1):

    if i == 1 or i % 20 == 0 or i == len(csv_files):
        print(f"\nProcessing file {i}/{len(csv_files)}: {file_path.name}")

    try:
        temp = pd.read_csv(file_path, low_memory=False)
    except Exception as e:
        print(f"Dosya okunamadı: {file_path.name} | Hata: {e}")
        skipped_files.append(file_path.name)
        continue

    raw_total_rows += len(temp)

    temp.columns = [str(c).strip().lower() for c in temp.columns]

    missing_cols = [c for c in needed_cols if c not in temp.columns]

    if missing_cols:
        print(f"Atlandı: {file_path.name}, eksik kolonlar: {missing_cols}")
        skipped_files.append(file_path.name)
        continue

    temp = temp[needed_cols].copy()

    temp["time"] = pd.to_datetime(temp["time"], errors="coerce", utc=True)
    temp["gateway"] = temp["gateway"].astype(str)

    temp["crc_ok"] = map_crc_to_binary_series(temp["crc_status"])

    for c in ["frequency", "spreading_factor", "rssi", "snr", "size"]:
        temp[c] = pd.to_numeric(temp[c], errors="coerce")

    temp = temp.dropna(subset=["time", "gateway", "crc_ok", "rssi", "snr"])
    temp["crc_ok"] = temp["crc_ok"].astype(int)

    # Fiziksel olarak makul olmayan RSSI/SNR değerlerini temizle
    temp = temp[(temp["rssi"] >= -160) & (temp["rssi"] <= -20)]
    temp = temp[(temp["snr"] >= -40) & (temp["snr"] <= 30)]

    # LoRa SF aralığı dışında kalanları NaN yap
    temp.loc[
        ~temp["spreading_factor"].between(6, 12),
        "spreading_factor"
    ] = np.nan

    clean_total_rows += len(temp)

    if len(temp) == 0:
        continue

    temp["window_start"] = temp["time"].dt.floor(WINDOW)

    group_cols = ["gateway", "window_start"]

    agg = temp.groupby(group_cols).agg(
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

    # SF oranları
    sf_counts = (
        temp.dropna(subset=["spreading_factor"])
            .groupby(group_cols + ["spreading_factor"])
            .size()
            .unstack(fill_value=0)
    )

    if len(sf_counts) > 0:
        sf_ratio = sf_counts.div(sf_counts.sum(axis=1), axis=0)
        sf_ratio.columns = [f"sf_{int(c)}_ratio" for c in sf_ratio.columns]
        sf_ratio = sf_ratio.reset_index()

        agg = agg.merge(sf_ratio, on=group_cols, how="left")

    window_parts.append(agg)


print("\n============================================================")
print("RAW AND CLEANING SUMMARY")
print("============================================================")
print("Raw total rows   :", raw_total_rows)
print("Clean total rows :", clean_total_rows)
print("Skipped files    :", len(skipped_files))

if skipped_files:
    print("Skipped file names:")
    for f in skipped_files:
        print(" -", f)

if len(window_parts) == 0:
    raise RuntimeError("Hiç window-level veri oluşmadı. Kolon adlarını ve dosya yolunu kontrol et.")


# ============================================================
# 6. WINDOW-LEVEL VERİYİ BİRLEŞTİR
# ============================================================

win = pd.concat(window_parts, ignore_index=True)

# Tüm SF oran kolonlarını garantiye al
for sf in range(6, 13):
    col = f"sf_{sf}_ratio"
    if col not in win.columns:
        win[col] = 0.0

for c in win.columns:
    if c.startswith("sf_") and c.endswith("_ratio"):
        win[c] = win[c].fillna(0.0)

# Tek paketli veya çok seyrek pencereleri çıkar
win = win[win["packet_count"] >= MIN_PACKETS_PER_WINDOW].copy()

# Olası duplicate gateway-window kayıtlarını kontrol et
duplicate_count = win.duplicated(subset=["gateway", "window_start"]).sum()
print("\nDuplicate gateway-window rows:", duplicate_count)

if duplicate_count > 0:
    print("Duplicate kayıtlar bulundu. İlk kayıt korunarak siliniyor.")
    win = win.drop_duplicates(subset=["gateway", "window_start"], keep="first")

win["hour"] = win["window_start"].dt.hour
win["dayofweek"] = win["window_start"].dt.dayofweek
win["date"] = win["window_start"].dt.date

win = win.sort_values(["gateway", "window_start"]).reset_index(drop=True)

print("\n============================================================")
print("WINDOW-LEVEL DATA SUMMARY")
print("============================================================")
print("WIN SHAPE       :", win.shape)
print("Gateway count   :", win["gateway"].nunique())
print("Date count      :", win["date"].nunique())
print("Date range      :", min(win["date"]), "to", max(win["date"]))
print("Packet count summary:")
print(win["packet_count"].describe())

win.to_csv(RESULT_DIR / "LoED_full_window_level.csv", index=False)


# ============================================================
# 7. STRICT NEXT-WINDOW TARGET OLUŞTUR
# ============================================================

window_minutes = pd.Timedelta(WINDOW).total_seconds() / 60

strict = win.sort_values(["gateway", "window_start"]).copy()

strict["next_window_start"] = strict.groupby("gateway")["window_start"].shift(-1)
strict["next_crc_success_rate"] = strict.groupby("gateway")["crc_success_rate"].shift(-1)
strict["next_packet_count"] = strict.groupby("gateway")["packet_count"].shift(-1)

strict["gap_minutes"] = (
    strict["next_window_start"] - strict["window_start"]
).dt.total_seconds() / 60

strict = strict[
    (strict["gap_minutes"] == window_minutes) &
    strict["next_crc_success_rate"].notna()
].copy()

strict["poor_next"] = (strict["next_crc_success_rate"] < 0.50).astype(int)

print("\n============================================================")
print("STRICT NEXT-WINDOW DATA SUMMARY")
print("============================================================")
print("STRICT SHAPE        :", strict.shape)
print("STRICT DATE COUNT   :", strict["date"].nunique())
print("STRICT GATEWAY COUNT:", strict["gateway"].nunique())

print("\nNext CRC success rate summary:")
print(strict["next_crc_success_rate"].describe())

print("\nGap check:")
print(strict["gap_minutes"].value_counts().head())

print("\nFirst dates:")
print(sorted(strict["date"].unique())[:10])

print("\nLast dates:")
print(sorted(strict["date"].unique())[-10:])

strict.to_csv(RESULT_DIR / "LoED_full_strict_forecasting.csv", index=False)


# ============================================================
# 8. EVENT FEATURE ENGINEERING
# ============================================================

base_event = strict.copy()
base_event = base_event.sort_values(["gateway", "window_start"])

# Sadece geçmişe dayalı özellikler
base_event["prev_crc_success_rate"] = (
    base_event.groupby("gateway")["crc_success_rate"].shift(1)
)

base_event["prev_delta"] = (
    base_event["crc_success_rate"] - base_event["prev_crc_success_rate"]
)

base_event["rolling_crc_mean_3"] = (
    base_event.groupby("gateway")["crc_success_rate"]
    .transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
)

base_event["rolling_crc_std_3"] = (
    base_event.groupby("gateway")["crc_success_rate"]
    .transform(lambda s: s.shift(1).rolling(3, min_periods=2).std())
)

base_event["rolling_crc_mean_6"] = (
    base_event.groupby("gateway")["crc_success_rate"]
    .transform(lambda s: s.shift(1).rolling(6, min_periods=1).mean())
)

base_event["rolling_crc_std_6"] = (
    base_event.groupby("gateway")["crc_success_rate"]
    .transform(lambda s: s.shift(1).rolling(6, min_periods=2).std())
)

base_event["rolling_rssi_mean_3"] = (
    base_event.groupby("gateway")["rssi_mean"]
    .transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
)

base_event["rolling_snr_mean_3"] = (
    base_event.groupby("gateway")["snr_mean"]
    .transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
)

base_event = base_event.dropna(
    subset=["prev_crc_success_rate", "prev_delta"]
).copy()

print("\n============================================================")
print("BASE EVENT DATA SUMMARY")
print("============================================================")
print("BASE EVENT SHAPE        :", base_event.shape)
print("BASE EVENT DATE COUNT   :", base_event["date"].nunique())
print("BASE EVENT GATEWAY COUNT:", base_event["gateway"].nunique())


# ============================================================
# 9. FEATURE SET
# ============================================================

leakage_cols = [
    "next_crc_success_rate",
    "next_packet_count",
    "next_window_start",
    "gap_minutes",
    "poor_next",
    "drop_event",
]

non_feature_cols = [
    "window_start",
    "date",
]

candidate_features = [
    c for c in base_event.columns
    if c not in leakage_cols + non_feature_cols
]

categorical_features = ["gateway"]
numeric_features = [c for c in candidate_features if c not in categorical_features]

print("\n============================================================")
print("FEATURE SUMMARY")
print("============================================================")
print("Feature count        :", len(candidate_features))
print("Numeric feature count:", len(numeric_features))
print("Categorical features :", categorical_features)


# ============================================================
# 10. PREPROCESSING VE MODEL TANIMLARI
# ============================================================

def build_preprocess(scale_numeric=False):
    if scale_numeric:
        numeric_transformer = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
    else:
        numeric_transformer = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocess = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    return preprocess


def make_models(y_train):
    models = {}

    models["LogisticRegression"] = Pipeline(steps=[
        ("preprocess", build_preprocess(scale_numeric=True)),
        ("model", LogisticRegression(
            max_iter=5000,
            solver="liblinear",
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )),
    ])

    models["RandomForest"] = Pipeline(steps=[
        ("preprocess", build_preprocess(scale_numeric=False)),
        ("model", RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_leaf=8,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )),
    ])

    if HAS_XGB:
        pos_count = int(np.sum(y_train == 1))
        neg_count = int(np.sum(y_train == 0))
        scale_pos_weight = neg_count / max(pos_count, 1)

        models["XGBoost"] = Pipeline(steps=[
            ("preprocess", build_preprocess(scale_numeric=False)),
            ("model", XGBClassifier(
                n_estimators=300,
                max_depth=3,
                learning_rate=0.03,
                subsample=0.9,
                colsample_bytree=0.9,
                scale_pos_weight=scale_pos_weight,
                eval_metric="logloss",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )),
        ])

    return models


# ============================================================
# 11. METRİK FONKSİYONLARI
# ============================================================

def safe_auc(y_true, y_score, metric="roc"):
    if len(np.unique(y_true)) < 2:
        return np.nan

    if metric == "roc":
        return roc_auc_score(y_true, y_score)

    if metric == "pr":
        return average_precision_score(y_true, y_score)

    return np.nan


def event_metrics(y_true, y_pred, y_score, name, threshold):
    return {
        "threshold": threshold,
        "model": name,

        "Accuracy": accuracy_score(y_true, y_pred),
        "BalancedAcc": balanced_accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1": f1_score(y_true, y_pred, zero_division=0),

        "ROC_AUC": safe_auc(y_true, y_score, "roc"),
        "PR_AUC": safe_auc(y_true, y_score, "pr"),

        "PositiveRate": float(np.mean(y_true)),
        "PositiveCount": int(np.sum(y_true == 1)),
        "NegativeCount": int(np.sum(y_true == 0)),
    }


def baseline_predictions(X, drop_threshold):
    # Her zaman bozulma yok der.
    always_no = np.zeros(len(X), dtype=int)

    # Bir önceki değişimde eşik kadar düşüş olmuşsa tekrar risk var der.
    prev_drop = (X["prev_delta"] <= -drop_threshold).astype(int).values

    # Mevcut CRC zaten düşükse risk var der.
    current_low = (X["crc_success_rate"] < 0.50).astype(int).values

    # Mevcut bağlantı iyi ama trend negatifse risk var der.
    trend_down = (
        (X["crc_success_rate"] >= 0.50) &
        (X["prev_delta"] < 0)
    ).astype(int).values

    return {
        "AlwaysNoDrop": (always_no, always_no.astype(float)),
        "PrevDropRule": (prev_drop, prev_drop.astype(float)),
        "CurrentLowRule": (current_low, 1 - X["crc_success_rate"].values),
        "TrendDownRule": (trend_down, -X["prev_delta"].values),
    }


# ============================================================
# 12. ANA DENEYLER
# ============================================================

all_time_results = []
all_gateway_details = []
all_gateway_summary = []

for drop_threshold in DROP_THRESHOLDS:

    event_data = base_event.copy()

    event_data["drop_event"] = (
        (event_data["crc_success_rate"] - event_data["next_crc_success_rate"])
        >= drop_threshold - 1e-12
    ).astype(int)

    print("\n" + "=" * 90)
    print(f"DROP THRESHOLD = {drop_threshold}")
    print("=" * 90)

    print("\nDrop-event distribution:")
    print(event_data["drop_event"].value_counts())
    print(event_data["drop_event"].value_counts(normalize=True))

    # --------------------------------------------------------
    # 12.1 TIME SPLIT
    # --------------------------------------------------------

    unique_dates = sorted(event_data["date"].unique())
    split_idx = int(len(unique_dates) * 0.70)

    train_dates = unique_dates[:split_idx]
    test_dates = unique_dates[split_idx:]

    train_data = event_data[event_data["date"].isin(train_dates)].copy()
    test_data = event_data[event_data["date"].isin(test_dates)].copy()

    print("\nTime split:")
    print("Train date count:", len(train_dates))
    print("Test date count :", len(test_dates))
    print("Train dates:", train_dates[:5], "...", train_dates[-5:])
    print("Test dates :", test_dates[:5], "...", test_dates[-5:])
    print("Train positive rate:", train_data["drop_event"].mean())
    print("Test positive rate :", test_data["drop_event"].mean())

    X_train = train_data[candidate_features]
    y_train = train_data["drop_event"].astype(int)

    X_test = test_data[candidate_features]
    y_test = test_data["drop_event"].astype(int)

    time_results = []

    # Baseline modeller
    for bname, (bpred, bscore) in baseline_predictions(X_test, drop_threshold).items():
        time_results.append(
            event_metrics(
                y_test,
                bpred,
                bscore,
                f"{bname}_time",
                drop_threshold,
            )
        )

    # Öğrenen modeller
    if y_train.nunique() == 2:
        models = make_models(y_train.values)

        for name, pipe in models.items():
            print(f"Training time-split model: {name}, threshold={drop_threshold}")

            pipe.fit(X_train, y_train)

            pred = pipe.predict(X_test)

            if hasattr(pipe.named_steps["model"], "predict_proba"):
                score = pipe.predict_proba(X_test)[:, 1]
            else:
                score = pred.astype(float)

            time_results.append(
                event_metrics(
                    y_test,
                    pred,
                    score,
                    f"{name}_time",
                    drop_threshold,
                )
            )

    time_results = pd.DataFrame(time_results)
    all_time_results.append(time_results)

    print("\n=== Time split results ===")
    print(time_results.sort_values("PR_AUC", ascending=False).to_string(index=False))

    # --------------------------------------------------------
    # 12.2 LEAVE-ONE-GATEWAY-OUT SPLIT
    # --------------------------------------------------------

    logo_results = []

    gateways = sorted(event_data["gateway"].unique())

    for idx, test_gateway in enumerate(gateways, start=1):

        print(f"\nGateway split {idx}/{len(gateways)} | Test gateway: {test_gateway} | threshold={drop_threshold}")

        train_data = event_data[event_data["gateway"] != test_gateway].copy()
        test_data = event_data[event_data["gateway"] == test_gateway].copy()

        if len(train_data) < 100 or len(test_data) < 20:
            print("Atlandı: yetersiz train/test boyutu.")
            continue

        X_train = train_data[candidate_features]
        y_train = train_data["drop_event"].astype(int)

        X_test = test_data[candidate_features]
        y_test = test_data["drop_event"].astype(int)

        # Baseline modeller
        for bname, (bpred, bscore) in baseline_predictions(X_test, drop_threshold).items():
            res = event_metrics(
                y_test,
                bpred,
                bscore,
                f"{bname}_gateway",
                drop_threshold,
            )
            res["test_gateway"] = test_gateway
            res["test_positive_rate"] = float(y_test.mean())
            res["test_positive_count"] = int(np.sum(y_test == 1))
            res["test_negative_count"] = int(np.sum(y_test == 0))
            res["valid_binary_test"] = int(y_test.nunique() == 2)

            logo_results.append(res)

        # Öğrenen modeller
        if y_train.nunique() == 2:
            models = make_models(y_train.values)

            for name, pipe in models.items():
                print(f"  Training gateway model: {name}")

                pipe.fit(X_train, y_train)

                pred = pipe.predict(X_test)

                if hasattr(pipe.named_steps["model"], "predict_proba"):
                    score = pipe.predict_proba(X_test)[:, 1]
                else:
                    score = pred.astype(float)

                res = event_metrics(
                    y_test,
                    pred,
                    score,
                    f"{name}_gateway",
                    drop_threshold,
                )
                res["test_gateway"] = test_gateway
                res["test_positive_rate"] = float(y_test.mean())
                res["test_positive_count"] = int(np.sum(y_test == 1))
                res["test_negative_count"] = int(np.sum(y_test == 0))
                res["valid_binary_test"] = int(y_test.nunique() == 2)

                logo_results.append(res)

    logo_results = pd.DataFrame(logo_results)
    all_gateway_details.append(logo_results)

    print("\n=== Leave-one-gateway-out detailed results ===")
    print(
        logo_results
        .sort_values(["test_gateway", "PR_AUC"], ascending=[True, False])
        .to_string(index=False)
    )

    # Tüm gateway ortalaması
    avg_all = (
        logo_results
        .groupby("model")[[
            "Accuracy",
            "BalancedAcc",
            "Precision",
            "Recall",
            "F1",
            "ROC_AUC",
            "PR_AUC",
            "test_positive_rate",
            "test_positive_count",
            "valid_binary_test",
        ]]
        .mean()
        .reset_index()
    )

    avg_all["threshold"] = drop_threshold
    avg_all["summary_type"] = "all_gateways"

    all_gateway_summary.append(avg_all)

    print("\n=== Average gateway results, all gateways ===")
    print(avg_all.sort_values("PR_AUC", ascending=False).to_string(index=False))

    # Sadece test setinde hem pozitif hem negatif sınıf bulunan gateway'ler
    valid_logo = logo_results[logo_results["valid_binary_test"] == 1].copy()

    if len(valid_logo) > 0:
        avg_valid = (
            valid_logo
            .groupby("model")[[
                "Accuracy",
                "BalancedAcc",
                "Precision",
                "Recall",
                "F1",
                "ROC_AUC",
                "PR_AUC",
                "test_positive_rate",
                "test_positive_count",
                "valid_binary_test",
            ]]
            .mean()
            .reset_index()
        )

        avg_valid["threshold"] = drop_threshold
        avg_valid["summary_type"] = "binary_test_gateways"

        all_gateway_summary.append(avg_valid)

        print("\n=== Average gateway results, only binary-test gateways ===")
        print(avg_valid.sort_values("PR_AUC", ascending=False).to_string(index=False))



# ============================================================
# 12.3 ORTA SEVİYE CRC ABLATION
# ============================================================
# Amaç:
#   Hakemlerin sorabileceği "model sadece mevcut CRC veya rolling CRC'ye mi dayanıyor?"
#   sorusunu test etmek.
#
# Orta seviye ablation:
#   Çıkarılanlar:
#       - crc_success_rate
#       - rolling_crc_mean_3
#       - rolling_crc_std_3
#       - rolling_crc_mean_6
#       - rolling_crc_std_6
#
#   Bırakılanlar:
#       - prev_crc_success_rate
#       - prev_delta
#
# Not:
#   Ana koddaki build_preprocess() fonksiyonu global numeric_features listesini
#   kullandığı için, sadece candidate_features listesinden kolon silmek yeterli
#   değildir. Bu nedenle ablation için feature listesine özel ayrı bir
#   Logistic Regression pipeline'ı kurulmuştur.

CRC_ABLATION_COLS = [
    "crc_success_rate",
    "rolling_crc_mean_3",
    "rolling_crc_std_3",
    "rolling_crc_mean_6",
    "rolling_crc_std_6",
]

crc_ablation_cols_present = [
    c for c in CRC_ABLATION_COLS
    if c in candidate_features
]

feature_sets_for_ablation = {
    "full_features": list(candidate_features),
    "without_current_rolling_crc": [
        c for c in candidate_features
        if c not in crc_ablation_cols_present
    ],
}

print("\n" + "=" * 90)
print("MEDIUM CRC ABLATION SETUP")
print("=" * 90)
print("Removed columns for ablation:", crc_ablation_cols_present)
print("Full feature count:", len(feature_sets_for_ablation["full_features"]))
print("Ablated feature count:", len(feature_sets_for_ablation["without_current_rolling_crc"]))


def make_lr_for_feature_list(feature_cols):
    """Feature listesine özel Logistic Regression pipeline'ı kurar."""

    cat_cols = [c for c in categorical_features if c in feature_cols]
    num_cols = [c for c in feature_cols if c not in cat_cols]

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocess = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, num_cols),
            ("cat", categorical_transformer, cat_cols),
        ]
    )

    pipe = Pipeline(steps=[
        ("preprocess", preprocess),
        ("model", LogisticRegression(
            max_iter=5000,
            solver="liblinear",
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )),
    ])

    return pipe


ablation_time_results = []
ablation_gateway_details = []

for feature_setting, feature_cols_variant in feature_sets_for_ablation.items():

    for drop_threshold in DROP_THRESHOLDS:

        event_data = base_event.copy()

        event_data["drop_event"] = (
            (event_data["crc_success_rate"] - event_data["next_crc_success_rate"])
            >= drop_threshold - 1e-12
        ).astype(int)

        print("\n" + "-" * 90)
        print(f"ABLATION | setting={feature_setting} | threshold={drop_threshold}")
        print("-" * 90)

        # --------------------------------------------------------
        # TIME SPLIT - Logistic Regression only
        # --------------------------------------------------------

        unique_dates = sorted(event_data["date"].unique())
        split_idx = int(len(unique_dates) * 0.70)

        train_dates = unique_dates[:split_idx]
        test_dates = unique_dates[split_idx:]

        train_data = event_data[event_data["date"].isin(train_dates)].copy()
        test_data = event_data[event_data["date"].isin(test_dates)].copy()

        X_train = train_data[feature_cols_variant]
        y_train = train_data["drop_event"].astype(int)

        X_test = test_data[feature_cols_variant]
        y_test = test_data["drop_event"].astype(int)

        if y_train.nunique() == 2:
            pipe = make_lr_for_feature_list(feature_cols_variant)

            print(f"Training ablation time model: {feature_setting}, threshold={drop_threshold}")
            pipe.fit(X_train, y_train)

            pred = pipe.predict(X_test)
            score = pipe.predict_proba(X_test)[:, 1]

            res = event_metrics(
                y_test,
                pred,
                score,
                "LogisticRegression_time",
                drop_threshold,
            )

            res["feature_setting"] = feature_setting
            res["split_type"] = "time_based"
            res["removed_columns"] = (
                "" if feature_setting == "full_features"
                else ",".join(crc_ablation_cols_present)
            )

            ablation_time_results.append(res)

        # --------------------------------------------------------
        # LEAVE-ONE-GATEWAY-OUT - Logistic Regression only
        # --------------------------------------------------------

        gateways = sorted(event_data["gateway"].unique())

        for idx, test_gateway in enumerate(gateways, start=1):

            train_data = event_data[event_data["gateway"] != test_gateway].copy()
            test_data = event_data[event_data["gateway"] == test_gateway].copy()

            if len(train_data) < 100 or len(test_data) < 20:
                continue

            X_train = train_data[feature_cols_variant]
            y_train = train_data["drop_event"].astype(int)

            X_test = test_data[feature_cols_variant]
            y_test = test_data["drop_event"].astype(int)

            if y_train.nunique() != 2:
                continue

            pipe = make_lr_for_feature_list(feature_cols_variant)

            print(
                f"Training ablation gateway model: "
                f"{feature_setting}, threshold={drop_threshold}, test_gateway={test_gateway}"
            )

            pipe.fit(X_train, y_train)

            pred = pipe.predict(X_test)
            score = pipe.predict_proba(X_test)[:, 1]

            res = event_metrics(
                y_test,
                pred,
                score,
                "LogisticRegression_gateway",
                drop_threshold,
            )

            res["feature_setting"] = feature_setting
            res["split_type"] = "leave_one_gateway_out"
            res["test_gateway"] = test_gateway
            res["test_positive_rate"] = float(y_test.mean())
            res["test_positive_count"] = int(np.sum(y_test == 1))
            res["test_negative_count"] = int(np.sum(y_test == 0))
            res["valid_binary_test"] = int(y_test.nunique() == 2)
            res["removed_columns"] = (
                "" if feature_setting == "full_features"
                else ",".join(crc_ablation_cols_present)
            )

            ablation_gateway_details.append(res)


ablation_time_results = pd.DataFrame(ablation_time_results)
ablation_gateway_details = pd.DataFrame(ablation_gateway_details)

if len(ablation_gateway_details) > 0:
    ablation_gateway_binary = ablation_gateway_details[
        ablation_gateway_details["valid_binary_test"] == 1
    ].copy()

    ablation_gateway_summary = (
        ablation_gateway_binary
        .groupby(["feature_setting", "threshold", "model"])[[
            "Accuracy",
            "BalancedAcc",
            "Precision",
            "Recall",
            "F1",
            "ROC_AUC",
            "PR_AUC",
            "test_positive_rate",
            "test_positive_count",
            "valid_binary_test",
        ]]
        .mean()
        .reset_index()
    )

    ablation_gateway_summary["split_type"] = "leave_one_gateway_out"
    ablation_gateway_summary["summary_type"] = "binary_test_gateways"
else:
    ablation_gateway_summary = pd.DataFrame()


# Makale için kompakt tablo:
#   Time-based ve LOGO binary-test gateway özetlerini aynı dosyada toplar.

compact_cols = [
    "feature_setting",
    "split_type",
    "threshold",
    "model",
    "BalancedAcc",
    "Precision",
    "Recall",
    "F1",
    "ROC_AUC",
    "PR_AUC",
]

ablation_time_compact = ablation_time_results.copy()
if len(ablation_time_compact) > 0:
    ablation_time_compact["summary_type"] = "time_based"

ablation_lr_compact = pd.concat(
    [
        ablation_time_compact[compact_cols + ["summary_type"]],
        ablation_gateway_summary[compact_cols + ["summary_type"]]
        if len(ablation_gateway_summary) > 0 else pd.DataFrame(columns=compact_cols + ["summary_type"]),
    ],
    ignore_index=True,
)

# Sonuçları kaydet
ablation_time_results.to_csv(
    RESULT_DIR / "ablation_time_split_lr.csv",
    index=False,
)

ablation_gateway_details.to_csv(
    RESULT_DIR / "ablation_gateway_split_lr_detailed.csv",
    index=False,
)

ablation_gateway_summary.to_csv(
    RESULT_DIR / "ablation_gateway_split_lr_summary.csv",
    index=False,
)

ablation_lr_compact.to_csv(
    RESULT_DIR / "ablation_lr_compact_for_manuscript.csv",
    index=False,
)

print("\n" + "=" * 90)
print("MEDIUM CRC ABLATION - COMPACT RESULTS")
print("=" * 90)

if len(ablation_lr_compact) > 0:
    print(
        ablation_lr_compact
        .sort_values(["split_type", "threshold", "feature_setting"])
        .to_string(index=False)
    )

print("\nSaved ablation files:")
print(" -", RESULT_DIR / "ablation_time_split_lr.csv")
print(" -", RESULT_DIR / "ablation_gateway_split_lr_detailed.csv")
print(" -", RESULT_DIR / "ablation_gateway_split_lr_summary.csv")
print(" -", RESULT_DIR / "ablation_lr_compact_for_manuscript.csv")


# ============================================================
# 13. SONUÇLARI BİRLEŞTİR VE KAYDET
# ============================================================

all_time_results = pd.concat(all_time_results, ignore_index=True)
all_gateway_details = pd.concat(all_gateway_details, ignore_index=True)
all_gateway_summary = pd.concat(all_gateway_summary, ignore_index=True)

all_time_results.to_csv(
    RESULT_DIR / "combined_time_split_summary.csv",
    index=False,
)

all_gateway_details.to_csv(
    RESULT_DIR / "gateway_split_detailed_results.csv",
    index=False,
)

all_gateway_summary.to_csv(
    RESULT_DIR / "combined_gateway_split_summary.csv",
    index=False,
)

print("\n" + "=" * 90)
print("FINAL COMBINED TIME-SPLIT SUMMARY")
print("=" * 90)

print(
    all_time_results
    .sort_values(["threshold", "PR_AUC"], ascending=[True, False])
    .to_string(index=False)
)

print("\n" + "=" * 90)
print("FINAL COMBINED GATEWAY-SPLIT SUMMARY")
print("=" * 90)

print(
    all_gateway_summary
    .sort_values(
        ["threshold", "summary_type", "PR_AUC"],
        ascending=[True, True, False]
    )
    .to_string(index=False)
)

print("\nSaved files:")
print(" -", RESULT_DIR / "LoED_full_window_level.csv")
print(" -", RESULT_DIR / "LoED_full_strict_forecasting.csv")
print(" -", RESULT_DIR / "combined_time_split_summary.csv")
print(" -", RESULT_DIR / "gateway_split_detailed_results.csv")
print(" -", RESULT_DIR / "combined_gateway_split_summary.csv")

print("\nDONE.")
