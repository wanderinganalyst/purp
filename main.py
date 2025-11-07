import os
import time
import re
import secrets
import urllib.request
from bs4 import BeautifulSoup
from flask import Flask, render_template, session, flash, redirect, url_for, request
from flask_migrate import Migrate
from extensions import db
from datetime import datetime
from auth import login_required, role_required
from models import User, Comment
from utils.data_fetcher import get_data_fetcher

# Global caches
_bills_cache = {'ts': 0, 'data': None}
_BILLS_TTL = int(os.environ.get('BILLS_CACHE_TTL', 300))
_reps_cache = {'ts': 0, 'data': None}
_REPS_TTL = int(os.environ.get('REPS_CACHE_TTL', 300))

def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(auth_bp)

    from routes.bills import bills_bp
    app.register_blueprint(bills_bp)

    from routes.representatives import reps_bp
    app.register_blueprint(reps_bp)
    
    from routes.messages import messages_bp
    app.register_blueprint(messages_bp)
    
    from routes.events import events_bp
    app.register_blueprint(events_bp)
    
    from routes.profile import profile_bp
    app.register_blueprint(profile_bp)
    
    from routes.bill_drafting import bill_drafting_bp
    app.register_blueprint(bill_drafting_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors."""
        return render_template('errors/403.html'), 403

    @app.context_processor
    def utility_processor():
        """Make common utilities available to templates."""
        def format_datetime(value, format='%Y-%m-%d %H:%M'):
            """Format a datetime object."""
            if value is None:
                return ""
            return value.strftime(format)
        
        def get_user_reps():
            """Get representative information for logged-in user."""
            if 'user_id' in session:
                user = User.query.get(session.get('user_id'))
                if user:
                    return user.get_representatives_display()
            return {'has_data': False, 'senator': None, 'representative': None}
        
        return dict(
            format_datetime=format_datetime,
            get_user_reps=get_user_reps
        )

    @app.route('/')
    def index():
        user = None
        if 'user_id' in session:
            user = User.query.get(session.get('user_id'))
        return render_template('index.html', user=user)

    @app.route('/about')
    def about():
        return render_template('about.html')

    # Start background scheduler for periodic syncs (weekly bills, quarterly reps)
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        if os.environ.get('ENABLE_SCHEDULER', '1') == '1':
            scheduler = BackgroundScheduler(timezone='UTC')

            def _sync_bills_job():
                from sync_bills import sync_bills_to_database
                with app.app_context():
                    app.logger.info(f"[Scheduler] Syncing bills @ {datetime.utcnow().isoformat()}Z")
                    sync_bills_to_database()

            def _sync_reps_job():
                from sync_reps import main as sync_reps_main
                with app.app_context():
                    app.logger.info(f"[Scheduler] Syncing representatives @ {datetime.utcnow().isoformat()}Z")
                    sync_reps_main()

            # Weekly on Sunday at 03:00 UTC
            scheduler.add_job(_sync_bills_job, CronTrigger(day_of_week='sun', hour=3, minute=0))
            # Quarterly on the 1st day of Jan, Apr, Jul, Oct at 04:00 UTC
            scheduler.add_job(_sync_reps_job, CronTrigger(month='1,4,7,10', day=1, hour=4, minute=0))
            scheduler.start()
            app.logger.info('Background scheduler started (weekly bills, quarterly reps).')
    except Exception as e:
        # Don't crash app if scheduler setup fails
        print(f"Scheduler initialization skipped/error: {e}")

    return app


def fetch_remote_page(url, timeout=10):
    """Fetch a remote page using urllib and return decoded text."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            content_bytes = resp.read()
            try:
                return content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return content_bytes.decode('latin-1')
    except Exception:
        return None


def parse_bills_with_bs(html_text):
    """Parse bills from HTML text using BeautifulSoup."""
    if not html_text:
        return []

    soup = BeautifulSoup(html_text, 'html.parser')
    bills = []
    bills_table = soup.find('table', class_='sortable')
    
    if not bills_table:
        return []

    for row in bills_table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) >= 3:
            bill_id = cols[0].text.strip()
            description = cols[1].text.strip()
            sponsor = cols[2].text.strip()
            
            bill_link = cols[0].find('a')
            bill_url = bill_link['href'] if bill_link else None
            
            if bill_id and sponsor:
                bills.append({
                    'id': bill_id,
                    'description': description,
                    'sponsor': sponsor,
                    'url': bill_url
                })
    
    return bills


def get_rep_by_name(name):
    """Get a representative by their name from the cache."""
    if _reps_cache['data']:
        for rep in _reps_cache['data']:
            if rep['name'].lower() == name.lower():
                rep['sponsored_bills'] = []
                if _bills_cache['data']:
                    for bill in _bills_cache['data']:
                        if bill['sponsor'].lower() == name.lower():
                            rep['sponsored_bills'].append(bill)
                return rep
    return None


# Create the application instance
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    app.run()