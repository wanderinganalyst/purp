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
                
            # Prepare the form data
            data = {
                'Address': address,
                'City': city,
                'Zip': zip_code,
                'Submit': 'Submit'
            }
            
            # Add any hidden fields from the form
            for hidden in form.find_all('input', type='hidden'):
                data[hidden.get('name', '')] = hidden.get('value', '')
                
            # Submit the form
            response = session.post(RepresentativeLookup.LOOKUP_URL, data=data)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract representative information
            results = {
                'state_senator': None,
                'state_representative': None,
                'district_info': {}
            }
            
            # Parse the results
            content = soup.find('div', {'class': 'content'}) or soup
            
            # Look for senator and representative information
            for p in content.find_all('p'):
                text = p.get_text()
                
                # Extract Senator info
                if 'Senator' in text:
                    results['state_senator'] = {
                        'name': re.search(r'Senator\s+(.*?)(?:\s+\(|$)', text).group(1) if re.search(r'Senator\s+(.*?)(?:\s+\(|$)', text) else None,
                        'district': re.search(r'District\s+(\d+)', text).group(1) if re.search(r'District\s+(\d+)', text) else None,
                        'party': re.search(r'\((.*?)\)', text).group(1) if re.search(r'\((.*?)\)', text) else None
                    }
                
                # Extract Representative info
                if 'Representative' in text:
                    results['state_representative'] = {
                        'name': re.search(r'Representative\s+(.*?)(?:\s+\(|$)', text).group(1) if re.search(r'Representative\s+(.*?)(?:\s+\(|$)', text) else None,
                        'district': re.search(r'District\s+(\d+)', text).group(1) if re.search(r'District\s+(\d+)', text) else None,
                        'party': re.search(r'\((.*?)\)', text).group(1) if re.search(r'\((.*?)\)', text) else None
                    }
                
                # Extract district information
                if 'District' in text:
                    district_match = re.search(r'District\s+(\d+)', text)
                    if district_match:
                        district_num = district_match.group(1)
                        results['district_info'][district_num] = text
            
            return results
            
        except Exception as e:
            print(f"Error looking up representatives: {e}")
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