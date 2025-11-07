"""Migration script to create run_supports table."""
from main import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS run_supports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_user_id INTEGER NOT NULL,
                supporter_user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_candidate FOREIGN KEY(candidate_user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_supporter FOREIGN KEY(supporter_user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT uq_candidate_supporter UNIQUE(candidate_user_id, supporter_user_id)
            )
        """))
        db.session.commit()
        print("✓ run_supports table ensured")
    except Exception as e:
        print(f"Error creating run_supports table: {e}")
