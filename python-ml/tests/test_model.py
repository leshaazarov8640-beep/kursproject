import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from model.train import generate_training_data, train_models
from model.predict import IDSPredictor
from features.parser import prepare_features


class TestIDSModel:
    def test_generate_training_data(self):
        X, y = generate_training_data(n_per_class=10)
        assert len(X) >= 50
        assert len(y) == len(X)
        assert 0 in y and 1 in y

    def test_train_models(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            X, y = generate_training_data(n_per_class=20)
            rf, mlp, iso, scaler = train_models(X, y, model_dir=tmpdir)
            assert rf is not None
            assert mlp is not None
            assert iso is not None
            assert scaler is not None
            for name in ["random_forest.pkl", "mlp_neural.pkl",
                         "isolation_forest.pkl", "scaler.pkl"]:
                assert Path(f"{tmpdir}/{name}").exists()

    def test_predict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            X, y = generate_training_data(n_per_class=20)
            train_models(X, y, model_dir=tmpdir)

            predictor = IDSPredictor(model_dir=tmpdir)
            test_df = pd.DataFrame({
                "packet_count": [25, 800],
                "total_bytes": [3000, 60000],
                "mean_packet_size": [350, 60],
                "std_packet_size": [50, 5],
                "min_packet_size": [40, 40],
                "max_packet_size": [1400, 80],
                "flow_duration_sec": [25, 2],
                "mean_inter_arrival_time": [0.8, 0.001],
                "std_inter_arrival_time": [0.5, 0.0005],
                "syn_count": [2, 700],
                "ack_count": [20, 5],
                "fin_count": [2, 0],
                "rst_count": [0, 0],
                "psh_count": [8, 0],
                "urg_count": [0, 0],
                "mean_ttl": [120, 64],
                "mean_window_size": [65000, 1024],
                "payload_bytes_total": [2000, 100],
                "protocol_encoded": [0, 0],
            })
            result = predictor.predict(test_df)
            assert result["total_flows"] == 2
            assert result["results"][1]["is_anomaly"] == True

    def test_prepare_features(self):
        df = pd.DataFrame({
            "packet_count": [10],
            "total_bytes": [1000],
            "protocol": ["TCP"],
        })
        prepared = prepare_features(df)
        assert "protocol_encoded" in prepared.columns
        assert prepared["protocol_encoded"].iloc[0] == 0

    def test_format_alert(self):
        from alerts.notifier import AlertNotifier
        notifier = AlertNotifier()
        alert_data = {
            "src_ip": "10.0.0.1",
            "src_port": 12345,
            "dst_ip": "192.168.1.1",
            "dst_port": 80,
            "protocol": "TCP",
            "anomaly_score": 0.95,
            "packet_count": 500,
            "total_bytes": 100000,
            "flow_duration_sec": 1.5,
            "syn_count": 50,
            "rst_count": 3,
        }
        message = notifier.format_alert_message(alert_data)
        assert "IDS ALERT" in message
        assert "SYN flood" in message
