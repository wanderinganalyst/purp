# Getting Started

This guide will help you set up and run Purp locally for development.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- (Optional) Docker for containerized deployment

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/wanderinganalyst/purp.git
cd purp
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python3 init_db.py
```

This creates the SQLite database and sets up the initial schema.

### 5. Seed Data (Optional)

```bash
# Fetch Missouri House representatives
python3 sync_reps.py

# Fetch current bills
python3 sync_bills.py

# Create event templates (Rally and Dinner)
python3 seed_templates.py

# Create an admin user (optional)
python3 create_admin.py
```

### 6. Run the Application

```bash
python main.py
```

The application will be available at http://localhost:5000

## Alternative Start Methods

### Flask CLI

```bash
export FLASK_APP=main.py
flask run
```

### Production Server

For production, use Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

## Troubleshooting

### Port Already in Use

If port 5000 is already in use:

```bash
# Kill the process using port 5000 (macOS/Linux)
lsof -ti:5000 | xargs kill -9

# Or run on a different port by modifying main.py
# Change: app.run(debug=True, port=5001)
```

### Import Errors

Ensure virtual environment is activated and dependencies are installed:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Database Issues

If you encounter database errors:

```bash
# Backup your current database (if needed)
cp instance/purp.db instance/purp.db.backup

# Reinitialize the database
rm instance/purp.db
python3 init_db.py
```

### Representative Lookup Not Working

The representative lookup relies on scraping the Missouri Legislature website. If it's not working:

1. Check your internet connection
2. Verify the Missouri Legislature website is accessible
3. The website structure may have changed - check `utils/data_fetcher.py`

## Next Steps

- [Configure your environment](configuration.md)
- [Learn about user roles](user-roles.md)
- [Explore features](features/)
- [Set up for development](development/)
