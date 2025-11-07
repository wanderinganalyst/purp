"""
Migration script to add profile fields to users table.
"""
from main import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Add bio column
        db.session.execute(text('ALTER TABLE users ADD COLUMN bio TEXT'))
        print("✓ Added bio column")
    except Exception as e:
        print(f"bio column: {e}")
    
    try:
        # Add thinking_about_running column
        db.session.execute(text('ALTER TABLE users ADD COLUMN thinking_about_running BOOLEAN NOT NULL DEFAULT 0'))
        print("✓ Added thinking_about_running column")
    except Exception as e:
        print(f"thinking_about_running column: {e}")
    
    db.session.commit()
    print("\n✓ Migration completed!")
