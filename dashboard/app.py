import streamlit as st
import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python-ml"))

from model.predict import IDSPredictor
from features.parser import prepare_features
from model.train import generate_training_data, train_models
from visualization.dashboard import IDSVisualizer

st.set_page_config(
    page_title="IDS — система обнаружения вторжений",
    page_icon="",
    layout="wide",
)

st.title("Система обнаружения вторжений (IDS)")
st.markdown("**Вариант 3** | Python + scikit-learn + Go + PCAP | Ансамбль: Random Forest + MLP + Isolation Forest")

@st.cache_resource
def load_predictor():
    model_dir = Path(__file__).parent.parent / "python-ml" / "models"
    if not (model_dir / "random_forest.pkl").exists():
        st.info("Модели не найдены. Выполните обучение на вкладке «Обучение».")
        return None
    try:
        return IDSPredictor(model_dir=str(model_dir))
    except Exception as e:
        st.error(f"Ошибка загрузки моделей: {e}")
        return None

def make_prediction(df):
    predictor = load_predictor()
    if predictor is None:
        return None
    features = prepare_features(df)
    return predictor.predict(features)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Аналитика", "Предсказание", "Пакетный анализ", "Обучение", "О проекте"])

with tab1:
    st.header("Аналитика детектирования")

    col1, col2, col3 = st.columns(3)
    from model.train import load_models
    model_dir = Path(__file__).parent.parent / "python-ml" / "models"
    report_file = model_dir / "training_report.txt"
    rf_acc = mlp_acc = iso_acc = "—"
    if report_file.exists():
        content = report_file.read_text(encoding="utf-8")
        for line in content.split("\n"):
            if "Random Forest Accuracy:" in line:
                rf_acc = line.split(":")[-1].strip()
            elif "MLP Neural Network Accuracy:" in line:
                mlp_acc = line.split(":")[-1].strip()
            elif "Isolation Forest Accuracy:" in line:
                iso_acc = line.split(":")[-1].strip()

    col1.metric("Random Forest", rf_acc)
    col2.metric("MLP Neural Network", mlp_acc)
    col3.metric("Isolation Forest", iso_acc)

    st.markdown("---")
    st.subheader("Визуализации")

    viz_dir = Path(__file__).parent.parent / "python-ml" / "visualizations"
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        img1 = viz_dir / "feature_comparison.png"
        if img1.exists():
            st.image(str(img1), caption="Сравнение признаков по потокам", use_container_width=True)
        else:
            st.info("График feature_comparison.png не найден. Запустите verify.py")

    with col_img2:
        img2 = viz_dir / "anomaly_scores.png"
        if img2.exists():
            st.image(str(img2), caption="Оценка аномальности", use_container_width=True)
        else:
            st.info("График anomaly_scores.png не найден")

    img3 = viz_dir / "model_comparison.png"
    if img3.exists():
        st.image(str(img3), caption="Сравнение моделей", use_container_width=True)

with tab2:
    st.header("Ручной анализ потока")

    with st.form("predict_form"):
        col1, col2 = st.columns(2)
        with col1:
            src_ip = st.text_input("Src IP", "10.0.0.1")
            dst_ip = st.text_input("Dst IP", "192.168.1.1")
            src_port = st.number_input("Src Port", 0, 65535, 12345)
            dst_port = st.number_input("Dst Port", 0, 65535, 80)
            protocol = st.selectbox("Protocol", ["TCP", "UDP", "ICMP"])
            packet_count = st.number_input("Packet Count", 0, 10000, 25)
            total_bytes = st.number_input("Total Bytes", 0, 500000, 3000)
        with col2:
            mean_packet_size = st.number_input("Mean Packet Size", 0.0, 1500.0, 350.0)
            std_packet_size = st.number_input("Std Packet Size", 0.0, 500.0, 45.0)
            min_packet_size = st.number_input("Min Packet Size", 0, 1500, 40)
            max_packet_size = st.number_input("Max Packet Size", 0, 1500, 1400)
            flow_duration = st.number_input("Flow Duration (sec)", 0.0, 1000.0, 10.0)
            syn_count = st.number_input("SYN Count", 0, 5000, 2)
            ack_count = st.number_input("ACK Count", 0, 5000, 18)

        with st.expander("Дополнительные признаки"):
            col3, col4 = st.columns(2)
            with col3:
                fin_count = st.number_input("FIN Count", 0, 1000, 2)
                rst_count = st.number_input("RST Count", 0, 1000, 0)
                psh_count = st.number_input("PSH Count", 0, 1000, 8)
                urg_count = st.number_input("URG Count", 0, 1000, 0)
                mean_ttl = st.number_input("Mean TTL", 0.0, 255.0, 120.0)
            with col4:
                mean_window = st.number_input("Mean Window Size", 0.0, 65535.0, 65000.0)
                payload_bytes = st.number_input("Payload Bytes", 0, 500000, 2000)
                mean_iat = st.number_input("Mean Inter-Arrival Time", 0.0, 10.0, 0.5)
                std_iat = st.number_input("Std Inter-Arrival Time", 0.0, 5.0, 0.3)

        submitted = st.form_submit_button("Анализировать", type="primary")

    if submitted:
        flow = {
            "src_ip": src_ip, "dst_ip": dst_ip,
            "src_port": src_port, "dst_port": dst_port,
            "protocol": protocol,
            "packet_count": packet_count, "total_bytes": total_bytes,
            "mean_packet_size": mean_packet_size, "std_packet_size": std_packet_size,
            "min_packet_size": min_packet_size, "max_packet_size": max_packet_size,
            "flow_duration_sec": flow_duration,
            "mean_inter_arrival_time": mean_iat, "std_inter_arrival_time": std_iat,
            "syn_count": syn_count, "ack_count": ack_count,
            "fin_count": fin_count, "rst_count": rst_count,
            "psh_count": psh_count, "urg_count": urg_count,
            "mean_ttl": mean_ttl, "mean_window_size": mean_window,
            "payload_bytes_total": payload_bytes,
        }
        result = make_prediction(pd.DataFrame([flow]))
        if result and result["results"]:
            r = result["results"][0]
            status = "АНОМАЛИЯ" if r["is_anomaly"] else "НОРМА"
            color = "red" if r["is_anomaly"] else "green"
            st.markdown(f"### Результат: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
            st.markdown(f"**Оценка аномалии:** {r['anomaly_score']:.4f}")
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Random Forest", "Аномалия" if r["rf_prediction"] else "Норма",
                          delta=f"{r['rf_confidence']:.0%}" if r["rf_confidence"] else None)
            col_m2.metric("MLP Neural Net", "Аномалия" if r["mlp_prediction"] else "Норма",
                          delta=f"{r['mlp_confidence']:.0%}" if r["mlp_confidence"] else None)
            col_m3.metric("Isolation Forest", "Аномалия" if r["iso_forest_prediction"] else "Норма")

with tab3:
    st.header("Пакетный анализ потоков")

    option = st.radio("Источник данных:", ["JSON текст", "Загрузить JSON файл"])

    flows_data = None
    if option == "JSON текст":
        json_text = st.text_area("Вставьте JSON с потоками:", height=200,
            value='[{"packet_count": 25, "total_bytes": 3200, "mean_packet_size": 350, "std_packet_size": 45, "min_packet_size": 40, "max_packet_size": 1400, "flow_duration_sec": 28.0, "mean_inter_arrival_time": 0.75, "std_inter_arrival_time": 0.45, "syn_count": 2, "ack_count": 18, "fin_count": 2, "rst_count": 0, "psh_count": 8, "urg_count": 0, "mean_ttl": 120, "mean_window_size": 65000, "payload_bytes_total": 2100, "protocol": "TCP"}]')
        if json_text.strip():
            try:
                data = json.loads(json_text)
                if isinstance(data, list):
                    flows_data = pd.json_normalize(data)
                else:
                    flows_data = pd.DataFrame([data])
                st.success(f"Загружено {len(flows_data)} потоков")
            except Exception as e:
                st.error(f"Ошибка парсинга JSON: {e}")
    else:
        uploaded = st.file_uploader("Выберите JSON файл", type=["json"])
        if uploaded:
            try:
                data = json.loads(uploaded.read())
                if isinstance(data, list):
                    flows_data = pd.json_normalize(data)
                else:
                    flows_data = pd.DataFrame([data])
                st.success(f"Загружено {len(flows_data)} потоков из файла")
            except Exception as e:
                st.error(f"Ошибка чтения файла: {e}")

    if flows_data is not None and st.button("Запустить анализ", type="primary"):
        result = make_prediction(flows_data)
        if result:
            st.markdown(f"### Результаты")
            st.metric("Всего потоков", result["total_flows"])
            col_r1, col_r2 = st.columns(2)
            col_r1.metric("Норма", result["normal_count"], delta_color="off")
            col_r2.metric("Аномалии", result["anomaly_count"], delta_color="off")

            rows = []
            for i, r in enumerate(result["results"]):
                rows.append({
                    "Поток": i + 1,
                    "Статус": "АНОМАЛИЯ" if r["is_anomaly"] else "НОРМА",
                    "Оценка": f"{r['anomaly_score']:.4f}",
                    "RF": "ДА" if r["rf_prediction"] else "НЕТ",
                    "MLP": "ДА" if r["mlp_prediction"] else "НЕТ",
                    "IF": "ДА" if r["iso_forest_prediction"] else "НЕТ",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.info("Графики на вкладке «Аналитика» показывают результаты verify.py (10 потоков). Запустите verify.py в консоли, чтобы обновить их.")

with tab4:
    st.header("Обучение моделей")

    st.markdown("""
    **Генерируемые типы трафика:**
    - **Норма:** HTTP, SSH, DNS
    - **Аномалии:** SYN Flood, Port Scan, DDoS
    """)

    n_samples = st.slider("Количество образцов на тип трафика", 50, 500, 200, step=50)

    if st.button("Начать обучение", type="primary"):
        with st.spinner("Генерация данных и обучение моделей..."):
            X, y = generate_training_data(n_per_class=n_samples)
            model_dir = str(Path(__file__).parent.parent / "python-ml" / "models")
            train_models(X, y, model_dir=model_dir)
        st.success(f"Обучение завершено! {len(X)} образцов, {sum(y == 0)} норма / {sum(y == 1)} аномалия")
        st.balloons()
        st.cache_resource.clear()
        st.info("Модели перезагружены. Перейдите на вкладку «Предсказание» для проверки.")

with tab5:
    st.header("О проекте")

    st.markdown("""
    **Система обнаружения вторжений (IDS) на основе машинного обучения**

    **Вариант 3** — Сетевая безопасность

    **Технологии:**
    - **Go** — захват пакетов (gopacket), извлечение 19 признаков потоков
    - **Python + scikit-learn** — ML-модели (Random Forest, MLP, Isolation Forest)
    - **FastAPI** — REST API
    - **matplotlib** — визуализация
    - **Streamlit** — данный дашборд

    **Ансамбль:** majority voting (≥2 моделей = аномалия)

    **Алерты:** Telegram / Slack

    **Статус:** ✅ Все 45 тестов проходят
    """)
