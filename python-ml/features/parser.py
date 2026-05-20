import json
import pandas as pd
import numpy as np


def load_flows_from_json(filepath: str) -> pd.DataFrame:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return pd.json_normalize(data)
    return pd.DataFrame([data])


def load_flows_from_stdin(json_lines: str) -> pd.DataFrame:
    records = []
    for line in json_lines.strip().split("\n"):
        if line.strip():
            records.append(json.loads(line))
    if records:
        return pd.json_normalize(records)
    return pd.DataFrame()


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    features = df.copy()

    if "src_port" in features.columns:
        features["src_port"] = features["src_port"].astype(int)
    if "dst_port" in features.columns:
        features["dst_port"] = features["dst_port"].astype(int)

    if "protocol" in features.columns:
        features["protocol_encoded"] = features["protocol"].map(
            {"TCP": 0, "UDP": 1, "ICMP": 2, "OTHER": 3}
        ).fillna(3)

    feature_cols = [
        "packet_count", "total_bytes", "mean_packet_size", "std_packet_size",
        "min_packet_size", "max_packet_size", "flow_duration_sec",
        "mean_inter_arrival_time", "std_inter_arrival_time",
        "syn_count", "ack_count", "fin_count", "rst_count", "psh_count", "urg_count",
        "mean_ttl", "mean_window_size", "payload_bytes_total",
    ]

    if "protocol_encoded" in features.columns:
        feature_cols.append("protocol_encoded")

    for col in feature_cols:
        if col not in features.columns:
            features[col] = 0.0

    return features[feature_cols].fillna(0)
