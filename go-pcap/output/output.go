package output

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/user/ids-pcap/features"
)

func WriteFlowsJSON(flows []features.FlowFeatures, filePath string) error {
	file, err := os.Create(filePath)
	if err != nil {
		return fmt.Errorf("failed to create output file: %w", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(flows); err != nil {
		return fmt.Errorf("failed to encode flows to JSON: %w", err)
	}
	return nil
}

func WriteFlowsStdout(flows []features.FlowFeatures) error {
	for _, flow := range flows {
		data, err := json.Marshal(flow)
		if err != nil {
			return fmt.Errorf("failed to marshal flow: %w", err)
		}
		fmt.Println(string(data))
	}
	return nil
}
