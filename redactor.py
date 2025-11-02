#!/usr/bin/env python3
"""
PDF Data Redactor - Replace sensitive data in PDF files
"""

import argparse
import json
import re
import sys
import time
import gc
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
            find_patterns = rule['find']
            if isinstance(find_patterns, str):
                find_patterns = [find_patterns]
            elif not isinstance(find_patterns, list):
                raise ValueError(f"Invalid 'find' value: {find_patterns}. Must be string or array of strings.")
            
            for pattern in find_patterns:
                self.add_replacement(
                    pattern,
                    rule['replace'],
                    rule.get('regex', False),
                    rule.get('caseInsensitive', False)
                )
        
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
                    find_text = rule['find']
                    replace_text = rule['replace']
                    result_lower = result.lower()
                    find_lower = find_text.lower()
                    
                    new_result = ""
                    last_pos = 0
                    pos = result_lower.find(find_lower)
                    
                    while pos != -1:
                        new_result += result[last_pos:pos]
                        new_result += replace_text
                        last_pos = pos + len(find_text)
                        pos = result_lower.find(find_lower, last_pos)
                    
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
            
            doc.save(output_path, 
                    deflate=False,
                    garbage=4,
                    clean=True)
            
            doc.close()
            return True
        except Exception as e:
            logger.error(f"Error decompressing PDF: {str(e)}")
            return False
    
    def compress_pdf(self, input_path: str, output_path: str, level: int = 9) -> bool:
        """Compress a PDF file"""
        try:
            doc = fitz.open(input_path)
            
            doc.save(output_path,
                    deflate=True,
                    garbage=4,
                    clean=True)
            
            doc.close()
            return True
        except Exception as e:
            logger.error(f"Error compressing PDF: {str(e)}")
            return False
    
    def rgb_from_srgb(self, srgb: int) -> Tuple[float, float, float]:
        """Convert sRGB integer to RGB float tuple"""
        return (
            ((srgb >> 16) & 0xFF) / 255.0,
            ((srgb >> 8) & 0xFF) / 255.0,
            (srgb & 0xFF) / 255.0
        )
    
    def redact_pdf(self, input_path: str, output_path: str) -> bool:
        """Process a single PDF file with compression handling"""
        try:
            logger.info(f"Processing: {input_path}")
            
            if not Path(input_path).is_file():
                logger.error(f"Input file {input_path} does not exist or is not accessible")
                return False
            
            pdf_info = self.get_pdf_info(input_path)
            logger.debug(f"PDF info: {pdf_info}")
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                logger.debug(f"Created temporary file: {temp_path}")
                if pdf_info.get('uses_compression', False):
                    logger.info("Decompressing PDF for processing...")
                    if not self.decompress_pdf(input_path, temp_path):
                        logger.info("Decompression failed, copying input file instead")
                        shutil.copy2(input_path, temp_path)
                else:
                    logger.info("Copying input file to temporary location")
                    shutil.copy2(input_path, temp_path)
                
                if not Path(temp_path).exists():
                    logger.error(f"Temporary file {temp_path} was not created")
                    return False
                
                logger.debug(f"Opening temporary file: {temp_path}")
                pdf_document = fitz.open(temp_path)
                
                try:
                    changes_made = False
                    
                    base_font_map = {
                        "Helvetica": "helv",
                        "Arial": "helv",
                        "Times-Roman": "tiro",
                        "Times New Roman": "tiro",
                        "Courier": "cour",
                        "Courier New": "cour",
                        "Symbol": "symb",
                        "ZapfDingbats": "zadb",
                        # Add more mappings as needed
                    }
                    
                    for page_num in range(len(pdf_document)):
                        page = pdf_document[page_num]
                        
                        blocks = page.get_text("dict")["blocks"]
                        
                        fonts = page.get_fonts(full=True)
                        font_dict = {}
                        for font in fonts:
                            if len(font) > 6 and font[6] is not None:
                                ref_name = font[4]
                                buffer = font[6]
                                font_dict[ref_name] = buffer
                        
                        to_redact = []
                        to_insert = []
                        
                        for block in blocks:
                            if block.get("type") == 0:
                                for line in block.get("lines", []):
                                    for span in line.get("spans", []):
                                        original_text = span.get("text", "")
                                        if not original_text.strip():
                                            continue
                                        
                                        processed_text = self.process_text(original_text)
                                        
                                        if processed_text != original_text:
                                            changes_made = True
                                            bbox = fitz.Rect(span["bbox"])
                                            to_redact.append(bbox)
                                            orig_font = span.get("font", "Helvetica")
                                            font_size = span.get("size", 11)
                                            text_color = self.rgb_from_srgb(span.get("color", 0))
                                            font_buffer = font_dict.get(orig_font, None)
                                            # FIXED: Use span["origin"] (baseline position) instead of bbox for accurate placement
                                            origin = fitz.Point(span["origin"])
                                            to_insert.append((origin, processed_text, orig_font, font_size, text_color, font_buffer))
                        
                        for bbox in to_redact:
                            page.add_redact_annot(bbox)
                        
                        page.apply_redactions()
                        
                        for origin, text, fontname, fontsize, color, fontbuffer in to_insert:
                            if fontbuffer is not None:
                                page.insert_font(fontname=fontname, fontbuffer=fontbuffer)
                                # FIXED: Insert at origin instead of bbox.tl
                                page.insert_text(
                                    origin,
                                    text,
                                    fontname=fontname,
                                    fontsize=fontsize,
                                    color=color
                                )
                            else:
                                standard_name = base_font_map.get(fontname, "helv")
                                # FIXED: Insert at origin instead of bbox.tl
                                page.insert_text(
                                    origin,
                                    text,
                                    fontname=standard_name,
                                    fontsize=fontsize,
                                    color=color
                                )
                    
                    if changes_made:
                        logger.info("Applied text replacements")
                    else:
                        logger.info("No text replacements were needed")
                    
                    logger.debug(f"Saving output to: {output_path}")
                    if self.preserve_compression and pdf_info.get('uses_compression', False):
                        logger.info("Saving with compression...")
                        pdf_document.save(output_path,
                                        deflate=True,
                                        garbage=4,
                                        clean=True)
                    else:
                        logger.info("Saving without compression...")
                        pdf_document.save(output_path,
                                        garbage=4,
                                        clean=True)
                    
                    original_size = Path(input_path).stat().st_size
                    final_size = Path(output_path).stat().st_size
                    logger.info(f"Original size: {original_size:,} bytes")
                    logger.info(f"Final size: {final_size:,} bytes ({(final_size - original_size) / original_size * 100:+.1f}%)")
                    logger.info(f"Successfully created: {output_path}")
                    
                    return True
                
                finally:
                    pdf_document.close()
                    gc.collect()
                    time.sleep(0.5)
                    
            finally:
                if Path(temp_path).exists():
                    for _ in range(5):
                        try:
                            Path(temp_path).unlink()
                            logger.debug(f"Successfully deleted temp file: {temp_path}")
                            break
                        except PermissionError as e:
                            logger.warning(f"Failed to delete temp file {temp_path}: {str(e)}. Retrying...")
                            time.sleep(0.3)
                    else:
                        logger.warning(f"Could not delete temp file {temp_path}. It will remain in the temp directory.")
                    
        except Exception as e:
            logger.error(f"Error processing {input_path}: {str(e)}")
            return False
    
    def process_directory(self, input_dir: str, output_dir: str):
        """Process all PDFs in a directory"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        pdf_files = list(input_path.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        success_count = 0
        total_original_size = 0
        total_final_size = 0
        
        for pdf_file in pdf_files:
            output_file = output_path / pdf_file.name
            
            total_original_size += pdf_file.stat().st_size
            
            if self.redact_pdf(str(pdf_file), str(output_file)):
                success_count += 1
                total_final_size += output_file.stat().st_size
        
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
    
    parser.add_argument('input', nargs='?', help='Input PDF file')
    parser.add_argument('output', nargs='?', help='Output PDF file')
    parser.add_argument('--input-dir', help='Input directory for batch processing')
    parser.add_argument('--output-dir', help='Output directory for batch processing')
    
    parser.add_argument('--find', help='Text to find')
    parser.add_argument('--replace', help='Replacement text')
    parser.add_argument('--regex', action='store_true', help='Use regular expression matching')
    parser.add_argument('--config', help='Configuration file with replacement rules')
    
    parser.add_argument('--no-compress', action='store_true', 
                       help='Do not compress output PDF')
    parser.add_argument('--compression-level', type=int, default=9, 
                       choices=range(0, 10), metavar='0-9',
                       help='Compression level (0=none, 9=maximum, default: 9)')
    
    parser.add_argument('--info', action='store_true', 
                       help='Show PDF information and exit')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
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
    
    if args.input_dir and args.output_dir:
        if not args.config and not (args.find and args.replace):
            parser.error("Batch mode requires either --config or --find/--replace")
    elif args.input and args.output:
        if not args.config and not (args.find and args.replace):
            parser.error("Single file mode requires either --config or --find/--replace")
    else:
        parser.error("Specify either input/output files or --input-dir/--output-dir")
    
    redactor = PDFRedactor()
    
    redactor.preserve_compression = not args.no_compress
    redactor.compression_level = args.compression_level
    
    if args.config:
        redactor.load_config(args.config)
    
    if args.find and args.replace:
        redactor.add_replacement(args.find, args.replace, args.regex)
    
    if args.input_dir and args.output_dir:
        redactor.process_directory(args.input_dir, args.output_dir)
    else:
        success = redactor.redact_pdf(args.input, args.output)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
