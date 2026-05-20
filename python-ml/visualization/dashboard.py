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

    def plot_feature_bar_chart(self, flows: pd.DataFrame, predictions: Dict,
                                filename: str = "feature_comparison.png"):
        if flows.empty or "results" not in predictions:
            return

        results = predictions["results"]
        flow_colors = ["green" if not r["is_anomaly"] else "red" for r in results]
        flow_names = [f.get("name", f"Flow {i}") for i, f in flows.iterrows()]

        feature_sets = [
            ("packet_count", "Количество пакетов", "пакетов"),
            ("syn_count", "Количество SYN-флагов", "SYN"),
            ("total_bytes", "Общий объём данных", "байт"),
            ("mean_packet_size", "Средний размер пакета", "байт"),
        ]

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()

        for idx, (col, title, unit) in enumerate(feature_sets):
            ax = axes[idx]
            if col not in flows.columns:
                continue
            values = flows[col].fillna(0).values
            bars = ax.bar(range(len(values)), values, color=flow_colors, alpha=0.75, edgecolor="black", linewidth=0.5)
            ax.set_xticks(range(len(values)))
            ax.set_xticklabels(flow_names, rotation=35, ha="right", fontsize=8)
            ax.set_title(title, fontsize=13, fontweight="bold")
            ax.set_ylabel(unit)
            ax.axhline(y=values.mean(), color="blue", linestyle="--", alpha=0.5, label=f"Среднее: {values.mean():.0f}")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3, axis="y")

            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                        f"{val:.0f}", ha="center", va="bottom", fontsize=7, rotation=45)

        handles = [plt.Rectangle((0, 0), 1, 1, color="green", alpha=0.7),
                   plt.Rectangle((0, 0), 1, 1, color="red", alpha=0.7)]
        fig.legend(handles, ["Нормальный трафик", "Аномалия"], loc="lower center",
                   ncol=2, fontsize=11, frameon=True)

        plt.tight_layout(rect=[0, 0.03, 1, 1])
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_anomaly_scores(self, predictions: Dict, filename: str = "anomaly_scores.png"):
        if not predictions or "results" not in predictions:
            return

        results = predictions["results"]
        scores = [r["anomaly_score"] for r in results]
        labels = ["Аномалия" if r["is_anomaly"] else "Норма" for r in results]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        colors = ["red" if l == "Аномалия" else "green" for l in labels]
        ax1.scatter(range(len(scores)), scores, c=colors, alpha=0.7, s=120, edgecolors="black", linewidth=0.5)
        ax1.axhline(y=0.5, color="orange", linestyle="--", alpha=0.8, linewidth=2, label="Порог (0.5)")
        ax1.set_xlabel("Индекс потока", fontsize=12)
        ax1.set_ylabel("Оценка аномалии", fontsize=12)
        ax1.set_title("Оценка аномальности каждого потока", fontsize=14, fontweight="bold")
        ax1.set_xticks(range(len(scores)))
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(-0.05, 1.05)

        for i, (s, c) in enumerate(zip(scores, colors)):
            ax1.annotate(f"{s:.3f}", (i, s), textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=8, color=c)

        ax2.pie(
            [predictions["normal_count"], predictions["anomaly_count"]],
            labels=["Норма\n(обычный трафик)", "Аномалия\n(атака)"],
            autopct="%1.1f%%",
            colors=["green", "red"],
            startangle=90,
            explode=(0, 0.08),
            textprops={"fontsize": 11},
        )
        ax2.set_title(f"Распределение трафика\nВсего: {predictions['total_flows']} потоков",
                      fontsize=14, fontweight="bold")

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

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        x = np.arange(len(models))
        width = 0.35
        normal_counts = [counts[m]["normal"] for m in models]
        anomaly_counts = [counts[m]["anomaly"] for m in models]

        bars1 = ax1.bar(x - width / 2, normal_counts, width, label="Норма", color="green", alpha=0.75, edgecolor="black")
        bars2 = ax1.bar(x + width / 2, anomaly_counts, width, label="Аномалия", color="red", alpha=0.75, edgecolor="black")

        ax1.set_xlabel("Модель", fontsize=12)
        ax1.set_ylabel("Количество потоков", fontsize=12)
        ax1.set_title("Сравнение результатов трёх моделей", fontsize=14, fontweight="bold")
        ax1.set_xticks(x)
        ax1.set_xticklabels(models, fontsize=10)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3, axis="y")

        for bar in bars1:
            height = bar.get_height()
            ax1.annotate(f"{int(height)}", xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5), textcoords="offset points", ha="center", va="bottom", fontsize=10)
        for bar in bars2:
            height = bar.get_height()
            ax1.annotate(f"{int(height)}", xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5), textcoords="offset points", ha="center", va="bottom", fontsize=10)

        flow_names = [f"{i+1}" for i in range(len(results))]
        rf_vals = [r["rf_prediction"] for r in results]
        mlp_vals = [r["mlp_prediction"] for r in results]
        iso_vals = [r["iso_forest_prediction"] for r in results]

        ax2.set_title("Прогноз каждой модели по потокам", fontsize=14, fontweight="bold")
        x2 = np.arange(len(results))
        w = 0.25
        ax2.bar(x2 - w, rf_vals, w, label="Random Forest", color="#1f77b4", alpha=0.8, edgecolor="black")
        ax2.bar(x2, mlp_vals, w, label="MLP Neural Net", color="#ff7f0e", alpha=0.8, edgecolor="black")
        ax2.bar(x2 + w, iso_vals, w, label="Isolation Forest", color="#2ca02c", alpha=0.8, edgecolor="black")
        ax2.set_xlabel("Поток", fontsize=12)
        ax2.set_ylabel("Прогноз (1 = аномалия)", fontsize=12)
        ax2.set_xticks(x2)
        ax2.set_xticklabels(flow_names, fontsize=9)
        ax2.set_yticks([0, 1])
        ax2.set_yticklabels(["Норма", "Аномалия"], fontsize=9)
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()
