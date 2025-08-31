# PDF Data Redactor

PDF Data Redactor is a multi-language console application for replacing sensitive data in PDF files using string replacement, with full support for compressed PDFs.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Python External Tools Implementation (RECOMMENDED)
This is the MOST RELIABLE implementation that works correctly:

- **Bootstrap and dependencies**: `sudo apt-get update && sudo apt-get install -y qpdf poppler-utils ghostscript`
- **Verify tools**: `python3 redactor-tools.py --check-tools`
- **Test basic functionality**: `python3 redactor-tools.py input.pdf output.pdf --find "text" --replace "[REDACTED]"`
- **Expected timing**: Tool installation takes ~15 seconds, basic redaction takes <1 second

### Python PyMuPDF Implementation (HAS ISSUES)
- **Install dependencies**: `pip3 install -r requirements.txt` -- takes ~10 seconds  
- **KNOWN ISSUE**: API compatibility problems with current PyMuPDF version causing `Document.save() got an unexpected keyword argument 'deflate_level'` errors
- **DO NOT USE** until API compatibility is fixed

### Node.js Implementation (LIMITED FUNCTIONALITY)
- **Install dependencies**: `cd nodejs && npm install` -- takes ~150 seconds. NEVER CANCEL: Set timeout to 180+ seconds
- **Build works but text replacement fails**: pdf-lib has very limited text manipulation capabilities  
- **Test**: `cd nodejs && node redactor.js --help` -- works in ~0.1 seconds
- **Note**: This implementation cannot effectively replace text in existing PDFs

### C# .NET Implementation (WORKING)
- **Build**: `cd csharp && dotnet build` -- takes ~9 seconds
- **CRITICAL**: Use .NET 8.0 target framework (updated from net6.0 to net8.0)
- **Test**: `cd csharp && dotnet run -- --help` -- works in ~1.4 seconds
- **Warnings about PDFsharp compatibility are normal and can be ignored**

### Go Implementation (BROKEN)
- **Dependencies**: `cd go && go mod tidy` -- takes ~6 seconds  
- **MAJOR ISSUE**: API incompatibility with pdfcpu v0.5.0, build fails with multiple undefined symbols
- **DO NOT USE** until API compatibility is fixed

### Java Implementation (BROKEN)
- **Dependencies**: `cd java && mvn compile` -- takes ~9 seconds
- **MAJOR ISSUE**: API incompatibility with PDFBox 3.0.0, compilation fails with `cannot find symbol: method load(java.io.File)`
- **DO NOT USE** until API compatibility is fixed

## Validation

### Manual Testing Steps  
Always run these validation scenarios after making changes:

1. **Create test PDF**: Use the sample creation script in repository root
2. **Test basic replacement**: `python3 redactor-tools.py sample.pdf output.pdf --find "John Doe" --replace "[NAME REDACTED]"`
3. **Test config file**: `python3 redactor-tools.py sample.pdf output.pdf --config config.example.json`
4. **Verify results**: Extract text from output PDF to confirm replacements worked

### NEVER CANCEL Build Commands
- **npm install**: Set timeout to 180+ seconds (takes ~150 seconds)
- **dotnet build**: Set timeout to 60+ seconds (takes ~9 seconds)
- **go mod tidy**: Set timeout to 60+ seconds (takes ~6 seconds)
- **mvn compile**: Set timeout to 60+ seconds (takes ~9 seconds)

## Common Tasks

### Repository Structure
```
.
├── README.md                    # Main documentation
├── config.example.json          # Example replacement rules configuration
├── redactor-tools.py           # WORKING Python external tools implementation
├── redactor.py                 # BROKEN Python PyMuPDF implementation  
├── requirements-tools.txt      # External tools Python dependencies
├── requirements.txt            # PyMuPDF Python dependencies
├── csharp/                     # WORKING C# implementation
│   ├── PDFRedactor.csproj
│   └── PDFRedactor.cs
├── go/                         # BROKEN Go implementation
│   ├── go.mod
│   ├── Makefile
│   └── redactor.go
├── java/                       # BROKEN Java implementation  
│   ├── pom.xml
│   └── src/main/java/PDFRedactor.java
└── nodejs/                     # LIMITED Node.js implementation
    ├── package.json
    └── redactor.js
```

### Configuration Format
The `config.example.json` shows the expected JSON format for replacement rules:
- `replacements[]` array with `find`, `replace`, and `regex` properties
- `compression` object with `preserve` boolean and `level` integer

### Build and Runtime Requirements Summary
- **Python**: Requires Python 3.x + external tools (qpdf, poppler-utils, ghostscript)
- **C#**: Requires .NET 8.0
- **Node.js**: Requires Node.js 20+ and npm (but functionality is limited)
- **Go**: Requires Go 1.21+ (but has API issues) 
- **Java**: Requires Java 17+ and Maven (but has API issues)

### Troubleshooting
- **Go build fails**: pdfcpu API incompatibility - known issue
- **Java compile fails**: PDFBox API incompatibility - known issue  
- **Python PyMuPDF fails**: API parameter incompatibility - known issue
- **Node.js doesn't replace text**: pdf-lib limitation - expected behavior
- **C# warnings about PDFsharp**: Framework compatibility warnings - safe to ignore

Use the Python external tools implementation (`redactor-tools.py`) for reliable PDF text redaction functionality.