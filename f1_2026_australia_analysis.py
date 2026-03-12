"""
F1 2026 オーストラリアGP 分析スクリプト
=====================================
必要なライブラリ:
  pip install fastf1 matplotlib pandas numpy seaborn

実行方法:
  python f1_2026_australia_analysis.py
"""

import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap

import os

# キャッシュディレクトリの自動作成
CACHE_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "f1_cache")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# キャッシュ設定（2回目以降の読み込みが速くなる）
fastf1.Cache.enable_cache(CACHE_DIR)

# ============================================================
# データ読み込み準備（年・GP・セッション選択）
# ============================================================


def get_selection():
    # 1. 年の選択
    print("--- F1 分析対象イヤー選択 ---")
    print(" 1: 2025年")
    print(" 2: 2026年")
    year_val = input("選択してください (1 or 2, デフォルト=2): ")
    year = 2025 if year_val == "1" else 2026

    # 2. GPの選択
    filename = f"Schedule{year}.txt"
    print(f"\n--- F1 {year} 開催スケジュール ---")
    races = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # 最初の2行（タイトルとヘッダー）を飛ばして3行目からパース
            for line in lines[2:]:
                if "Grand Prix" in line:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        # "Australian Grand Prix" から "Australian" を抽出
                        name_raw = parts[1].strip()
                        race_name = name_raw.replace(
                            " Grand Prix", "").replace("Grand Prix", "").strip()
                        if race_name:
                            races.append(race_name)
    except FileNotFoundError:
        print(f"警告: {filename} が見つかりません。")
        races = ["Australia"]

    if not races:
        races = ["Australia"]
    for i, race in enumerate(races, 1):
        print(f"{i:2}: {race}")

    while True:
        val = input(f"\n分析したいGPの番号を入力してください (1-{len(races)}, デフォルト=1): ")
        if not val:
            race = races[0]
            break
        try:
            choice = int(val)
            if 1 <= choice <= len(races):
                race = races[choice-1]
                break
        except ValueError:
            pass
        print(f"1から{len(races)}の番号を入力してください。")

    # 3. セッションの選択
    print("\n--- 分析セッション選択 ---")
    print(" 1: 決勝 (Race) のみ")
    print(" 2: 予選 (Qualifying) のみ")
    print(" 3: 両方 (Both)")
    sess_val = input("選択してください (1, 2 or 3, デフォルト=3): ")
    if sess_val == "1":
        session_type = "R"
    elif sess_val == "2":
        session_type = "Q"
    else:
        session_type = "B"

    return year, race, session_type


YEAR, RACE, SESSION_TYPE = get_selection()
print(f"\n設定完了: {YEAR} {RACE} GP (セッション: {'決勝' if SESSION_TYPE == 'R' else '予選' if SESSION_TYPE == 'Q' else '両方'})")

print("データ読み込み中...")

# 選択されたセッションのみをロードする
try:
    if SESSION_TYPE in ["R", "B"]:
        race_session = fastf1.get_session(YEAR, RACE, "R")
        race_session.load(telemetry=False, weather=False)
        # データが空かどうかの簡易チェック
        if len(race_session.laps) == 0:
            print(f"⚠️ 警告: {YEAR} {RACE} 決勝のデータがまだ利用できないか、存在しません。")
            race_session = None
    else:
        race_session = None

    if SESSION_TYPE in ["Q", "B"]:
        quali_session = fastf1.get_session(YEAR, RACE, "Q")
        quali_session.load(telemetry=True, weather=False)
        if len(quali_session.laps) == 0:
            print(f"⚠️ 警告: {YEAR} {RACE} 予選のデータがまだ利用できないか、存在しません。")
            quali_session = None
    else:
        quali_session = None
except Exception as e:
    print(f"❌ エラー: データの読み込み中に問題が発生しました: {e}")
    print("指定したGP名が正しいか、または開催後のデータがあるか確認してください。")
    race_session = None
    quali_session = None

print("完了！")

# タイヤカラーの定義
COMPOUND_COLORS = {
    "SOFT": "#FF3333",
    "MEDIUM": "#FFD700",
    "HARD": "#EEEEEE",
    "INTERMEDIATE": "#39B54A",
    "WET": "#0067FF",
    "UNKNOWN": "#999999",
}

# チームカラー（FastF1から取得 or フォールバック）
try:
    fastf1.plotting.setup_mpl(mpl_timedelta_support=True, misc_mpl_mods=False)
except Exception:
    pass


# ============================================================
# ① 決勝ラップタイム（全車）
# ============================================================
def plot_race_laptimes(session):
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    laps = session.laps.pick_quicklaps(threshold=1.07)

    drivers = session.drivers
    driver_info = {
        d: session.get_driver(d) for d in drivers
    }

    for drv in drivers:
        drv_laps = laps.pick_drivers(drv)
        if drv_laps.empty:
            continue

        abbr = driver_info[drv].get("Abbreviation", drv)
        try:
            color = fastf1.plotting.driver_color(abbr)
        except Exception:
            color = "#AAAAAA"

        ax.plot(
            drv_laps["LapNumber"],
            drv_laps["LapTime"].dt.total_seconds(),
            label=abbr,
            color=color,
            linewidth=1.2,
            alpha=0.85,
        )

        # ピットストップのマーカー
        pit_laps = drv_laps[drv_laps["PitOutTime"].notna()]
        ax.scatter(
            pit_laps["LapNumber"],
            pit_laps["LapTime"].dt.total_seconds(),
            color=color,
            marker="v",
            s=60,
            zorder=5,
        )

    ax.set_xlabel("Lap Number", color="white", fontsize=12)
    ax.set_ylabel("Lap Time (seconds)", color="white", fontsize=12)
    ax.set_title(
        f"F1 {YEAR} {RACE} GP — Race Lap Times (▼ = Pit Stop)",
        color="white",
        fontsize=15,
        fontweight="bold",
        pad=15,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444466")
    ax.legend(
        loc="upper right",
        fontsize=7,
        ncol=3,
        facecolor="#1a1a2e",
        labelcolor="white",
        framealpha=0.7,
    )
    ax.grid(axis="y", color="#334466", linewidth=0.5, linestyle="--")

    plt.tight_layout()
    plt.savefig(f"f1_{YEAR}_{RACE}_race_laptimes.png", dpi=150,
                bbox_inches="tight", facecolor=fig.get_facecolor())

    # CSV出力
    laps_csv = laps[["Driver", "LapNumber", "LapTime", "PitOutTime",
                     "PitInTime", "Compound", "TyreLife", "FreshTyre"]].copy()
    laps_csv.to_csv(f"f1_{YEAR}_{RACE}_race_laps.csv", index=False)

    print(
        f"✅ 保存: f1_{YEAR}_{RACE}_race_laptimes.png / f1_{YEAR}_{RACE}_race_laps.csv")
    plt.show()


# ============================================================
# ② タイヤ戦略ガントチャート
# ============================================================
def plot_tyre_strategy(session):
    laps = session.laps
    drivers = session.drivers

    # 各ドライバーのスティント情報をまとめる
    stints = laps[["Driver", "Stint", "Compound", "LapNumber"]].copy()
    stints = stints.groupby(["Driver", "Stint", "Compound"]).agg(
        LapStart=("LapNumber", "min"),
        LapEnd=("LapNumber", "max"),
    ).reset_index()

    # 最終順位でドライバーをソート
    results = session.results.sort_values("Position")
    ordered_drivers = results["Abbreviation"].tolist()
    ordered_drivers = [
        d for d in ordered_drivers if d in stints["Driver"].values]

    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    for i, drv in enumerate(ordered_drivers):
        drv_stints = stints[stints["Driver"] == drv]
        for _, row in drv_stints.iterrows():
            compound = row["Compound"] if row["Compound"] in COMPOUND_COLORS else "UNKNOWN"
            color = COMPOUND_COLORS[compound]
            ax.barh(
                i,
                row["LapEnd"] - row["LapStart"] + 1,
                left=row["LapStart"],
                color=color,
                edgecolor="#1a1a2e",
                linewidth=0.8,
                height=0.7,
            )

    ax.set_yticks(range(len(ordered_drivers)))
    ax.set_yticklabels(ordered_drivers, color="white", fontsize=10)
    ax.set_xlabel("Lap Number", color="white", fontsize=12)
    ax.set_title(
        f"F1 {YEAR} {RACE} GP — Tyre Strategy",
        color="white",
        fontsize=15,
        fontweight="bold",
        pad=15,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444466")
    ax.grid(axis="x", color="#334466", linewidth=0.5, linestyle="--")
    ax.invert_yaxis()

    # 凡例
    legend_patches = [
        mpatches.Patch(color=v, label=k) for k, v in COMPOUND_COLORS.items() if k != "UNKNOWN"
    ]
    ax.legend(
        handles=legend_patches,
        loc="lower right",
        facecolor="#1a1a2e",
        labelcolor="white",
        fontsize=9,
    )

    plt.tight_layout()
    plt.savefig(f"f1_{YEAR}_{RACE}_tyre_strategy.png", dpi=150,
                bbox_inches="tight", facecolor=fig.get_facecolor())

    # CSV出力
    stints.to_csv(f"f1_{YEAR}_{RACE}_tyre_strategy.csv", index=False)

    print(
        f"✅ 保存: f1_{YEAR}_{RACE}_tyre_strategy.png / f1_{YEAR}_{RACE}_tyre_strategy.csv")
    plt.show()


# ============================================================
# ③ 予選セクタータイム比較
# ============================================================
def plot_quali_sectors(session):
    laps = session.laps.pick_quicklaps()

    # 各ドライバーのベストラップ
    best_laps = laps.loc[laps.groupby("Driver")["LapTime"].idxmin()].copy()

    # セクタータイムを秒に変換
    for s in ["Sector1Time", "Sector2Time", "Sector3Time"]:
        best_laps[s + "_s"] = best_laps[s].dt.total_seconds()

    # 各セクターの最速タイムからのデルタ
    for s in ["Sector1Time_s", "Sector2Time_s", "Sector3Time_s"]:
        best_laps[s + "_delta"] = best_laps[s] - best_laps[s].min()

    # ラップタイム順でソート
    best_laps = best_laps.sort_values("LapTime")
    drivers = best_laps["Driver"].tolist()

    sectors = ["Sector1Time_s_delta",
               "Sector2Time_s_delta", "Sector3Time_s_delta"]
    sector_labels = ["Sector 1", "Sector 2", "Sector 3"]
    sector_colors = ["#FF6B6B", "#4ECDC4", "#45B7D1"]

    fig, axes = plt.subplots(1, 3, figsize=(16, 9), sharey=True)
    fig.patch.set_facecolor("#1a1a2e")

    for ax, col, label, color in zip(axes, sectors, sector_labels, sector_colors):
        ax.set_facecolor("#16213e")
        values = best_laps[col].values

        bars = ax.barh(
            range(len(drivers)),
            values,
            color=color,
            alpha=0.85,
            edgecolor="#1a1a2e",
        )

        # 値ラベル
        for bar, val in zip(bars, values):
            ax.text(
                val + 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"+{val:.3f}s" if val > 0 else "BEST",
                va="center",
                ha="left",
                color="white",
                fontsize=8,
            )

        ax.set_title(label, color=color, fontsize=13, fontweight="bold")
        ax.set_xlabel("Delta (s)", color="white", fontsize=10)
        ax.tick_params(colors="white")
        ax.spines[:].set_color("#444466")
        ax.grid(axis="x", color="#334466", linewidth=0.5, linestyle="--")
        ax.set_xlim(0, best_laps[col].max() * 1.3)

    axes[0].set_yticks(range(len(drivers)))
    axes[0].set_yticklabels(drivers, color="white", fontsize=10)
    axes[0].invert_yaxis()

    fig.suptitle(
        f"F1 {YEAR} {RACE} GP — Qualifying Sector Time Delta",
        color="white",
        fontsize=15,
        fontweight="bold",
        y=1.01,
    )

    plt.tight_layout()
    plt.savefig(f"f1_{YEAR}_{RACE}_quali_sectors.png", dpi=150,
                bbox_inches="tight", facecolor=fig.get_facecolor())

    # CSV出力
    best_laps_csv = best_laps[["Driver", "LapTime", "Sector1Time_s", "Sector2Time_s", "Sector3Time_s",
                               "Sector1Time_s_delta", "Sector2Time_s_delta", "Sector3Time_s_delta"]].copy()
    best_laps_csv.to_csv(
        f"f1_{YEAR}_{RACE}_quali_best_sectors.csv", index=False)

    print(
        f"✅ 保存: f1_{YEAR}_{RACE}_quali_sectors.png / f1_{YEAR}_{RACE}_quali_best_sectors.csv")
    plt.show()


# ============================================================
# 実行
# ============================================================
if SESSION_TYPE in ["R", "B"] and race_session is not None:
    print("\n📊 ① 決勝ラップタイムグラフ")
    plot_race_laptimes(race_session)

    print("\n📊 ② タイヤ戦略ガントチャート")
    plot_tyre_strategy(race_session)

if SESSION_TYPE in ["Q", "B"] and quali_session is not None:
    print("\n📊 ③ 予選セクタータイム比較")
    plot_quali_sectors(quali_session)

print("\n🏁 完了！")
