import time
import os
from bs4 import BeautifulSoup
from .web_utils import fetch_remote_page
from urllib.parse import urlparse, parse_qs
from .bills import get_bills_by_sponsor

# Cache configuration
_reps_cache = {'ts': 0, 'data': None}
_REPS_TTL = int(os.environ.get('REPS_CACHE_TTL', 300))

def get_cached_reps():
    """Get representatives from cache if not expired."""
    if _reps_cache['data'] is None or time.time() - _reps_cache['ts'] > _REPS_TTL:
        return None
    return _reps_cache['data']

def parse_reps_with_bs(html_text):
    """Parse representatives from HTML text using BeautifulSoup."""
    _reps_cache['ts'] = time.time()
    _reps_cache['data'] = []

    if not html_text:
        return []

    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Find all table rows with representative data
    rows = soup.find_all('tr')
    
    for row in rows:
        cols = row.find_all('td')
        # Each row has: Photo | Last Name | First Name | District | Party | City | Phone | Room
        if len(cols) >= 8:
            try:
                last_name = cols[1].get_text(strip=True)
                first_name = cols[2].get_text(strip=True)
                district = cols[3].get_text(strip=True)
                party = cols[4].get_text(strip=True)
                city = cols[5].get_text(strip=True)
                
                # Skip empty/vacant seats
                if last_name and first_name and last_name != 'Vacant':
                    full_name = f"{first_name} {last_name}"
                    _reps_cache['data'].append({
                        'id': district,
                        'name': full_name,
                        'district': district,
                        'party': party,
                        'city': city
                    })
            except Exception:
                continue  # Skip malformed rows
    
    return _reps_cache['data']

def get_rep_by_name(name):
    """Get a representative by their name and include their sponsored bills."""
    reps = get_cached_reps()
    if not reps:
        return None
        
    for rep in reps:
        if rep['name'].lower() == name.lower():
            rep_data = rep.copy()
            rep_data['sponsored_bills'] = get_bills_by_sponsor(name)
            return rep_data
            
    return None

def get_all_reps():
    """Get all representatives with their sponsored bills."""
    reps = get_cached_reps()
    if not reps:
        # Try to fetch fresh data
        html = fetch_remote_page('https://house.mo.gov/MemberGridCluster.aspx')
        if html:
            reps = parse_reps_with_bs(html)
        
    if not reps:
        return []
        
    # Add sponsored bills to each representative
    for rep in reps:
        rep['sponsored_bills'] = get_bills_by_sponsor(rep['name'])
        
    return reps


def _extract_bill_numbers_from_member_details(html_text):
    """Parse a MemberDetails page and extract bill numbers from bill links.

    Returns a list of normalized bill numbers like 'HB772', 'HB1004'.
    """
    if not html_text:
        return []
    soup = BeautifulSoup(html_text, 'html.parser')
    bills = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'bill.aspx' in href and 'bill=' in href:
            try:
                # Normalize to absolute path for parsing
                parsed = urlparse(href if href.startswith('http') else f'https://house.mo.gov/{href.lstrip("/")}')
                qs = parse_qs(parsed.query)
                bill_vals = qs.get('bill') or []
                for val in bill_vals:
                    # Normalize: remove spaces, uppercase
                    number = val.replace(' ', '').strip().upper()
                    if number and number not in bills:
                        bills.append(number)
            except Exception:
                continue
    return bills


def get_member_sponsorships(district: str, year: str = '2025', code: str = 'R'):
    """Fetch sponsored and co-sponsored bills for a member by district.

    Returns dict { 'sponsored': [bill_numbers], 'cosponsored': [bill_numbers] }
    """
    base = 'https://house.mo.gov/MemberDetails.aspx'
    sponsored_url = f"{base}?year={year}&code={code}&district={district}&category=sponsor"
    cosponsored_url = f"{base}?year={year}&code={code}&district={district}&category=cosponsor"

    sponsored = _extract_bill_numbers_from_member_details(fetch_remote_page(sponsored_url))
    cosponsored = _extract_bill_numbers_from_member_details(fetch_remote_page(cosponsored_url))

    return {
        'sponsored': sponsored,
        'cosponsored': cosponsored
    }