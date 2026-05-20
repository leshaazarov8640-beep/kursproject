package capture

import (
	"fmt"
	"time"

	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
)

type PacketInfo struct {
	Timestamp    time.Time
	SrcIP        string
	DstIP        string
	SrcPort      uint16
	DstPort      uint16
	Protocol     string
	PacketSize   int
	TCPFlags     string
	TTL          uint8
	WindowSize   uint16
	PayloadLen   int
}

type CaptureConfig struct {
	Interface   string
	Filename    string
	BPFFilter   string
	SnapshotLen int32
	Timeout     time.Duration
}

func DefaultConfig() CaptureConfig {
	return CaptureConfig{
		Interface:   "eth0",
		SnapshotLen: 65536,
		Timeout:     pcap.BlockForever,
		BPFFilter:   "",
	}
}

func ListInterfaces() error {
	devices, err := pcap.FindAllDevs()
	if err != nil {
		return fmt.Errorf("failed to list devices: %w", err)
	}
	if len(devices) == 0 {
		fmt.Println("No network interfaces found")
		return nil
	}
	for _, d := range devices {
		fmt.Printf("Interface: %s\n", d.Name)
		fmt.Printf("  Description: %s\n", d.Description)
		for _, addr := range d.Addresses {
			fmt.Printf("  IP: %s\n", addr.IP)
		}
	}
	return nil
}

func OpenLive(cfg CaptureConfig) (*pcap.Handle, error) {
	handle, err := pcap.OpenLive(cfg.Interface, cfg.SnapshotLen, true, cfg.Timeout)
	if err != nil {
		return nil, fmt.Errorf("failed to open interface %s: %w", cfg.Interface, err)
	}
	if cfg.BPFFilter != "" {
		if err := handle.SetBPFFilter(cfg.BPFFilter); err != nil {
			handle.Close()
			return nil, fmt.Errorf("failed to set BPF filter: %w", err)
		}
	}
	return handle, nil
}

func OpenFile(filename string) (*pcap.Handle, error) {
	handle, err := pcap.OpenOffline(filename)
	if err != nil {
		return nil, fmt.Errorf("failed to open pcap file %s: %w", filename, err)
	}
	return handle, nil
}

func ProcessPackets(handle *pcap.Handle, packetChan chan<- PacketInfo, errChan chan<- error) {
	defer close(packetChan)
	defer close(errChan)

	packetSource := gopacket.NewPacketSource(handle, handle.LinkType())
	for packet := range packetSource.Packets() {
		info, err := extractPacketInfo(packet)
		if err != nil {
			errChan <- fmt.Errorf("failed to extract packet info: %w", err)
			continue
		}
		packetChan <- info
	}
}

func extractPacketInfo(packet gopacket.Packet) (PacketInfo, error) {
	info := PacketInfo{
		Timestamp:  packet.Metadata().Timestamp,
		PacketSize: packet.Metadata().CaptureLength,
	}

	ipLayer := packet.Layer(layers.LayerTypeIPv4)
	if ipLayer != nil {
		ip, _ := ipLayer.(*layers.IPv4)
		info.SrcIP = ip.SrcIP.String()
		info.DstIP = ip.DstIP.String()
		info.TTL = ip.TTL
	}

	ip6Layer := packet.Layer(layers.LayerTypeIPv6)
	if ip6Layer != nil {
		ip6, _ := ip6Layer.(*layers.IPv6)
		if info.SrcIP == "" {
			info.SrcIP = ip6.SrcIP.String()
		}
		if info.DstIP == "" {
			info.DstIP = ip6.DstIP.String()
		}
		info.TTL = ip6.HopLimit
	}

	tcpLayer := packet.Layer(layers.LayerTypeTCP)
	if tcpLayer != nil {
		tcp, _ := tcpLayer.(*layers.TCP)
		info.SrcPort = uint16(tcp.SrcPort)
		info.DstPort = uint16(tcp.DstPort)
		info.Protocol = "TCP"
		info.WindowSize = tcp.Window
		info.PayloadLen = len(tcp.Payload)

		var flags string
		if tcp.SYN {
			flags += "S"
		}
		if tcp.ACK {
			flags += "A"
		}
		if tcp.FIN {
			flags += "F"
		}
		if tcp.RST {
			flags += "R"
		}
		if tcp.PSH {
			flags += "P"
		}
		if tcp.URG {
			flags += "U"
		}
		info.TCPFlags = flags
		return info, nil
	}

	udpLayer := packet.Layer(layers.LayerTypeUDP)
	if udpLayer != nil {
		udp, _ := udpLayer.(*layers.UDP)
		info.SrcPort = uint16(udp.SrcPort)
		info.DstPort = uint16(udp.DstPort)
		info.Protocol = "UDP"
		info.PayloadLen = len(udp.Payload)
		return info, nil
	}

	icmpLayer := packet.Layer(layers.LayerTypeICMPv4)
	if icmpLayer != nil {
		info.Protocol = "ICMP"
		return info, nil
	}

	if info.SrcIP != "" && info.Protocol == "" {
		info.Protocol = "OTHER"
	}

	return info, nil
}
