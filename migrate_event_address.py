"""
Migration script to add address fields and time fields to events table.
"""
from main import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Add address fields and event_time to events table
    try:
        # Add street_address
        db.session.execute(text('ALTER TABLE events ADD COLUMN street_address VARCHAR(255)'))
        print('✓ Added street_address column')
    except Exception as e:
        print(f'street_address column may already exist: {e}')
    
    try:
        # Add city
        db.session.execute(text('ALTER TABLE events ADD COLUMN city VARCHAR(100)'))
        print('✓ Added city column')
    except Exception as e:
        print(f'city column may already exist: {e}')
    
    try:
        # Add state
        db.session.execute(text('ALTER TABLE events ADD COLUMN state VARCHAR(2)'))
        print('✓ Added state column')
    except Exception as e:
        print(f'state column may already exist: {e}')
    
    try:
        # Add zipcode
        db.session.execute(text('ALTER TABLE events ADD COLUMN zipcode VARCHAR(10)'))
        print('✓ Added zipcode column')
    except Exception as e:
        print(f'zipcode column may already exist: {e}')
    
    try:
        # Add event_time (separate time field if different from event_date)
        db.session.execute(text('ALTER TABLE events ADD COLUMN event_time VARCHAR(20)'))
        print('✓ Added event_time column')
    except Exception as e:
        print(f'event_time column may already exist: {e}')
    
    db.session.commit()
    print('\n✅ Event address migration completed!')
    
    # Show the updated schema
    result = db.session.execute(text('PRAGMA table_info(events)'))
    print('\nEvents table columns:')
    for row in result:
        print(f'  {row[1]}: {row[2]}')
