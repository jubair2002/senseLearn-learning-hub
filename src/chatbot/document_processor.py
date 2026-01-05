"""
Document processing utilities for chatbot.
Extracts text from various document formats.
"""
import os
from typing import Optional, Tuple
from flask import current_app


class DocumentProcessor:
    """Service for processing documents and extracting text."""
    
    @staticmethod
    def extract_text(file_path: str, file_type: str) -> Optional[str]:
        """
        Extract text from a document file.
        
        Args:
            file_path: Full path to the file
            file_type: File extension (pdf, docx, txt, etc.)
            
        Returns:
            Extracted text or None if extraction fails
        """
        file_type_lower = file_type.lower()
        
        try:
            if file_type_lower == 'pdf':
                return DocumentProcessor._extract_from_pdf(file_path)
            elif file_type_lower in ['docx', 'doc']:
                return DocumentProcessor._extract_from_docx(file_path)
            elif file_type_lower == 'txt':
                return DocumentProcessor._extract_from_txt(file_path)
            else:
                current_app.logger.warning(f"Unsupported file type for text extraction: {file_type}")
                return None
        except Exception as e:
            current_app.logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return None
    
    @staticmethod
    def _extract_from_pdf(file_path: str) -> Optional[str]:
        """Extract text from PDF file."""
        text = None
        
        # Try pdfplumber first (better text extraction)
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        current_app.logger.warning(f"Error extracting text from PDF page {page_num}: {str(e)}")
                        continue
            if text.strip():
                current_app.logger.info(f"Successfully extracted {len(text)} characters from PDF using pdfplumber")
                return text.strip()
        except ImportError:
            current_app.logger.warning("pdfplumber not available, trying PyPDF2")
        except Exception as e:
            current_app.logger.warning(f"pdfplumber extraction failed: {str(e)}, trying PyPDF2")
        
        # Fallback to PyPDF2
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    current_app.logger.warning("PDF is encrypted, attempting to decrypt with empty password")
                    try:
                        pdf_reader.decrypt("")
                    except Exception as e:
                        current_app.logger.error(f"Could not decrypt PDF: {str(e)}")
                        return None
                
                text = ""
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        current_app.logger.warning(f"Error extracting text from PDF page {page_num}: {str(e)}")
                        continue
                
                if text.strip():
                    current_app.logger.info(f"Successfully extracted {len(text)} characters from PDF using PyPDF2")
                    return text.strip()
                else:
                    current_app.logger.warning("PDF extraction returned empty text - PDF may be image-based (scanned)")
                    return None
        except ImportError:
            current_app.logger.error("No PDF library available. Install PyPDF2 or pdfplumber.")
            return None
        except Exception as e:
            current_app.logger.error(f"Error extracting text from PDF with PyPDF2: {str(e)}")
            return None
        
        # If we get here, extraction failed
        current_app.logger.error("All PDF extraction methods failed")
        return None
    
    @staticmethod
    def _extract_from_docx(file_path: str) -> Optional[str]:
        """Extract text from DOCX file."""
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip() if text.strip() else None
        except ImportError:
            current_app.logger.warning("python-docx not installed. Cannot extract text from DOCX files.")
            return None
        except Exception as e:
            current_app.logger.error(f"Error extracting text from DOCX: {str(e)}")
            return None
    
    @staticmethod
    def _extract_from_txt(file_path: str) -> Optional[str]:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                return text.strip() if text.strip() else None
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read()
                    return text.strip() if text.strip() else None
            except Exception as e:
                current_app.logger.error(f"Error reading TXT file: {str(e)}")
                return None
        except Exception as e:
            current_app.logger.error(f"Error extracting text from TXT: {str(e)}")
            return None

