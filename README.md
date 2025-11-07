# BecauseImStuck

![Tests](https://github.com/wanderinganalyst/purp/workflows/Test%20Suite/badge.svg)
![Branch Protection](https://github.com/wanderinganalyst/purp/workflows/Branch%20Protection/badge.svg)

A comprehensive civic engagement platform for Missouri citizens to track legislation, connect with representatives, participate in events, and engage in the democratic process.

## Features

- **📜 Bill Tracking**: View, comment on, and support/oppose Missouri House bills
- **👔 Representative Finder**: Automatically discover your state representatives based on your address
- **✉️ Direct Messaging**: Send messages directly to your representatives
- **📅 Event Management**: Representatives can create events with purchasable options (tickets, merchandise, etc.)
- **🗳️ Run Support**: Support users who are thinking about running for office
- **💬 Comment System**: Engage with legislation and other constituents
- **🔐 Role-Based Access**: Different permissions for citizens, representatives, candidates, staffers, and admins

## Quick Start (Local Development)

### 1. Create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Initialize the database:

```bash
python3 init_db.py
```

### 4. (Optional) Seed data:

```bash
# Fetch current Missouri House representatives
python3 sync_reps.py

# Fetch current bills from Missouri House
python3 sync_bills.py

# Create event templates (Rally and Dinner)
python3 seed_templates.py

# Create an admin user
python3 create_admin.py
```

### 5. Run the application:

```bash
python main.py
```

Open http://localhost:5000 in your browser.

## User Roles

The application supports several user roles with different permissions:

- **Regular User**: Can view bills, comment, message representatives, RSVP to events
- **Power User**: Enhanced permissions (configurable)
- **Candidate**: User running for office, can create and manage events
- **Rep Staffer**: Can manage events and invitations for their representative
- **Representative**: Linked to a Representative profile, full event and constituent management
- **Admin**: Full system access, can create events for any representative, manage all users

## Key Features Explained

### Bill Tracking
- Browse current Missouri House bills
- View bill details, sponsors, and status
- Comment on legislation
- Support or oppose bills with one click
- See aggregated support/opposition counts

### Representative Connection
- Automatic representative lookup by address using Missouri Legislature data
- View representative profiles with district, party, and contact info
- Direct messaging system to contact your representatives
- See bills introduced by your representatives

### Event System
- Create events using customizable templates (Rally, Dinner, etc.)
- Purchasable options organized by category:
  - Seating (VIP, Front Row, General Admission)
  - Food & Drinks (Meals, Wine Pairing, Bar Packages)
  - Merchandise (Hats, Pins, Stickers, Flags)
  - Transportation (Bus, Valet, Shuttle)
- Shopping cart functionality
- Invitation management with personal messages
- RSVP tracking (Attending, Maybe, Not Attending)
- Event templates with reusable options

### Run Support System
- Users can indicate they're "thinking about running for office"
- Other users can show support for potential candidates
- Support counts displayed on:
  - User profiles
  - Bill comments (candidates marked with ~* symbol)
  - Representative detail pages (Local Candidates section)
- Toggle support on/off with one click

### Profile Management
- Customizable bio
- Political aspirations indicator
- View representative information
- See support counts for potential candidates

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

## Database Migrations

The project includes migration scripts for adding new database features:

```bash
# Add representative_id to users table
python3 migrate_users.py

# Create run_supports table
python3 migrate_run_supports.py

# Add bio and thinking_about_running to users
python3 migrate_profile.py

# Create events and related tables
python3 migrate_events.py

# Create comment_supports and bill_supports tables
python3 migrate_comment_supports.py
python3 migrate_bill_supports.py
```

## Project Structure

```
becauseImstuck/
├── main.py                     # Application entry point
├── models.py                   # Database models (User, Bill, Comment, Event, etc.)
├── extensions.py               # Flask extensions (SQLAlchemy, APScheduler)
├── auth.py                     # Authentication decorators
├── requirements.txt            # Python dependencies
├── init_db.py                  # Database initialization
├── create_admin.py             # Admin user creation utility
├── routes/                     # Route blueprints
│   ├── auth_routes.py          # Authentication routes (login, register)
│   ├── bills.py                # Bill tracking and commenting
│   ├── representatives.py      # Representative profiles and lookup
│   ├── messages.py             # Constituent messaging system
│   ├── events.py               # Event management (create, RSVP, purchase)
│   └── profile.py              # User profile management
├── templates/                  # HTML templates (Jinja2)
│   ├── base.html               # Base template with navigation
│   ├── index.html              # Homepage/dashboard
│   ├── auth/                   # Authentication templates
│   ├── bills/                  # Bill listing and detail templates
│   ├── representatives/        # Representative templates
│   ├── events/                 # Event templates
│   ├── messages/               # Messaging templates
│   └── profile/                # Profile templates
├── static/                     # Static files
│   ├── css/                    # Custom styles
│   └── js/                     # JavaScript files
├── utils/                      # Utility modules
│   ├── data_fetcher.py         # Web scraping for bills and reps
│   └── validators.py           # Input validation and sanitization
├── migrations/                 # Database migration scripts
├── tests/                      # Test suite (100+ tests)
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── e2e/                    # End-to-end tests
│   └── docker/                 # Docker tests
└── infrastructure/             # Multi-cloud deployment
    ├── terraform/              # Infrastructure as code
    ├── ansible/                # Configuration management
    └── scripts/                # Deployment automation
```

## Database Schema Overview

### Core Tables
- **users**: User accounts with roles and address information
- **representatives**: Missouri House representatives with district info
- **bills**: Missouri House bills with metadata
- **comments**: User comments on bills

### Support/Engagement Tables
- **comment_supports**: Track which users support which comments
- **bill_supports**: Track user support/opposition to bills
- **run_supports**: Track support for users thinking about running

### Messaging & Events
- **messages**: Messages from constituents to representatives
- **events**: Representative-hosted events
- **event_templates**: Reusable event configurations
- **event_options**: Purchasable items for events
- **event_invitations**: Event invitations to constituents
- **event_rsvps**: RSVP responses
- **event_purchases**: Completed purchases
- **event_cart**: Shopping cart items

## Configuration

Key configuration in `main.py`:

```python
app.config['SECRET_KEY'] = 'your-secret-key'  # Change for production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/becauseimstuck.db'
```

For production:
- Use a strong, random SECRET_KEY
- Consider PostgreSQL instead of SQLite
- Set DEBUG = False
- Use environment variables for secrets

## Troubleshooting

### Database Issues

If you encounter database errors:

```bash
# Backup your current database (if needed)
cp instance/becauseimstuck.db instance/becauseimstuck.db.backup

# Reinitialize the database
rm instance/becauseimstuck.db
python3 init_db.py
```

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

### Representative Lookup Not Working

The representative lookup relies on scraping the Missouri Legislature website. If it's not working:

1. Check your internet connection
2. Verify the Missouri Legislature website is accessible
3. The website structure may have changed - check `utils/data_fetcher.py`

### Missing Templates or Static Files

If you see template errors, ensure all files are present:

```bash
git status  # Check for uncommitted changes
git pull    # Pull latest changes
```

## Docker

Build the image and run the container (from the repository root):

```bash
# build the image
docker build -t becauseimstuck .

# run the container (maps container port 5000 to host 5000)
docker run --rm -p 5000:5000 becauseimstuck
```

Or use docker-compose:

```bash
docker-compose up --build
```

Then open http://localhost:5000 in your browser.

### Database initialization (Postgres)

If you use the included Postgres container (via `docker-compose.yml`):

```bash
# start only the database service
docker-compose up -d db

# run the init_db script
docker-compose run --rm web python init_db.py
```

## Development Workflow

### Adding New Features

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests:
   ```bash
   pytest
   ```

4. Commit and push:
   ```bash
   git add .
   git commit -m "Add your feature"
   git push origin feature/your-feature-name
   ```

### Database Schema Changes

1. Create a migration script in the root directory (e.g., `migrate_your_feature.py`)
2. Test the migration on a copy of the database
3. Document the migration in this README
4. Commit the migration script with your changes

### Code Style

- Follow PEP 8 guidelines
- Use descriptive variable names
- Add docstrings to functions
- Keep functions focused and small
- Add comments for complex logic

Database initialization (Postgres)
---------------------------------

If you use the included Postgres container (via `docker-compose.yml`) you need to initialize the database schema and seed demo users once. From the repository root:

```bash
# start only the database service
docker-compose up -d db

# run the init_db script using the web service's image and environment
docker-compose run --rm web python init_db.py
```

This creates the tables and inserts two demo users:
- `regular` / `password` (role: regular)
- `power` / `powerpass` (role: power)

If Postgres isn't ready when you run the init command, wait a few seconds and try again. See `docker-compose logs db` for DB startup logs.

## Cloud Deployment

Deploy the application to AWS, Azure, or GCP with automated infrastructure provisioning:

```bash
cd infrastructure/scripts
./deploy.sh
```

Features:
- **Multi-cloud support**: Choose AWS, Azure, or GCP
- **Environment modes**: Production (larger resources) or Demo (minimal resources)
- **Fully automated**: Terraform + Ansible handle everything
- **Production-ready**: Nginx reverse proxy, Systemd service, Gunicorn

See [infrastructure/README.md](infrastructure/README.md) for complete documentation.

Quick links:
- [Quick Start Guide](infrastructure/QUICKSTART.md) - Deploy in 5 minutes
- [Architecture](infrastructure/ARCHITECTURE.md) - Diagrams and design
- [Testing Checklist](infrastructure/TESTING.md) - Verification procedures

## Testing

Comprehensive test suite with 100+ tests:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests
pytest tests/docker/       # Docker tests

# Run specific test file
pytest tests/unit/test_models.py

# Run with verbose output
pytest -v
```

See [tests/README.md](tests/README.md) for complete testing documentation.

## Production Deployment

### Deployment Checklist

Before deploying to production:

- [ ] Set `DEBUG = False` in `main.py`
- [ ] Use a strong, random `SECRET_KEY`
- [ ] Switch to PostgreSQL (or another production database)
- [ ] Set up environment variables for secrets
- [ ] Configure a WSGI server (Gunicorn, uWSGI)
- [ ] Set up a reverse proxy (Nginx, Apache)
- [ ] Enable HTTPS/SSL
- [ ] Set up proper logging
- [ ] Configure backups for database
- [ ] Set up monitoring and error tracking
- [ ] Review and harden security settings

### Example Production Setup (Nginx + Gunicorn)

1. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Run Gunicorn:
   ```bash
   gunicorn -w 4 -b 127.0.0.1:8000 main:app
   ```

3. Configure Nginx as reverse proxy (example):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /static {
           alias /path/to/becauseimstuck/static;
       }
   }
   ```

## Representative Confirmation

### User Interface

Logged-in users can confirm and update their representative information:

1. **Navigation**: Click "Find My Reps" in the sidebar or user menu
2. **Confirmation Page** (`/confirm-reps`):
   - Shows registered address
   - Displays current representative information
   - One-click lookup from Missouri Legislature website
   - Automatically updates user profile

### Command-Line Script

Administrators can batch-update representative information:

```bash
# Update all users with missing or stale rep data (90+ days old)
python3 confirm_user_reps.py

# Update a specific user
python3 confirm_user_reps.py --user-id 123
python3 confirm_user_reps.py --username johndoe

# Force update even if data is recent
python3 confirm_user_reps.py --user-id 123 --force

# Update all users
python3 confirm_user_reps.py --all

# Custom staleness threshold
python3 confirm_user_reps.py --stale-days 30
```

Example output:
```
============================================================
REPRESENTATIVE CONFIRMATION REPORT
============================================================
Processing 5 user(s)...

🔍 Looking up representatives for: johndoe
   Address: 123 Main St, Jefferson City, MO 65101

✅ User: johndoe (ID: 1)
   Representatives updated successfully
   👔 State Senator: Jane Smith
      District: 15, Party: D
   🏛️  State Representative: John Johnson
      District: 48, Party: R
```

## API Endpoints

### Authentication
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /register` - Registration page
- `POST /register` - Process registration
- `GET /logout` - Logout user
- `GET /confirm-reps` - Representative confirmation page

### Bills
- `GET /bills` - List all bills
- `GET /bill/<id>` - View bill detail
- `POST /bill/<id>/comment` - Add comment to bill
- `POST /bill/<id>/support` - Support/oppose bill
- `POST /comment/<id>/support` - Support a comment

### Representatives
- `GET /representatives` - List all representatives
- `GET /representative/<id>` - View representative detail

### Events
- `GET /rep/events` - Manage events (reps/admins)
- `GET /rep/events/create` - Create new event
- `POST /rep/events/create` - Process event creation
- `GET /event/<id>` - View event details
- `POST /event/<id>/rsvp` - RSVP to event
- `POST /event/<id>/purchase` - Purchase event options
- `GET /my-invitations` - View event invitations

### Messages
- `GET /messages` - Message inbox
- `GET /message/compose` - Compose new message
- `POST /message/compose` - Send message
- `GET /message/<id>` - View message

### Profile
- `GET /profile` - View own profile
- `GET /profile/edit` - Edit profile page
- `POST /profile/edit` - Update profile
- `POST /profile/run_support/<user_id>/toggle` - Toggle run support

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Contribution Guidelines

- Write tests for new features
- Update documentation as needed
- Follow existing code style
- Keep commits focused and atomic
- Write descriptive commit messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support & Contact

- **Issues**: Open an issue on GitHub
- **Questions**: Use GitHub Discussions
- **Security**: Report security issues privately to repository maintainers

## Acknowledgments

- Missouri House of Representatives for public bill and representative data
- Bootstrap 5 for UI components
- Flask framework and extensions
- All contributors to this project

---

**Note**: This application is for educational and civic engagement purposes. Always verify legislative information with official government sources.
