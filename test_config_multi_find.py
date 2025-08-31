#!/usr/bin/env python3
"""
Test script to validate the multiple find patterns feature
"""

import json
import tempfile
import os


def test_current_config_format():
    """Test loading the current config format"""
    config = {
        "replacements": [
            {
                "find": "John Doe",
                "replace": "[NAME REDACTED]",
                "regex": False
            },
            {
                "find": "Jane Smith", 
                "replace": "[NAME REDACTED]",
                "regex": False
            }
        ]
    }
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    try:
        # Test loading with a simple replacement processor
        class SimpleReplacer:
            def __init__(self):
                self.replacements = []
            
            def add_replacement(self, find, replace, is_regex=False):
                self.replacements.append({
                    'find': find,
                    'replace': replace,
                    'regex': is_regex
                })
            
            def load_config(self, config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                for rule in config.get('replacements', []):
                    self.add_replacement(
                        rule['find'],
                        rule['replace'],
                        rule.get('regex', False)
                    )
            
            def process_text(self, text):
                result = text
                for rule in self.replacements:
                    result = result.replace(rule['find'], rule['replace'])
                return result
        
        replacer = SimpleReplacer()
        replacer.load_config(config_path)
        
        # Test replacement
        test_text = "Hello John Doe and Jane Smith"
        result = replacer.process_text(test_text)
        expected = "Hello [NAME REDACTED] and [NAME REDACTED]"
        
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print("✓ Current config format test passed")
        
    finally:
        os.unlink(config_path)


def test_new_config_format():
    """Test loading the new config format with multiple find patterns"""
    config = {
        "replacements": [
            {
                "find": ["John Doe", "Jane Smith"],
                "replace": "[NAME REDACTED]",
                "regex": False
            }
        ]
    }
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    try:
        # Test loading with an enhanced replacement processor
        class EnhancedReplacer:
            def __init__(self):
                self.replacements = []
            
            def add_replacement(self, find, replace, is_regex=False):
                # Support both string and list for find parameter
                if isinstance(find, str):
                    find_patterns = [find]
                else:
                    find_patterns = find
                
                for pattern in find_patterns:
                    self.replacements.append({
                        'find': pattern,
                        'replace': replace,
                        'regex': is_regex
                    })
            
            def load_config(self, config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                for rule in config.get('replacements', []):
                    self.add_replacement(
                        rule['find'],
                        rule['replace'],
                        rule.get('regex', False)
                    )
            
            def process_text(self, text):
                result = text
                for rule in self.replacements:
                    result = result.replace(rule['find'], rule['replace'])
                return result
        
        replacer = EnhancedReplacer()
        replacer.load_config(config_path)
        
        # Test replacement
        test_text = "Hello John Doe and Jane Smith"
        result = replacer.process_text(test_text)
        expected = "Hello [NAME REDACTED] and [NAME REDACTED]"
        
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print("✓ New config format test passed")
        
    finally:
        os.unlink(config_path)


def test_mixed_config_format():
    """Test loading config with both old and new formats mixed"""
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
        # Test loading with an enhanced replacement processor
        class EnhancedReplacer:
            def __init__(self):
                self.replacements = []
            
            def add_replacement(self, find, replace, is_regex=False):
                # Support both string and list for find parameter
                if isinstance(find, str):
                    find_patterns = [find]
                else:
                    find_patterns = find
                
                for pattern in find_patterns:
                    self.replacements.append({
                        'find': pattern,
                        'replace': replace,
                        'regex': is_regex
                    })
            
            def load_config(self, config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                for rule in config.get('replacements', []):
                    self.add_replacement(
                        rule['find'],
                        rule['replace'],
                        rule.get('regex', False)
                    )
            
            def process_text(self, text):
                result = text
                for rule in self.replacements:
                    result = result.replace(rule['find'], rule['replace'])
                return result
        
        replacer = EnhancedReplacer()
        replacer.load_config(config_path)
        
        # Test replacement
        test_text = "Hello John Doe and Jane Smith, this is confidential"
        result = replacer.process_text(test_text)
        expected = "Hello [NAME REDACTED] and [NAME REDACTED], this is [REDACTED]"
        
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print("✓ Mixed config format test passed")
        
    finally:
        os.unlink(config_path)


if __name__ == "__main__":
    print("Testing configuration formats...")
    test_current_config_format()
    test_new_config_format()
    test_mixed_config_format()
    print("All tests passed! ✓")