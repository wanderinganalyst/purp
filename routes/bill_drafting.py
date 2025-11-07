"""
Routes for AI-powered bill drafting.
Representatives can use LLM to draft new bills based on successful/failed bill patterns.
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from functools import wraps
from models import User, Bill, Representative
from services.bill_drafting import (
    create_llm_bill_draft,
    get_bill_drafting_statistics,
    get_bills_by_category,
    save_draft_bill,
    update_draft_visibility,
    get_rep_drafts,
    get_visible_drafts_for_user,
    get_draft_by_id,
    delete_draft_bill,
    add_draft_comment,
    get_draft_comments,
    get_draft_statistics
)

bill_drafting_bp = Blueprint('bill_drafting', __name__)


def rep_required(f):
    """Decorator to require representative role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(user_id)
        if not user or user.role != 'rep':
            flash('This feature is only available to representatives.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


def rep_or_staffer_required(f):
    """Decorator to require representative or staffer role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(user_id)
        if not user or user.role not in ['rep', 'staffer']:
            flash('This feature is only available to representatives and staff.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


@bill_drafting_bp.route('/draft-bill')
@rep_required
def draft_bill():
    """
    Main bill drafting interface for representatives.
    Shows statistics and provides form to generate bill drafts.
    """
    from flask import session
    user = User.query.get(session.get('user_id'))
    
    # Get overall statistics
    stats = get_bill_drafting_statistics()
    
    # Get topic filter from query params
    topic_filter = request.args.get('topic')
    if topic_filter:
        filtered_stats = get_bill_drafting_statistics(topic_filter)
        stats['filtered'] = filtered_stats
    
    return render_template(
        'bill_drafting/draft.html',
        user=user,
        stats=stats,
        topic_filter=topic_filter
    )


@bill_drafting_bp.route('/draft-bill/generate', methods=['POST'])
@rep_required
def generate_draft():
    """
    Generate a bill draft using LLM.
    Accepts form data and returns the LLM prompt + context.
    """
    from flask import session
    
    # Get form data
    topic = request.form.get('topic', '').strip()
    description = request.form.get('description', '').strip()
    topic_filter = request.form.get('topic_filter', '').strip()
    additional_instructions = request.form.get('additional_instructions', '').strip()
    max_examples = int(request.form.get('max_examples', 3))
    
    # Validate
    if not topic:
        flash('Please provide a bill topic.', 'error')
        return redirect(url_for('bill_drafting.draft_bill'))
    
    if not description:
        flash('Please provide a bill description.', 'error')
        return redirect(url_for('bill_drafting.draft_bill'))
    
    # Generate prompt
    try:
        prompt, context_info = create_llm_bill_draft(
            topic=topic,
            description=description,
            topic_filter=topic_filter or None,
            additional_instructions=additional_instructions or None,
            max_examples=max_examples
        )
        
        return render_template(
            'bill_drafting/result.html',
            topic=topic,
            description=description,
            prompt=prompt,
            context_info=context_info,
            additional_instructions=additional_instructions
        )
        
    except Exception as e:
        flash(f'Error generating draft: {str(e)}', 'error')
        return redirect(url_for('bill_drafting.draft_bill'))


@bill_drafting_bp.route('/draft-bill/api/generate', methods=['POST'])
@rep_required
def api_generate_draft():
    """
    API endpoint to generate bill draft.
    Returns JSON with prompt and context.
    """
    data = request.get_json()
    
    topic = data.get('topic', '').strip()
    description = data.get('description', '').strip()
    topic_filter = data.get('topic_filter')
    additional_instructions = data.get('additional_instructions')
    max_examples = data.get('max_examples', 3)
    
    if not topic or not description:
        return jsonify({
            'error': 'Topic and description are required'
        }), 400
    
    try:
        prompt, context_info = create_llm_bill_draft(
            topic=topic,
            description=description,
            topic_filter=topic_filter,
            additional_instructions=additional_instructions,
            max_examples=max_examples
        )
        
        return jsonify({
            'success': True,
            'prompt': prompt,
            'context': context_info
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@bill_drafting_bp.route('/draft-bill/statistics')
@rep_required
def statistics():
    """
    Show detailed statistics about passed/failed bills.
    """
    topic = request.args.get('topic')
    stats = get_bill_drafting_statistics(topic)
    
    return render_template(
        'bill_drafting/statistics.html',
        stats=stats,
        topic=topic
    )


@bill_drafting_bp.route('/draft-bill/api/statistics')
@rep_required
def api_statistics():
    """
    API endpoint for bill statistics.
    """
    topic = request.args.get('topic')
    stats = get_bill_drafting_statistics(topic)
    
    return jsonify(stats)


@bill_drafting_bp.route('/draft-bill/browse')
@rep_required
def browse_examples():
    """
    Browse passed and failed bills as examples.
    """
    topic = request.args.get('topic')
    category = request.args.get('category', 'passed')  # passed, failed, or active
    
    categorized = get_bills_by_category(topic)
    bills = categorized.get(category, [])
    
    return render_template(
        'bill_drafting/browse.html',
        bills=bills,
        category=category,
        topic=topic,
        categorized=categorized
    )


# ============================================================================
# DRAFT WORKSPACE ROUTES
# ============================================================================

@bill_drafting_bp.route('/draft-bill/workspace')
@rep_or_staffer_required
def workspace():
    """
    Representative's draft bill workspace.
    Shows all their draft bills with visibility controls.
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # Get representative ID (could be rep themselves or their staffer's boss)
    if user.role == 'rep':
        rep_id = user.representative_id
    elif user.role == 'staffer':
        rep_id = user.rep_boss_id
    else:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    # Get representative and their drafts
    representative = Representative.query.get(rep_id)
    if not representative:
        flash('Representative profile not found.', 'error')
        return redirect(url_for('index'))
    
    drafts = get_rep_drafts(rep_id)
    stats = get_draft_statistics(rep_id)
    
    return render_template(
        'bill_drafting/workspace.html',
        user=user,
        representative=representative,
        drafts=drafts,
        stats=stats
    )


@bill_drafting_bp.route('/draft-bill/save', methods=['POST'])
@rep_required
def save_draft():
    """
    Save a new draft bill or update an existing one.
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user.representative_id:
        flash('You must have a representative profile to save drafts.', 'error')
        return redirect(url_for('bill_drafting.draft_bill'))
    
    # Get form data
    draft_id = request.form.get('draft_id')  # If updating
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    content = request.form.get('content', '').strip()
    visibility = request.form.get('visibility', 'hidden')
    topic = request.form.get('topic', '').strip()
    llm_prompt = request.form.get('llm_prompt')
    
    # Validate
    if not title:
        flash('Please provide a bill title.', 'error')
        return redirect(request.referrer or url_for('bill_drafting.workspace'))
    
    if not content:
        flash('Please provide bill content.', 'error')
        return redirect(request.referrer or url_for('bill_drafting.workspace'))
    
    try:
        if draft_id:
            # Update existing draft
            from services.bill_drafting import update_draft_bill
            draft = update_draft_bill(
                int(draft_id),
                title=title,
                content=content,
                description=description,
                visibility=visibility
            )
            if draft:
                flash('Draft bill updated successfully!', 'success')
            else:
                flash('Draft not found.', 'error')
        else:
            # Create new draft
            draft = save_draft_bill(
                representative_id=user.representative_id,
                title=title,
                content=content,
                description=description,
                visibility=visibility,
                topic=topic or None,
                llm_prompt_used=llm_prompt
            )
            flash('Draft bill saved successfully!', 'success')
        
        return redirect(url_for('bill_drafting.view_draft', draft_id=draft.id))
        
    except Exception as e:
        flash(f'Error saving draft: {str(e)}', 'error')
        return redirect(request.referrer or url_for('bill_drafting.workspace'))


@bill_drafting_bp.route('/draft-bill/<int:draft_id>/visibility', methods=['POST'])
@rep_required
def update_visibility(draft_id):
    """
    Update visibility of a draft bill.
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    draft = get_draft_by_id(draft_id)
    if not draft:
        return jsonify({'error': 'Draft not found'}), 404
    
    # Only the rep who created it can update
    if draft.representative_id != user.representative_id:
        return jsonify({'error': 'Access denied'}), 403
    
    visibility = request.json.get('visibility') if request.is_json else request.form.get('visibility')
    
    if visibility not in ['hidden', 'constituents', 'public']:
        return jsonify({'error': 'Invalid visibility'}), 400
    
    try:
        draft = update_draft_visibility(draft_id, visibility)
        if request.is_json:
            return jsonify({
                'success': True,
                'visibility': draft.visibility
            })
        else:
            flash(f'Visibility updated to {visibility}!', 'success')
            return redirect(url_for('bill_drafting.view_draft', draft_id=draft_id))
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('bill_drafting.view_draft', draft_id=draft_id))


@bill_drafting_bp.route('/draft-bill/<int:draft_id>')
def view_draft(draft_id):
    """
    View a draft bill with comments.
    Visibility controlled - only visible to those with permission.
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    
    draft = get_draft_by_id(draft_id)
    if not draft:
        flash('Draft not found.', 'error')
        return redirect(url_for('index'))
    
    # Check if user can view this draft
    if not draft.can_view(user):
        flash('You do not have permission to view this draft.', 'error')
        return redirect(url_for('index'))
    
    # Get comments
    comments = get_draft_comments(draft_id)
    
    # Check if user is owner or staffer
    is_owner = user and user.representative_id == draft.representative_id
    is_staffer = user and user.role == 'staffer' and user.rep_boss_id == draft.representative_id
    can_edit = is_owner or is_staffer
    
    return render_template(
        'bill_drafting/draft_detail.html',
        user=user,
        draft=draft,
        comments=comments,
        is_owner=is_owner,
        is_staffer=is_staffer,
        can_edit=can_edit
    )


@bill_drafting_bp.route('/draft-bill/<int:draft_id>/comment', methods=['POST'])
def add_comment(draft_id):
    """
    Add a comment to a draft bill.
    Anyone who can view the draft can comment.
    """
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to comment.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    draft = get_draft_by_id(draft_id)
    
    if not draft:
        flash('Draft not found.', 'error')
        return redirect(url_for('index'))
    
    # Check if user can view (and thus comment on) this draft
    if not draft.can_view(user):
        flash('You do not have permission to comment on this draft.', 'error')
        return redirect(url_for('index'))
    
    comment_text = request.form.get('comment_text', '').strip()
    if not comment_text:
        flash('Please enter a comment.', 'error')
        return redirect(url_for('bill_drafting.view_draft', draft_id=draft_id))
    
    # Determine if this is a staffer comment
    is_staffer = user.role == 'staffer' and user.rep_boss_id == draft.representative_id
    
    try:
        add_draft_comment(
            draft_bill_id=draft_id,
            user_id=user_id,
            comment_text=comment_text,
            is_staffer=is_staffer
        )
        flash('Comment added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding comment: {str(e)}', 'error')
    
    return redirect(url_for('bill_drafting.view_draft', draft_id=draft_id))


@bill_drafting_bp.route('/draft-bill/<int:draft_id>/delete', methods=['POST'])
@rep_required
def delete_draft(draft_id):
    """
    Delete a draft bill.
    Only the rep who created it can delete.
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    draft = get_draft_by_id(draft_id)
    if not draft:
        flash('Draft not found.', 'error')
        return redirect(url_for('bill_drafting.workspace'))
    
    # Only the rep who created it can delete
    if draft.representative_id != user.representative_id:
        flash('Access denied.', 'error')
        return redirect(url_for('bill_drafting.workspace'))
    
    try:
        delete_draft_bill(draft_id)
        flash('Draft bill deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting draft: {str(e)}', 'error')
    
    return redirect(url_for('bill_drafting.workspace'))
