import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


class IDSVisualizer:
    def __init__(self, output_dir: str = "visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_feature_distribution(self, flows: pd.DataFrame, predictions: Dict,
                                   filename: str = "feature_distribution.png"):
        if flows.empty:
            return

        fig, axes = plt.subplots(3, 2, figsize=(14, 12))
        axes = axes.flatten()

        plot_configs = [
            ("packet_count", "Количество пакетов в потоке", "Пакеты"),
            ("total_bytes", "Общий объём данных в потоке", "Байты"),
            ("mean_packet_size", "Средний размер пакета", "Байты"),
            ("flow_duration_sec", "Длительность потока", "Секунды"),
            ("syn_count", "Количество SYN-флагов", "Количество"),
            ("mean_inter_arrival_time", "Среднее время между пакетами", "Секунды"),
        ]

        for idx, (col, title, xlabel) in enumerate(plot_configs):
            if col in flows.columns:
                ax = axes[idx]
                data = flows[col].fillna(0)
                ax.hist(data, bins=50, alpha=0.7, color="steelblue", edgecolor="black")
                ax.set_title(title, fontsize=12, fontweight="bold")
                ax.set_xlabel(xlabel)
                ax.set_ylabel("Частота")
                ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_anomaly_scores(self, predictions: Dict, filename: str = "anomaly_scores.png"):
        if not predictions or "results" not in predictions:
            return

        results = predictions["results"]
        scores = [r["anomaly_score"] for r in results]
        labels = ["Аномалия" if r["is_anomaly"] else "Норма" for r in results]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        colors = ["red" if l == "Аномалия" else "green" for l in labels]
        ax1.scatter(range(len(scores)), scores, c=colors, alpha=0.6, s=50)
        ax1.axhline(y=0.5, color="orange", linestyle="--", alpha=0.7, label="Порог (0.5)")
        ax1.set_xlabel("Индекс потока")
        ax1.set_ylabel("Оценка аномалии")
        ax1.set_title("Оценка аномальности потоков")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.pie(
            [predictions["normal_count"], predictions["anomaly_count"]],
            labels=["Норма", "Аномалия"],
            autopct="%1.1f%%",
            colors=["green", "red"],
            startangle=90,
            explode=(0, 0.05),
        )
        ax2.set_title(f"Классификация трафика\n(Всего: {predictions['total_flows']} потоков)")

        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_model_comparison(self, predictions: Dict, filename: str = "model_comparison.png"):
        if not predictions or "results" not in predictions:
            return

        results = predictions["results"]
        models = ["Random Forest", "MLP Neural Net", "Isolation Forest"]
        model_keys = ["rf_prediction", "mlp_prediction", "iso_forest_prediction"]

        counts = {m: {"anomaly": 0, "normal": 0} for m in models}
        for r in results:
            for model, key in zip(models, model_keys):
                if r[key] == 1:
                    counts[model]["anomaly"] += 1
                else:
                    counts[model]["normal"] += 1

        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(models))
        width = 0.35

        normal_counts = [counts[m]["normal"] for m in models]
        anomaly_counts = [counts[m]["anomaly"] for m in models]

        bars1 = ax.bar(x - width / 2, normal_counts, width, label="Норма", color="green", alpha=0.7)
        bars2 = ax.bar(x + width / 2, anomaly_counts, width, label="Аномалия", color="red", alpha=0.7)

        ax.set_xlabel("Модель")
        ax.set_ylabel("Количество потоков")
        ax.set_title("Сравнение предсказаний моделей")
        ax.set_xticks(x)
        ax.set_xticklabels(models)
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f"{int(height)}", xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points", ha="center", va="bottom")
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f"{int(height)}", xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points", ha="center", va="bottom")

        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()
