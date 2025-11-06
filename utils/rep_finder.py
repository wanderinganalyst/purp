"""
Utility to find representatives for logged-in users based on their address.
"""
from rep_lookup import RepresentativeLookup

def get_user_representatives(user):
    """
    Get representatives for a user based on their stored address.
    
    Args:
        user: User model instance with address fields
        
    Returns:
        Dictionary with senator and representative information, or None if lookup fails
    """
    if not user or not user.street_address or not user.city or not user.zipcode:
        return None
    
    # Build the full address
    address = user.street_address
    if user.apt_unit:
        address += f" {user.apt_unit}"
    
    # Lookup representatives
    rep_info = RepresentativeLookup.lookup_representatives(
        address=address,
        city=user.city,
        zip_code=user.zipcode
    )
    
    return rep_info


def format_rep_display(rep_info):
    """
    Format representative information for display in templates.
    
    Args:
        rep_info: Dictionary from RepresentativeLookup
        
    Returns:
        Dictionary with formatted display data
    """
    if not rep_info:
        return {
            'has_data': False,
            'senator': None,
            'representative': None
        }
    
    display_data = {'has_data': True}
    
    # Format senator
    if rep_info.get('state_senator'):
        senator = rep_info['state_senator']
        display_data['senator'] = {
            'name': senator.get('name', 'Unknown'),
            'district': senator.get('district', 'N/A'),
            'party': senator.get('party', 'N/A'),
            'display': f"{senator.get('name', 'Unknown')} (D-{senator.get('district', 'N/A')})"
        }
    else:
        display_data['senator'] = None
    
    # Format representative
    if rep_info.get('state_representative'):
        rep = rep_info['state_representative']
        display_data['representative'] = {
            'name': rep.get('name', 'Unknown'),
            'district': rep.get('district', 'N/A'),
            'party': rep.get('party', 'N/A'),
            'display': f"{rep.get('name', 'Unknown')} (D-{rep.get('district', 'N/A')})"
        }
    else:
        display_data['representative'] = None
    
    return display_data
