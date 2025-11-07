#!/usr/bin/env python3
"""
Add bill text columns to the database.
This migration adds columns for storing full bill text and PDF URLs.
"""
from extensions import db
from main import app

def migrate():
    """Add new columns to bills table."""
    with app.app_context():
        try:
            # Try to add columns using raw SQL
            with db.engine.connect() as conn:
                # Check if columns already exist
                result = conn.execute(db.text("PRAGMA table_info(bills)"))
                columns = [row[1] for row in result]
                
                if 'full_text' in columns:
                    print("✓ Columns already exist, no migration needed")
                    return
                
                print("Adding new columns to bills table...")
                
                # Add columns
                conn.execute(db.text("ALTER TABLE bills ADD COLUMN full_text TEXT"))
                conn.execute(db.text("ALTER TABLE bills ADD COLUMN text_pdf_url VARCHAR(500)"))
                conn.execute(db.text("ALTER TABLE bills ADD COLUMN summary_pdf_url VARCHAR(500)"))
                conn.execute(db.text("ALTER TABLE bills ADD COLUMN text_fetched_at DATETIME"))
                conn.commit()
                
                print("✓ Successfully added bill text columns")
                
        except Exception as e:
            print(f"✗ Error during migration: {e}")
            raise

if __name__ == '__main__':
    migrate()
