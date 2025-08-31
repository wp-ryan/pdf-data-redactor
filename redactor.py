#!/usr/bin/env python3
"""
PDF Data Redactor - Replace sensitive data in PDF files
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import fitz  # PyMuPDF
import logging
import tempfile
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFRedactor:
    """Main class for PDF text redaction"""
    
    def __init__(self):
        self.replacements = []
        self.preserve_compression = True
        self.compression_level = 9  # 0-9, where 9 is maximum compression
    
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
        
        # Load compression settings if present
        if 'compression' in config:
            self.preserve_compression = config['compression'].get('preserve', True)
            self.compression_level = config['compression'].get('level', 9)
    
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
    
    def get_pdf_info(self, pdf_path: str) -> Dict:
        """Get information about PDF including compression status"""
        try:
            doc = fitz.open(pdf_path)
            info = {
                'pages': len(doc),
                'is_encrypted': doc.is_encrypted,
                'metadata': doc.metadata,
                'compressed_size': Path(pdf_path).stat().st_size,
                'uses_compression': False,
                'compression_objects': 0
            }
            
            # Check for compressed objects
            for xref in range(1, doc.xref_length()):
                try:
                    if doc.xref_is_stream(xref):
                        info['uses_compression'] = True
                        info['compression_objects'] += 1
                except:
                    continue
            
            doc.close()
            return info
        except Exception as e:
            logger.error(f"Error getting PDF info: {str(e)}")
            return {}
    
    def decompress_pdf(self, input_path: str, output_path: str) -> bool:
        """Decompress a PDF file"""
        try:
            doc = fitz.open(input_path)
            
            # Save with no compression for easier text manipulation
            doc.save(output_path, 
                    deflate=False,  # No compression
                    garbage=4,      # Maximum garbage collection
                    clean=True)     # Clean up unused objects
            
            doc.close()
            return True
        except Exception as e:
            logger.error(f"Error decompressing PDF: {str(e)}")
            return False
    
    def compress_pdf(self, input_path: str, output_path: str, level: int = 9) -> bool:
        """Compress a PDF file"""
        try:
            doc = fitz.open(input_path)
            
            # Save with compression
            doc.save(output_path,
                    deflate=True,           # Enable compression
                    deflate_level=level,    # Compression level (0-9)
                    garbage=4,              # Maximum garbage collection
                    clean=True)             # Clean up unused objects
            
            doc.close()
            return True
        except Exception as e:
            logger.error(f"Error compressing PDF: {str(e)}")
            return False
    
    def redact_pdf(self, input_path: str, output_path: str) -> bool:
        """Process a single PDF file with compression handling"""
        try:
            logger.info(f"Processing: {input_path}")
            
            # Get PDF info
            pdf_info = self.get_pdf_info(input_path)
            logger.debug(f"PDF info: {pdf_info}")
            
            # Create temporary file for processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Decompress if needed for better text processing
                if pdf_info.get('uses_compression', False):
                    logger.info("Decompressing PDF for processing...")
                    if not self.decompress_pdf(input_path, temp_path):
                        shutil.copy2(input_path, temp_path)
                else:
                    shutil.copy2(input_path, temp_path)
                
                # Open PDF for processing
                pdf_document = fitz.open(temp_path)
                
                # Track if any changes were made
                changes_made = False
                
                # Process each page
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    
                    # Get all text blocks with their positions
                    blocks = page.get_text("dict")
                    
                    # Process each text block
                    for block in blocks.get("blocks", []):
                        if block.get("type") == 0:  # Text block
                            for line in block.get("lines", []):
                                for span in line.get("spans", []):
                                    original_text = span.get("text", "")
                                    if not original_text.strip():
                                        continue
                                    
                                    processed_text = self.process_text(original_text)
                                    
                                    if processed_text != original_text:
                                        changes_made = True
                                        # Get the bounding box of the text
                                        bbox = fitz.Rect(span["bbox"])
                                        
                                        # Add redaction annotation
                                        page.add_redact_annot(bbox)
                                        
                                        # Store the replacement text and position
                                        font_size = span.get("size", 11)
                                        font_name = span.get("font", "Helvetica")
                                        text_color = span.get("color", 0)
                                        
                                        # Apply redactions
                                        page.apply_redactions()
                                        
                                        # Add replacement text
                                        page.insert_text(
                                            bbox.tl,  # top-left point
                                            processed_text,
                                            fontsize=font_size,
                                            fontname=font_name,
                                            color=text_color
                                        )
                
                # Save the modified PDF
                if changes_made:
                    logger.info(f"Applied text replacements to {page_num + 1} pages")
                else:
                    logger.info("No text replacements were needed")
                
                # Save with appropriate compression
                if self.preserve_compression and pdf_info.get('uses_compression', False):
                    logger.info(f"Saving with compression (level {self.compression_level})...")
                    pdf_document.save(output_path,
                                    deflate=True,
                                    deflate_level=self.compression_level,
                                    garbage=4,
                                    clean=True)
                else:
                    pdf_document.save(output_path,
                                    garbage=4,
                                    clean=True)
                
                pdf_document.close()
                
                # Log size comparison
                original_size = Path(input_path).stat().st_size
                final_size = Path(output_path).stat().st_size
                size_diff = final_size - original_size
                size_pct = (size_diff / original_size) * 100 if original_size > 0 else 0
                
                logger.info(f"Original size: {original_size:,} bytes")
                logger.info(f"Final size: {final_size:,} bytes ({size_pct:+.1f}%)")
                logger.info(f"Successfully created: {output_path}")
                
                return True
                
            finally:
                # Clean up temporary file
                if Path(temp_path).exists():
                    Path(temp_path).unlink()
                    
        except Exception as e:
            logger.error(f"Error processing {input_path}: {str(e)}")
            return False
    
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
        total_original_size = 0
        total_final_size = 0
        
        for pdf_file in pdf_files:
            output_file = output_path / pdf_file.name
            
            # Track sizes
            total_original_size += pdf_file.stat().st_size
            
            if self.redact_pdf(str(pdf_file), str(output_file)):
                success_count += 1
                total_final_size += output_file.stat().st_size
        
        # Summary
        logger.info(f"Successfully processed {success_count}/{len(pdf_files)} files")
        if success_count > 0:
            size_diff = total_final_size - total_original_size
            size_pct = (size_diff / total_original_size) * 100 if total_original_size > 0 else 0
            logger.info(f"Total size change: {size_diff:,} bytes ({size_pct:+.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Replace sensitive data in PDF files with compression support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.pdf output.pdf --find "John Doe" --replace "[REDACTED]"
  %(prog)s input.pdf output.pdf --find "\\d{3}-\\d{2}-\\d{4}" --replace "XXX-XX-XXXX" --regex
  %(prog)s input.pdf output.pdf --config replacements.json
  %(prog)s --input-dir ./pdfs --output-dir ./redacted --config replacements.json
  %(prog)s input.pdf output.pdf --find "SSN" --replace "[REDACTED]" --no-compress
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
    
    # Compression options
    parser.add_argument('--no-compress', action='store_true', 
                       help='Do not compress output PDF')
    parser.add_argument('--compression-level', type=int, default=9, 
                       choices=range(0, 10), metavar='0-9',
                       help='Compression level (0=none, 9=maximum, default: 9)')
    
    # Other options
    parser.add_argument('--info', action='store_true', 
                       help='Show PDF information and exit')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Info mode
    if args.info:
        if not args.input:
            parser.error("--info requires an input file")
        redactor = PDFRedactor()
        info = redactor.get_pdf_info(args.input)
        print(f"\nPDF Information for: {args.input}")
        print(f"Pages: {info.get('pages', 'Unknown')}")
        print(f"Encrypted: {info.get('is_encrypted', 'Unknown')}")
        print(f"Uses Compression: {info.get('uses_compression', 'Unknown')}")
        print(f"Compressed Objects: {info.get('compression_objects', 0)}")
        print(f"File Size: {info.get('compressed_size', 0):,} bytes")
        if info.get('metadata'):
            print("\nMetadata:")
            for key, value in info['metadata'].items():
                if value:
                    print(f"  {key}: {value}")
        sys.exit(0)
    
    # Validate arguments
    if args.input_dir and args.output_dir:
        # Batch mode
        if not args.config and not (args.find and args.replace):
            parser.error("Batch mode requires either --config or --find/--replace")
    elif args.input and args.output:
        # Single file mode
        if not args.config and not (args.find and args.replace):
            parser.error("Single file mode requires either --config or --find/--replace")
    else:
        parser.error("Specify either input/output files or --input-dir/--output-dir")
    
    # Create redactor instance
    redactor = PDFRedactor()
    
    # Set compression options
    redactor.preserve_compression = not args.no_compress
    redactor.compression_level = args.compression_level
    
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
