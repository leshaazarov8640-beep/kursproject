package features

import (
	"encoding/json"
	"math"
	"time"

	"github.com/user/ids-pcap/capture"
)

type flowKey struct {
	srcIP, dstIP     string
	srcPort, dstPort uint16
	protocol         string
}

type FlowFeatures struct {
	TimeWindowStart time.Time `json:"time_window_start"`
	TimeWindowEnd   time.Time `json:"time_window_end"`
	SrcIP           string    `json:"src_ip"`
	DstIP           string    `json:"dst_ip"`
	SrcPort         uint16    `json:"src_port"`
	DstPort         uint16    `json:"dst_port"`
	Protocol        string    `json:"protocol"`
	PacketCount     int       `json:"packet_count"`
	TotalBytes      int       `json:"total_bytes"`
	MeanPacketSize  float64   `json:"mean_packet_size"`
	StdPacketSize   float64   `json:"std_packet_size"`
	MinPacketSize   int       `json:"min_packet_size"`
	MaxPacketSize   int       `json:"max_packet_size"`
	FlowDuration    float64   `json:"flow_duration_sec"`
	MeanIAT         float64   `json:"mean_inter_arrival_time"`
	StdIAT          float64   `json:"std_inter_arrival_time"`
	SYNCount        int       `json:"syn_count"`
	ACKCount        int       `json:"ack_count"`
	FINCount        int       `json:"fin_count"`
	RSTCount        int       `json:"rst_count"`
	PSHCount        int       `json:"psh_count"`
	URGCount        int       `json:"urg_count"`
	MeanTTL         float64   `json:"mean_ttl"`
	MeanWindowSize  float64   `json:"mean_window_size"`
	PayloadBytes    int       `json:"payload_bytes_total"`
	Label           string    `json:"label,omitempty"`
	Score           float64   `json:"score,omitempty"`
}

type FeatureExtractor struct {
	windowDuration time.Duration
	packets        []capture.PacketInfo
}

func NewFeatureExtractor(windowDuration time.Duration) *FeatureExtractor {
	return &FeatureExtractor{
		windowDuration: windowDuration,
		packets:        make([]capture.PacketInfo, 0),
	}
}

func (fe *FeatureExtractor) AddPacket(p capture.PacketInfo) {
	fe.packets = append(fe.packets, p)
}

func (fe *FeatureExtractor) Clear() {
	fe.packets = fe.packets[:0]
}

func (fe *FeatureExtractor) Count() int {
	return len(fe.packets)
}

func (fe *FeatureExtractor) ExtractFlows() []FlowFeatures {
	if len(fe.packets) == 0 {
		return nil
	}

	flowPackets := make(map[flowKey][]capture.PacketInfo)

	for _, p := range fe.packets {
		key := flowKey{
			srcIP:    p.SrcIP,
			dstIP:    p.DstIP,
			srcPort:  p.SrcPort,
			dstPort:  p.DstPort,
			protocol: p.Protocol,
		}
		flowPackets[key] = append(flowPackets[key], p)
	}

	var flows []FlowFeatures
	for key, packets := range flowPackets {
		flow := computeFlowFeatures(key, packets)
		flows = append(flows, flow)
	}
	return flows
}

func computeFlowFeatures(key flowKey, packets []capture.PacketInfo) FlowFeatures {
	flow := FlowFeatures{
		SrcIP:    key.srcIP,
		DstIP:    key.dstIP,
		SrcPort:  key.srcPort,
		DstPort:  key.dstPort,
		Protocol: key.protocol,
	}

	flow.TimeWindowStart = packets[0].Timestamp
	flow.TimeWindowEnd = packets[len(packets)-1].Timestamp
	flow.FlowDuration = flow.TimeWindowEnd.Sub(flow.TimeWindowStart).Seconds()
	flow.PacketCount = len(packets)

	var totalSize int
	var sizes []int
	var iats []float64

	for i, p := range packets {
		totalSize += p.PacketSize
		sizes = append(sizes, p.PacketSize)
		flow.TotalBytes += p.PacketSize
		flow.PayloadBytes += p.PayloadLen

		if i > 0 {
			iat := p.Timestamp.Sub(packets[i-1].Timestamp).Seconds()
			iats = append(iats, iat)
		}

		flow.MeanTTL += float64(p.TTL)
		flow.MeanWindowSize += float64(p.WindowSize)

		for _, flag := range p.TCPFlags {
			switch flag {
			case 'S':
				flow.SYNCount++
			case 'A':
				flow.ACKCount++
			case 'F':
				flow.FINCount++
			case 'R':
				flow.RSTCount++
			case 'P':
				flow.PSHCount++
			case 'U':
				flow.URGCount++
			}
		}
	}

	flow.MeanPacketSize = float64(totalSize) / float64(len(packets))
	flow.MeanTTL /= float64(len(packets))
	flow.MeanWindowSize /= float64(len(packets))

	var sizeVariance float64
	for _, s := range sizes {
		diff := float64(s) - flow.MeanPacketSize
		sizeVariance += diff * diff
	}
	flow.StdPacketSize = math.Sqrt(sizeVariance / float64(len(sizes)))

	flow.MinPacketSize = minInt(sizes)
	flow.MaxPacketSize = maxInt(sizes)

	if len(iats) > 0 {
		var iatSum float64
		for _, iat := range iats {
			iatSum += iat
		}
		flow.MeanIAT = iatSum / float64(len(iats))

		var iatVariance float64
		for _, iat := range iats {
			diff := iat - flow.MeanIAT
			iatVariance += diff * diff
		}
		flow.StdIAT = math.Sqrt(iatVariance / float64(len(iats)))
	}

	return flow
}

func minInt(values []int) int {
	if len(values) == 0 {
		return 0
	}
	min := values[0]
	for _, v := range values[1:] {
		if v < min {
			min = v
		}
	}
	return min
}

func maxInt(values []int) int {
	if len(values) == 0 {
		return 0
	}
	max := values[0]
	for _, v := range values[1:] {
		if v > max {
			max = v
		}
	}
	return max
}

func (f FlowFeatures) ToJSON() (string, error) {
	data, err := json.Marshal(f)
	if err != nil {
		return "", err
	}
	return string(data), nil
}
