"""
Migration script to add template_id column to events table.
SQLite doesn't support ALTER TABLE ADD COLUMN with foreign keys easily,
so we'll recreate the table.
"""
from main import create_app
from extensions import db
from sqlalchemy import text

def migrate_events_table():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if template_id column already exists
            result = db.session.execute(text("PRAGMA table_info(events)"))
            columns = [row[1] for row in result]
            
            if 'template_id' in columns:
                print('✓ template_id column already exists in events table')
                return
            
            print('📝 Migrating events table to add template_id column...')
            
            # Step 1: Rename old table
            db.session.execute(text('ALTER TABLE events RENAME TO events_old'))
            
            # Step 2: Create new table with template_id
            db.session.execute(text('''
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    representative_id INTEGER NOT NULL,
                    template_id INTEGER,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    event_date DATETIME NOT NULL,
                    location VARCHAR(255),
                    event_type VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (representative_id) REFERENCES representatives(id),
                    FOREIGN KEY (template_id) REFERENCES event_templates(id)
                )
            '''))
            
            # Step 3: Copy data from old table
            db.session.execute(text('''
                INSERT INTO events (id, representative_id, title, description, event_date, location, event_type, created_at, updated_at)
                SELECT id, representative_id, title, description, event_date, location, event_type, created_at, updated_at
                FROM events_old
            '''))
            
            # Step 4: Drop old table
            db.session.execute(text('DROP TABLE events_old'))
            
            db.session.commit()
            print('✅ Events table migrated successfully!')
            print('✓ template_id column added')
            
        except Exception as e:
            db.session.rollback()
            print(f'❌ Migration failed: {e}')
            raise

if __name__ == '__main__':
    migrate_events_table()
