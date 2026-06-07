import json
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from model.train import generate_training_data, train_models, load_models
from model.predict import IDSPredictor
from features.parser import prepare_features


class TestFullPipeline:
    def test_generate_train_predict_cycle(self):
        X, y = generate_training_data(n_per_class=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            train_models(X, y, model_dir=tmpdir)
            predictor = IDSPredictor(model_dir=tmpdir)
            result = predictor.predict(X.head(2))
            assert result["total_flows"] == 2
            assert "results" in result
            assert "anomaly_count" in result
            assert "normal_count" in result

    def test_predict_normal_flow_classified_correctly(self):
        X, y = generate_training_data(n_per_class=20)
        with tempfile.TemporaryDirectory() as tmpdir:
            train_models(X, y, model_dir=tmpdir)
            predictor = IDSPredictor(model_dir=tmpdir)
            normal_flow = pd.DataFrame([{
                "packet_count": 25, "total_bytes": 3000, "mean_packet_size": 350,
                "std_packet_size": 50, "min_packet_size": 40, "max_packet_size": 1400,
                "flow_duration_sec": 25, "mean_inter_arrival_time": 0.8,
                "std_inter_arrival_time": 0.5, "syn_count": 2, "ack_count": 20,
                "fin_count": 2, "rst_count": 0, "psh_count": 8, "urg_count": 0,
                "mean_ttl": 120, "mean_window_size": 65000, "payload_bytes_total": 2000,
                "protocol_encoded": 0,
            }])
            result = predictor.predict(normal_flow)
            assert result["results"][0]["is_anomaly"] is False

    def test_predict_anomaly_flow_classified_correctly(self):
        X, y = generate_training_data(n_per_class=20)
        with tempfile.TemporaryDirectory() as tmpdir:
            train_models(X, y, model_dir=tmpdir)
            predictor = IDSPredictor(model_dir=tmpdir)
            attack_flow = pd.DataFrame([{
                "packet_count": 800, "total_bytes": 60000, "mean_packet_size": 60,
                "std_packet_size": 5, "min_packet_size": 40, "max_packet_size": 80,
                "flow_duration_sec": 2, "mean_inter_arrival_time": 0.001,
                "std_inter_arrival_time": 0.0005, "syn_count": 700, "ack_count": 5,
                "fin_count": 0, "rst_count": 0, "psh_count": 0, "urg_count": 0,
                "mean_ttl": 64, "mean_window_size": 1024, "payload_bytes_total": 100,
                "protocol_encoded": 0,
            }])
            result = predictor.predict(attack_flow)
            assert result["results"][0]["is_anomaly"] is True


class TestEnsembleVoting:
    def test_all_models_agree_normal(self):
        X, y = generate_training_data(n_per_class=20)
        with tempfile.TemporaryDirectory() as tmpdir:
            train_models(X, y, model_dir=tmpdir)
            predictor = IDSPredictor(model_dir=tmpdir)
            features = pd.DataFrame([{
                "packet_count": 25, "total_bytes": 3000, "mean_packet_size": 350,
                "std_packet_size": 50, "min_packet_size": 40, "max_packet_size": 1400,
                "flow_duration_sec": 25, "mean_inter_arrival_time": 0.8,
                "std_inter_arrival_time": 0.5, "syn_count": 2, "ack_count": 20,
                "fin_count": 2, "rst_count": 0, "psh_count": 8, "urg_count": 0,
                "mean_ttl": 120, "mean_window_size": 65000, "payload_bytes_total": 2000,
                "protocol_encoded": 0,
            }])
            result = predictor.predict(features)
            r = result["results"][0]
            votes = [r["rf_prediction"], r["mlp_prediction"], r["iso_forest_prediction"]]
            assert sum(votes) == 0

    def test_all_models_agree_anomaly(self):
        X, y = generate_training_data(n_per_class=20)
        with tempfile.TemporaryDirectory() as tmpdir:
            train_models(X, y, model_dir=tmpdir)
            predictor = IDSPredictor(model_dir=tmpdir)
            features = pd.DataFrame([{
                "packet_count": 2000, "total_bytes": 200000, "mean_packet_size": 100,
                "std_packet_size": 40, "min_packet_size": 40, "max_packet_size": 800,
                "flow_duration_sec": 30, "mean_inter_arrival_time": 0.0005,
                "std_inter_arrival_time": 0.0002, "syn_count": 1000, "ack_count": 500,
                "fin_count": 50, "rst_count": 100, "psh_count": 200, "urg_count": 10,
                "mean_ttl": 64, "mean_window_size": 512, "payload_bytes_total": 100000,
                "protocol_encoded": 0,
            }])
            result = predictor.predict(features)
            r = result["results"][0]
            assert r["is_anomaly"] is True

    def test_result_structure(self):
        X, y = generate_training_data(n_per_class=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            train_models(X, y, model_dir=tmpdir)
            predictor = IDSPredictor(model_dir=tmpdir)
            features = pd.DataFrame([{"packet_count": 1, "total_bytes": 1, "mean_packet_size": 1,
                 "std_packet_size": 1, "min_packet_size": 1, "max_packet_size": 1,
                 "flow_duration_sec": 1, "mean_inter_arrival_time": 1,
                 "std_inter_arrival_time": 1, "syn_count": 1, "ack_count": 1,
                 "fin_count": 1, "rst_count": 1, "psh_count": 1, "urg_count": 1,
                 "mean_ttl": 1, "mean_window_size": 1, "payload_bytes_total": 1,
                 "protocol_encoded": 0}])
            result = predictor.predict(features)
            assert "total_flows" in result
            assert "anomaly_count" in result
            assert "normal_count" in result
            assert "results" in result
            r = result["results"][0]
            assert "index" in r
            assert "is_anomaly" in r
            assert "anomaly_score" in r
            assert "rf_prediction" in r
            assert "mlp_prediction" in r
            assert "iso_forest_prediction" in r
            assert "rf_confidence" in r
            assert "mlp_confidence" in r


class TestModelTraining:
    def test_training_report_created(self):
        X, y = generate_training_data(n_per_class=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            train_models(X, y, model_dir=tmpdir)
            report = Path(tmpdir) / "training_report.txt"
            assert report.exists()
            content = report.read_text(encoding="utf-8")
            assert "Random Forest" in content
            assert "MLP Neural Network" in content
            assert "Isolation Forest" in content

    def test_load_models_returns_all_components(self):
        X, y = generate_training_data(n_per_class=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            train_models(X, y, model_dir=tmpdir)
            rf, mlp, iso, scaler = load_models(model_dir=tmpdir)
            assert hasattr(rf, "predict")
            assert hasattr(mlp, "predict")
            assert hasattr(iso, "predict")
            assert hasattr(scaler, "transform")

    def test_predict_with_missing_feature_columns(self):
        X, y = generate_training_data(n_per_class=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            train_models(X, y, model_dir=tmpdir)
            predictor = IDSPredictor(model_dir=tmpdir)
            incomplete = pd.DataFrame({"packet_count": [10]})
            result = predictor.predict(incomplete)
            assert result["total_flows"] == 1

    def test_multiple_flows_in_single_call(self):
        X, y = generate_training_data(n_per_class=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            train_models(X, y, model_dir=tmpdir)
            predictor = IDSPredictor(model_dir=tmpdir)
            flows = pd.DataFrame([{"packet_count": 1, "total_bytes": 1, "mean_packet_size": 1,
                 "std_packet_size": 1, "min_packet_size": 1, "max_packet_size": 1,
                 "flow_duration_sec": 1, "mean_inter_arrival_time": 1,
                 "std_inter_arrival_time": 1, "syn_count": 1, "ack_count": 1,
                 "fin_count": 1, "rst_count": 1, "psh_count": 1, "urg_count": 1,
                 "mean_ttl": 1, "mean_window_size": 1, "payload_bytes_total": 1,
                 "protocol_encoded": 0}] * 5)
            result = predictor.predict(flows)
            assert result["total_flows"] == 5
            assert len(result["results"]) == 5
