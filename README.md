# PDF Data Redactor

A console application for replacing sensitive data in PDF files using string replacement, with full support for compressed PDFs.

## Features

- Replace text in PDF files using string patterns
- Support for regular expressions
- Case insensitive matching support
- Automatic handling of compressed PDFs
- Preserves original compression settings or applies custom compression
- Batch processing of multiple PDFs
- Configuration file support for replacement rules
- PDF information inspection tool
- Preserve PDF formatting and structure

## Configuration Format

Replacement rules can be configured using a JSON file. Each rule supports the following properties:

- `find` - The text or pattern to find (can be a single string or an array of strings)
- `replace` - The replacement text
- `regex` - Boolean flag for regular expression matching (default: false)
- `caseInsensitive` - Boolean flag for case insensitive matching (default: false)

### Multiple Patterns Support

You can specify multiple text patterns that share the same replacement text in a single configuration entry, reducing config file duplication and improving maintainability:

```json
{
  "replacements": [
    {
      "find": ["John Doe", "jane smith", "Bob Johnson"],
      "replace": "[NAME REDACTED]",
      "regex": false,
      "caseInsensitive": true
    },
    {
      "find": ["123-45-6789", "987-65-4321", "555-12-3456"],
      "replace": "XXX-XX-XXXX",
      "regex": false
    },
    {
      "find": ["Confidential", "CONFIDENTIAL", "Private", "PRIVATE"],
      "replace": "[CLASSIFIED]",
      "regex": false,
      "caseInsensitive": true
    }
  ]
}
```

This approach offers several benefits:
- **Reduced duplication**: Multiple patterns sharing the same replacement don't need separate entries
- **Easier maintenance**: Update replacement text in one place for multiple patterns
- **Cleaner configuration**: Grouping related patterns together improves readability
- **Consistent formatting**: All related patterns get exactly the same replacement text

### Mixed Configuration

You can mix both single patterns and multiple patterns in the same configuration file:

```json
{
  "replacements": [
    {
      "find": ["John Doe", "jane smith", "Bob Johnson"],
      "replace": "[NAME REDACTED]",
      "regex": false,
      "caseInsensitive": true
    },
    {
      "find": "\\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}\\b",
      "replace": "[EMAIL REDACTED]",
      "regex": true,
      "caseInsensitive": true
    },
    {
      "find": ["Confidential", "Top Secret"],
      "replace": "[CLASSIFIED]",
      "regex": false,
      "caseInsensitive": true
    }
  ]
}
```

### Single Pattern (Backward Compatible)

The traditional single-string format is still fully supported:

Example configuration file:
```json
{
  "replacements": [
    {
      "find": "John Doe",
      "replace": "[NAME REDACTED]",
      "regex": false,
      "caseInsensitive": true
    },
    {
      "find": "\\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}\\b",
      "replace": "[EMAIL REDACTED]",
      "regex": true,
      "caseInsensitive": true
    }
  ]
}
```

## Implementation Options

This repository provides implementations in multiple languages and approaches. Choose based on your licensing needs and feature requirements:

### Compression Support Comparison

| Library/Approach | Language | License | Reads Compressed | Writes Compressed | Compression Control | Text Replacement Quality |
|-----------------|----------|---------|-----------------|-------------------|--------------------|-----------------------|
| **PyMuPDF** | Python | AGPL | ✅ Excellent | ✅ Excellent | ✅ Full control | ✅ Excellent |
| **External Tools** | Python/Bash | MIT | ✅ Excellent | ✅ Excellent | ✅ Full control | ⚠️ Good |
| **pdfcpu** | Go | Apache 2.0 | ✅ Excellent | ✅ Excellent | ✅ Good control | ⚠️ Moderate |
| **PDFBox** | Java | Apache 2.0 | ✅ Excellent | ✅ Excellent | ⚠️ Automatic | ⚠️ Moderate |
| **pdf-lib** | Node.js | MIT | ✅ Good | ✅ Good | ❌ Limited | ❌ Poor |
| **HummusJS** | Node.js | Apache 2.0 | ✅ Good | ✅ Good | ✅ Good | ⚠️ Moderate |
| **PDFsharp** | C# | MIT | ✅ Good | ⚠️ Basic | ❌ Limited | ❌ Poor |

### Recommendations

1. **Best Overall**: Python with PyMuPDF (if AGPL license is acceptable)
2. **Best MIT Option**: External Tools approach (qpdf + poppler + ghostscript)
3. **Best Pure Code MIT/Apache**: Go with pdfcpu
4. **Enterprise Java**: Apache PDFBox
5. **Node.js**: HummusJS for features, pdf-lib for simplicity

---

## External Tools Implementation (MIT License)

This approach uses command-line tools through subprocess calls, avoiding AGPL licensing issues while maintaining good functionality.

### Required Tools

- **qpdf** (Apache 2.0) - PDF manipulation and compression
- **poppler-utils** (GPL, used as external tool) - PDF text extraction
- **ghostscript** (AGPL, used as external tool) - PDF/PostScript conversion

### Installation

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y qpdf poppler-utils ghostscript python3-pip
pip3 install pikepdf  # Optional: MIT-licensed PDF library
