import io
import logging
import re
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
from docx import Document

logger = logging.getLogger(__name__)

# Approximate tokens per character (GPT models average ~4 chars per token)
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate token count based on character count."""
    return len(text) // CHARS_PER_TOKEN


def recursive_text_split(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: List[str] = None
) -> List[str]:
    """
    Split text recursively using different separators until chunks are small enough.
    
    Args:
        text: Text to split
        chunk_size: Target chunk size in estimated tokens
        chunk_overlap: Overlap between chunks in estimated tokens
        separators: List of separators to try, in order of preference
    
    Returns:
        List of text chunks
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", ", ", " ", ""]
    
    # Convert token targets to character targets
    max_chars = chunk_size * CHARS_PER_TOKEN
    overlap_chars = chunk_overlap * CHARS_PER_TOKEN
    
    # Base case: text is small enough
    if len(text) <= max_chars:
        return [text.strip()] if text.strip() else []
    
    # Try each separator
    for i, separator in enumerate(separators):
        if separator == "":
            # Last resort: split by character count
            chunks = []
            start = 0
            while start < len(text):
                end = start + max_chars
                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                start = end - overlap_chars
                if start < 0:
                    start = 0
                if start >= len(text):
                    break
            return chunks
        
        # Split by current separator
        parts = text.split(separator)
        
        if len(parts) == 1:
            # Separator not found, try next one
            continue
        
        # Merge parts into chunks that fit the size limit
        chunks = []
        current_chunk = ""
        
        for part in parts:
            # Add separator back (except for the first part)
            part_with_sep = part if not current_chunk else separator + part
            
            if len(current_chunk) + len(part_with_sep) <= max_chars:
                current_chunk += part_with_sep
            else:
                # Current chunk is full
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                # Check if the part itself is too big
                if len(part) > max_chars:
                    # Recursively split with next separator
                    sub_chunks = recursive_text_split(
                        part,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        separators=separators[i+1:]
                    )
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    # Start new chunk with overlap from previous
                    if chunks and overlap_chars > 0:
                        # Get overlap from end of last chunk
                        last_chunk = chunks[-1]
                        overlap_text = last_chunk[-overlap_chars:] if len(last_chunk) > overlap_chars else last_chunk
                        current_chunk = overlap_text + separator + part
                    else:
                        current_chunk = part
        
        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    return [text.strip()] if text.strip() else []


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:
    """
    Chunk text by estimated tokens, respecting paragraph and sentence boundaries.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in estimated tokens
        chunk_overlap: Overlap between chunks in estimated tokens
    
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    
    # Clean up text
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.strip()
    
    return recursive_text_split(text, chunk_size, chunk_overlap)


def extract_text_from_pdf_bytes(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """Extract text from PDF file bytes, returning pages with text and page numbers."""
    pages = []
    try:
        pdf_file = io.BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            text = page.extract_text()
            if text.strip():
                pages.append({
                    'text': text,
                    'page_number': page_num
                })
        logger.info(f"Extracted {len(pages)} pages from PDF: {filename}")
    except Exception as e:
        logger.error(f"Error extracting text from PDF {filename}: {e}")
        raise
    return pages


def extract_text_from_docx_bytes(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """Extract text from Word document bytes."""
    try:
        docx_file = io.BytesIO(file_bytes)
        doc = Document(docx_file)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        
        text = '\n\n'.join(full_text)
        if text.strip():
            logger.info(f"Extracted text from DOCX: {filename}")
            return [{
                'text': text,
                'page_number': None  # Word docs don't have clear page numbers
            }]
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {filename}: {e}")
        raise
    return []


def process_uploaded_file(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Process an uploaded file (PDF or Word) and return chunks with metadata.
    
    Args:
        file_bytes: The file content as bytes
        filename: Original filename
    
    Returns:
        List of chunks with metadata
    """
    file_ext = Path(filename).suffix.lower()
    chunks = []
    
    try:
        if file_ext == '.pdf':
            pages = extract_text_from_pdf_bytes(file_bytes, filename)
            for page_data in pages:
                page_chunks = chunk_text(page_data['text'])
                for idx, chunk_text_content in enumerate(page_chunks):
                    chunks.append({
                        'text': chunk_text_content,
                        'source_file': filename,
                        'folder_path': None,
                        'page_number': page_data['page_number'],
                        'chunk_index': idx,
                        'metadata': {
                            'file_path': filename,
                            'file_type': 'pdf'
                        }
                    })
        
        elif file_ext in ['.docx', '.doc']:
            pages = extract_text_from_docx_bytes(file_bytes, filename)
            for page_data in pages:
                page_chunks = chunk_text(page_data['text'])
                for idx, chunk_text_content in enumerate(page_chunks):
                    chunks.append({
                        'text': chunk_text_content,
                        'source_file': filename,
                        'folder_path': None,
                        'page_number': page_data['page_number'],
                        'chunk_index': idx,
                        'metadata': {
                            'file_path': filename,
                            'file_type': 'docx'
                        }
                    })
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return []
        
        logger.info(f"Processed uploaded file {filename}: {len(chunks)} chunks created")
        
    except Exception as e:
        logger.error(f"Error processing uploaded file {filename}: {e}")
        raise
    
    return chunks
