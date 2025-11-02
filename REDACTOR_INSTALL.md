# redactor.py - Installation and Usage Guide

Complete installation and usage instructions for the PyMuPDF-based PDF Data Redactor (`redactor.py`) across Windows, macOS, and Linux operating systems.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
  - [Windows](#windows-prerequisites)
  - [macOS](#macos-prerequisites)
  - [Linux](#linux-prerequisites)
- [Installation](#installation)
  - [Windows Installation](#windows-installation)
  - [macOS Installation](#macos-installation)
  - [Linux Installation](#linux-installation)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Configuration File Usage](#configuration-file-usage)
  - [Batch Processing](#batch-processing)
  - [Advanced Options](#advanced-options)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
  - [Windows Troubleshooting](#windows-troubleshooting)
  - [macOS Troubleshooting](#macos-troubleshooting)
  - [Linux Troubleshooting](#linux-troubleshooting)

---

## Overview

`redactor.py` is a Python-based PDF redaction tool that uses PyMuPDF (fitz) to replace sensitive data in PDF files. It supports:
- String-based text replacement
- Regular expression patterns
- Case-insensitive matching
- Automatic compression handling
- Batch processing
- Configuration file support

---

## Prerequisites

### Windows Prerequisites

1. **Python 3.7 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify installation:
     ```cmd
     python --version
     ```

2. **pip (Python package manager)**
   - Included with Python 3.4+
   - Verify installation:
     ```cmd
     pip --version
     ```

### macOS Prerequisites

1. **Python 3.7 or higher**
   - macOS 10.15+ includes Python 3, but you may need to install a newer version
   - Install via Homebrew (recommended):
     ```bash
     brew install python3
     ```
   - Or download from [python.org](https://www.python.org/downloads/)
   - Verify installation:
     ```bash
     python3 --version
     ```

2. **pip (Python package manager)**
   - Included with Python 3.4+
   - Verify installation:
     ```bash
     pip3 --version
     ```

### Linux Prerequisites

1. **Python 3.7 or higher**
   - Most Linux distributions include Python 3
   - If not installed, use your package manager:
     
     **Ubuntu/Debian:**
     ```bash
     sudo apt-get update
     sudo apt-get install python3 python3-pip
     ```
     
     **Fedora/RHEL/CentOS:**
     ```bash
     sudo dnf install python3 python3-pip
     ```
     
     **Arch Linux:**
     ```bash
     sudo pacman -S python python-pip
     ```
   
   - Verify installation:
     ```bash
     python3 --version
     ```

2. **pip (Python package manager)**
   - Verify installation:
     ```bash
     pip3 --version
     ```

---

## Installation

### Windows Installation

1. **Open Command Prompt or PowerShell**
   - Press `Win + R`, type `cmd`, press Enter

2. **Navigate to the project directory**
   ```cmd
   cd path\to\pdf-data-redactor
   ```

3. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```
   
   This will install PyMuPDF (the main dependency).

4. **Verify installation**
   ```cmd
   python redactor.py --help
   ```
   
   You should see the help message with all available options.

### macOS Installation

1. **Open Terminal**
   - Press `Cmd + Space`, type "Terminal", press Enter

2. **Navigate to the project directory**
   ```bash
   cd /path/to/pdf-data-redactor
   ```

3. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```
   
   This will install PyMuPDF (the main dependency).

4. **Verify installation**
   ```bash
   python3 redactor.py --help
   ```
   
   You should see the help message with all available options.

### Linux Installation

1. **Open Terminal**

2. **Navigate to the project directory**
   ```bash
   cd /path/to/pdf-data-redactor
   ```

3. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```
   
   Or use a virtual environment (recommended):
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python3 redactor.py --help
   ```
   
   You should see the help message with all available options.

---

## Usage

### Basic Usage

Replace text in a PDF file:

**Windows:**
```cmd
python redactor.py input.pdf output.pdf --find "John Doe" --replace "[REDACTED]"
```

**macOS/Linux:**
```bash
python3 redactor.py input.pdf output.pdf --find "John Doe" --replace "[REDACTED]"
```

### Configuration File Usage

Use a JSON configuration file to define multiple replacement rules. Configuration files support additional options like case-insensitive matching and allow you to define multiple patterns efficiently.

**Note:** Case-insensitive matching is only available through configuration files using the `caseInsensitive` property.

1. **Create a configuration file** (e.g., `config.json`):
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
       },
       {
         "find": "\\d{3}-\\d{2}-\\d{4}",
         "replace": "XXX-XX-XXXX",
         "regex": true
       }
     ],
     "compression": {
       "preserve": true,
       "level": 9
     }
   }
   ```

2. **Run with configuration file:**

   **Windows:**
   ```cmd
   python redactor.py input.pdf output.pdf --config config.json
   ```

   **macOS/Linux:**
   ```bash
   python3 redactor.py input.pdf output.pdf --config config.json
   ```

### Batch Processing

Process all PDFs in a directory:

**Windows:**
```cmd
python redactor.py --input-dir C:\pdfs --output-dir C:\redacted --config config.json
```

**macOS/Linux:**
```bash
python3 redactor.py --input-dir ./pdfs --output-dir ./redacted --config config.json
```

### Advanced Options

#### Regular Expression Matching

**Windows:**
```cmd
python redactor.py input.pdf output.pdf --find "\d{3}-\d{2}-\d{4}" --replace "XXX-XX-XXXX" --regex
```

**macOS/Linux:**
```bash
python3 redactor.py input.pdf output.pdf --find "\d{3}-\d{2}-\d{4}" --replace "XXX-XX-XXXX" --regex
```

#### Disable Compression

**Windows:**
```cmd
python redactor.py input.pdf output.pdf --find "sensitive" --replace "[REDACTED]" --no-compress
```

**macOS/Linux:**
```bash
python3 redactor.py input.pdf output.pdf --find "sensitive" --replace "[REDACTED]" --no-compress
```

#### Get PDF Information

**Windows:**
```cmd
python redactor.py input.pdf --info
```

**macOS/Linux:**
```bash
python3 redactor.py input.pdf --info
```

#### Verbose Output

**Windows:**
```cmd
python redactor.py input.pdf output.pdf --find "text" --replace "[REDACTED]" --verbose
```

**macOS/Linux:**
```bash
python3 redactor.py input.pdf output.pdf --find "text" --replace "[REDACTED]" --verbose
```

---

## Examples

### Example 1: Redact Social Security Numbers

**Windows:**
```cmd
python redactor.py document.pdf redacted.pdf --find "\d{3}-\d{2}-\d{4}" --replace "XXX-XX-XXXX" --regex
```

**macOS/Linux:**
```bash
python3 redactor.py document.pdf redacted.pdf --find "\d{3}-\d{2}-\d{4}" --replace "XXX-XX-XXXX" --regex
```

### Example 2: Redact Multiple Names (Case-Insensitive)

Create `names-config.json`:
```json
{
  "replacements": [
    {
      "find": ["John Doe", "Jane Smith", "Bob Johnson"],
      "replace": "[NAME REDACTED]",
      "regex": false,
      "caseInsensitive": true
    }
  ]
}
```

**Windows:**
```cmd
python redactor.py document.pdf redacted.pdf --config names-config.json
```

**macOS/Linux:**
```bash
python3 redactor.py document.pdf redacted.pdf --config names-config.json
```

### Example 3: Batch Processing with Verbose Output

**Windows:**
```cmd
python redactor.py --input-dir .\documents --output-dir .\redacted --config config.json --verbose
```

**macOS/Linux:**
```bash
python3 redactor.py --input-dir ./documents --output-dir ./redacted --config config.json --verbose
```

### Example 4: Multiple Replacements on Command Line

For multiple patterns, use a config file. For a single replacement, use command line:

**Windows:**
```cmd
python redactor.py input.pdf output.pdf --find "confidential" --replace "[CLASSIFIED]"
```

**macOS/Linux:**
```bash
python3 redactor.py input.pdf output.pdf --find "confidential" --replace "[CLASSIFIED]"
```

---

## Troubleshooting

### Windows Troubleshooting

#### Error: "python is not recognized"
- **Cause:** Python is not in the system PATH
- **Solution:** 
  1. Reinstall Python and check "Add Python to PATH"
  2. Or manually add Python to PATH:
     - Search for "Environment Variables" in Windows
     - Add Python installation directory to PATH variable
  3. Use `py` command instead: `py redactor.py --help`

#### Error: "No module named 'fitz'"
- **Cause:** PyMuPDF is not installed
- **Solution:** 
  ```cmd
  pip install PyMuPDF
  ```

#### Error: "Permission denied" when saving PDF
- **Cause:** Output file is open in another program or in a protected directory
- **Solution:**
  1. Close any PDF viewers that might have the file open
  2. Run Command Prompt as Administrator
  3. Choose a different output directory where you have write permissions

#### Error: Long path names
- **Cause:** Windows has a 260-character path limit (older versions)
- **Solution:**
  1. Use shorter file paths
  2. Enable long path support in Windows 10+:
     - Run `gpedit.msc`
     - Navigate to: Computer Configuration > Administrative Templates > System > Filesystem
     - Enable "Enable Win32 long paths"

### macOS Troubleshooting

#### Error: "command not found: python"
- **Cause:** Python 3 is installed as `python3` on macOS
- **Solution:** Use `python3` instead of `python`:
  ```bash
  python3 redactor.py --help
  ```

#### Error: "No module named 'fitz'"
- **Cause:** PyMuPDF is not installed
- **Solution:** 
  ```bash
  pip3 install PyMuPDF
  ```

#### Error: "Permission denied"
- **Cause:** No write permissions for output directory
- **Solution:**
  1. Check directory permissions: `ls -la`
  2. Use a directory where you have write permissions
  3. Or use `sudo` (not recommended): `sudo python3 redactor.py ...`

#### Error: SSL certificate errors during pip install
- **Cause:** Outdated certificates or network security software
- **Solution:**
  ```bash
  pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org PyMuPDF
  ```

### Linux Troubleshooting

#### Error: "command not found: python"
- **Cause:** Python 3 is installed as `python3` on most Linux distributions
- **Solution:** Use `python3` instead of `python`:
  ```bash
  python3 redactor.py --help
  ```

#### Error: "No module named 'fitz'"
- **Cause:** PyMuPDF is not installed
- **Solution:** 
  ```bash
  pip3 install PyMuPDF
  ```
  
  If you get a permissions error, use one of these:
  ```bash
  # Install for current user only
  pip3 install --user PyMuPDF
  
  # Or use sudo (system-wide)
  sudo pip3 install PyMuPDF
  
  # Or use virtual environment (recommended)
  python3 -m venv venv
  source venv/bin/activate
  pip install PyMuPDF
  ```

#### Error: "externally-managed-environment" (Python 3.11+)
- **Cause:** System prevents pip from installing packages globally
- **Solution:** Use a virtual environment:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

#### Error: Missing system dependencies
- **Cause:** Some systems may need additional libraries
- **Solution:** Install build dependencies:
  
  **Ubuntu/Debian:**
  ```bash
  sudo apt-get install python3-dev build-essential
  ```
  
  **Fedora/RHEL:**
  ```bash
  sudo dnf install python3-devel gcc
  ```

#### Error: "Permission denied" when writing output
- **Cause:** No write permissions for output directory
- **Solution:**
  1. Check directory permissions: `ls -la`
  2. Use a directory where you have write permissions
  3. Change permissions if needed: `chmod 755 /path/to/directory`

---

## Additional Resources

- **PyMuPDF Documentation:** https://pymupdf.readthedocs.io/
- **Project Repository:** https://github.com/wp-ryan/pdf-data-redactor
- **Configuration Examples:** See `config.example.json` in the repository

## License Note

This tool uses PyMuPDF, which is licensed under AGPL. If you need a more permissive license, consider using the `redactor-tools.py` implementation which uses external command-line tools with MIT/Apache licenses.

---

## Quick Reference

### Command Syntax

**Windows:**
```cmd
python redactor.py <input.pdf> <output.pdf> [options]
```

**macOS/Linux:**
```bash
python3 redactor.py <input.pdf> <output.pdf> [options]
```

### Common Options

| Option | Description |
|--------|-------------|
| `--find TEXT` | Text to find |
| `--replace TEXT` | Replacement text |
| `--regex` | Use regular expression matching |
| `--config FILE` | Load configuration from JSON file |
| `--input-dir DIR` | Input directory for batch processing |
| `--output-dir DIR` | Output directory for batch processing |
| `--no-compress` | Disable compression in output |
| `--compression-level 0-9` | Set compression level (default: 9) |
| `--info` | Show PDF information and exit |
| `--verbose`, `-v` | Enable verbose output |
| `--help` | Show help message |
