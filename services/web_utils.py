import urllib.request

def fetch_remote_page(url, timeout=10):
    """Fetch a remote page using urllib and return decoded text.
    Keeps dependency list small (no requests required).
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            content_bytes = resp.read()
            # try to decode, fallback to latin-1
            try:
                return content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return content_bytes.decode('latin-1')
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None