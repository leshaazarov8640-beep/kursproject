from pathlib import Path
import pandas as pd
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from visualization.dashboard import IDSVisualizer


class TestVisualization:
    def test_creates_output_directory(self, tmp_path):
        out = tmp_path / "viz"
        v = IDSVisualizer(output_dir=str(out))
        assert out.exists()

    def test_plot_feature_bar_chart(self, tmp_path):
        out = tmp_path / "viz"
        v = IDSVisualizer(output_dir=str(out))
        flows = pd.DataFrame({
            "packet_count": [10, 20],
            "syn_count": [1, 5],
            "total_bytes": [100, 200],
            "mean_packet_size": [50, 60],
        })
        predictions = {
            "results": [
                {"is_anomaly": False, "anomaly_score": 0.1,
                 "rf_prediction": 0, "mlp_prediction": 0, "iso_forest_prediction": 0,
                 "rf_confidence": 0.9, "mlp_confidence": 0.9},
                {"is_anomaly": True, "anomaly_score": 0.9,
                 "rf_prediction": 1, "mlp_prediction": 1, "iso_forest_prediction": 1,
                 "rf_confidence": 0.9, "mlp_confidence": 0.9},
            ]
        }
        v.plot_feature_bar_chart(flows, predictions)
        assert (out / "feature_comparison.png").exists()

    def test_plot_anomaly_scores(self, tmp_path):
        out = tmp_path / "viz"
        v = IDSVisualizer(output_dir=str(out))
        predictions = {
            "total_flows": 2,
            "normal_count": 1,
            "anomaly_count": 1,
            "results": [
                {"is_anomaly": False, "anomaly_score": 0.1,
                 "rf_prediction": 0, "mlp_prediction": 0, "iso_forest_prediction": 0,
                 "rf_confidence": 0.9, "mlp_confidence": 0.9},
                {"is_anomaly": True, "anomaly_score": 0.9,
                 "rf_prediction": 1, "mlp_prediction": 1, "iso_forest_prediction": 1,
                 "rf_confidence": 0.9, "mlp_confidence": 0.9},
            ]
        }
        v.plot_anomaly_scores(predictions)
        assert (out / "anomaly_scores.png").exists()

    def test_plot_model_comparison(self, tmp_path):
        out = tmp_path / "viz"
        v = IDSVisualizer(output_dir=str(out))
        predictions = {
            "total_flows": 2,
            "normal_count": 1,
            "anomaly_count": 1,
            "results": [
                {"is_anomaly": False, "anomaly_score": 0.1,
                 "rf_prediction": 0, "mlp_prediction": 0, "iso_forest_prediction": 0,
                 "rf_confidence": 0.9, "mlp_confidence": 0.9},
                {"is_anomaly": True, "anomaly_score": 0.9,
                 "rf_prediction": 1, "mlp_prediction": 1, "iso_forest_prediction": 1,
                 "rf_confidence": 0.9, "mlp_confidence": 0.9},
            ]
        }
        v.plot_model_comparison(predictions)
        assert (out / "model_comparison.png").exists()

    def test_plot_empty_flows(self, tmp_path):
        out = tmp_path / "viz"
        v = IDSVisualizer(output_dir=str(out))
        v.plot_feature_bar_chart(pd.DataFrame(), {})
        v.plot_anomaly_scores({})
        v.plot_model_comparison({})

    def test_plot_with_no_results_key(self, tmp_path):
        out = tmp_path / "viz"
        v = IDSVisualizer(output_dir=str(out))
        v.plot_feature_bar_chart(pd.DataFrame({"a": [1]}), {"no_results": []})
        v.plot_anomaly_scores({"total_flows": 0})
        v.plot_model_comparison({"total_flows": 0})
