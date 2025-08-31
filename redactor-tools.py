#!/usr/bin/env python3
"""
PDF Data Redactor - Using external tools for MIT license compatibility
This version uses subprocess calls to external tools, avoiding AGPL dependencies
"""

import argparse
import json
import re
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFRedactorTools:
    """PDF text redaction using external tools"""
    
    def __init__(self):
        self.replacements = []
        self.required_tools = ['qpdf', 'pdftotext', 'ps2pdf']
        self.check_tools()
    
    def check_tools(self):
        """Check if required external tools are installed"""
        missing_tools = []
        for tool in self.required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)
        
        if missing_tools:
            logger.error(f"Missing required tools: {', '.join(missing_tools)}")
            logger.error("Install them using:")
            logger.error("  Ubuntu/Debian: sudo apt-get install qpdf poppler-utils ghostscript")
            logger.error("  macOS: brew install qpdf poppler ghostscript")
            logger.error("  Windows: Use WSL or install tools individually")
            sys.exit(1)
    
    def add_replacement(self, find: str, replace: str, is_regex: bool = False, case_insensitive: bool = False):
        """Add a replacement rule"""
        self.replacements.append({
            'find': find,
            'replace': replace,
            'regex': is_regex,
            'caseInsensitive': case_insensitive
        })
    
    def load_config(self, config_path: str):
        """Load replacement rules from configuration file"""
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        for rule in config.get('replacements', []):
            self.add_replacement(
                rule['find'],
                rule['replace'],
                rule.get('regex', False),
                rule.get('caseInsensitive', False)
            )
    
    def process_text(self, text: str) -> str:
        """Apply all replacement rules to text"""
        result = text
        
        for rule in self.replacements:
            if rule['regex']:
                flags = re.IGNORECASE if rule.get('caseInsensitive', False) else 0
                result = re.sub(rule['find'], rule['replace'], result, flags=flags)
            else:
                if rule.get('caseInsensitive', False):
                    # For case insensitive string replacement, we need to find all occurrences
                    # while preserving the original case of the surrounding text
                    find_text = rule['find']
                    replace_text = rule['replace']
                    result_lower = result.lower()
                    find_lower = find_text.lower()
                    
                    # Find all positions where the text occurs (case insensitive)
                    new_result = ""
                    last_pos = 0
                    pos = result_lower.find(find_lower)
                    
                    while pos != -1:
                        # Add text before the match
                        new_result += result[last_pos:pos]
                        # Add the replacement
                        new_result += replace_text
                        # Move past the match
                        last_pos = pos + len(find_text)
                        # Find next occurrence
                        pos = result_lower.find(find_lower, last_pos)
                    
                    # Add remaining text
                    new_result += result[last_pos:]
                    result = new_result
                else:
                    result = result.replace(rule['find'], rule['replace'])
        
        return result
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF using pdftotext"""
        try:
            result = subprocess.run(
                ['pdftotext', '-layout', pdf_path, '-'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def pdf_to_ps(self, pdf_path: str, ps_path: str) -> bool:
        """Convert PDF to PostScript"""
        try:
            subprocess.run(
                ['pdf2ps', pdf_path, ps_path],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting to PostScript: {e}")
            return False
    
    def ps_to_pdf(self, ps_path: str, pdf_path: str, compress: bool = True) -> bool:
        """Convert PostScript to PDF with optional compression"""
        try:
            cmd = ['ps2pdf']
            if compress:
                # Use compression settings
                cmd.extend([
                    '-dPDFSETTINGS=/printer',
                    '-dCompressPages=true',
                    '-dCompressStreams=true'
                ])
            else:
                cmd.extend([
                    '-dCompressPages=false',
                    '-dCompressStreams=false'
                ])
            
            cmd.extend([ps_path, pdf_path])
            
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting to PDF: {e}")
            return False
    
    def decompress_pdf(self, input_path: str, output_path: str) -> bool:
        """Decompress PDF using qpdf"""
        try:
            subprocess.run(
                ['qpdf', '--stream-data=uncompress', '--decode-level=all', 
                 input_path, output_path],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error decompressing PDF: {e}")
            return False
    
    def compress_pdf(self, input_path: str, output_path: str) -> bool:
        """Compress PDF using qpdf"""
        try:
            subprocess.run(
                ['qpdf', '--compress-streams=y', '--object-streams=generate',
                 input_path, output_path],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error compressing PDF: {e}")
            return False
    
    def process_postscript(self, ps_path: str) -> bool:
        """Process PostScript file to replace text"""
        try:
            # Read the PostScript file
            with open(ps_path, 'r', encoding='latin-1') as f:
                content = f.read()
            
            # Apply replacements
            modified = False
            for rule in self.replacements:
                if rule['regex']:
                    new_content = re.sub(rule['find'], rule['replace'], content)
                else:
                    new_content = content.replace(rule['find'], rule['replace'])
                
                if new_content != content:
                    modified = True
                    content = new_content
            
            if modified:
                # Write back the modified content
                with open(ps_path, 'w', encoding='latin-1') as f:
                    f.write(content)
                logger.info("Text replacements applied successfully")
            else:
                logger.info("No text replacements were needed")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing PostScript: {e}")
            return False
    
    def redact_pdf(self, input_path: str, output_path: str) -> bool:
        """Process a single PDF file using external tools"""
        logger.info(f"Processing: {input_path}")
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Step 1: Extract text to see what needs redaction
            text_content = self.extract_text(input_path)
            processed_text = self.process_text(text_content)
            
            if processed_text == text_content:
                logger.info("No replacements needed, copying file as-is")
                shutil.copy2(input_path, output_path)
                return True
            
            logger.info("Text replacements needed, processing PDF...")
            
            # Step 2: Decompress PDF
            decompressed_pdf = temp_path / "decompressed.pdf"
            if not self.decompress_pdf(input_path, str(decompressed_pdf)):
                logger.warning("Failed to decompress, using original")
                decompressed_pdf = input_path
            
            # Step 3: Convert to PostScript
            ps_file = temp_path / "document.ps"
            if not self.pdf_to_ps(str(decompressed_pdf), str(ps_file)):
                logger.error("Failed to convert to PostScript")
                return False
            
            # Step 4: Process PostScript file
            if not self.process_postscript(str(ps_file)):
                logger.error("Failed to process PostScript")
                return False
            
            # Step 5: Convert back to PDF
            processed_pdf = temp_path / "processed.pdf"
            if not self.ps_to_pdf(str(ps_file), str(processed_pdf)):
                logger.error("Failed to convert back to PDF")
                return False
            
            # Step 6: Final compression/optimization
            subprocess.run(
                ['qpdf', '--linearize', str(processed_pdf), output_path],
                check=True,
                capture_output=True
            )
            
            # Log size comparison
            original_size = Path(input_path).stat().st_size
            final_size = Path(output_path).stat().st_size
            size_diff = final_size - original_size
            size_pct = (size_diff / original_size) * 100 if original_size > 0 else 0
            
            logger.info(f"Original size: {original_size:,} bytes")
            logger.info(f"Final size: {final_size:,} bytes ({size_pct:+.1f}%)")
            logger.info(f"Successfully created: {output_path}")
            
            return True
    
    def process_directory(self, input_dir: str, output_dir: str):
        """Process all PDFs in a directory"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Process all PDF files
        pdf_files = list(input_path.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        success_count = 0
        for pdf_file in pdf_files:
            output_file = output_path / pdf_file.name
            if self.redact_pdf(str(pdf_file), str(output_file)):
                success_count += 1
        
        logger.info(f"Successfully processed {success_count}/{len(pdf_files)} files")


def main():
    parser = argparse.ArgumentParser(
        description="Replace sensitive data in PDF files using external tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This version uses external tools to maintain MIT license compatibility.
Required tools: qpdf, pdftotext, ps2pdf, pdf2ps

Examples:
  %(prog)s input.pdf output.pdf --find "John Doe" --replace "[REDACTED]"
  %(prog)s input.pdf output.pdf --find "\\d{3}-\\d{2}-\\d{4}" --replace "XXX-XX-XXXX" --regex
  %(prog)s input.pdf output.pdf --config replacements.json
  %(prog)s --input-dir ./pdfs --output-dir ./redacted --config replacements.json
        """
    )
    
    # Input/Output arguments
    parser.add_argument('input', nargs='?', help='Input PDF file')
    parser.add_argument('output', nargs='?', help='Output PDF file')
    parser.add_argument('--input-dir', help='Input directory for batch processing')
    parser.add_argument('--output-dir', help='Output directory for batch processing')
    
    # Replacement arguments
    parser.add_argument('--find', help='Text to find')
    parser.add_argument('--replace', help='Replacement text')
    parser.add_argument('--regex', action='store_true', help='Use regular expression matching')
    parser.add_argument('--config', help='Configuration file with replacement rules')
    
    # Other options
    parser.add_argument('--check-tools', action='store_true', 
                       help='Check if required tools are installed')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create redactor instance
    redactor = PDFRedactorTools()
    
    if args.check_tools:
        print("All required tools are installed!")
        sys.exit(0)
    
    # Validate arguments
    if args.input_dir and args.output_dir:
        if not args.config and not (args.find and args.replace):
            parser.error("Batch mode requires either --config or --find/--replace")
    elif args.input and args.output:
        if not args.config and not (args.find and args.replace):
            parser.error("Single file mode requires either --config or --find/--replace")
    else:
        parser.error("Specify either input/output files or --input-dir/--output-dir")
    
    # Load replacements
    if args.config:
        redactor.load_config(args.config)
    
    if args.find and args.replace:
        redactor.add_replacement(args.find, args.replace, args.regex)
    
    # Process files
    if args.input_dir and args.output_dir:
        redactor.process_directory(args.input_dir, args.output_dir)
    else:
        success = redactor.redact_pdf(args.input, args.output)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
