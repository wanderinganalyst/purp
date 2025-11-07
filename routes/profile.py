"""
Profile routes for viewing and editing user profiles.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import User, RunSupport
from auth import login_required
from utils.validators import sanitize_input

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/')
@login_required
def view_profile():
    """View the current user's profile."""
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.')
        return redirect(url_for('auth.login'))
    
    # Compute run support count if user is thinking about running
    run_support_count = 0
    user_has_self_flag = user.thinking_about_running
    current_user_supports = False
    if user_has_self_flag:
        try:
            from sqlalchemy import func
            run_support_count = RunSupport.query.filter_by(candidate_user_id=user.id).count()
            if session.get('user_id') and session['user_id'] != user.id:
                existing = RunSupport.query.filter_by(candidate_user_id=user.id, supporter_user_id=session['user_id']).first()
                current_user_supports = existing is not None
        except Exception:
            pass
    return render_template('profile/view.html', user=user, run_support_count=run_support_count, current_user_supports=current_user_supports)

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit the current user's profile."""
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Get form data
        bio = sanitize_input(request.form.get('bio', ''), 5000)
        thinking_about_running = request.form.get('thinking_about_running') == 'on'
        
        # Update user profile
        try:
            user.bio = bio if bio else None
            user.thinking_about_running = thinking_about_running
            
            db.session.commit()
            flash('Profile updated successfully!')
            return redirect(url_for('profile.view_profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.')
            return redirect(url_for('profile.edit_profile'))
    
    return render_template('profile/edit.html', user=user)


@profile_bp.route('/run_support/<int:candidate_user_id>/toggle', methods=['POST'])
@login_required
def toggle_run_support(candidate_user_id):
    """Toggle current user's support for someone thinking about running.

    Rules:
    - Cannot support yourself.
    - Target user must exist and have thinking_about_running True.
    - Toggle off if already supported.
    """
    current_user = User.query.get(session['user_id'])
    candidate = User.query.get(candidate_user_id)

    if not candidate or not candidate.thinking_about_running:
        flash('User is not marked as thinking about running.')
        return redirect(request.referrer or url_for('profile.view_profile'))
    if candidate.id == current_user.id:
        flash('You cannot mark support for yourself.')
        return redirect(request.referrer or url_for('profile.view_profile'))

    existing = RunSupport.query.filter_by(candidate_user_id=candidate.id, supporter_user_id=current_user.id).first()
    try:
        if existing:
            db.session.delete(existing)  # toggle off
            flash('Removed your support.')
        else:
            db.session.add(RunSupport(candidate_user_id=candidate.id, supporter_user_id=current_user.id))
            flash('You now support this user running!')
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Could not update your support. Please try again.')

    # Redirect back where the action originated (bill detail, profile, etc.)
    return redirect(request.referrer or url_for('profile.view_profile'))
