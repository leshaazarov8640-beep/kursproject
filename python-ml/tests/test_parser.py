import json
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from features.parser import load_flows_from_json, load_flows_from_stdin, prepare_features


class TestLoadFlows:
    def test_load_from_json_list(self):
        df = load_flows_from_json("test_data.json")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_load_from_json_single_dict(self, tmp_path):
        data = {"packet_count": 10, "protocol": "TCP"}
        f = tmp_path / "single.json"
        with open(f, "w") as fp:
            json.dump(data, fp)
        df = load_flows_from_json(str(f))
        assert len(df) == 1
        assert df["packet_count"].iloc[0] == 10

    def test_load_from_stdin_single_line(self):
        line = '{"packet_count": 5, "protocol": "UDP"}'
        df = load_flows_from_stdin(line)
        assert len(df) == 1
        assert df["protocol"].iloc[0] == "UDP"

    def test_load_from_stdin_multiple_lines(self):
        lines = '{"packet_count": 1}\n{"packet_count": 2}\n'
        df = load_flows_from_stdin(lines)
        assert len(df) == 2

    def test_load_from_stdin_empty(self):
        df = load_flows_from_stdin("")
        assert df.empty

    def test_load_from_stdin_blank_lines(self):
        lines = '{"a": 1}\n\n{"a": 2}\n  \n'
        df = load_flows_from_stdin(lines)
        assert len(df) == 2


class TestPrepareFeatures:
    def test_protocol_encoding_tcp(self):
        df = pd.DataFrame({"protocol": ["TCP"], "packet_count": [1]})
        result = prepare_features(df)
        assert result["protocol_encoded"].iloc[0] == 0

    def test_protocol_encoding_udp(self):
        df = pd.DataFrame({"protocol": ["UDP"], "packet_count": [1]})
        result = prepare_features(df)
        assert result["protocol_encoded"].iloc[0] == 1

    def test_protocol_encoding_icmp(self):
        df = pd.DataFrame({"protocol": ["ICMP"], "packet_count": [1]})
        result = prepare_features(df)
        assert result["protocol_encoded"].iloc[0] == 2

    def test_protocol_encoding_other(self):
        df = pd.DataFrame({"protocol": ["IGMP"], "packet_count": [1]})
        result = prepare_features(df)
        assert result["protocol_encoded"].iloc[0] == 3

    def test_missing_columns_default_to_zero(self):
        df = pd.DataFrame({"packet_count": [5]})
        result = prepare_features(df)
        assert "total_bytes" in result.columns
        assert result["total_bytes"].iloc[0] == 0.0
        assert "syn_count" in result.columns
        assert result["syn_count"].iloc[0] == 0.0

    def test_no_protocol_column(self):
        df = pd.DataFrame({"packet_count": [5], "total_bytes": [100]})
        result = prepare_features(df)
        assert "protocol_encoded" not in result.columns or result["protocol_encoded"].iloc[0] == 0.0

    def test_all_expected_columns_present(self):
        df = pd.DataFrame({"protocol": ["TCP"], "packet_count": [1]})
        result = prepare_features(df)
        expected = [
            "packet_count", "total_bytes", "mean_packet_size", "std_packet_size",
            "min_packet_size", "max_packet_size", "flow_duration_sec",
            "mean_inter_arrival_time", "std_inter_arrival_time",
            "syn_count", "ack_count", "fin_count", "rst_count", "psh_count", "urg_count",
            "mean_ttl", "mean_window_size", "payload_bytes_total",
        ]
        for col in expected:
            assert col in result.columns, f"Missing column: {col}"

    def test_fillna_applied(self):
        df = pd.DataFrame({"packet_count": [1], "mean_ttl": [None]})
        result = prepare_features(df)
        assert result["mean_ttl"].iloc[0] == 0.0

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = prepare_features(df)
        assert result.empty or len(result) == 0
