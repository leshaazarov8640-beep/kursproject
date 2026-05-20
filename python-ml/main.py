import argparse
import json
import sys

from features.parser import load_flows_from_json, load_flows_from_stdin, prepare_features
from model.train import generate_training_data, train_models
from model.predict import IDSPredictor
from alerts.notifier import AlertNotifier
from visualization.dashboard import IDSVisualizer


def cmd_train(args):
    print("Generating training data (HTTP, SSH, DNS, SYN Flood, Port Scan, DDoS)...")
    X, y = generate_training_data(n_per_class=args.samples)
    print(f"Generated {len(X)} samples ({sum(y == 0)} normal, {sum(y == 1)} anomaly)")
    train_models(X, y, model_dir=args.model_dir)
    print("Training complete!")


def cmd_predict(args):
    predictor = IDSPredictor(model_dir=args.model_dir)
    notifier = AlertNotifier()
    visualizer = IDSVisualizer()

    if args.file:
        flows = load_flows_from_json(args.file)
    else:
        flows = load_flows_from_stdin(sys.stdin.read())

    if flows.empty:
        print("No flows to analyze")
        return

    features = prepare_features(flows)
    predictions = predictor.predict(features)

    print(json.dumps(predictions, indent=2, ensure_ascii=False))

    if predictions["anomaly_count"] > 0:
        for i, result in enumerate(predictions["results"]):
            if result["is_anomaly"]:
                alert_data = flows.iloc[i].to_dict()
                alert_data["anomaly_score"] = result["anomaly_score"]
                notifier.send_alert(alert_data)

    visualizer.plot_feature_bar_chart(flows, predictions)
    visualizer.plot_anomaly_scores(predictions)
    visualizer.plot_model_comparison(predictions)


def cmd_analyze(args):
    predictor = IDSPredictor(model_dir=args.model_dir)
    notifier = AlertNotifier()
    visualizer = IDSVisualizer()

    flows = load_flows_from_json(args.file)
    if flows.empty:
        print("No flows to analyze")
        return

    features = prepare_features(flows)
    predictions = predictor.predict(features)

    print(json.dumps(predictions, indent=2, ensure_ascii=False))

    if predictions["anomaly_count"] > 0:
        for i, result in enumerate(predictions["results"]):
            if result["is_anomaly"]:
                alert_data = flows.iloc[i].to_dict()
                alert_data["anomaly_score"] = result["anomaly_score"]
                notifier.send_alert(alert_data)

    visualizer.plot_feature_bar_chart(flows, predictions)
    visualizer.plot_anomaly_scores(predictions)
    visualizer.plot_model_comparison(predictions)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(predictions, f, indent=2, ensure_ascii=False)


def cmd_api(args):
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI(title="IDS ML Service", version="1.0.0")
    predictor = IDSPredictor(model_dir=args.model_dir)

    @app.post("/predict")
    async def predict_flows(data: dict):
        import pandas as pd
        flows = pd.json_normalize(data.get("flows", []))
        if flows.empty:
            return {"error": "No flows provided"}
        features = prepare_features(flows)
        return predictor.predict(features)

    @app.get("/health")
    async def health():
        return {"status": "ok", "model": "IDS v1.0"}

    uvicorn.run(app, host=args.host, port=args.port)


def main():
    parser = argparse.ArgumentParser(description="IDS - Intrusion Detection System")
    subparsers = parser.add_subparsers(dest="command")

    train_parser = subparsers.add_parser("train", help="Train ML models")
    train_parser.add_argument("--samples", type=int, default=300, help="Samples per traffic type")
    train_parser.add_argument("--model-dir", default="models")

    predict_parser = subparsers.add_parser("predict", help="Predict anomalies from stdin or file")
    predict_parser.add_argument("--file", help="JSON file with flow features")
    predict_parser.add_argument("--model-dir", default="models")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze JSON file with flow features")
    analyze_parser.add_argument("file", help="JSON file with flow features")
    analyze_parser.add_argument("--output", help="Output predictions JSON file")
    analyze_parser.add_argument("--model-dir", default="models")

    api_parser = subparsers.add_parser("api", help="Start FastAPI server")
    api_parser.add_argument("--host", default="0.0.0.0")
    api_parser.add_argument("--port", type=int, default=8000)
    api_parser.add_argument("--model-dir", default="models")

    args = parser.parse_args()
    if args.command == "train":
        cmd_train(args)
    elif args.command == "predict":
        cmd_predict(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "api":
        cmd_api(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
