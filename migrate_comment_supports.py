"""Migration script to create comment_supports table."""
from main import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS comment_supports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                value INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_comment FOREIGN KEY(comment_id) REFERENCES comments(id) ON DELETE CASCADE,
                CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT uq_comment_user_vote UNIQUE(comment_id, user_id)
            )
        """))
        db.session.commit()
        print("✓ comment_supports table ensured")
    except Exception as e:
        print(f"Error creating comment_supports table: {e}")
