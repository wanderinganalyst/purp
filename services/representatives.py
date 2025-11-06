import time
import os
from bs4 import BeautifulSoup
from .web_utils import fetch_remote_page
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
    
    # Implementation of representative parsing logic
    # This would be specific to the source HTML structure
    
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
        return []
        
    # Add sponsored bills to each representative
    for rep in reps:
        rep['sponsored_bills'] = get_bills_by_sponsor(rep['name'])
        
    return reps