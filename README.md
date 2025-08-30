# PDF Data Redactor

A console application for replacing sensitive data in PDF files using string replacement, with full support for compressed PDFs.

## Features

- Replace text in PDF files using string patterns
- Support for regular expressions
- Automatic handling of compressed PDFs
- Preserves original compression settings or applies custom compression
- Batch processing of multiple PDFs
- Configuration file support for replacement rules
- PDF information inspection tool
- Preserve PDF formatting and structure

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
