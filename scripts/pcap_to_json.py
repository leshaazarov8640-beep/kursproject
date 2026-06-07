"""
Скрипт для чтения PCAP-файла и преобразования в JSON-потоки
для передачи в ML-модуль IDS.

Использование:
  py pcap_to_json.py --file traffic.pcap --output flows.json
  py pcap_to_json.py --file traffic.pcap | python ../python-ml/main.py predict
"""

import argparse
import json
import sys
import math
from collections import defaultdict
from datetime import datetime, timezone

try:
    from scapy.all import rdpcap, IP, IPv6, TCP, UDP, ICMP
except ImportError:
    print("Установите scapy: pip install scapy", file=sys.stderr)
    sys.exit(1)


def extract_flows(pcap_path, window_sec=60):
    packets = rdpcap(pcap_path)
    flows = defaultdict(list)

    for pkt in packets:
        ts = pkt.time
        if IP in pkt:
            ip = pkt[IP]
            src_ip = ip.src
            dst_ip = ip.dst
            ttl = ip.ttl
        elif IPv6 in pkt:
            ip6 = pkt[IPv6]
            src_ip = ip6.src
            dst_ip = ip6.dst
            ttl = ip6.hlim
        else:
            continue

        size = len(pkt)
        src_port = 0
        dst_port = 0
        protocol = "OTHER"
        flags = ""
        window_size = 0
        payload_len = 0

        if TCP in pkt:
            tcp = pkt[TCP]
            src_port = tcp.sport
            dst_port = tcp.dport
            protocol = "TCP"
            window_size = tcp.window
            payload_len = len(bytes(tcp.payload))
            if tcp.flags & 0x02: flags += "S"
            if tcp.flags & 0x10: flags += "A"
            if tcp.flags & 0x01: flags += "F"
            if tcp.flags & 0x04: flags += "R"
            if tcp.flags & 0x08: flags += "P"
            if tcp.flags & 0x20: flags += "U"
        elif UDP in pkt:
            udp = pkt[UDP]
            src_port = udp.sport
            dst_port = udp.dport
            protocol = "UDP"
            payload_len = len(bytes(udp.payload))
        elif ICMP in pkt:
            protocol = "ICMP"

        key = (src_ip, dst_ip, src_port, dst_port, protocol)
        flows[key].append({
            "ts": ts, "size": size, "ttl": ttl,
            "window_size": window_size, "flags": flags,
            "payload_len": payload_len,
        })

    results = []
    for key, pkts in flows.items():
        src_ip, dst_ip, src_port, dst_port, protocol = key
        pkts.sort(key=lambda x: float(x["ts"]))
        ts_start = float(pkts[0]["ts"])
        ts_end = float(pkts[-1]["ts"])
        duration = ts_end - ts_start
        pkt_count = len(pkts)
        total_bytes = sum(p["size"] for p in pkts)
        sizes = [p["size"] for p in pkts]
        mean_size = total_bytes / pkt_count if pkt_count else 0
        std_size = math.sqrt(sum((s - mean_size) ** 2 for s in sizes) / pkt_count) if pkt_count > 1 else 0
        min_size = min(sizes) if sizes else 0
        max_size = max(sizes) if sizes else 0

        iats = [float(pkts[i]["ts"]) - float(pkts[i - 1]["ts"]) for i in range(1, len(pkts))]
        mean_iat = sum(iats) / len(iats) if iats else 0
        std_iat = math.sqrt(sum((iat - mean_iat) ** 2 for iat in iats) / len(iats)) if len(iats) > 1 else 0

        syn = sum(1 for p in pkts if "S" in p["flags"])
        ack = sum(1 for p in pkts if "A" in p["flags"])
        fin = sum(1 for p in pkts if "F" in p["flags"])
        rst = sum(1 for p in pkts if "R" in p["flags"])
        psh = sum(1 for p in pkts if "P" in p["flags"])
        urg = sum(1 for p in pkts if "U" in p["flags"])
        mean_ttl = sum(p["ttl"] for p in pkts) / pkt_count if pkt_count else 0
        mean_win = sum(p["window_size"] for p in pkts) / pkt_count if pkt_count else 0
        total_payload = sum(p["payload_len"] for p in pkts)

        ts_start_dt = datetime.fromtimestamp(float(ts_start), tz=timezone.utc).isoformat()
        ts_end_dt = datetime.fromtimestamp(float(ts_end), tz=timezone.utc).isoformat()

        results.append({
            "time_window_start": ts_start_dt,
            "time_window_end": ts_end_dt,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "protocol": protocol,
            "packet_count": pkt_count,
            "total_bytes": total_bytes,
            "mean_packet_size": round(mean_size, 2),
            "std_packet_size": round(std_size, 2),
            "min_packet_size": min_size,
            "max_packet_size": max_size,
            "flow_duration_sec": round(duration, 4),
            "mean_inter_arrival_time": round(mean_iat, 6),
            "std_inter_arrival_time": round(std_iat, 6),
            "syn_count": syn,
            "ack_count": ack,
            "fin_count": fin,
            "rst_count": rst,
            "psh_count": psh,
            "urg_count": urg,
            "mean_ttl": round(mean_ttl, 2),
            "mean_window_size": round(mean_win, 2),
            "payload_bytes_total": total_payload,
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="PCAP → JSON для IDS ML-модуля")
    parser.add_argument("--file", required=True, help="Путь к PCAP-файлу")
    parser.add_argument("--output", help="Выходной JSON-файл (по умолчанию stdout)")
    parser.add_argument("--window", type=int, default=60, help="Временное окно в секундах")
    args = parser.parse_args()

    print(f"[INFO] Чтение {args.file}...", file=sys.stderr)
    flows = extract_flows(args.file, window_sec=args.window)
    print(f"[INFO] Извлечено {len(flows)} потоков", file=sys.stderr)

    output = json.dumps(flows, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[INFO] Сохранено в {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
