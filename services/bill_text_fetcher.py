"""
Service for fetching and extracting full bill text from Missouri Legislature.

This module provides functionality to:
1. Fetch bill text from PDFs or HTML pages
2. Extract clean text for database storage
3. Prepare text for LLM processing
"""
import re
import io
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup
from typing import Optional, Dict, Tuple

# Try to import PDF parsing libraries
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


def fetch_bill_text_from_url(url: str, timeout: int = 30) -> Optional[str]:
    """
    Fetch bill text from a URL (PDF or HTML).
    
    Args:
        url: URL to fetch from
        timeout: Request timeout in seconds
        
    Returns:
        Extracted text or None if failed
    """
    if not url:
        return None
    
    try:
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'pdf' in content_type or url.lower().endswith('.pdf'):
                # PDF content
                pdf_data = response.read()
                return extract_text_from_pdf(pdf_data)
            else:
                # HTML content
                html = response.read().decode('utf-8', errors='ignore')
                return extract_text_from_html(html)
                
    except (URLError, HTTPError, Exception) as e:
        print(f"Error fetching bill text from {url}: {e}")
        return None


def extract_text_from_pdf(pdf_data: bytes) -> Optional[str]:
    """
    Extract text from PDF data using available libraries.
    
    Args:
        pdf_data: Raw PDF bytes
        
    Returns:
        Extracted text or None if failed
    """
    # Try pdfplumber first (better text extraction)
    if PDFPLUMBER_AVAILABLE:
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                if text_parts:
                    full_text = '\n\n'.join(text_parts)
                    return clean_bill_text(full_text)
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
    
    # Fall back to PyPDF2
    if PYPDF2_AVAILABLE:
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            text_parts = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            if text_parts:
                full_text = '\n\n'.join(text_parts)
                return clean_bill_text(full_text)
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
    
    print("No PDF parsing library available. Install pdfplumber or PyPDF2.")
    return None


def extract_text_from_html(html: str) -> Optional[str]:
    """
    Extract bill text from HTML page.
    
    Args:
        html: HTML content
        
    Returns:
        Extracted text or None if failed
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find bill content container
        # Common patterns in MO Legislature pages
        content = None
        
        # Look for specific content divs/sections
        for selector in ['div.billtext', 'div.bill-content', 'div#content', 'main', 'article']:
            content = soup.select_one(selector)
            if content:
                break
        
        if not content:
            # Fall back to body
            content = soup.find('body')
        
        if content:
            text = content.get_text(separator='\n', strip=True)
            return clean_bill_text(text)
        
        return None
        
    except Exception as e:
        print(f"Error extracting text from HTML: {e}")
        return None


def clean_bill_text(text: str) -> str:
    """
    Clean and normalize bill text for storage and LLM processing.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Remove trailing/leading whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove page numbers (common pattern: "Page 1 of 10")
    text = re.sub(r'Page \d+ of \d+', '', text)
    
    # Remove excessive spaces
    text = re.sub(r' {3,}', '  ', text)
    
    # Remove common PDF artifacts
    text = re.sub(r'\x0c', '', text)  # Form feed
    
    return text.strip()


def get_bill_pdfs(bill_number: str, year: str = '2025', code: str = 'R') -> Dict[str, Optional[str]]:
    """
    Get PDF URLs for a bill from Missouri Legislature website.
    
    Args:
        bill_number: Bill number (e.g., 'HB101')
        year: Legislative year
        code: Session code
        
    Returns:
        Dict with 'text_pdf_url' and 'summary_pdf_url' keys
    """
    from urllib.parse import urlencode
    
    params = urlencode({'bill': bill_number, 'year': year, 'code': code})
    content_url = f"https://house.mo.gov/BillContent.aspx?{params}&style=new"
    
    try:
        request = Request(content_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        soup = BeautifulSoup(html, 'html.parser')
        
        text_pdf_url = None
        summary_pdf_url = None
        
        # Find PDF links
        for a in soup.find_all('a', href=True):
            href = a['href']
            link_text = a.get_text(strip=True).lower()
            
            # Bill text PDF
            if not text_pdf_url and ('hlrbillspdf' in href or '/billtracking/bills' in href):
                if href.lower().endswith('.pdf'):
                    text_pdf_url = href if href.startswith('http') else f"https://documents.house.mo.gov{href if href.startswith('/') else '/' + href}"
            
            # Summary PDF
            if not summary_pdf_url and ('/sumpdf/' in href or 'summary' in link_text):
                if href.lower().endswith('.pdf'):
                    summary_pdf_url = href if href.startswith('http') else f"https://documents.house.mo.gov{href if href.startswith('/') else '/' + href}"
            
            if text_pdf_url and summary_pdf_url:
                break
        
        return {
            'text_pdf_url': text_pdf_url,
            'summary_pdf_url': summary_pdf_url
        }
        
    except Exception as e:
        print(f"Error fetching PDF URLs for {bill_number}: {e}")
        return {'text_pdf_url': None, 'summary_pdf_url': None}


def fetch_bill_full_text(bill_number: str, year: str = '2025', code: str = 'R') -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Fetch full bill text for a given bill number.
    
    Args:
        bill_number: Bill number (e.g., 'HB101')
        year: Legislative year
        code: Session code
        
    Returns:
        Tuple of (full_text, text_pdf_url, summary_pdf_url)
    """
    # Get PDF URLs
    pdf_urls = get_bill_pdfs(bill_number, year, code)
    text_pdf_url = pdf_urls['text_pdf_url']
    summary_pdf_url = pdf_urls['summary_pdf_url']
    
    # Try to fetch text from the bill text PDF
    full_text = None
    if text_pdf_url:
        print(f"Fetching bill text from: {text_pdf_url}")
        full_text = fetch_bill_text_from_url(text_pdf_url)
    
    # If no text from bill PDF, try summary PDF
    if not full_text and summary_pdf_url:
        print(f"Fetching from summary PDF: {summary_pdf_url}")
        full_text = fetch_bill_text_from_url(summary_pdf_url)
    
    return full_text, text_pdf_url, summary_pdf_url


def extract_key_sections(full_text: str) -> Dict[str, str]:
    """
    Extract key sections from bill text for structured analysis.
    
    Args:
        full_text: Full bill text
        
    Returns:
        Dict with sections like 'enacting_clause', 'sections', 'effective_date'
    """
    if not full_text:
        return {}
    
    sections = {}
    
    # Extract enacting clause (common in MO bills)
    enacting_match = re.search(
        r'(Be it enacted.*?follows:)',
        full_text,
        re.IGNORECASE | re.DOTALL
    )
    if enacting_match:
        sections['enacting_clause'] = enacting_match.group(1).strip()
    
    # Extract effective date
    effective_match = re.search(
        r'(effective\s+(?:date|upon).*?)(?:\n|$)',
        full_text,
        re.IGNORECASE
    )
    if effective_match:
        sections['effective_date'] = effective_match.group(1).strip()
    
    # Extract section numbers (e.g., "Section 1.", "Section A.")
    section_pattern = re.compile(r'\n(Section [A-Z0-9]+\..*?)(?=\nSection [A-Z0-9]+\.|\Z)', re.DOTALL | re.IGNORECASE)
    bill_sections = section_pattern.findall(full_text)
    if bill_sections:
        sections['numbered_sections'] = bill_sections
    
    return sections


def prepare_for_llm(bill_data: Dict) -> str:
    """
    Prepare bill data in optimal format for LLM processing.
    
    Args:
        bill_data: Dict with bill information including full_text
        
    Returns:
        Formatted string ready for LLM
    """
    output = []
    
    # Metadata header
    output.append("=" * 80)
    output.append(f"MISSOURI HOUSE BILL: {bill_data.get('bill_number', 'Unknown')}")
    output.append("=" * 80)
    output.append("")
    
    if bill_data.get('title'):
        output.append(f"TITLE: {bill_data['title']}")
        output.append("")
    
    if bill_data.get('sponsor'):
        output.append(f"SPONSOR: {bill_data['sponsor']}")
        output.append("")
    
    if bill_data.get('status'):
        output.append(f"STATUS: {bill_data['status']}")
        output.append("")
    
    if bill_data.get('description'):
        output.append("DESCRIPTION:")
        output.append(bill_data['description'])
        output.append("")
    
    output.append("-" * 80)
    output.append("FULL BILL TEXT:")
    output.append("-" * 80)
    output.append("")
    
    if bill_data.get('full_text'):
        output.append(bill_data['full_text'])
    else:
        output.append("[Full text not available]")
    
    return '\n'.join(output)
