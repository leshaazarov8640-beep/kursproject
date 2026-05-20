import numpy as np
import pandas as pd
from typing import Dict


class IDSPredictor:
    def __init__(self, model_dir: str = "models"):
        from model.train import load_models
        self.rf_model, self.mlp_model, self.iso_forest, self.scaler = load_models(model_dir)
        self.feature_names = [
            "packet_count", "total_bytes", "mean_packet_size", "std_packet_size",
            "min_packet_size", "max_packet_size", "flow_duration_sec",
            "mean_inter_arrival_time", "std_inter_arrival_time",
            "syn_count", "ack_count", "fin_count", "rst_count", "psh_count", "urg_count",
            "mean_ttl", "mean_window_size", "payload_bytes_total",
            "protocol_encoded",
        ]

    def predict(self, features: pd.DataFrame) -> Dict:
        for col in self.feature_names:
            if col not in features.columns:
                features[col] = 0.0
        X = features[self.feature_names].fillna(0).values
        X_scaled = self.scaler.transform(X)

        rf_pred = self.rf_model.predict(X_scaled)
        rf_prob = self.rf_model.predict_proba(X_scaled)

        mlp_pred = self.mlp_model.predict(X_scaled)
        mlp_prob = self.mlp_model.predict_proba(X_scaled)

        iso_pred = self.iso_forest.predict(X_scaled)
        iso_pred = np.where(iso_pred == -1, 1, 0)

        results = []
        for i in range(len(X)):
            votes = [rf_pred[i], mlp_pred[i], iso_pred[i]]
            final_vote = 1 if sum(votes) >= 2 else 0
            avg_prob = (rf_prob[i][1] + mlp_prob[i][1]) / 2.0

            results.append({
                "index": int(i),
                "is_anomaly": bool(final_vote),
                "anomaly_score": float(avg_prob),
                "rf_prediction": int(rf_pred[i]),
                "mlp_prediction": int(mlp_pred[i]),
                "iso_forest_prediction": int(iso_pred[i]),
                "rf_confidence": float(max(rf_prob[i])),
                "mlp_confidence": float(max(mlp_prob[i])),
            })

        anomaly_count = sum(1 for r in results if r["is_anomaly"])
        return {
            "total_flows": len(results),
            "anomaly_count": anomaly_count,
            "normal_count": len(results) - anomaly_count,
            "results": results,
        }
