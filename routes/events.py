from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import User, Event, Representative, EventTemplate, EventOption, EventPurchase, EventInvitation, EventRSVP, EventCart, EventCartItem
from extensions import db
from auth import login_required
from utils.validators import sanitize_input
from datetime import datetime

events_bp = Blueprint('events', __name__)

def rep_required(f):
    """Decorator to require rep, rep_staffer, candidate, or admin role."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = User.query.get(session.get('user_id'))
        if not user or user.role not in ['rep', 'rep_staffer', 'candidate', 'admin']:
            flash('You must be a representative, candidate, rep staffer, or administrator to access this page.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@events_bp.route('/rep/events')
@login_required
@rep_required
def manage_events():
    """View all events for the logged-in representative or all events for admins."""
    user = User.query.get(session['user_id'])
    
    if user.role == 'admin':
        # Admins can see all events
        events = Event.query.order_by(Event.event_date.desc()).all()
        rep = None
    else:
        # Reps and rep_staffers see events for their representative
        if not user.representative_id:
            flash('Your account is not linked to a representative profile.')
            return redirect(url_for('index'))
        
        rep = Representative.query.get(user.representative_id)
        events = Event.query.filter_by(representative_id=rep.id).order_by(Event.event_date.desc()).all()
    
    return render_template('events/manage.html', events=events, rep=rep, user=user)

@events_bp.route('/rep/events/create', methods=['GET', 'POST'])
@login_required
@rep_required
def create_event():
    """Create a new event."""
    user = User.query.get(session['user_id'])
    
    # Non-admins must be linked to a representative profile
    if user.role != 'admin' and not user.representative_id:
        flash('Your account is not linked to a representative profile.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = sanitize_input(request.form.get('title', ''), 255)
        description = sanitize_input(request.form.get('description', ''), 5000)
        location = sanitize_input(request.form.get('location', ''), 255)
        street_address = sanitize_input(request.form.get('street_address', ''), 255)
        city = sanitize_input(request.form.get('city', ''), 100)
        state = sanitize_input(request.form.get('state', ''), 2).upper()
        zipcode = sanitize_input(request.form.get('zipcode', ''), 10)
        event_type = sanitize_input(request.form.get('event_type', ''), 50)
        event_date_str = request.form.get('event_date', '')
        event_time = sanitize_input(request.form.get('event_time', ''), 20)
        template_id = request.form.get('template_id', None)
        
        # Determine representative_id
        if user.role == 'admin':
            rep_id_raw = request.form.get('representative_id')
            try:
                representative_id = int(rep_id_raw)
                # Validate rep exists
                if not Representative.query.get(representative_id):
                    raise ValueError('Invalid representative')
            except Exception:
                flash('Please select a valid representative for this event.')
                return redirect(url_for('events.create_event'))
        else:
            representative_id = user.representative_id
        
        # Convert empty template_id to None
        if template_id:
            try:
                template_id = int(template_id)
            except:
                template_id = None
        
        # Validate required fields
        if not title or len(title.strip()) < 3:
            flash('Event title must be at least 3 characters.')
            return redirect(url_for('events.create_event'))
        
        # Parse date
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format.')
            return redirect(url_for('events.create_event'))
        
        # Create event
        try:
            event = Event(
                representative_id=representative_id,
                title=title,
                description=description,
                location=location,
                street_address=street_address if street_address else None,
                city=city if city else None,
                state=state if state else None,
                zipcode=zipcode if zipcode else None,
                event_type=event_type,
                event_date=event_date,
                event_time=event_time if event_time else None,
                template_id=template_id
            )
            db.session.add(event)
            db.session.commit()
            flash('Event created successfully!')
            return redirect(url_for('events.manage_events'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating event. Please try again.')
            return redirect(url_for('events.create_event'))
    
    templates = EventTemplate.query.all()
    representatives = []
    if user.role == 'admin':
        representatives = Representative.query.order_by(Representative.district).all()
    return render_template('events/create.html', templates=templates, user=user, representatives=representatives)

@events_bp.route('/rep/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
@rep_required
def edit_event(event_id):
    """Edit an existing event."""
    user = User.query.get(session['user_id'])
    event = Event.query.get_or_404(event_id)
    
    # Ensure user owns this event (admins, reps, and rep_staffers for their rep's events)
    if user.role == 'admin':
        pass  # Admins can edit any event
    elif event.representative_id != user.representative_id:
        flash('You do not have permission to edit this event.')
        return redirect(url_for('events.manage_events'))
    
    if request.method == 'POST':
        title = sanitize_input(request.form.get('title', ''), 255)
        description = sanitize_input(request.form.get('description', ''), 5000)
        location = sanitize_input(request.form.get('location', ''), 255)
        street_address = sanitize_input(request.form.get('street_address', ''), 255)
        city = sanitize_input(request.form.get('city', ''), 100)
        state = sanitize_input(request.form.get('state', ''), 2).upper()
        zipcode = sanitize_input(request.form.get('zipcode', ''), 10)
        event_type = sanitize_input(request.form.get('event_type', ''), 50)
        event_date_str = request.form.get('event_date', '')
        event_time = sanitize_input(request.form.get('event_time', ''), 20)
        
        # Validate
        if not title or len(title.strip()) < 3:
            flash('Event title must be at least 3 characters.')
            return redirect(url_for('events.edit_event', event_id=event_id))
        
        if not event_date_str:
            flash('Event date is required.')
            return redirect(url_for('events.edit_event', event_id=event_id))
        
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format.')
            return redirect(url_for('events.edit_event', event_id=event_id))
        
        # Update event
        try:
            event.title = title
            event.description = description
            event.location = location
            event.street_address = street_address if street_address else None
            event.city = city if city else None
            event.state = state if state else None
            event.zipcode = zipcode if zipcode else None
            event.event_type = event_type
            event.event_date = event_date
            event.event_time = event_time if event_time else None
            db.session.commit()
            flash('Event updated successfully!')
            return redirect(url_for('events.manage_events'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating event. Please try again.')
            return redirect(url_for('events.edit_event', event_id=event_id))
    
    return render_template('events/edit.html', event=event)

@events_bp.route('/rep/events/<int:event_id>/delete', methods=['POST'])
@login_required
@rep_required
def delete_event(event_id):
    """Delete an event."""
    user = User.query.get(session['user_id'])
    event = Event.query.get_or_404(event_id)
    
    # Ensure user owns this event (admins, reps, and rep_staffers for their rep's events)
    if user.role == 'admin':
        pass  # Admins can delete any event
    elif event.representative_id != user.representative_id:
        flash('You do not have permission to delete this event.')
        return redirect(url_for('events.manage_events'))
    
    try:
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting event. Please try again.')
    
    return redirect(url_for('events.manage_events'))


# Template Management Routes
@events_bp.route('/rep/templates')
@login_required
@rep_required
def manage_templates():
    """View all event templates."""
    templates = EventTemplate.query.all()
    return render_template('events/templates.html', templates=templates)


@events_bp.route('/rep/templates/create', methods=['GET', 'POST'])
@login_required
@rep_required
def create_template():
    """Create a new event template."""
    if request.method == 'POST':
        name = sanitize_input(request.form.get('name', ''), 100)
        description = sanitize_input(request.form.get('description', ''), 500)
        
        if not name or len(name) < 3:
            flash('Template name must be at least 3 characters.')
            return redirect(url_for('events.create_template'))
        
        try:
            template = EventTemplate(name=name, description=description)
            db.session.add(template)
            db.session.commit()
            flash(f'Template "{name}" created successfully!')
            return redirect(url_for('events.edit_template_options', template_id=template.id))
        except Exception as e:
            db.session.rollback()
            flash('Error creating template. Template name may already exist.')
    
    return render_template('events/create_template.html')


@events_bp.route('/rep/templates/<int:template_id>/options', methods=['GET', 'POST'])
@login_required
@rep_required
def edit_template_options(template_id):
    """Edit options for a template."""
    template = EventTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        option_name = sanitize_input(request.form.get('option_name', ''), 100)
        option_type = sanitize_input(request.form.get('option_type', ''), 50)
        price = request.form.get('price', 0)
        description = sanitize_input(request.form.get('description', ''), 255)
        
        try:
            price = float(price)
            if price < 0:
                price = 0
        except:
            price = 0.0
        
        if option_name and option_type:
            try:
                option = EventOption(
                    template_id=template.id,
                    option_name=option_name,
                    option_type=option_type,
                    price=price,
                    description=description
                )
                db.session.add(option)
                db.session.commit()
                flash(f'Option "{option_name}" added successfully!')
            except Exception as e:
                db.session.rollback()
                flash('Error adding option. Please try again.')
        
        return redirect(url_for('events.edit_template_options', template_id=template_id))
    
    options = EventOption.query.filter_by(template_id=template.id).all()
    return render_template('events/edit_template_options.html', template=template, options=options)


@events_bp.route('/rep/templates/<int:template_id>/options/<int:option_id>/delete', methods=['POST'])
@login_required
@rep_required
def delete_option(template_id, option_id):
    """Delete an option from a template."""
    option = EventOption.query.get_or_404(option_id)
    
    if option.template_id != template_id:
        flash('Invalid option.')
        return redirect(url_for('events.manage_templates'))
    
    try:
        db.session.delete(option)
        db.session.commit()
        flash('Option deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting option.')
    
    return redirect(url_for('events.edit_template_options', template_id=template_id))


# Public Event Purchase Routes
@events_bp.route('/event/<int:event_id>')
def view_event(event_id):
    """View event details and purchase options."""
    event = Event.query.get_or_404(event_id)
    options = []
    user_rsvp = None
    cart_count = 0
    
    if event.template_id:
        options = EventOption.query.filter_by(template_id=event.template_id, is_active=True).all()
    
    # Get user RSVP if logged in
    if 'user_id' in session:
        user_id = session['user_id']
        user_rsvp = EventRSVP.query.filter_by(event_id=event_id, user_id=user_id).first()
        
        # Get cart count
        cart = EventCart.query.filter_by(event_id=event_id, user_id=user_id).first()
        if cart:
            cart_count = sum(item.quantity for item in cart.items.all())
    
    return render_template('events/view.html', event=event, options=options, user_rsvp=user_rsvp, cart_count=cart_count)


@events_bp.route('/event/<int:event_id>/purchase', methods=['POST'])
@login_required
def purchase_event_options(event_id):
    """Purchase event options."""
    event = Event.query.get_or_404(event_id)
    user_id = session.get('user_id')
    
    if not event.template_id:
        flash('This event does not have purchasable options.')
        return redirect(url_for('events.view_event', event_id=event_id))
    
    # Get selected options from form
    purchases = []
    total_amount = 0
    
    for key, value in request.form.items():
        if key.startswith('option_') and value:
            try:
                option_id = int(key.split('_')[1])
                quantity = int(value)
                
                if quantity > 0:
                    option = EventOption.query.get(option_id)
                    if option and option.template_id == event.template_id and option.is_active:
                        purchase = EventPurchase(
                            event_id=event.id,
                            user_id=user_id,
                            option_id=option.id,
                            quantity=quantity,
                            price_paid=option.price * quantity
                        )
                        purchases.append(purchase)
                        total_amount += option.price * quantity
            except:
                continue
    
    if purchases:
        try:
            db.session.add_all(purchases)
            db.session.commit()
            flash(f'Purchase successful! Total: ${total_amount:.2f}')
        except Exception as e:
            db.session.rollback()
            flash('Error processing purchase. Please try again.')
    else:
        flash('No items selected for purchase.')
    
    return redirect(url_for('events.view_event', event_id=event_id))


# Event Invitation Routes
@events_bp.route('/rep/events/<int:event_id>/invitations', methods=['GET', 'POST'])
@login_required
@rep_required
def manage_invitations(event_id):
    """Invite constituents to an event."""
    user = User.query.get(session['user_id'])
    event = Event.query.get_or_404(event_id)
    
    # Ensure user owns this event (admins may manage any event)
    if user.role != 'admin' and event.representative_id != user.representative_id:
        flash('You do not have permission to manage invitations for this event.')
        return redirect(url_for('events.manage_events'))
    
    # Use event representative for context (admins may not have a rep)
    rep = Representative.query.get(event.representative_id)
    
    if request.method == 'POST':
        # Get list of user IDs to invite
        user_ids = request.form.getlist('user_ids')
        message = sanitize_input(request.form.get('message', ''), 1000)
        
        invited_count = 0
        for uid in user_ids:
            try:
                uid = int(uid)
                # Check if already invited
                existing = EventInvitation.query.filter_by(event_id=event.id, user_id=uid).first()
                if not existing:
                    invitation = EventInvitation(
                        event_id=event.id,
                        user_id=uid,
                        message=message if message else None
                    )
                    db.session.add(invitation)
                    invited_count += 1
            except:
                continue
        
        if invited_count > 0:
            db.session.commit()
            flash(f'Invited {invited_count} constituent(s) to the event!')
        else:
            flash('No new invitations sent.')
        
        return redirect(url_for('events.manage_invitations', event_id=event_id))
    
    # Get constituents for this rep (users in their district)
    constituents = User.query.filter(
        db.or_(
            User.senator_district == rep.district,
            User.representative_district == rep.district
        )
    ).all()
    
    # Get already invited users
    invited_user_ids = [inv.user_id for inv in event.invitations.all()]
    
    # Get RSVP counts
    rsvp_counts = {
        'attending': event.rsvps.filter_by(status='attending').count(),
        'not_attending': event.rsvps.filter_by(status='not_attending').count(),
        'maybe': event.rsvps.filter_by(status='maybe').count()
    }
    
    return render_template('events/invitations.html', 
                         event=event, 
                         rep=rep,
                         constituents=constituents,
                         invited_user_ids=invited_user_ids,
                         rsvp_counts=rsvp_counts)


@events_bp.route('/my-invitations')
@login_required
def my_invitations():
    """View all event invitations for the logged-in user."""
    user_id = session.get('user_id')
    invitations = EventInvitation.query.filter_by(user_id=user_id).order_by(EventInvitation.invited_at.desc()).all()
    
    # Enrich with RSVP status
    invitation_data = []
    for inv in invitations:
        rsvp = EventRSVP.query.filter_by(event_id=inv.event_id, user_id=user_id).first()
        invitation_data.append({
            'invitation': inv,
            'event': inv.event,
            'rsvp': rsvp
        })
    
    return render_template('events/my_invitations.html', invitations=invitation_data)


@events_bp.route('/event/<int:event_id>/rsvp', methods=['POST'])
@login_required
def rsvp_event(event_id):
    """RSVP to an event."""
    event = Event.query.get_or_404(event_id)
    user_id = session.get('user_id')
    status = request.form.get('status', 'attending')
    
    if status not in ['attending', 'not_attending', 'maybe']:
        flash('Invalid RSVP status.')
        return redirect(url_for('events.view_event', event_id=event_id))
    
    # Check if RSVP already exists
    rsvp = EventRSVP.query.filter_by(event_id=event_id, user_id=user_id).first()
    
    if rsvp:
        rsvp.status = status
        rsvp.updated_at = datetime.now()
    else:
        rsvp = EventRSVP(
            event_id=event_id,
            user_id=user_id,
            status=status
        )
        db.session.add(rsvp)
    
    try:
        db.session.commit()
        if status == 'attending':
            flash('Great! You\'re attending this event.')
        elif status == 'not_attending':
            flash('Your RSVP has been updated to not attending.')
        else:
            flash('Your RSVP has been updated to maybe.')
    except Exception as e:
        db.session.rollback()
        flash('Error updating RSVP. Please try again.')
    
    return redirect(url_for('events.view_event', event_id=event_id))


# Shopping Cart Routes
@events_bp.route('/event/<int:event_id>/cart/add', methods=['POST'])
@login_required
def add_to_cart(event_id):
    """Add an item to the event shopping cart."""
    event = Event.query.get_or_404(event_id)
    user_id = session.get('user_id')
    option_id = request.form.get('option_id')
    quantity = request.form.get('quantity', 1)
    
    try:
        option_id = int(option_id)
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except:
        flash('Invalid item or quantity.')
        return redirect(url_for('events.view_event', event_id=event_id))
    
    # Verify option belongs to this event's template
    option = EventOption.query.get(option_id)
    if not option or option.template_id != event.template_id:
        flash('Invalid item.')
        return redirect(url_for('events.view_event', event_id=event_id))
    
    # Get or create cart
    cart = EventCart.query.filter_by(event_id=event_id, user_id=user_id).first()
    if not cart:
        cart = EventCart(event_id=event_id, user_id=user_id)
        db.session.add(cart)
        db.session.flush()
    
    # Check if item already in cart
    cart_item = EventCartItem.query.filter_by(cart_id=cart.id, option_id=option_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = EventCartItem(cart_id=cart.id, option_id=option_id, quantity=quantity)
        db.session.add(cart_item)
    
    try:
        db.session.commit()
        flash(f'Added {quantity}x {option.option_name} to your cart!')
    except Exception as e:
        db.session.rollback()
        flash('Error adding item to cart.')
    
    return redirect(url_for('events.view_event', event_id=event_id))


@events_bp.route('/event/<int:event_id>/cart')
@login_required
def view_cart(event_id):
    """View shopping cart for an event."""
    event = Event.query.get_or_404(event_id)
    user_id = session.get('user_id')
    
    cart = EventCart.query.filter_by(event_id=event_id, user_id=user_id).first()
    
    cart_items = []
    total = 0
    
    if cart:
        for item in cart.items.all():
            subtotal = item.option.price * item.quantity
            cart_items.append({
                'item': item,
                'option': item.option,
                'subtotal': subtotal
            })
            total += subtotal
    
    return render_template('events/cart.html', event=event, cart=cart, cart_items=cart_items, total=total)


@events_bp.route('/event/<int:event_id>/cart/update', methods=['POST'])
@login_required
def update_cart(event_id):
    """Update cart item quantities."""
    user_id = session.get('user_id')
    cart = EventCart.query.filter_by(event_id=event_id, user_id=user_id).first()
    
    if not cart:
        flash('No cart found.')
        return redirect(url_for('events.view_event', event_id=event_id))
    
    for key, value in request.form.items():
        if key.startswith('quantity_'):
            try:
                item_id = int(key.split('_')[1])
                quantity = int(value)
                
                item = EventCartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
                if item:
                    if quantity > 0:
                        item.quantity = quantity
                    else:
                        db.session.delete(item)
            except:
                continue
    
    try:
        db.session.commit()
        flash('Cart updated!')
    except Exception as e:
        db.session.rollback()
        flash('Error updating cart.')
    
    return redirect(url_for('events.view_cart', event_id=event_id))


@events_bp.route('/event/<int:event_id>/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(event_id, item_id):
    """Remove an item from the cart."""
    user_id = session.get('user_id')
    cart = EventCart.query.filter_by(event_id=event_id, user_id=user_id).first()
    
    if cart:
        item = EventCartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            flash('Item removed from cart.')
    
    return redirect(url_for('events.view_cart', event_id=event_id))


@events_bp.route('/event/<int:event_id>/cart/checkout', methods=['POST'])
@login_required
def checkout_cart(event_id):
    """Checkout and complete purchase from cart."""
    user_id = session.get('user_id')
    cart = EventCart.query.filter_by(event_id=event_id, user_id=user_id).first()
    
    if not cart or cart.items.count() == 0:
        flash('Your cart is empty.')
        return redirect(url_for('events.view_event', event_id=event_id))
    
    # Create purchases from cart items
    purchases = []
    total_amount = 0
    
    for item in cart.items.all():
        purchase = EventPurchase(
            event_id=event_id,
            user_id=user_id,
            option_id=item.option_id,
            quantity=item.quantity,
            price_paid=item.option.price * item.quantity
        )
        purchases.append(purchase)
        total_amount += purchase.price_paid
    
    try:
        # Add purchases
        db.session.add_all(purchases)
        # Clear cart
        for item in cart.items.all():
            db.session.delete(item)
        db.session.delete(cart)
        db.session.commit()
        flash(f'Purchase successful! Total: ${total_amount:.2f}')
        return redirect(url_for('events.view_event', event_id=event_id))
    except Exception as e:
        db.session.rollback()
        flash('Error processing checkout. Please try again.')
        return redirect(url_for('events.view_cart', event_id=event_id))


# Rep Staffer Management Routes
@events_bp.route('/rep/staffers', methods=['GET', 'POST'])
@login_required
def manage_staffers():
    """Manage rep staffers (reps and admins only)."""
    user = User.query.get(session['user_id'])
    
    # Only reps and admins can manage staffers
    if user.role not in ['rep', 'candidate', 'admin']:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    if user.role in ['rep', 'candidate'] and not user.representative_id:
        flash('Your account is not linked to a representative profile.')
        return redirect(url_for('index'))
    
    # Get representative
    if user.role == 'admin':
        # For now, admins manage staffers for all reps (could be enhanced later)
        staffers = User.query.filter_by(role='rep_staffer').all()
        rep = None
    else:
        rep = Representative.query.get(user.representative_id)
        # Get all staffers for this rep
        staffers = User.query.filter_by(role='rep_staffer', representative_id=user.representative_id).all()
    
    if request.method == 'POST':
        # Get form data
        staffer_username = sanitize_input(request.form.get('username', ''), 150)
        staffer_password = request.form.get('password', '')
        street_address = sanitize_input(request.form.get('street_address', ''), 255)
        city = sanitize_input(request.form.get('city', ''), 100)
        state = sanitize_input(request.form.get('state', ''), 2).upper()
        zipcode = sanitize_input(request.form.get('zipcode', ''), 10)
        
        # Validate
        if not staffer_username or len(staffer_username) < 3:
            flash('Username must be at least 3 characters.')
            return redirect(url_for('events.manage_staffers'))
        
        if not staffer_password or len(staffer_password) < 10:
            flash('Password must be at least 10 characters.')
            return redirect(url_for('events.manage_staffers'))
        
        # Check if username exists
        if User.query.filter_by(username=staffer_username).first():
            flash('Username already exists.')
            return redirect(url_for('events.manage_staffers'))
        
        # Create staffer
        try:
            staffer = User(
                username=staffer_username,
                role='rep_staffer',
                representative_id=user.representative_id if user.role in ['rep', 'candidate'] else None,
                street_address=street_address,
                city=city,
                state=state,
                zipcode=zipcode
            )
            staffer.set_password(staffer_password)
            db.session.add(staffer)
            db.session.commit()
            flash(f'Staffer "{staffer_username}" created successfully!')
            return redirect(url_for('events.manage_staffers'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating staffer. Please try again.')
    
    return render_template('events/staffers.html', staffers=staffers, rep=rep, user=user)


@events_bp.route('/rep/staffers/<int:staffer_id>/delete', methods=['POST'])
@login_required
def delete_staffer(staffer_id):
    """Delete a rep staffer."""
    user = User.query.get(session['user_id'])
    
    # Only reps, candidates, and admins can delete staffers
    if user.role not in ['rep', 'candidate', 'admin']:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    staffer = User.query.get_or_404(staffer_id)
    
    # Verify staffer belongs to this rep/candidate (unless admin)
    if user.role in ['rep', 'candidate'] and staffer.representative_id != user.representative_id:
        flash('You do not have permission to delete this staffer.')
        return redirect(url_for('events.manage_staffers'))
    
    if staffer.role != 'rep_staffer':
        flash('This user is not a rep staffer.')
        return redirect(url_for('events.manage_staffers'))
    
    try:
        db.session.delete(staffer)
        db.session.commit()
        flash('Staffer deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting staffer.')
    
    return redirect(url_for('events.manage_staffers'))
