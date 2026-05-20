import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path
from typing import Tuple


def generate_training_data(n_per_class: int = 300) -> Tuple[pd.DataFrame, np.ndarray]:
    np.random.seed(42)

    def normal_http():
        return pd.DataFrame({
            "packet_count": np.random.poisson(25, n_per_class),
            "total_bytes": np.random.normal(3000, 800, n_per_class).clip(100),
            "mean_packet_size": np.random.normal(350, 80, n_per_class).clip(60),
            "std_packet_size": np.random.exponential(50, n_per_class),
            "min_packet_size": np.random.uniform(40, 80, n_per_class),
            "max_packet_size": np.random.normal(1400, 100, n_per_class).clip(200, 1500),
            "flow_duration_sec": np.random.exponential(25, n_per_class),
            "mean_inter_arrival_time": np.random.exponential(0.8, n_per_class),
            "std_inter_arrival_time": np.random.exponential(0.5, n_per_class),
            "syn_count": np.random.poisson(2, n_per_class),
            "ack_count": np.random.poisson(20, n_per_class),
            "fin_count": np.random.poisson(2, n_per_class),
            "rst_count": np.zeros(n_per_class),
            "psh_count": np.random.poisson(8, n_per_class),
            "urg_count": np.zeros(n_per_class),
            "mean_ttl": np.random.normal(120, 10, n_per_class).clip(1, 255),
            "mean_window_size": np.random.normal(65000, 3000, n_per_class).clip(0),
            "payload_bytes_total": np.random.normal(2000, 600, n_per_class).clip(0),
            "protocol_encoded": np.zeros(n_per_class),
        })

    def normal_ssh():
        return pd.DataFrame({
            "packet_count": np.random.poisson(40, n_per_class),
            "total_bytes": np.random.normal(600, 200, n_per_class).clip(50),
            "mean_packet_size": np.random.normal(80, 20, n_per_class).clip(40),
            "std_packet_size": np.random.exponential(15, n_per_class),
            "min_packet_size": np.random.uniform(40, 60, n_per_class),
            "max_packet_size": np.random.normal(300, 100, n_per_class).clip(100, 600),
            "flow_duration_sec": np.random.exponential(200, n_per_class),
            "mean_inter_arrival_time": np.random.exponential(3.0, n_per_class),
            "std_inter_arrival_time": np.random.exponential(2.0, n_per_class),
            "syn_count": np.random.poisson(1, n_per_class),
            "ack_count": np.random.poisson(35, n_per_class),
            "fin_count": np.random.poisson(1, n_per_class),
            "rst_count": np.zeros(n_per_class),
            "psh_count": np.random.poisson(30, n_per_class),
            "urg_count": np.zeros(n_per_class),
            "mean_ttl": np.random.normal(128, 5, n_per_class).clip(1, 255),
            "mean_window_size": np.random.normal(35000, 5000, n_per_class).clip(0),
            "payload_bytes_total": np.random.normal(400, 150, n_per_class).clip(0),
            "protocol_encoded": np.zeros(n_per_class),
        })

    def normal_dns():
        return pd.DataFrame({
            "packet_count": np.random.poisson(5, n_per_class),
            "total_bytes": np.random.normal(400, 150, n_per_class).clip(50),
            "mean_packet_size": np.random.normal(80, 20, n_per_class).clip(40),
            "std_packet_size": np.random.exponential(10, n_per_class),
            "min_packet_size": np.random.uniform(40, 60, n_per_class),
            "max_packet_size": np.random.normal(200, 50, n_per_class).clip(80, 400),
            "flow_duration_sec": np.random.exponential(5, n_per_class),
            "mean_inter_arrival_time": np.random.exponential(0.1, n_per_class),
            "std_inter_arrival_time": np.random.exponential(0.05, n_per_class),
            "syn_count": np.zeros(n_per_class),
            "ack_count": np.zeros(n_per_class),
            "fin_count": np.zeros(n_per_class),
            "rst_count": np.zeros(n_per_class),
            "psh_count": np.zeros(n_per_class),
            "urg_count": np.zeros(n_per_class),
            "mean_ttl": np.random.normal(64, 5, n_per_class).clip(1, 255),
            "mean_window_size": np.zeros(n_per_class),
            "payload_bytes_total": np.random.normal(300, 100, n_per_class).clip(0),
            "protocol_encoded": np.ones(n_per_class),
        })

    def syn_flood():
        return pd.DataFrame({
            "packet_count": np.random.poisson(800, n_per_class),
            "total_bytes": np.random.normal(60000, 15000, n_per_class).clip(1000),
            "mean_packet_size": np.random.normal(60, 10, n_per_class).clip(40),
            "std_packet_size": np.random.exponential(5, n_per_class),
            "min_packet_size": np.random.uniform(40, 50, n_per_class),
            "max_packet_size": np.random.normal(80, 20, n_per_class).clip(60, 200),
            "flow_duration_sec": np.random.exponential(2, n_per_class),
            "mean_inter_arrival_time": np.random.exponential(0.001, n_per_class),
            "std_inter_arrival_time": np.random.exponential(0.0005, n_per_class),
            "syn_count": np.random.poisson(700, n_per_class),
            "ack_count": np.random.poisson(5, n_per_class),
            "fin_count": np.zeros(n_per_class),
            "rst_count": np.zeros(n_per_class),
            "psh_count": np.zeros(n_per_class),
            "urg_count": np.zeros(n_per_class),
            "mean_ttl": np.random.normal(64, 15, n_per_class).clip(1, 255),
            "mean_window_size": np.random.normal(1024, 512, n_per_class).clip(0),
            "payload_bytes_total": np.random.normal(100, 50, n_per_class).clip(0),
            "protocol_encoded": np.zeros(n_per_class),
        })

    def port_scan():
        return pd.DataFrame({
            "packet_count": np.random.poisson(300, n_per_class),
            "total_bytes": np.random.normal(25000, 8000, n_per_class).clip(500),
            "mean_packet_size": np.random.normal(60, 10, n_per_class).clip(40),
            "std_packet_size": np.random.exponential(10, n_per_class),
            "min_packet_size": np.random.uniform(40, 60, n_per_class),
            "max_packet_size": np.random.normal(100, 30, n_per_class).clip(60, 300),
            "flow_duration_sec": np.random.exponential(10, n_per_class),
            "mean_inter_arrival_time": np.random.exponential(0.01, n_per_class),
            "std_inter_arrival_time": np.random.exponential(0.005, n_per_class),
            "syn_count": np.random.poisson(250, n_per_class),
            "ack_count": np.random.poisson(20, n_per_class),
            "fin_count": np.random.poisson(5, n_per_class),
            "rst_count": np.random.poisson(30, n_per_class),
            "psh_count": np.zeros(n_per_class),
            "urg_count": np.zeros(n_per_class),
            "mean_ttl": np.random.normal(128, 20, n_per_class).clip(1, 255),
            "mean_window_size": np.random.normal(65535, 1000, n_per_class).clip(0),
            "payload_bytes_total": np.random.normal(50, 20, n_per_class).clip(0),
            "protocol_encoded": np.zeros(n_per_class),
        })

    def ddos():
        return pd.DataFrame({
            "packet_count": np.random.poisson(2000, n_per_class),
            "total_bytes": np.random.normal(200000, 50000, n_per_class).clip(5000),
            "mean_packet_size": np.random.normal(100, 30, n_per_class).clip(40),
            "std_packet_size": np.random.exponential(40, n_per_class),
            "min_packet_size": np.random.uniform(40, 60, n_per_class),
            "max_packet_size": np.random.normal(800, 300, n_per_class).clip(200, 1500),
            "flow_duration_sec": np.random.exponential(30, n_per_class),
            "mean_inter_arrival_time": np.random.exponential(0.0005, n_per_class),
            "std_inter_arrival_time": np.random.exponential(0.0002, n_per_class),
            "syn_count": np.random.poisson(1000, n_per_class),
            "ack_count": np.random.poisson(500, n_per_class),
            "fin_count": np.random.poisson(50, n_per_class),
            "rst_count": np.random.poisson(100, n_per_class),
            "psh_count": np.random.poisson(200, n_per_class),
            "urg_count": np.random.poisson(10, n_per_class),
            "mean_ttl": np.random.normal(64, 20, n_per_class).clip(1, 255),
            "mean_window_size": np.random.normal(512, 256, n_per_class).clip(0),
            "payload_bytes_total": np.random.normal(100000, 30000, n_per_class).clip(0),
            "protocol_encoded": np.random.choice([0, 1, 2], n_per_class),
        })

    normal = pd.concat([
        normal_http(),
        normal_ssh(),
        normal_dns(),
    ], ignore_index=True)

    anomaly = pd.concat([
        syn_flood(),
        port_scan(),
        ddos(),
    ], ignore_index=True)

    X = pd.concat([normal, anomaly], ignore_index=True)
    y = np.array([0] * len(normal) + [1] * len(anomaly))

    return X, y


def train_models(
    X: pd.DataFrame,
    y: np.ndarray,
    model_dir: str = "models",
) -> Tuple[RandomForestClassifier, MLPClassifier, IsolationForest, StandardScaler]:
    Path(model_dir).mkdir(parents=True, exist_ok=True)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_pred)

    mlp_model = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        solver="adam",
        max_iter=500,
        random_state=42,
        early_stopping=True,
    )
    mlp_model.fit(X_train, y_train)
    mlp_pred = mlp_model.predict(X_test)
    mlp_acc = accuracy_score(y_test, mlp_pred)

    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42,
    )
    iso_forest.fit(X_train)
    iso_pred = iso_forest.predict(X_test)
    iso_pred = np.where(iso_pred == -1, 1, 0)
    iso_acc = accuracy_score(y_test, iso_pred)

    with open(f"{model_dir}/training_report.txt", "w", encoding="utf-8") as f:
        f.write("=== IDS Model Training Report ===\n\n")
        f.write(f"Total samples: {len(X)}\n")
        f.write(f"  Normal: {sum(y == 0)} (HTTP + SSH + DNS)\n")
        f.write(f"  Anomaly: {sum(y == 1)} (SYN Flood + Port Scan + DDoS)\n")
        f.write(f"Training samples: {len(X_train)}\n")
        f.write(f"Test samples: {len(X_test)}\n\n")
        f.write(f"Random Forest Accuracy: {rf_acc:.4f}\n")
        f.write(classification_report(y_test, rf_pred, target_names=["Normal", "Anomaly"]))
        f.write("\n")
        f.write(f"MLP Neural Network Accuracy: {mlp_acc:.4f}\n")
        f.write(classification_report(y_test, mlp_pred, target_names=["Normal", "Anomaly"]))
        f.write("\n")
        f.write(f"Isolation Forest Accuracy: {iso_acc:.4f}\n")
        f.write(classification_report(y_test, iso_pred, target_names=["Normal", "Anomaly"]))

    joblib.dump(rf_model, f"{model_dir}/random_forest.pkl")
    joblib.dump(mlp_model, f"{model_dir}/mlp_neural.pkl")
    joblib.dump(iso_forest, f"{model_dir}/isolation_forest.pkl")
    joblib.dump(scaler, f"{model_dir}/scaler.pkl")

    print(f"Models saved to {model_dir}/")
    print(f"Random Forest Accuracy: {rf_acc:.4f}")
    print(f"MLP Neural Network Accuracy: {mlp_acc:.4f}")
    print(f"Isolation Forest Accuracy: {iso_acc:.4f}")

    return rf_model, mlp_model, iso_forest, scaler


def load_models(model_dir: str = "models"):
    return (
        joblib.load(f"{model_dir}/random_forest.pkl"),
        joblib.load(f"{model_dir}/mlp_neural.pkl"),
        joblib.load(f"{model_dir}/isolation_forest.pkl"),
        joblib.load(f"{model_dir}/scaler.pkl"),
    )
