"""
Data Fetcher Module
Handles fetching bills and representatives data.
- Production: Fetches real data from external sources
- Development: Uses cached mock data or generates it if not exists
"""

import os
import json
from datetime import datetime
from pathlib import Path


class DataFetcher:
    """Fetches bills and representatives data based on environment"""
    
    MOCK_DATA_FILE = Path(__file__).parent.parent / 'data' / 'mock_data.json'
    
    def __init__(self):
        self.is_production = os.environ.get('FLASK_ENV') == 'production'
        self.mock_data = None
        
    def fetch_bills(self):
        """Fetch bills data - real in production, mock in development"""
        if self.is_production:
            return self._fetch_real_bills()
        else:
            return self._get_mock_bills()
    
    def fetch_representatives(self, address_data):
        """
        Fetch representatives data based on address
        
        Args:
            address_data (dict): Dictionary with keys: street, city, state, zip
        
        Returns:
            dict: Representative information
        """
        if self.is_production:
            return self._fetch_real_reps(address_data)
        else:
            return self._get_mock_reps(address_data)
    
    def _fetch_real_bills(self):
        """Fetch real bills data from Missouri Legislature website"""
        try:
            from urllib.request import urlopen, Request
            from bs4 import BeautifulSoup
            
            url = "https://house.mo.gov/BillList.aspx"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            request = Request(url, headers=headers)
            page = urlopen(request, timeout=15)
            soup = BeautifulSoup(page, 'html.parser')
            
            bills = []
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
                            bills.append({
                                'number': bill_number,
                                'sponsor': sponsor,
                                'title': description[:200] if len(description) > 200 else description,
                                'status': 'Active',
                                'last_action': datetime.now().strftime('%Y-%m-%d')
                            })
                            
                            # Limit to first 50 bills
                            if len(bills) >= 50:
                                break
                except Exception as e:
                    continue  # Skip malformed rows
            
            return bills if bills else self._generate_mock_bills()
        except Exception as e:
            print(f"Error fetching real bills: {e}")
            return self._generate_mock_bills()
    
    def _fetch_real_reps(self, address_data):
        """Fetch real representatives data using RepresentativeLookup"""
        try:
            from utils.rep_finder import RepresentativeLookup
            
            lookup = RepresentativeLookup()
            full_address = f"{address_data.get('street', '')}, {address_data.get('city', '')}, {address_data.get('state', 'MO')} {address_data.get('zip', '')}"
            
            rep_info = lookup.lookup_representatives(full_address)
            return rep_info
        except Exception as e:
            print(f"Error fetching real representatives: {e}")
            return {
                'senator': {'name': 'Unknown', 'district': 'N/A', 'party': 'N/A'},
                'representative': {'name': 'Unknown', 'district': 'N/A', 'party': 'N/A'}
            }
    
    def _get_mock_bills(self):
        """Get mock bills data - load from cache or generate"""
        self._ensure_mock_data()
        return self.mock_data.get('bills', [])
    
    def _get_mock_reps(self, address_data):
        """Get mock representatives data - load from cache or generate"""
        self._ensure_mock_data()
        
        # Try to match by zip code first
        zip_code = address_data.get('zip', '')
        mock_reps = self.mock_data.get('representatives', {})
        
        if zip_code in mock_reps:
            return mock_reps[zip_code]
        
        # Default mock data if no match
        return mock_reps.get('default', {
            'senator': {'name': 'Mock Senator', 'district': '1', 'party': 'D'},
            'representative': {'name': 'Mock Representative', 'district': '1', 'party': 'R'}
        })
    
    def _ensure_mock_data(self):
        """Ensure mock data is loaded or generated"""
        if self.mock_data is not None:
            return
        
        # Try to load existing mock data
        if self.MOCK_DATA_FILE.exists():
            self._load_mock_data()
        else:
            # Generate and save new mock data
            self._generate_and_save_mock_data()
    
    def _load_mock_data(self):
        """Load mock data from JSON file"""
        try:
            with open(self.MOCK_DATA_FILE, 'r') as f:
                self.mock_data = json.load(f)
            print(f"✓ Loaded mock data from {self.MOCK_DATA_FILE}")
        except Exception as e:
            print(f"Error loading mock data: {e}")
            self._generate_and_save_mock_data()
    
    def _generate_and_save_mock_data(self):
        """Generate mock data and save to cache file"""
        print("Generating mock data...")
        
        self.mock_data = {
            'generated_at': datetime.now().isoformat(),
            'bills': self._generate_mock_bills(),
            'representatives': self._generate_mock_representatives()
        }
        
        # Ensure data directory exists
        self.MOCK_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        try:
            with open(self.MOCK_DATA_FILE, 'w') as f:
                json.dump(self.mock_data, f, indent=2)
            print(f"✓ Saved mock data to {self.MOCK_DATA_FILE}")
        except Exception as e:
            print(f"Error saving mock data: {e}")
    
    def _generate_mock_bills(self):
        """Generate mock bills data"""
        return [
            {
                'number': 'HB 101',
                'sponsor': 'Rep. John Smith',
                'title': 'An Act to Improve Education Funding',
                'status': 'In Committee',
                'last_action': '2025-11-01',
                'summary': 'This bill proposes to increase education funding by 15% over the next fiscal year.',
                'committee': 'Education Committee',
                'introduced': '2025-10-15'
            },
            {
                'number': 'HB 202',
                'sponsor': 'Rep. Jane Doe',
                'title': 'Transportation Infrastructure Act',
                'status': 'Passed House',
                'last_action': '2025-11-03',
                'summary': 'Allocates $500 million for highway and bridge repairs across the state.',
                'committee': 'Transportation Committee',
                'introduced': '2025-10-20'
            },
            {
                'number': 'SB 50',
                'sponsor': 'Sen. Robert Johnson',
                'title': 'Healthcare Access Expansion',
                'status': 'Active',
                'last_action': '2025-11-05',
                'summary': 'Expands healthcare access to underserved communities in rural Missouri.',
                'committee': 'Health and Welfare Committee',
                'introduced': '2025-10-25'
            },
            {
                'number': 'HB 303',
                'sponsor': 'Rep. Maria Garcia',
                'title': 'Small Business Tax Relief',
                'status': 'In Committee',
                'last_action': '2025-10-30',
                'summary': 'Provides tax incentives for small businesses with fewer than 50 employees.',
                'committee': 'Ways and Means Committee',
                'introduced': '2025-10-18'
            },
            {
                'number': 'SB 75',
                'sponsor': 'Sen. Michael Brown',
                'title': 'Environmental Protection Act',
                'status': 'Passed Senate',
                'last_action': '2025-11-04',
                'summary': 'Strengthens environmental regulations and establishes new conservation areas.',
                'committee': 'Natural Resources Committee',
                'introduced': '2025-10-22'
            },
            {
                'number': 'HB 404',
                'sponsor': 'Rep. David Wilson',
                'title': 'Criminal Justice Reform',
                'status': 'Active',
                'last_action': '2025-11-02',
                'summary': 'Reforms sentencing guidelines and expands rehabilitation programs.',
                'committee': 'Judiciary Committee',
                'introduced': '2025-10-28'
            },
            {
                'number': 'HB 505',
                'sponsor': 'Rep. Sarah Lee',
                'title': 'Rural Broadband Expansion',
                'status': 'In Committee',
                'last_action': '2025-10-29',
                'summary': 'Invests in broadband infrastructure for rural and underserved areas.',
                'committee': 'Technology and Innovation Committee',
                'introduced': '2025-10-19'
            },
            {
                'number': 'SB 100',
                'sponsor': 'Sen. Patricia Martinez',
                'title': 'Worker Protection Act',
                'status': 'Active',
                'last_action': '2025-11-06',
                'summary': 'Enhances workplace safety standards and worker compensation benefits.',
                'committee': 'Labor and Industrial Relations Committee',
                'introduced': '2025-10-26'
            }
        ]
    
    def _generate_mock_representatives(self):
        """Generate mock representatives data for different zip codes"""
        return {
            '65101': {  # Jefferson City
                'senator': {
                    'name': 'Mike Bernskoetter',
                    'district': '6',
                    'party': 'Republican'
                },
                'representative': {
                    'name': 'Dave Griffith',
                    'district': '58',
                    'party': 'Republican'
                }
            },
            '63101': {  # St. Louis
                'senator': {
                    'name': 'Steve Roberts',
                    'district': '5',
                    'party': 'Democrat'
                },
                'representative': {
                    'name': 'Peter Merideth',
                    'district': '80',
                    'party': 'Democrat'
                }
            },
            '64101': {  # Kansas City
                'senator': {
                    'name': 'Barbara Washington',
                    'district': '9',
                    'party': 'Democrat'
                },
                'representative': {
                    'name': 'Mark Sharp',
                    'district': '36',
                    'party': 'Democrat'
                }
            },
            'default': {
                'senator': {
                    'name': 'Mock Senator',
                    'district': '1',
                    'party': 'Independent'
                },
                'representative': {
                    'name': 'Mock Representative',
                    'district': '1',
                    'party': 'Independent'
                }
            }
        }
    
    def refresh_mock_data(self):
        """Force regeneration of mock data"""
        self._generate_and_save_mock_data()
        return self.mock_data


# Singleton instance
_data_fetcher = None

def get_data_fetcher():
    """Get the singleton DataFetcher instance"""
    global _data_fetcher
    if _data_fetcher is None:
        _data_fetcher = DataFetcher()
    return _data_fetcher
