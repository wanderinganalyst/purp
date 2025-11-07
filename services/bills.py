import time
from bs4 import BeautifulSoup
from .web_utils import fetch_remote_page
import os
from urllib.parse import urlencode

# Cache configuration
_bills_cache = {'ts': 0, 'data': None}
_BILLS_TTL = int(os.environ.get('BILLS_CACHE_TTL', 300))

# Per-bill details cache (longer TTL, details change less often)
_bill_details_cache = {}
_BILL_DETAILS_TTL = int(os.environ.get('BILL_DETAILS_CACHE_TTL', 3600))


def get_cached_bills():
    """Get bills from cache if not expired, otherwise fetch fresh data."""
    if _bills_cache['data'] is None or time.time() - _bills_cache['ts'] > _BILLS_TTL:
        # Try to fetch fresh data
        html = fetch_remote_page('https://house.mo.gov/BillList.aspx')
        if html:
            return parse_bills_with_bs(html)
        return None
    return _bills_cache['data']


def parse_bills_with_bs(html_text):
    """Parse bills from HTML text using BeautifulSoup."""
    _bills_cache['ts'] = time.time()
    _bills_cache['data'] = []

    if not html_text:
        return []

    soup = BeautifulSoup(html_text, 'html.parser')

    # Find all table rows - each bill has a 2-row pattern
    rows = soup.find_all('tr')

    for i in range(0, len(rows) - 1, 2):  # Process pairs of rows
        try:
            row1 = rows[i]
            row2 = rows[i + 1]

            cols1 = row1.find_all('td')
            cols2 = row2.find_all('td')

            if len(cols1) >= 2 and len(cols2) >= 1:
                # First row has bill number and sponsor
                bill_number = cols1[0].get_text(strip=True)
                sponsor = cols1[1].get_text(strip=True) if len(cols1) > 1 else 'Unknown'

                # Second row has description
                description = cols2[0].get_text(strip=True) if cols2 else ''

                # Skip if empty or header rows
                if bill_number and bill_number.startswith('HB'):
                    _bills_cache['data'].append({
                        'id': bill_number,
                        'number': bill_number,
                        'sponsor': sponsor,
                        'title': description[:200] if len(description) > 200 else description,
                        'description': description,
                        'status': 'Active',
                        'last_action': 'Filed'
                    })
        except Exception:
            continue  # Skip malformed rows

    return _bills_cache['data']


def get_bill_by_id(bill_id):
    """Get a specific bill by ID from the cache."""
    bills = get_cached_bills()
    if bills:
        return next((b for b in bills if b['id'] == bill_id), None)
    return None


def get_bills_by_sponsor(sponsor_name):
    """Get all bills sponsored by a specific representative."""
    bills = get_cached_bills()
    if bills:
        return [b for b in bills if b['sponsor'].lower() == sponsor_name.lower()]
    return []


def _build_bill_urls(bill_number: str, year: str = '2025', code: str = 'R'):
    """Construct official URLs for a bill.

    Returns a dict with: content_url, actions_url, hearings_url, cosponsors_url
    """
    params = urlencode({'bill': bill_number, 'year': year, 'code': code})
    content_url = f"https://house.mo.gov/BillContent.aspx?{params}&style=new"
    actions_url = f"https://house.mo.gov/BillActions.aspx?{params}"
    hearings_url = f"https://house.mo.gov/BillHearings.aspx?Bill={bill_number}&year={year}&code={code}"
    cosponsors_url = f"https://house.mo.gov/CoSponsors.aspx?{params}"
    return {
        'content_url': content_url,
        'actions_url': actions_url,
        'hearings_url': hearings_url,
        'cosponsors_url': cosponsors_url,
    }


def _parse_text_and_summary_pdfs(soup: BeautifulSoup):
    """Extract links to the Bill Text and Bill Summary PDFs from the content page."""
    text_pdf_url = None
    summary_pdf_url = None

    # Text PDF: often contains 'hlrbillspdf' or 'billtracking/bills' in href
    for a in soup.find_all('a', href=True):
        href = a['href']
        if not text_pdf_url and ('hlrbillspdf' in href or '/billtracking/bills' in href) and href.lower().endswith('.pdf'):
            text_pdf_url = href if href.startswith('http') else f"https://documents.house.mo.gov{href if href.startswith('/') else '/' + href}"
        if not summary_pdf_url and ('/sumpdf/' in href or 'Bill Summary' in a.get_text(strip=True)) and href.lower().endswith('.pdf'):
            summary_pdf_url = href if href.startswith('http') else f"https://documents.house.mo.gov{href if href.startswith('/') else '/' + href}"
        if text_pdf_url and summary_pdf_url:
            break

    return text_pdf_url, summary_pdf_url


def _parse_hearing_status(hearings_html: str):
    """Parse hearing status text from the hearings page."""
    if not hearings_html:
        return None
    hsoup = BeautifulSoup(hearings_html, 'html.parser')
    text = hsoup.get_text(separator=' ', strip=True)
    # Return a concise message
    for phrase in [
        'not scheduled',
        'scheduled',
        'cancelled',
        'canceled',
    ]:
        if phrase in text.lower():
            # Return the sentence containing the phrase if possible
            parts = [p.strip() for p in text.split('.') if phrase in p.lower()]
            return (parts[0] + '.') if parts else text[:200]
    return text[:200]


def _parse_actions(actions_html: str):
    """Parse actions table into a list of dicts: {date, journal, description}."""
    actions = []
    if not actions_html:
        return actions
    soup = BeautifulSoup(actions_html, 'html.parser')
    rows = soup.find_all('tr')
    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
        # Expect at least 3 columns: Date | JRN PG | Description
        if len(cols) >= 3 and cols[0] and cols[2]:
            actions.append({
                'date': cols[0],
                'journal': cols[1],
                'description': cols[2],
            })
    # Filter out header rows if any
    actions = [a for a in actions if a['date'] and a['description'] and not a['date'].lower().startswith('date')]
    return actions


def get_bill_details(bill_number: str, year: str = '2025', code: str = 'R'):
    """Fetch and cache detailed information for a specific bill from the official site.

    Returns a dict with optional keys:
      - text_pdf_url, summary_pdf_url
      - actions: list of {date, journal, description}
      - hearing_status: short string
      - content_url, actions_url, hearings_url, cosponsors_url
    """
    if not bill_number:
        return None

    now = time.time()
    entry = _bill_details_cache.get(bill_number)
    if entry and now - entry['ts'] < _BILL_DETAILS_TTL:
        return entry['data']

    urls = _build_bill_urls(bill_number, year, code)

    # Fetch pages
    content_html = fetch_remote_page(urls['content_url'])
    actions_html = fetch_remote_page(urls['actions_url'])
    hearings_html = fetch_remote_page(urls['hearings_url'])

    details = {
        'content_url': urls['content_url'],
        'actions_url': urls['actions_url'],
        'hearings_url': urls['hearings_url'],
        'cosponsors_url': urls['cosponsors_url'],
    }

    # Parse content page for PDFs and possible headline/summary
    if content_html:
        csoup = BeautifulSoup(content_html, 'html.parser')
        text_pdf_url, summary_pdf_url = _parse_text_and_summary_pdfs(csoup)
        if text_pdf_url:
            details['text_pdf_url'] = text_pdf_url
        if summary_pdf_url:
            details['summary_pdf_url'] = summary_pdf_url
        # Try to extract a short headline/summary line following bill header
        # Look for the first <h1> or <h2> with the bill number, then next text block
        header = None
        for tag in csoup.find_all(['h1', 'h2']):
            if bill_number in tag.get_text():
                header = tag
                break
        if header:
            # Find next text-containing element
            nxt = header.find_next(string=True)
            if nxt:
                candidate = nxt.strip()
                # Sanity check: avoid just bill number repeats
                if candidate and bill_number not in candidate and len(candidate) > 10:
                    details['summary'] = candidate

    # Parse actions
    details['actions'] = _parse_actions(actions_html)

    # Parse hearing status
    hearing_status = _parse_hearing_status(hearings_html)
    if hearing_status:
        details['hearing_status'] = hearing_status

    _bill_details_cache[bill_number] = {'ts': now, 'data': details}
    return details
