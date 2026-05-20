"""
Проверочный скрипт для курсовой работы (Вариант 3)
Система обнаружения вторжений (IDS) на основе машинного обучения

Запуск: python verify.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

from features.parser import prepare_features
from model.train import generate_training_data, train_models
from model.predict import IDSPredictor
from visualization.dashboard import IDSVisualizer


def print_separator(title: str):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def main():
    print_separator("IDS — проверка работоспособности")

    # 1. Генерация данных и обучение
    print("\n[1/4] Генерация обучающих данных 6 типов трафика:")
    print("      Норма: HTTP, SSH, DNS")
    print("      Аномалии: SYN-flood, Port scan, DDoS")

    X, y = generate_training_data(n_per_class=200)
    normal_count = sum(y == 0)
    anomaly_count = sum(y == 1)
    print(f"      Сгенерировано: {len(X)} образцов ({normal_count} норма, {anomaly_count} аномалия)")

    print("\n[2/4] Обучение моделей ML...")
    rf, mlp, iso, scaler = train_models(X, y, model_dir="models")
    print("      Модели сохранены в папке models/")

    # 2. Тестовые данные — 10 потоков (6 норма, 4 атаки)
    print("\n[3/4] Проверка на 10 тестовых потоках...")

    test_flows = [
        # ===== НОРМАЛЬНЫЙ ТРАФИК (6 потоков) =====
        {
            "name": "1. HTTP (веб-сёрфинг)",
            "src_ip": "10.0.0.1", "dst_ip": "192.168.1.1",
            "src_port": 12345, "dst_port": 80, "protocol": "TCP",
            "packet_count": 25, "total_bytes": 3200, "mean_packet_size": 350,
            "std_packet_size": 45, "min_packet_size": 40, "max_packet_size": 1400,
            "flow_duration_sec": 28.0, "mean_inter_arrival_time": 0.75,
            "std_inter_arrival_time": 0.45, "syn_count": 2, "ack_count": 18,
            "fin_count": 2, "rst_count": 0, "psh_count": 8, "urg_count": 0,
            "mean_ttl": 120, "mean_window_size": 65000, "payload_bytes_total": 2100,
        },
        {
            "name": "2. HTTPS (защищённый сайт)",
            "src_ip": "10.0.0.4", "dst_ip": "192.168.1.1",
            "src_port": 44000, "dst_port": 443, "protocol": "TCP",
            "packet_count": 60, "total_bytes": 18000, "mean_packet_size": 800,
            "std_packet_size": 200, "min_packet_size": 60, "max_packet_size": 1460,
            "flow_duration_sec": 15.0, "mean_inter_arrival_time": 0.3,
            "std_inter_arrival_time": 0.2, "syn_count": 3, "ack_count": 45,
            "fin_count": 2, "rst_count": 0, "psh_count": 25, "urg_count": 0,
            "mean_ttl": 64, "mean_window_size": 65535, "payload_bytes_total": 15000,
        },
        {
            "name": "3. SSH (удалённый доступ)",
            "src_ip": "10.0.0.2", "dst_ip": "192.168.1.2",
            "src_port": 50001, "dst_port": 22, "protocol": "TCP",
            "packet_count": 42, "total_bytes": 650, "mean_packet_size": 85,
            "std_packet_size": 18, "min_packet_size": 40, "max_packet_size": 300,
            "flow_duration_sec": 180.0, "mean_inter_arrival_time": 3.2,
            "std_inter_arrival_time": 2.1, "syn_count": 1, "ack_count": 36,
            "fin_count": 1, "rst_count": 0, "psh_count": 32, "urg_count": 0,
            "mean_ttl": 128, "mean_window_size": 35000, "payload_bytes_total": 420,
        },
        {
            "name": "4. DNS (запросы имён)",
            "src_ip": "10.0.0.3", "dst_ip": "8.8.8.8",
            "src_port": 53000, "dst_port": 53, "protocol": "UDP",
            "packet_count": 5, "total_bytes": 450, "mean_packet_size": 90,
            "std_packet_size": 12, "min_packet_size": 50, "max_packet_size": 200,
            "flow_duration_sec": 4.0, "mean_inter_arrival_time": 0.12,
            "std_inter_arrival_time": 0.06, "syn_count": 0, "ack_count": 0,
            "fin_count": 0, "rst_count": 0, "psh_count": 0, "urg_count": 0,
            "mean_ttl": 64, "mean_window_size": 0, "payload_bytes_total": 320,
        },
        {
            "name": "5. FTP (скачивание файла)",
            "src_ip": "10.0.0.5", "dst_ip": "192.168.1.10",
            "src_port": 31000, "dst_port": 21, "protocol": "TCP",
            "packet_count": 120, "total_bytes": 45000, "mean_packet_size": 1200,
            "std_packet_size": 300, "min_packet_size": 40, "max_packet_size": 1460,
            "flow_duration_sec": 45.0, "mean_inter_arrival_time": 0.4,
            "std_inter_arrival_time": 0.15, "syn_count": 2, "ack_count": 100,
            "fin_count": 2, "rst_count": 0, "psh_count": 60, "urg_count": 0,
            "mean_ttl": 128, "mean_window_size": 65535, "payload_bytes_total": 42000,
        },
        {
            "name": "6. SMTP (отправка почты)",
            "src_ip": "10.0.0.6", "dst_ip": "192.168.1.20",
            "src_port": 25000, "dst_port": 25, "protocol": "TCP",
            "packet_count": 35, "total_bytes": 8500, "mean_packet_size": 450,
            "std_packet_size": 150, "min_packet_size": 40, "max_packet_size": 1400,
            "flow_duration_sec": 12.0, "mean_inter_arrival_time": 0.5,
            "std_inter_arrival_time": 0.3, "syn_count": 2, "ack_count": 25,
            "fin_count": 4, "rst_count": 0, "psh_count": 15, "urg_count": 0,
            "mean_ttl": 120, "mean_window_size": 50000, "payload_bytes_total": 6500,
        },
        # ===== АТАКИ (4 потока) =====
        {
            "name": "7. SYN-FLOOD (атака)",
            "src_ip": "10.0.0.100", "dst_ip": "192.168.1.1",
            "src_port": 31337, "dst_port": 80, "protocol": "TCP",
            "packet_count": 850, "total_bytes": 55000, "mean_packet_size": 60,
            "std_packet_size": 5, "min_packet_size": 40, "max_packet_size": 80,
            "flow_duration_sec": 1.5, "mean_inter_arrival_time": 0.001,
            "std_inter_arrival_time": 0.0005, "syn_count": 750, "ack_count": 3,
            "fin_count": 0, "rst_count": 0, "psh_count": 0, "urg_count": 0,
            "mean_ttl": 64, "mean_window_size": 1024, "payload_bytes_total": 50,
        },
        {
            "name": "8. PORT SCAN (атака)",
            "src_ip": "10.0.0.200", "dst_ip": "192.168.1.1",
            "src_port": 40000, "dst_port": 0, "protocol": "TCP",
            "packet_count": 320, "total_bytes": 22000, "mean_packet_size": 60,
            "std_packet_size": 8, "min_packet_size": 40, "max_packet_size": 100,
            "flow_duration_sec": 8.0, "mean_inter_arrival_time": 0.015,
            "std_inter_arrival_time": 0.008, "syn_count": 260, "ack_count": 15,
            "fin_count": 5, "rst_count": 35, "psh_count": 0, "urg_count": 0,
            "mean_ttl": 128, "mean_window_size": 65535, "payload_bytes_total": 40,
        },
        {
            "name": "9. DDoS (атака)",
            "src_ip": "10.0.0.50", "dst_ip": "192.168.1.1",
            "src_port": 12345, "dst_port": 443, "protocol": "TCP",
            "packet_count": 2200, "total_bytes": 180000, "mean_packet_size": 90,
            "std_packet_size": 35, "min_packet_size": 40, "max_packet_size": 1200,
            "flow_duration_sec": 25.0, "mean_inter_arrival_time": 0.0004,
            "std_inter_arrival_time": 0.0002, "syn_count": 1100, "ack_count": 450,
            "fin_count": 60, "rst_count": 120, "psh_count": 180, "urg_count": 8,
            "mean_ttl": 64, "mean_window_size": 512, "payload_bytes_total": 95000,
        },
        {
            "name": "10. DNS Amplification (атака)",
            "src_ip": "10.0.0.150", "dst_ip": "8.8.8.8",
            "src_port": 53000, "dst_port": 53, "protocol": "UDP",
            "packet_count": 600, "total_bytes": 120000, "mean_packet_size": 400,
            "std_packet_size": 200, "min_packet_size": 40, "max_packet_size": 1450,
            "flow_duration_sec": 3.0, "mean_inter_arrival_time": 0.005,
            "std_inter_arrival_time": 0.002, "syn_count": 0, "ack_count": 0,
            "fin_count": 0, "rst_count": 0, "psh_count": 0, "urg_count": 0,
            "mean_ttl": 255, "mean_window_size": 0, "payload_bytes_total": 115000,
        },
    ]

    # 3. Предсказание
    df = pd.json_normalize(test_flows)
    features = prepare_features(df)
    predictor = IDSPredictor(model_dir="models")
    predictions = predictor.predict(features)

    # 4. Вывод отчёта
    print(f"\n{'Тип трафика':<25} {'Статус':<12} {'Оценка':<10} {'RF':<6} {'MLP':<6} {'IF':<6}")
    print("-" * 65)

    for i, flow in enumerate(test_flows):
        r = predictions["results"][i]
        status = "АНOМАЛИЯ" if r["is_anomaly"] else "НОРМА"
        status_mark = " <<<" if r["is_anomaly"] else ""
        print(f"{flow['name']:<25} {status:<12} {r['anomaly_score']:.4f}{'':5} "
              f"{'ДА' if r['rf_prediction'] else 'НЕТ':<6} "
              f"{'ДА' if r['mlp_prediction'] else 'НЕТ':<6} "
              f"{'ДА' if r['iso_forest_prediction'] else 'НЕТ':<6}"
              f"{status_mark}")

    print(f"\n  Итого: {predictions['normal_count']} норма / {predictions['anomaly_count']} аномалия")
    print(f"  Соотношение: {predictions['normal_count'] / predictions['total_flows'] * 100:.0f}% / "
          f"{predictions['anomaly_count'] / predictions['total_flows'] * 100:.0f}%")

    # 5. Генерация графиков
    print("\n[4/4] Генерация графиков...")
    visualizer = IDSVisualizer(output_dir="visualizations")
    visualizer.plot_feature_bar_chart(df, predictions)
    visualizer.plot_anomaly_scores(predictions)
    visualizer.plot_model_comparison(predictions)

    # 6. Сохранение результатов
    results_path = Path("verify_results")
    results_path.mkdir(exist_ok=True)

    report = {
        "test_flows": test_flows,
        "predictions": predictions,
        "summary": {
            "total": predictions["total_flows"],
            "normal": predictions["normal_count"],
            "anomaly": predictions["anomaly_count"],
            "ratio": f"{predictions['normal_count'] / predictions['total_flows'] * 100:.0f}% норма / "
                     f"{predictions['anomaly_count'] / predictions['total_flows'] * 100:.0f}% аномалия",
        }
    }
    with open(results_path / "report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n      Графики сохранены: visualizations/")
    print(f"      Отчёт сохранён: verify_results/report.json")

    print_separator("ПРОВЕРКА ЗАВЕРШЕНА")
    print(f"\n  Всего потоков: {predictions['total_flows']}")
    print(f"  Нормальных: {predictions['normal_count']}")
    print(f"  Аномалий: {predictions['anomaly_count']}")
    print(f"\n  Модели: Random Forest, MLP Neural Network, Isolation Forest")
    print(f"  Решение: голосование (>= 2 моделей = аномалия)")


if __name__ == "__main__":
    main()
