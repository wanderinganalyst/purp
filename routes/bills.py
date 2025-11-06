from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.bills import get_cached_bills, parse_bills_with_bs
from services.web_utils import fetch_remote_page
from services.comments import get_comments_for_bill, add_comment
from auth import login_required
from utils.validators import validate_comment_content, sanitize_input
from utils.data_fetcher import get_data_fetcher

bills_bp = Blueprint('bills', __name__)

@bills_bp.route('/bills')
def bills_list():
    """Display list of all bills."""
    # Use data fetcher - automatically handles production vs development
    data_fetcher = get_data_fetcher()
    bills = data_fetcher.fetch_bills()
    
    # If no bills from data fetcher, fall back to old method
    if not bills:
        bills = get_cached_bills()
        if not bills:
            html = fetch_remote_page('URL_TO_BILLS_PAGE')  # Replace with actual URL
            if html:
                bills = parse_bills_with_bs(html)
    
    return render_template('bills.html', bills=bills or [])

@bills_bp.route('/bill/<bill_id>')
def bill_detail(bill_id):
    """Display details of a specific bill."""
    # Use data fetcher - automatically handles production vs development
    data_fetcher = get_data_fetcher()
    bills = data_fetcher.fetch_bills()
    
    # If no bills from data fetcher, fall back to old method
    if not bills:
        bills = get_cached_bills()
        if not bills:
            html = fetch_remote_page('URL_TO_BILLS_PAGE')  # Replace with actual URL
            if html:
                bills = parse_bills_with_bs(html)
    
    # Match by 'number' field (new mock data) or 'id' field (old data)
    bill = next((b for b in bills if b.get('number') == bill_id or b.get('id') == bill_id), None) if bills else None
    comments = get_comments_for_bill(bill_id) if bill else []
    
    return render_template('bill_detail.html', bill=bill, comments=comments)

@bills_bp.route('/bill/<bill_id>/comment', methods=['POST'])
@login_required
def add_bill_comment(bill_id):
    """Add a comment to a bill."""
    # Sanitize and validate input
    content = sanitize_input(request.form.get('content', ''), 5000)
    
    # Validate bill_id format (should be alphanumeric with possible hyphens)
    if not bill_id or not bill_id.replace('-', '').replace('_', '').isalnum():
        flash('Invalid bill ID.')
        return redirect(url_for('bills.bills_list'))
    
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