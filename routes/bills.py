from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.bills import get_cached_bills, parse_bills_with_bs, get_bill_details
from services.web_utils import fetch_remote_page
from services.comments import get_comments_for_bill, add_comment, delete_comment, update_comment
from models import User, Comment, Bill, CommentSupport, BillSupport, RunSupport
from extensions import db
from auth import login_required
from utils.validators import validate_comment_content, sanitize_input
from utils.data_fetcher import get_data_fetcher

bills_bp = Blueprint('bills', __name__)
from sqlalchemy import func

@bills_bp.route('/bills')
def bills_list():
    """Display list of all bills from database with pagination, search, and sorting."""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    search = request.args.get('search', '', type=str).strip()
    sort_by = request.args.get('sort', 'number', type=str)  # number, title, updated
    
    # Limit per_page to reasonable values
    per_page = min(max(per_page, 10), 500)
    
    bills = None
    pagination = None
    
    # Try database first
    try:
        # Start with base query
        query = Bill.query
        
        # Apply search filter if provided
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                db.or_(
                    Bill.bill_number.ilike(search_filter),
                    Bill.title.ilike(search_filter),
                    Bill.description.ilike(search_filter),
                    Bill.sponsor.ilike(search_filter)
                )
            )
        
        # Apply sorting
        if sort_by == 'title':
            query = query.order_by(Bill.title.asc())
        elif sort_by == 'updated':
            query = query.order_by(Bill.updated_at.desc())
        else:  # default to number
            query = query.order_by(Bill.bill_number.asc())
        
        # Get paginated results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        if pagination.items:
            # Annotate counts for supports/opposes
            numbers = [b.bill_number for b in pagination.items]
            if numbers:
                counts = db.session.query(BillSupport.bill_number, BillSupport.value, func.count('*')) \
                    .filter(BillSupport.bill_number.in_(numbers)) \
                    .group_by(BillSupport.bill_number, BillSupport.value).all()
                counts_map = {}
                for num, val, cnt in counts:
                    counts_map.setdefault(num, {1: 0, -1: 0})
                    counts_map[num][val] = cnt
                for b in pagination.items:
                    c = counts_map.get(b.bill_number, {1: 0, -1: 0})
                    # attach for template consumption when using model objects
                    b.support_count = c.get(1, 0)
                    b.oppose_count = c.get(-1, 0)
            bills = [bill.to_dict() for bill in pagination.items]
    except Exception as e:
        # Database table doesn't exist or other error - fall back to cached data
        bills = None
        pagination = None
    
    # Fallback to old method if database query failed or returned nothing
    if bills is None or (pagination and pagination.total == 0):
        data_fetcher = get_data_fetcher()
        bills = data_fetcher.fetch_bills()
        
        if not bills:
            bills = get_cached_bills()
        
        # Apply search and sort to fallback data
        if bills and search:
            search_lower = search.lower()
            bills = [b for b in bills if 
                    search_lower in str(b.get('number', '')).lower() or
                    search_lower in str(b.get('title', '')).lower() or
                    search_lower in str(b.get('description', '')).lower() or
                    search_lower in str(b.get('sponsor', '')).lower()]
        
        if bills and sort_by == 'title':
            bills = sorted(bills, key=lambda x: x.get('title', '') or '')
        elif bills and sort_by == 'updated':
            bills = sorted(bills, key=lambda x: x.get('last_action', ''), reverse=True)
        
        # Manual pagination for fallback
        total = len(bills) if bills else 0
        start = (page - 1) * per_page
        end = start + per_page
        bills_page = bills[start:end] if bills else []
        
        # Create a simple pagination object for fallback
        class SimplePagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
        
        pagination = SimplePagination(bills_page, page, per_page, total)
        # For fallback dicts, best effort annotate with counts if numbers exist
        bills = bills_page
        try:
            numbers = [b.get('number') or b.get('id') for b in bills if b]
            if numbers:
                counts = db.session.query(BillSupport.bill_number, BillSupport.value, func.count('*')) \
                    .filter(BillSupport.bill_number.in_(numbers)) \
                    .group_by(BillSupport.bill_number, BillSupport.value).all()
                counts_map = {}
                for num, val, cnt in counts:
                    counts_map.setdefault(num, {1: 0, -1: 0})
                    counts_map[num][val] = cnt
                for b in bills:
                    num = b.get('number') or b.get('id')
                    c = counts_map.get(num, {1: 0, -1: 0})
                    b['support_count'] = c.get(1, 0)
                    b['oppose_count'] = c.get(-1, 0)
        except Exception:
            pass
    
    return render_template('bills.html', 
                         bills=bills or [], 
                         pagination=pagination,
                         search=search,
                         sort_by=sort_by,
                         per_page=per_page)

@bills_bp.route('/bill/<bill_id>')
def bill_detail(bill_id):
    """Display details of a specific bill from database."""
    # Try to get bill from database first
    bill = Bill.query.filter_by(bill_number=bill_id).first()

    if bill:
        bill_dict = bill.to_dict()
    else:
        # Fallback to old method if not in database
        data_fetcher = get_data_fetcher()
        bills = data_fetcher.fetch_bills()

        if not bills:
            bills = get_cached_bills()

        bill_dict = next((b for b in bills if b.get('number') == bill_id or b.get('id') == bill_id), None) if bills else None

    # Enrich with official bill details (actions, PDFs, hearing status)
    if bill_dict:
        try:
            details = get_bill_details(bill_id)
            if details:
                # Merge details into the bill dict for the template
                bill_dict.update(details)
        except Exception:
            # Non-fatal if upstream site changes; continue with base info
            pass

    # Support/oppose counts for this bill (if in DB)
    support_count = 0
    oppose_count = 0
    user_vote = 0
    try:
        # bill_id is the bill_number key
        support_count = BillSupport.query.filter_by(bill_number=bill_id, value=1).count()
        oppose_count = BillSupport.query.filter_by(bill_number=bill_id, value=-1).count()
        if session.get('user_id'):
            uv = BillSupport.query.filter_by(bill_number=bill_id, user_id=session['user_id']).first()
            user_vote = uv.value if uv else 0
    except Exception:
        pass

    comments = get_comments_for_bill(bill_id) if bill_dict else []

    # Precompute comment support/not support counts and current user vote
    comment_vote_map = {}
    if comments:
        try:
            from models import CommentSupport
            comment_ids = [c.id for c in comments]
            # Counts grouped
            grouped = db.session.query(CommentSupport.comment_id, CommentSupport.value, func.count('*')) \
                .filter(CommentSupport.comment_id.in_(comment_ids)) \
                .group_by(CommentSupport.comment_id, CommentSupport.value).all()
            for cid, val, cnt in grouped:
                comment_vote_map.setdefault(cid, {1:0, -1:0})
                comment_vote_map[cid][val] = cnt
            user_map = {}
            if session.get('user_id'):
                user_votes = CommentSupport.query.filter_by(user_id=session['user_id']).filter(CommentSupport.comment_id.in_(comment_ids)).all()
                for uv in user_votes:
                    user_map[uv.comment_id] = uv.value
            # Attach lightweight attrs
            for c in comments:
                counts = comment_vote_map.get(c.id, {1:0, -1:0})
                c.support_count = counts.get(1,0)
                c.oppose_count = counts.get(-1,0)
                c.user_vote = user_map.get(c.id, 0)
        except Exception:
            pass

    # For run support: annotate each comment's user with running flag & support counts
    run_support_map = {}
    user_run_votes = set()
    candidate_ids = []
    for c in comments:
        if c.user and c.user.thinking_about_running:
            candidate_ids.append(c.user.id)
    if candidate_ids:
        try:
            # Counts grouped by candidate
            grouped = db.session.query(RunSupport.candidate_user_id, db.func.count('*')) \
                .filter(RunSupport.candidate_user_id.in_(candidate_ids)) \
                .group_by(RunSupport.candidate_user_id).all()
            run_support_map = {cid: cnt for cid, cnt in grouped}
            if session.get('user_id'):
                user_votes = RunSupport.query.filter_by(supporter_user_id=session['user_id']) \
                    .filter(RunSupport.candidate_user_id.in_(candidate_ids)).all()
                user_run_votes = {rv.candidate_user_id for rv in user_votes}
        except Exception:
            pass
    # Attach lightweight attrs
    for c in comments:
        if c.user and c.user.thinking_about_running:
            c.is_thinking_running = True
            c.run_support_count = run_support_map.get(c.user.id, 0)
            c.user_run_supported = c.user.id in user_run_votes
        else:
            c.is_thinking_running = False
            c.run_support_count = 0
            c.user_run_supported = False

    return render_template('bill_detail.html', bill=bill_dict, comments=comments,
                           bill_support_count=support_count, bill_oppose_count=oppose_count,
                           bill_user_vote=user_vote)

@bills_bp.route('/bill/<bill_id>/comment', methods=['POST'])
@login_required
def add_bill_comment(bill_id):
    """Add a comment to a bill."""
    # Sanitize and validate input
    content = sanitize_input(request.form.get('content', ''), 5000)
    
    # Validate comment content
    valid, error = validate_comment_content(content)
    if not valid:
        flash(error)
        return redirect(url_for('bills.bill_detail', bill_id=bill_id))
    
    try:
        add_comment(bill_id, session['user_id'], content)
        flash('Comment added successfully.')
    except Exception as e:
        flash('Error adding comment. Please try again.')
    
    return redirect(url_for('bills.bill_detail', bill_id=bill_id))

@bills_bp.route('/bill/<bill_id>/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_bill_comment(bill_id, comment_id):
    """Delete a comment. Regular users can delete their own; power users can delete any."""
    user = User.query.get(session['user_id'])
    if not user:
        flash('You must be logged in to delete comments.')
        return redirect(url_for('bills.bill_detail', bill_id=bill_id))
    try:
        if delete_comment(comment_id, user):
            flash('Comment deleted.')
        else:
            flash('You do not have permission to delete this comment.')
    except Exception:
        flash('Error deleting comment.')
    return redirect(url_for('bills.bill_detail', bill_id=bill_id))

@bills_bp.route('/bill/<bill_id>/comment/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_bill_comment(bill_id, comment_id):
    """Edit a comment content and save it so all users see the updated content."""
    # Sanitize and validate input
    new_content = sanitize_input(request.form.get('content', ''), 5000)
    valid, error = validate_comment_content(new_content)
    if not valid:
        flash(error)
        return redirect(url_for('bills.bill_detail', bill_id=bill_id))

    user = User.query.get(session['user_id'])
    if not user:
        flash('You must be logged in to edit comments.')
        return redirect(url_for('bills.bill_detail', bill_id=bill_id))
    try:
        if update_comment(comment_id, user, new_content):
            flash('Comment updated.')
        else:
            flash('You do not have permission to edit this comment.')
    except Exception:
        flash('Error updating comment.')
    return redirect(url_for('bills.bill_detail', bill_id=bill_id))


def _toggle_bill_vote(bill_id: str, desired: int):
    user_id = session['user_id']
    vote = BillSupport.query.filter_by(bill_number=bill_id, user_id=user_id).first()
    try:
        if vote and vote.value == desired:
            db.session.delete(vote)
        elif vote:
            vote.value = desired
        else:
            db.session.add(BillSupport(bill_number=bill_id, user_id=user_id, value=desired))
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Could not register your preference. Please try again.')
    return redirect(url_for('bills.bill_detail', bill_id=bill_id))


@bills_bp.route('/bill/<bill_id>/support', methods=['POST'])
@login_required
def support_bill(bill_id):
    return _toggle_bill_vote(bill_id, desired=1)


@bills_bp.route('/bill/<bill_id>/not_support', methods=['POST'])
@login_required
def not_support_bill(bill_id):
    return _toggle_bill_vote(bill_id, desired=-1)


def _toggle_comment_vote(comment_id: int, desired: int):
    user_id = session['user_id']
    comment = Comment.query.get_or_404(comment_id)
    vote = CommentSupport.query.filter_by(comment_id=comment_id, user_id=user_id).first()
    try:
        if vote and vote.value == desired:
            db.session.delete(vote)  # toggle off
        elif vote:
            vote.value = desired
        else:
            db.session.add(CommentSupport(comment_id=comment_id, user_id=user_id, value=desired))
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Could not register your preference. Please try again.')
    return redirect(url_for('bills.bill_detail', bill_id=comment.bill_id))


@bills_bp.route('/comment/<int:comment_id>/support', methods=['POST'])
@login_required
def support_comment(comment_id):
    """Mark a comment as supported by the current user (toggle)."""
    return _toggle_comment_vote(comment_id, desired=1)


@bills_bp.route('/comment/<int:comment_id>/not_support', methods=['POST'])
@login_required
def not_support_comment(comment_id):
    """Mark a comment as not supported by the current user (toggle)."""
    return _toggle_comment_vote(comment_id, desired=-1)


# Legacy endpoints kept for compatibility
@bills_bp.route('/comment/<int:comment_id>/up', methods=['POST'])
@login_required
def upvote_comment(comment_id):
    return _toggle_comment_vote(comment_id, desired=1)


@bills_bp.route('/comment/<int:comment_id>/down', methods=['POST'])
@login_required
def downvote_comment(comment_id):
    return _toggle_comment_vote(comment_id, desired=-1)