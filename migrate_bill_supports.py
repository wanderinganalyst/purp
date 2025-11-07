"""Migration script to create bill_supports table."""
from main import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS bill_supports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_number VARCHAR(20) NOT NULL,
                user_id INTEGER NOT NULL,
                value INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_bill FOREIGN KEY(bill_number) REFERENCES bills(bill_number) ON DELETE CASCADE,
                CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT uq_bill_user_vote UNIQUE(bill_number, user_id)
            )
        """))
        db.session.commit()
        print("✓ bill_supports table ensured")
    except Exception as e:
        print(f"Error creating bill_supports table: {e}")
