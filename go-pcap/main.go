package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/google/gopacket/pcap"
	"github.com/user/ids-pcap/capture"
	"github.com/user/ids-pcap/features"
	"github.com/user/ids-pcap/output"
)

func main() {
	mode := flag.String("mode", "live", "Capture mode: live or file")
	iface := flag.String("interface", "", "Network interface for live capture")
	pcapFile := flag.String("file", "", "PCAP file path for offline analysis")
	bpfFilter := flag.String("filter", "", "BPF filter expression")
	outputFile := flag.String("output", "", "Output JSON file path")
	windowSec := flag.Int("window", 60, "Time window in seconds for flow aggregation")
	listDevices := flag.Bool("list", false, "List available network interfaces")
	flag.Parse()

	if *listDevices {
		if err := capture.ListInterfaces(); err != nil {
			log.Fatalf("Failed to list interfaces: %v", err)
		}
		return
	}

	windowDuration := time.Duration(*windowSec) * time.Second

	cfg := capture.DefaultConfig()
	if *iface != "" {
		cfg.Interface = *iface
	}
	if *bpfFilter != "" {
		cfg.BPFFilter = *bpfFilter
	}

	var handle *pcap.Handle
	var err error

	switch *mode {
	case "live":
		handle, err = capture.OpenLive(cfg)
		if err != nil {
			log.Fatalf("Failed to open live capture: %v", err)
		}
		fmt.Fprintf(os.Stderr, "Starting live capture on interface: %s\n", cfg.Interface)
	case "file":
		if *pcapFile == "" {
			log.Fatal("PCAP file path is required in file mode")
		}
		handle, err = capture.OpenFile(*pcapFile)
		if err != nil {
			log.Fatalf("Failed to open pcap file: %v", err)
		}
		fmt.Fprintf(os.Stderr, "Analyzing PCAP file: %s\n", *pcapFile)
	default:
		log.Fatalf("Unknown mode: %s. Use 'live' or 'file'", *mode)
	}
	defer handle.Close()

	packetChan := make(chan capture.PacketInfo, 1000)
	errChan := make(chan error, 100)

	go capture.ProcessPackets(handle, packetChan, errChan)

	extractor := features.NewFeatureExtractor(windowDuration)
	ticker := time.NewTicker(windowDuration)
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	running := true
	for running {
		select {
		case packet, ok := <-packetChan:
			if !ok {
				running = false
				break
			}
			extractor.AddPacket(packet)

		case err, ok := <-errChan:
			if !ok {
				continue
			}
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)

		case <-ticker.C:
			flows := extractor.ExtractFlows()
			if len(flows) > 0 {
				if *outputFile != "" {
					if err := output.WriteFlowsJSON(flows, *outputFile); err != nil {
						fmt.Fprintf(os.Stderr, "Failed to write output: %v\n", err)
					}
				} else {
					if err := output.WriteFlowsStdout(flows); err != nil {
						fmt.Fprintf(os.Stderr, "Failed to write output: %v\n", err)
					}
				}
			}
			extractor.Clear()

		case <-sigChan:
			fmt.Fprintf(os.Stderr, "\nShutting down...\n")
			running = false
		}
	}

	flows := extractor.ExtractFlows()
	if len(flows) > 0 {
		if *outputFile != "" {
			if err := output.WriteFlowsJSON(flows, *outputFile); err != nil {
				fmt.Fprintf(os.Stderr, "Failed to write output: %v\n", err)
			}
		} else {
			output.WriteFlowsStdout(flows)
		}
	}

	fmt.Fprintf(os.Stderr, "Capture complete. %d packets processed.\n", extractor.Count())
}
