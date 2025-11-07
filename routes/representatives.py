from flask import Blueprint, render_template, session, flash, redirect, url_for
from services.representatives import get_all_reps, get_rep_by_name, get_member_sponsorships
from services.web_utils import fetch_remote_page
from models import Representative, User, RunSupport
from services.bills import get_bills_by_sponsor

reps_bp = Blueprint('reps', __name__)

@reps_bp.route('/representatives')
def reps_list():
    """Display list of all representatives."""
    # Prefer database if populated
    db_reps = Representative.query.order_by(Representative.district).all()
    if db_reps:
        members = []
        for r in db_reps:
            name = r.name or ''
            members.append({
                'id': r.id,
                'name': name,
                'district': r.district,
                'party': r.party,
                'city': r.city,
                'sponsored_bills': get_bills_by_sponsor(name) if name else []
            })
    else:
        members = get_all_reps()
    return render_template('reps.html', members=members)

@reps_bp.route('/representative/<district>')
def rep_detail(district):
    """Display details of a specific representative from database if available, otherwise fallback."""
    # Normalize district to handle leading zeros or different formats
    raw = str(district)
    variants = [raw]
    stripped = raw.lstrip('0')
    if stripped and stripped not in variants:
        variants.append(stripped)
    padded = raw.zfill(3)
    if padded not in variants:
        variants.append(padded)

    # Prefer DB by district for stability (try variants)
    r = None
    for d in variants:
        r = Representative.query.filter_by(district=d).first()
        if r:
            break
    if r:
        name = r.name or ''
        # Pull official sponsored/co-sponsored lists from MemberDetails
        sc = get_member_sponsorships(r.district)
        
        # Get all bills to enrich with titles
        from models import Bill, Event, DraftBill
        from utils.data_fetcher import get_data_fetcher
        from datetime import datetime
        
        # Get events for this representative
        events = Event.query.filter_by(representative_id=r.id).filter(
            Event.event_date >= datetime.now()
        ).order_by(Event.event_date.asc()).all()
        
        # Get draft bills visible to current user
        draft_bills = []
        try:
            # Get user if logged in
            user_id = session.get('user_id')
            current_user = User.query.get(user_id) if user_id else None
            
            # Get all drafts for this rep and filter by visibility
            all_drafts = DraftBill.query.filter_by(representative_id=r.id).order_by(
                DraftBill.updated_at.desc()
            ).all()
            
            for draft in all_drafts:
                if draft.can_view(current_user):
                    draft_bills.append(draft)
        except Exception as e:
            # If there's any error, just don't show drafts
            print(f"Error loading draft bills: {e}")
            draft_bills = []
        
        # Try to get bills from database or cache
        all_bills = {}
        try:
            db_bills = Bill.query.all()
            if db_bills:
                all_bills = {bill.bill_number: bill.to_dict() for bill in db_bills}
        except:
            pass
        
        # Fallback to cached bills if database is empty
        if not all_bills:
            data_fetcher = get_data_fetcher()
            bills_list = data_fetcher.fetch_bills()
            if bills_list:
                all_bills = {b.get('number') or b.get('id'): b for b in bills_list}
        
        # Compose display lists with enriched data
        sponsored = []
        sponsored_with_status = []
        cosponsored = []
        if sc.get('sponsored'):
            for num in sc['sponsored']:
                bill_data = all_bills.get(num, {})
                sponsored.append({
                    'number': num,
                    'id': num,
                    'title': bill_data.get('title') or bill_data.get('description')
                })
                # Also create version with full status info for track record
                sponsored_with_status.append({
                    'number': num,
                    'id': num,
                    'title': bill_data.get('title') or bill_data.get('description'),
                    'status': bill_data.get('status'),
                    'last_action': bill_data.get('last_action')
                })
        if sc.get('cosponsored'):
            for num in sc['cosponsored']:
                bill_data = all_bills.get(num, {})
                cosponsored.append({
                    'number': num,
                    'id': num,
                    'title': bill_data.get('title') or bill_data.get('description')
                })

        rep = {
            'id': r.id,
            'name': name,
            'district': r.district,
            'party': r.party,
            'city': r.city,
            'phone': r.phone,
            'room': r.room,
            'sponsored_bills': sponsored,
            'sponsored_bills_with_status': sponsored_with_status,
            'cosponsored_bills': cosponsored,
            'events': events
        }
        # Attach candidate run support info if this representative is linked to user accounts (rep users or candidate placeholder)
        try:
            # Find users referencing this representative
            candidate_users = User.query.filter_by(representative_id=r.id).all()
            candidates_data = []
            viewer_id = session.get('user_id')
            viewer_supports = set()
            if viewer_id:
                viewer_supports = {rs.candidate_user_id for rs in RunSupport.query.filter_by(supporter_user_id=viewer_id).all()}
            if candidate_users:
                from sqlalchemy import func
                ids = [u.id for u in candidate_users if u.thinking_about_running]
                counts_map = {}
                if ids:
                    grouped = RunSupport.query.with_entities(RunSupport.candidate_user_id, func.count('*')) \
                        .filter(RunSupport.candidate_user_id.in_(ids)).group_by(RunSupport.candidate_user_id).all()
                    counts_map = {cid: cnt for cid, cnt in grouped}
                for u in candidate_users:
                    if u.thinking_about_running:
                        candidates_data.append({
                            'id': u.id,
                            'username': u.username,
                            'run_support_count': counts_map.get(u.id, 0),
                            'user_supported': u.id in viewer_supports,
                            'is_self': viewer_id == u.id
                        })
            rep['candidate_users'] = candidates_data
        except Exception:
            rep['candidate_users'] = []
        return render_template('rep_detail.html', rep=rep, draft_bills=draft_bills)

    # Fallback: Try to find in scraped data by district (with normalization)
    from services.representatives import get_all_reps
    all_reps = get_all_reps()
    
    if all_reps:
        # Try to find by district match across variants
        for member in all_reps:
            md = str(member.get('district', '')).strip()
            md_strip = md.lstrip('0')
            md_pad = md.zfill(3)
            if md in variants or md_strip in variants or md_pad in variants:
                return render_template('rep_detail.html', rep=member)
    
    # Last fallback: try by name (for backward compatibility)
    rep = get_rep_by_name(district)
    if not rep:
        flash('Representative not found.')
        return redirect(url_for('reps.reps_list'))
    return render_template('rep_detail.html', rep=rep)