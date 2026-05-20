import argparse
import json
import os
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
    import json
    from datetime import datetime
    from fastapi import FastAPI, Query
    import uvicorn
    import pandas as pd
    from pathlib import Path

    HISTORY_FILE = Path("api_history.json")
    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history.extend(json.load(f))

    def save_history():
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[-100:], f, indent=2, ensure_ascii=False)

    app = FastAPI(title="IDS — система обнаружения вторжений", version="1.0.0",
                  description="Вариант 3. Python + scikit-learn + Go + PCAP")
    predictor = IDSPredictor(model_dir=args.model_dir)

    @app.get("/")
    async def root():
        return {
            "service": "IDS — Intrusion Detection System",
            "version": "1.0.0",
            "variant": 3,
            "endpoints": {
                "GET  /": "информация о сервисе",
                "GET  /health": "проверка работоспособности",
                "POST /predict": "классификация потоков трафика (сохраняется в историю)",
                "GET  /history": "история всех запросов",
                "GET  /history/{id}": "конкретный запрос из истории",
                "POST /train": "переобучить модели",
                "GET  /visualize": "сгенерировать графики из истории",
                "GET  /model": "информация о моделях",
                "GET  /stats": "статистика детектирования",
                "POST /clear-history": "очистить историю",
            }
        }

    @app.get("/health")
    async def health():
        return {"status": "ok", "model": "IDS v1.0", "variant": 3}

    @app.post("/predict")
    async def predict_flows(data: dict):
        flows = pd.json_normalize(data.get("flows", []))
        if flows.empty:
            return {"error": "No flows provided"}
        features = prepare_features(flows)
        result = predictor.predict(features)
        entry = {
            "id": len(history) + 1,
            "timestamp": datetime.now().isoformat(),
            "input": data.get("flows", []),
            "result": result,
        }
        history.append(entry)
        save_history()
        return result

    @app.get("/history")
    async def get_history(limit: int = Query(20, description="Last N records")):
        return {"total": len(history), "records": history[-limit:]}

    @app.get("/history/{item_id}")
    async def get_history_item(item_id: int):
        for item in reversed(history):
            if item["id"] == item_id:
                return item
        return {"error": "Not found"}

    @app.post("/clear-history")
    async def clear_history():
        history.clear()
        save_history()
        return {"status": "ok", "message": "History cleared"}

    @app.get("/visualize")
    async def visualize():
        from visualization.dashboard import IDSVisualizer
        if not history:
            return {"error": "No data in history"}
        last = history[-1]
        flows = pd.json_normalize(last["input"])
        visualizer = IDSVisualizer()
        visualizer.plot_feature_bar_chart(flows, last["result"])
        visualizer.plot_anomaly_scores(last["result"])
        visualizer.plot_model_comparison(last["result"])
        return {
            "status": "ok",
            "message": "Graphs generated from last request",
            "files": [
                "visualizations/feature_comparison.png",
                "visualizations/anomaly_scores.png",
                "visualizations/model_comparison.png",
            ]
        }

    @app.post("/train")
    async def train_endpoint(samples: int = Query(200, description="Samples per traffic type")):
        from model.train import generate_training_data, train_models
        X, y = generate_training_data(n_per_class=samples)
        train_models(X, y, model_dir=args.model_dir)
        return {
            "status": "ok",
            "samples": len(X),
            "normal": int(sum(y == 0)),
            "anomaly": int(sum(y == 1)),
            "message": "Models retrained successfully"
        }

    @app.get("/model")
    async def model_info():
        return {
            "models": [
                {"name": "Random Forest", "params": "100 trees, max_depth=15"},
                {"name": "MLP Neural Network", "params": "layers=[64, 32], adam, relu"},
                {"name": "Isolation Forest", "params": "100 estimators, contamination=0.1"},
            ],
            "ensemble": "Majority voting (>= 2 models = anomaly)",
            "features_count": 19,
            "features": [
                "packet_count", "total_bytes", "mean_packet_size",
                "syn_count", "ack_count", "rst_count",
                "flow_duration_sec", "mean_ttl", "mean_window_size",
            ]
        }

    @app.get("/stats")
    async def stats():
        return {
            "total_models": 3,
            "total_requests_in_history": len(history),
            "detection_method": "ensemble_voting",
            "threshold": ">= 2 models detect anomaly",
            "traffic_types": {
                "normal": ["HTTP", "HTTPS", "SSH", "DNS", "FTP", "SMTP"],
                "anomaly": ["SYN Flood", "Port Scan", "DDoS", "DNS Amplification"],
            }
        }

    uvicorn.run(app, host=args.host, port=args.port)


def main():
    parser = argparse.ArgumentParser(description="IDS - Intrusion Detection System")
    parser.add_argument("--telegram-token", help="Telegram bot token for alerts")
    parser.add_argument("--slack-webhook", help="Slack webhook URL for alerts")
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
    if args.telegram_token:
        os.environ["TELEGRAM_BOT_TOKEN"] = args.telegram_token
    if args.slack_webhook:
        os.environ["SLACK_WEBHOOK_URL"] = args.slack_webhook
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
