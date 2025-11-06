"""Address verification utilities.

In production we attempt to use the USPS API if the `usps` package and
`USPS_USER_ID` env var are available. In development (or if the dependency
is missing) we gracefully degrade to a no-op verifier that returns the
original address as 'standardized'.
"""

import os

USPS_USER_ID = os.environ.get('USPS_USER_ID')

_usps_client = None
try:
    if USPS_USER_ID:
        from usps import USPSApi  # type: ignore
        _usps_client = USPSApi(USPS_USER_ID)
except Exception as e:  # pragma: no cover
    # Log and continue without USPS capabilities
    print(f"USPS integration disabled: {e}")

def verify_address(street_address, city, state, zipcode, apt_unit=None):
    """Verify an address.

    Returns: (is_valid: bool, standardized_address: dict|None)
    - If USPS is configured and succeeds, returns standardized components.
    - If USPS not available, returns True with a basic normalized structure.
    - On error, returns False, None.
    """
    if not street_address or not city or not state or not zipcode:
        return False, None

    # Attempt USPS validation if client present
    if _usps_client:
        try:
            address = {
                'address_1': street_address,
                'address_2': apt_unit or '',
                'city': city,
                'state': state,
                'zipcode': zipcode
            }
            validation = _usps_client.validate_address(address)
            resp = validation.result.get('AddressValidateResponse')
            if resp and 'Address' in resp:
                addr = resp['Address']
                if addr.get('Error'):
                    return False, None
                standardized = {
                    'street_address': addr.get('Address2', addr.get('Address1', '')),
                    'apt_unit': addr.get('Address1') if addr.get('Address2') else None,
                    'city': addr.get('City', city),
                    'state': addr.get('State', state),
                    'zipcode': addr.get('Zip5', '') + (('-' + addr.get('Zip4')) if addr.get('Zip4') else '')
                }
                return True, standardized
            return False, None
        except Exception as e:  # pragma: no cover
            print(f"Address verification error (USPS fallback): {e}")
            # fall through to local normalization

    # Fallback normalization (non-USPS)
    standardized = {
        'street_address': street_address.strip(),
        'apt_unit': apt_unit.strip() if apt_unit else None,
        'city': city.strip(),
        'state': state.strip().upper(),
        'zipcode': zipcode.strip()
    }
    return True, standardized


def format_address(street_address, city, state, zipcode, apt_unit=None):
    """Format address components into a single string."""
    parts = [street_address]
    if apt_unit:
        parts.append(f"Unit {apt_unit}")
    parts.extend([f"{city}, {state} {zipcode}"])
    return ", ".join(parts)