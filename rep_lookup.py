import requests
from bs4 import BeautifulSoup
import re

class RepresentativeLookup:
    LOOKUP_URL = "https://www.senate.mo.gov/legislookup/default"
    
    @staticmethod
    def lookup_representatives(address, city, zip_code):
        """
        Look up representatives for a given address using the MO Senate website.
        Returns a dictionary with senator and representative information.
        """
        try:
            # Initial page load to get session tokens/cookies
            session = requests.Session()
            response = session.get(RepresentativeLookup.LOOKUP_URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the form and extract any hidden fields
            form = soup.find('form')
            if not form:
                return None
                
            # Prepare the form data with proper ASP.NET field names
            data = {}
            
            # Get all hidden fields (VIEWSTATE, etc.)
            for hidden in form.find_all('input', type='hidden'):
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    data[name] = value
            
            # Set the address fields using correct ASP.NET control names
            data['ctl00$MainContent$txtAddress'] = address
            data['ctl00$MainContent$txtCity'] = city
            data['ctl00$MainContent$txtZip'] = zip_code
            
            # Set the submit button that was clicked
            data['ctl00$MainContent$ZipButton'] = 'Lookup Legislators'
                
            # Submit the form
            response = session.post(RepresentativeLookup.LOOKUP_URL, data=data)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract representative information
            results = {
                'state_senator': None,
                'state_representative': None,
                'district_info': {}
            }
            
            # Parse the results - look for the results panel or divs
            # The results typically appear in specific div elements after form submission
            result_divs = soup.find_all('div', {'class': ['panel', 'resultPanel', 'legislator-info']})
            
            # Also check for any divs with legislator information
            if not result_divs:
                result_divs = soup.find_all('div', id=lambda x: x and ('result' in x.lower() or 'legislator' in x.lower()))
            
            # Parse all text for Senator and Representative info
            full_text = soup.get_text()
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            # Join lines to handle multi-line results
            combined_text = ' '.join(lines)
            
            # Look for pattern: "Senatorial district MO### - Senator Name"
            senator_match = re.search(r'Senatorial district\s+MO(\d+)\s+-\s+Senator\s+([A-Za-z\s\.\-\']+?)(?:House|U\.S\.|Your|$)', combined_text, re.IGNORECASE)
            if senator_match:
                results['state_senator'] = {
                    'name': senator_match.group(2).strip(),
                    'district': senator_match.group(1),
                    'party': None  # Party info not in this format
                }
            
            # Look for pattern: "House district MO### - Representative Name"
            rep_match = re.search(r'House district\s+MO(\d+)\s+-\s+Representative\s+([A-Za-z\s\.\-\']+?)(?:U\.S\.|Your|Senatorial|$)', combined_text, re.IGNORECASE)
            if rep_match:
                results['state_representative'] = {
                    'name': rep_match.group(2).strip(),
                    'district': rep_match.group(1),
                    'party': None  # Party info not in this format
                }
            
            return results
            
        except Exception as e:
            print(f"Error looking up representatives: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    @staticmethod
    def format_representative_info(rep_info):
        """Format representative information for display."""
        if not rep_info:
            return "No representative information found."
            
        output = []
        
        if rep_info.get('state_senator'):
            senator = rep_info['state_senator']
            output.append(
                f"State Senator: {senator['name']}\n"
                f"District: {senator['district']}\n"
                f"Party: {senator['party']}"
            )
            
        if rep_info.get('state_representative'):
            rep = rep_info['state_representative']
            output.append(
                f"State Representative: {rep['name']}\n"
                f"District: {rep['district']}\n"
                f"Party: {rep['party']}"
            )
            
        return "\n\n".join(output) if output else "No representative information found."