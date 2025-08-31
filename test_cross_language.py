#!/usr/bin/env python3
"""
Test C# style JSON handling for the multi-find feature
"""

import json
import tempfile
import os


def simulate_csharp_json_handling():
    """Simulate the C# JSON.NET handling"""
    config = {
        "replacements": [
            {
                "find": ["John Doe", "Jane Smith"],
                "replace": "[NAME REDACTED]",
                "regex": False
            },
            {
                "find": "confidential",
                "replace": "[REDACTED]",
                "regex": False
            }
        ]
    }
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    try:
        # Simulate C# ConfigReplacementRule processing
        with open(config_path, 'r') as f:
            loaded_config = json.load(f)
        
        replacements = []
        
        for config_rule in loaded_config['replacements']:
            find_value = config_rule['find']
            
            # Simulate GetFindPatterns() method
            if isinstance(find_value, str):
                find_patterns = [find_value]
            elif isinstance(find_value, list):
                find_patterns = find_value
            else:
                find_patterns = []
            
            # Add individual replacement rules for each pattern
            for pattern in find_patterns:
                replacements.append({
                    'find': pattern,
                    'replace': config_rule['replace'],
                    'regex': config_rule.get('regex', False)
                })
        
        print("C# style processing created replacements:")
        for rule in replacements:
            print(f"  Find: '{rule['find']}' -> Replace: '{rule['replace']}'")
        
        # Verify we got all expected patterns
        find_patterns = [r['find'] for r in replacements]
        assert "John Doe" in find_patterns
        assert "Jane Smith" in find_patterns
        assert "confidential" in find_patterns
        assert len(replacements) == 3  # Should have expanded to 3 individual rules
        
        print("✓ C# JSON handling simulation passed")
        
    finally:
        os.unlink(config_path)


def simulate_java_gson_handling():
    """Simulate Java Gson handling"""
    config = {
        "replacements": [
            {
                "find": ["John Doe", "Jane Smith", "Bob Johnson"],
                "replace": "[NAME REDACTED]",
                "regex": False
            },
            {
                "find": "secret",
                "replace": "[SENSITIVE]",
                "regex": False
            }
        ]
    }
    
    # Simulate Gson parsing where Object can be String or List
    replacements = []
    
    for config_rule in config['replacements']:
        find_value = config_rule['find']
        
        # Simulate Java getFindPatterns() method
        if isinstance(find_value, str):
            find_patterns = [find_value]
        elif isinstance(find_value, list):
            find_patterns = find_value
        else:
            find_patterns = []
        
        # Create ReplacementRule objects
        for pattern in find_patterns:
            replacements.append({
                'find': pattern,
                'replace': config_rule['replace'],
                'regex': config_rule.get('regex', False)
            })
    
    print("Java Gson style processing created replacements:")
    for rule in replacements:
        print(f"  Find: '{rule['find']}' -> Replace: '{rule['replace']}'")
    
    # Verify we got all expected patterns
    find_patterns = [r['find'] for r in replacements]
    assert "John Doe" in find_patterns
    assert "Jane Smith" in find_patterns  
    assert "Bob Johnson" in find_patterns
    assert "secret" in find_patterns
    assert len(replacements) == 4  # Should have expanded to 4 individual rules
    
    print("✓ Java Gson handling simulation passed")


if __name__ == "__main__":
    print("Testing cross-language JSON handling approaches...")
    simulate_csharp_json_handling()
    simulate_java_gson_handling()
    print("All cross-language tests passed! ✓")