package main

import (
	"encoding/json"
	"fmt"
	"testing"
)

// Test struct to match the new Go implementation
type ConfigReplacementRule struct {
	Find    interface{} `json:"find"`
	Replace string      `json:"replace"`
	Regex   bool        `json:"regex"`
}

func (r *ConfigReplacementRule) GetFindPatterns() []string {
	switch v := r.Find.(type) {
	case string:
		return []string{v}
	case []interface{}:
		patterns := make([]string, len(v))
		for i, pattern := range v {
			if str, ok := pattern.(string); ok {
				patterns[i] = str
			}
		}
		return patterns
	default:
		return []string{}
	}
}

type Config struct {
	Replacements []ConfigReplacementRule `json:"replacements"`
}

func TestGoConfigParsing(t *testing.T) {
	// Test JSON with mixed string and array finds
	configJSON := `{
		"replacements": [
			{
				"find": ["John Doe", "Jane Smith"],
				"replace": "[NAME REDACTED]",
				"regex": false
			},
			{
				"find": "confidential",
				"replace": "[REDACTED]",
				"regex": false
			}
		]
	}`

	var config Config
	err := json.Unmarshal([]byte(configJSON), &config)
	if err != nil {
		t.Fatalf("Failed to parse config: %v", err)
	}

	if len(config.Replacements) != 2 {
		t.Fatalf("Expected 2 replacement rules, got %d", len(config.Replacements))
	}

	// Test first rule with array
	patterns1 := config.Replacements[0].GetFindPatterns()
	expectedPatterns1 := []string{"John Doe", "Jane Smith"}
	if len(patterns1) != len(expectedPatterns1) {
		t.Errorf("Expected %d patterns, got %d", len(expectedPatterns1), len(patterns1))
	}
	for i, expected := range expectedPatterns1 {
		if patterns1[i] != expected {
			t.Errorf("Expected pattern '%s', got '%s'", expected, patterns1[i])
		}
	}

	// Test second rule with string
	patterns2 := config.Replacements[1].GetFindPatterns()
	if len(patterns2) != 1 || patterns2[0] != "confidential" {
		t.Errorf("Expected single pattern 'confidential', got %v", patterns2)
	}

	fmt.Println("✓ Go config parsing test passed")
}

func main() {
	TestGoConfigParsing(&testing.T{})
}