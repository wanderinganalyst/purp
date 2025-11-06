import time
from bs4 import BeautifulSoup
from .web_utils import fetch_remote_page
import os

# Cache configuration
_bills_cache = {'ts': 0, 'data': None}
_BILLS_TTL = int(os.environ.get('BILLS_CACHE_TTL', 300))

def get_cached_bills():
    """Get bills from cache if not expired."""
    if _bills_cache['data'] is None or time.time() - _bills_cache['ts'] > _BILLS_TTL:
        return None
    return _bills_cache['data']

def parse_bills_with_bs(html_text):
    """Parse bills from HTML text using BeautifulSoup."""
    _bills_cache['ts'] = time.time()
    _bills_cache['data'] = []

    if not html_text:
        return []

    soup = BeautifulSoup(html_text, 'html.parser')
    bills_table = soup.find('table', class_='sortable')
    
    if not bills_table:
        return []

    for row in bills_table.find_all('tr')[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) >= 3:
            bill_id = cols[0].text.strip()
            description = cols[1].text.strip()
            sponsor = cols[2].text.strip()
            
            bill_link = cols[0].find('a')
            bill_url = bill_link['href'] if bill_link else None
            
            if bill_id and sponsor:
                _bills_cache['data'].append({
                    'id': bill_id,
                    'description': description,
                    'sponsor': sponsor,
                    'url': bill_url
                })
    
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