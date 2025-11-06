"""Initialize the SQL database (Postgres) and create two demo users.

Run (after database is available):

    python init_db.py

This script uses the application's SQLAlchemy `db` and `User` model.
"""
from main import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash
from rep_lookup import RepresentativeLookup


def init_db():
    with app.app_context():
        # First, create all tables
        db.create_all()
        
        # Create demo users directly
        try:
            # Regular user with Jefferson City address
            u = User(
                username='regular',
                role='regular',
                street_address='201 W Capitol Ave',
                apt_unit='',
                city='Jefferson City',
                state='MO',
                zipcode='65101',
                address_verified=True
            )
            u.set_password('Password1!')
            db.session.add(u)
            
            # Power user with St. Louis address
            p = User(
                username='power',
                role='power',
                street_address='200 N Broadway',
                apt_unit='',
                city='St Louis',
                state='MO',
                zipcode='63102',
                address_verified=True
            )
            p.set_password('Powerpass1!')
            db.session.add(p)
            
            db.session.commit()
            
            # Add representative data for demo users
            # Note: Using mock data since live lookup may require browser session
            try:
                from datetime import datetime
                
                # Regular user - Kansas City
                u.senator_name = "Barbara Washington"
                u.senator_district = "9"
                u.senator_party = "D"
                u.representative_name = "Mark Sharp"
                u.representative_district = "36"
                u.representative_party = "D"
                u.reps_last_updated = datetime.utcnow()
                
                # Power user - St. Louis
                p.senator_name = "Steven Roberts"
                p.senator_district = "5"
                p.senator_party = "D"
                p.representative_name = "Peter Merideth"
                p.representative_district = "80"
                p.representative_party = "D"
                p.reps_last_updated = datetime.utcnow()
                
                db.session.commit()
                print('Initialized DB and added demo users with representative data:')
                print('  regular/Password1! (Jefferson City - Sen. Washington D-9, Rep. Sharp D-36)')
                print('  power/Powerpass1! (St. Louis - Sen. Roberts D-5, Rep. Merideth D-80)')
            except Exception as e:
                print(f'Note: Error adding representative data: {e}')
                print('Initialized DB and added demo users: regular/Password1! and power/Powerpass1!')
                
        except Exception as e:
            print(f'Error: {e}')
            db.session.rollback()


if __name__ == '__main__':
    init_db()
