import io
import logging
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
from docx import Document
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Initialize tokenizer for token counting
encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    return len(encoding.encode(text))


def chunk_text_by_tokens(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    respect_sentences: bool = True
) -> List[str]:
    """
    Chunk text by tokens, respecting paragraph and sentence boundaries.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens
        respect_sentences: Whether to respect sentence boundaries
    
    Returns:
        List of text chunks
    """
    # Use RecursiveCharacterTextSplitter which respects paragraph/sentence boundaries
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=count_tokens,
        separators=["\n\n", "\n", ". ", " ", ""]  # Try to split at paragraphs, then sentences
    )
    
    chunks = text_splitter.split_text(text)
    return chunks


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
                page_chunks = chunk_text_by_tokens(page_data['text'])
                for idx, chunk_text in enumerate(page_chunks):
                    chunks.append({
                        'text': chunk_text,
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
                page_chunks = chunk_text_by_tokens(page_data['text'])
                for idx, chunk_text in enumerate(page_chunks):
                    chunks.append({
                        'text': chunk_text,
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
