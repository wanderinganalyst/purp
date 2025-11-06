import os
from usps import USPSApi

# Initialize USPS API with your user ID
USPS_USER_ID = os.environ.get('USPS_USER_ID', 'REPLACE_WITH_YOUR_USPS_ID')
usps = USPSApi(USPS_USER_ID)

def verify_address(street_address, city, state, zipcode, apt_unit=None):
    """
    Verify an address using USPS API.
    Returns (is_valid, standardized_address) tuple.
    """
    try:
        # Prepare address for verification
        address = {
            'address_1': street_address,
            'address_2': apt_unit or '',
            'city': city,
            'state': state,
            'zipcode': zipcode
        }

        # Validate through USPS API
        validation = usps.validate_address(address)

        if validation.result.get('AddressValidateResponse'):
            address = validation.result['AddressValidateResponse']['Address']
            
            # Check if address was found and standardized
            if address.get('Error'):
                return False, None
            
            # Return standardized address
            standardized = {
                'street_address': address.get('Address2', address.get('Address1', '')),
                'apt_unit': address.get('Address1') if address.get('Address2') else None,
                'city': address.get('City', ''),
                'state': address.get('State', ''),
                'zipcode': address.get('Zip5', '') + ('-' + address.get('Zip4', '') if address.get('Zip4') else '')
            }
            return True, standardized
            
        return False, None
        
    except Exception as e:
        print(f"Address verification error: {e}")
        return False, None


def format_address(street_address, city, state, zipcode, apt_unit=None):
    """Format address components into a single string."""
    parts = [street_address]
    if apt_unit:
        parts.append(f"Unit {apt_unit}")
    parts.extend([f"{city}, {state} {zipcode}"])
    return ", ".join(parts)