# Data Fetcher Module

## Overview

The Data Fetcher module automatically handles fetching bills and representatives data based on the environment mode (production vs development).

## Features

- **Environment-Aware**: Automatically detects if running in production or development
- **Mock Data Caching**: Generates and caches mock data for development/testing
- **Seamless Integration**: Works transparently with existing code
- **Smart Fallback**: Falls back to mock data if real data fetch fails in production

## How It Works

### Production Mode
- Fetches real bills from Missouri Legislature website
- Looks up real representatives using the RepresentativeLookup utility
- No caching of mock data

### Development Mode
1. **First Run**: 
   - Checks if mock data exists at `data/mock_data.json`
   - If not found, generates comprehensive mock data
   - Saves to cache file for future use
   
2. **Subsequent Runs**:
   - Loads cached mock data from `data/mock_data.json`
   - No network requests needed
   - Fast and reliable testing

## Usage

### In Your Code

```python
from utils.data_fetcher import get_data_fetcher

# Get the singleton instance
fetcher = get_data_fetcher()

# Fetch bills (automatically handles production vs development)
bills = fetcher.fetch_bills()

# Fetch representatives for an address
address_data = {
    'street': '201 W Capitol Ave',
    'city': 'Jefferson City',
    'state': 'MO',
    'zip': '65101'
}
reps = fetcher.fetch_representatives(address_data)
```

### Setting Environment Mode

The module checks the `FLASK_ENV` environment variable:

**Production Mode:**
```bash
export FLASK_ENV=production
python main.py
```

**Development Mode (default):**
```bash
export FLASK_ENV=development
python main.py
# or just
python main.py  # defaults to development
```

### Refreshing Mock Data

If you want to regenerate the mock data:

```python
from utils.data_fetcher import get_data_fetcher

fetcher = get_data_fetcher()
fetcher.refresh_mock_data()
```

Or simply delete the file:
```bash
rm data/mock_data.json
```

The next run will automatically generate fresh mock data.

## Mock Data Structure

### Bills
Each mock bill includes:
- `number`: Bill number (e.g., "HB 101")
- `sponsor`: Name of the sponsor
- `title`: Bill title
- `status`: Current status
- `last_action`: Date of last action
- `summary`: Brief description
- `committee`: Assigned committee
- `introduced`: Date introduced

### Representatives
Mock representatives are organized by zip code:
- `65101`: Jefferson City representatives
- `63101`: St. Louis representatives
- `64101`: Kansas City representatives
- `default`: Fallback for unknown zip codes

Each representative entry includes:
- `senator`: Name, district, party
- `representative`: Name, district, party

## Files

- `utils/data_fetcher.py`: Main data fetcher module
- `utils/environment.py`: Environment configuration helpers
- `data/mock_data.json`: Cached mock data (auto-generated)
- `data/.gitkeep`: Ensures data directory exists in git

## Integration Points

The data fetcher is integrated into:
1. **Bills Blueprint** (`routes/bills.py`): Fetches bills for display
2. **Auth Module** (`auth.py`): Looks up representatives during signup and profile view
3. **Main App** (`main.py`): Imported for use throughout the app

## Testing

To verify the data fetcher is working:

```bash
cd /Users/joeoconnell/purp
source .venv/bin/activate
python -c "from utils.data_fetcher import get_data_fetcher; fetcher = get_data_fetcher(); print('Bills:', len(fetcher.fetch_bills())); print('Reps:', fetcher.fetch_representatives({'zip': '65101'}))"
```

## Notes

- Mock data is generated once and reused across sessions
- No network calls are made in development mode after initial generation
- Production mode always fetches fresh data (consider adding caching if needed)
- The singleton pattern ensures consistent data across the app
