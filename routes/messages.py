from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User, Message
from extensions import db
from auth import login_required
from utils.validators import validate_comment_content, sanitize_input
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/messages')
@login_required
def inbox():
    """Display user's sent messages."""
    user = User.query.get(session['user_id'])
    if not user:
        flash('Please log in to view messages.')
        return redirect(url_for('auth.login'))
    
    # Get all messages sent by this user
    sent_messages = Message.query.filter_by(sender_id=user.id).order_by(Message.sent_at.desc()).all()
    
    return render_template('messages/inbox.html', messages=sent_messages, user=user)

@messages_bp.route('/message/compose', methods=['GET', 'POST'])
@login_required
def compose():
    """Compose a message to user's representative or senator."""
    user = User.query.get(session['user_id'])
    if not user:
        flash('Please log in to send messages.')
        return redirect(url_for('auth.login'))
    
    # Check if user has representatives set up
    user_reps = user.get_representatives_display()
    if not user_reps.get('has_data'):
        flash('Please set up your representatives first to send messages.')
        return redirect(url_for('auth.confirm_reps'))
    
    if request.method == 'POST':
        recipient_type = sanitize_input(request.form.get('recipient_type', ''), 20)
        subject = sanitize_input(request.form.get('subject', ''), 255)
        content = sanitize_input(request.form.get('content', ''), 5000)
        
        # Validate recipient type
        if recipient_type not in ['representative', 'senator']:
            flash('Invalid recipient type.')
            return redirect(url_for('messages.compose'))
        
        # Validate that user is messaging their own representative
        if recipient_type == 'representative':
            if not user.representative_name:
                flash('You do not have a representative set up.')
                return redirect(url_for('messages.compose'))
            recipient_name = user.representative_name
            recipient_district = user.representative_district
        else:  # senator
            if not user.senator_name:
                flash('You do not have a senator set up.')
                return redirect(url_for('messages.compose'))
            recipient_name = user.senator_name
            recipient_district = user.senator_district
        
        # Validate subject
        if not subject or len(subject.strip()) < 3:
            flash('Subject must be at least 3 characters.')
            return redirect(url_for('messages.compose'))
        
        # Validate content
        valid, error = validate_comment_content(content)
        if not valid:
            flash(error)
            return redirect(url_for('messages.compose'))
        
        # Create and save message
        try:
            message = Message(
                sender_id=user.id,
                recipient_rep_name=recipient_name,
                recipient_rep_district=recipient_district,
                recipient_type=recipient_type,
                subject=subject,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            flash(f'Your message to {recipient_name} has been sent!')
            return redirect(url_for('messages.inbox'))
        except Exception as e:
            db.session.rollback()
            flash('Error sending message. Please try again.')
            return redirect(url_for('messages.compose'))
    
    return render_template('messages/compose.html', user_reps=user_reps)

@messages_bp.route('/message/<int:message_id>')
@login_required
def view_message(message_id):
    """View a specific message."""
    user = User.query.get(session['user_id'])
    if not user:
        flash('Please log in to view messages.')
        return redirect(url_for('auth.login'))
    
    message = Message.query.get_or_404(message_id)
    
    # Ensure user can only view their own messages (unless admin)
    if user.role != 'admin' and message.sender_id != user.id:
        flash('You do not have permission to view this message.')
        return redirect(url_for('messages.inbox'))
    
    return render_template('messages/view.html', message=message)


@messages_bp.route('/message/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    """Delete a message."""
    user = User.query.get(session['user_id'])
    if not user:
        flash('Please log in.')
        return redirect(url_for('auth.login'))
    
    message = Message.query.get_or_404(message_id)
    
    # Users can delete their own messages, admins can delete any message
    if user.role != 'admin' and message.sender_id != user.id:
        flash('You do not have permission to delete this message.')
        return redirect(url_for('messages.inbox'))
    
    try:
        db.session.delete(message)
        db.session.commit()
        flash('Message deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting message. Please try again.')
    
    return redirect(url_for('messages.inbox'))
