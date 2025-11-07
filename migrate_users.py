"""
Migration script to add representative_id column to users table.
"""
from main import create_app
from extensions import db
from sqlalchemy import text

def migrate_users_table():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if representative_id column already exists
            result = db.session.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            if 'representative_id' in columns:
                print('✓ representative_id column already exists in users table')
                return
            
            print('📝 Migrating users table to add representative_id column...')
            
            # Add the column (SQLite supports this for simple columns without foreign keys)
            db.session.execute(text('ALTER TABLE users ADD COLUMN representative_id INTEGER'))
            
            db.session.commit()
            print('✅ Users table migrated successfully!')
            print('✓ representative_id column added')
            
        except Exception as e:
            db.session.rollback()
            print(f'❌ Migration failed: {e}')
            raise

if __name__ == '__main__':
    migrate_users_table()
