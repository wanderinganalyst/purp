from extensions import db
from models import Comment, User

def add_comment(bill_id, user_id, content):
    """Add a new comment to a bill."""
    try:
        comment = Comment(
            bill_id=bill_id,
            user_id=user_id,
            content=content
        )
        db.session.add(comment)
        db.session.commit()
        return comment
    except Exception as e:
        db.session.rollback()
        raise e

def get_comments_for_bill(bill_id):
    """Get all visible comments for a bill."""
    return Comment.query.filter_by(
        bill_id=bill_id,
        is_hidden=False
    ).order_by(Comment.created_at.desc()).all()

def hide_comment(comment_id, user):
    """Hide a comment (power users only)."""
    try:
        comment = Comment.query.get(comment_id)
        if comment and user.role == 'power':
            comment.is_hidden = True
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        raise e

def delete_comment(comment_id, user: User):
    """Delete a comment.

    - Power users can delete any comment.
    - Regular users can delete only their own comments.
    """
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return False
        if user.role == 'power' or (comment.user_id == user.id):
            db.session.delete(comment)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        raise e

def update_comment(comment_id, user: User, content: str):
    """Update a comment's content.

    - Power users can edit any comment.
    - Regular users can edit only their own comments.
    Returns True on success, False otherwise.
    """
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return False
        if user.role == 'power' or (comment.user_id == user.id):
            comment.content = content
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        raise e