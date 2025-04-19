# === trend_analyzer.py ===

import pandas as pd
import os
from collections import defaultdict
from datetime import datetime, timedelta


def load_trend_scores(log_path='output', months=3):
    """
    指定された月数以内のログから スタッフ×ジャンル 出動回数を集計
    """
    trend_scores = defaultdict(lambda: defaultdict(int))
    cutoff_date = datetime.today() - timedelta(days=30 * months)

    for file in os.listdir(log_path):
        if file.startswith("log_") and file.endswith(".csv"):
            df = pd.read_csv(os.path.join(log_path, file))
            df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
            df = df[df["日付"] >= cutoff_date]
            for _, row in df.iterrows():
                name = row['スタッフ名']
                genre = row['ジャンル']
                trend_scores[name][genre] += 1

    return trend_scores


def normalize_scores(trend_scores, max_score=10):
    normalized = {}
    for name, genre_counts in trend_scores.items():
        max_count = max(genre_counts.values()) if genre_counts else 1
        normalized[name] = {
            genre: round((count / max_count) * max_score, 2)
            for genre, count in genre_counts.items()
        }
    return normalized


def load_project_history_scores(log_path='output', months=3):
    """
    指定された月数以内のログから スタッフ×案件（午前/午後別） の出動回数を集計
    """
    project_scores = defaultdict(lambda: defaultdict(int))
    cutoff_date = datetime.today() - timedelta(days=30 * months)

    for file in os.listdir(log_path):
        if file.startswith("log_") and file.endswith(".csv"):
            df = pd.read_csv(os.path.join(log_path, file))
            df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
            df = df[df["日付"] >= cutoff_date]
            for _, row in df.iterrows():
                name = row['スタッフ名']
                project = row['案件名']
                shift = row['シフト']
                key = f"{project}_{shift}"
                project_scores[name][key] += 1

    return project_scores
