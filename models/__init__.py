"""
Models package for database models.
"""
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from models.document_verification import DocumentVerification

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)  # Nullable for existing users
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='regular')  # regular, power, rep, staffer
    
    # Email verification fields
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)
    
    # For rep users: link to their Representative record
    representative_id = db.Column(db.Integer, db.ForeignKey('representatives.id'), nullable=True)
    
    # For staffer users: link to the representative they work for
    rep_boss_id = db.Column(db.Integer, db.ForeignKey('representatives.id'), nullable=True)
    
    # Address fields
    street_address = db.Column(db.String(255), nullable=False)
    apt_unit = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    zipcode = db.Column(db.String(10), nullable=False)
    address_verified = db.Column(db.Boolean, nullable=False, default=False)
    
    # Representative information (for regular users)
    senator_name = db.Column(db.String(255), nullable=True)
    senator_district = db.Column(db.String(10), nullable=True)
    senator_party = db.Column(db.String(50), nullable=True)
    representative_name = db.Column(db.String(255), nullable=True)
    representative_district = db.Column(db.String(10), nullable=True)
    representative_party = db.Column(db.String(50), nullable=True)
    reps_last_updated = db.Column(db.DateTime, nullable=True)
    
    # Profile fields
    bio = db.Column(db.Text, nullable=True)
    thinking_about_running = db.Column(db.Boolean, nullable=False, default=False)
    
    # Relationship to Representative (for rep users)
    rep_profile = db.relationship('Representative', backref='user_account', foreign_keys=[representative_id])
    
    # Relationship to Representative (for staffer users)
    rep_boss = db.relationship('Representative', backref='staffers', foreign_keys=[rep_boss_id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_representatives(self, rep_info):
        """Update representative information from lookup result."""
        from datetime import datetime
        
        if not rep_info:
            return False
        
        # Update senator info (support legacy and new keys)
        senator_block = rep_info.get('state_senator') or rep_info.get('senator')
        if senator_block:
            senator = senator_block
            self.senator_name = senator.get('name')
            self.senator_district = senator.get('district')
            self.senator_party = senator.get('party')
        
        # Update representative info (support legacy and new keys)
        representative_block = rep_info.get('state_representative') or rep_info.get('representative')
        if representative_block:
            rep = representative_block
            self.representative_name = rep.get('name')
            self.representative_district = rep.get('district')
            self.representative_party = rep.get('party')
        
        self.reps_last_updated = datetime.utcnow()
        return True
    
    def get_representatives_display(self):
        """Get formatted representative information for display."""
        result = {'has_data': False}
        
        if self.senator_name or self.representative_name:
            result['has_data'] = True
        
        if self.senator_name:
            result['senator'] = {
                'name': self.senator_name,
                'district': self.senator_district or 'N/A',
                'party': self.senator_party or 'N/A',
                'display': f"{self.senator_name} ({self.senator_party or 'N/A'}-{self.senator_district or 'N/A'})"
            }
        else:
            result['senator'] = None
        
        if self.representative_name:
            result['representative'] = {
                'name': self.representative_name,
                'district': self.representative_district or 'N/A',
                'party': self.representative_party or 'N/A',
                'display': f"{self.representative_name} ({self.representative_party or 'N/A'}-{self.representative_district or 'N/A'})"
            }
        else:
            result['representative'] = None
        
        return result

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Bill(db.Model):
    __tablename__ = 'bills'
    id = db.Column(db.Integer, primary_key=True)
    bill_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    sponsor = db.Column(db.String(255), nullable=True)
    title = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=True, default='Active')
    last_action = db.Column(db.String(255), nullable=True)
    
    # Full bill text for LLM processing
    full_text = db.Column(db.Text, nullable=True)
    text_pdf_url = db.Column(db.String(500), nullable=True)
    summary_pdf_url = db.Column(db.String(500), nullable=True)
    text_fetched_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        """Convert bill to dictionary for template rendering."""
        return {
            'id': self.bill_number,
            'number': self.bill_number,
            'sponsor': self.sponsor,
            'title': self.title or self.description,
            'description': self.description,
            'status': self.status,
            'last_action': self.last_action,
            'support_count': getattr(self, 'support_count', None),
            'oppose_count': getattr(self, 'oppose_count', None),
            'score': (getattr(self, 'support_count', 0) or 0) - (getattr(self, 'oppose_count', 0) or 0),
            'has_full_text': bool(self.full_text),
            'text_pdf_url': self.text_pdf_url,
            'summary_pdf_url': self.summary_pdf_url,
        }
    
    def get_llm_context(self, max_length=None):
        """Get bill text formatted for LLM processing.
        
        Args:
            max_length: Optional max characters to return (for context length limits)
            
        Returns:
            Formatted string with bill metadata and full text
        """
        context = f"""Bill: {self.bill_number}
Title: {self.title or 'No title'}
Sponsor: {self.sponsor or 'Unknown'}
Status: {self.status or 'Unknown'}
Last Action: {self.last_action or 'None'}

"""
        if self.description:
            context += f"Description:\n{self.description}\n\n"
        
        if self.full_text:
            context += f"Full Bill Text:\n{self.full_text}\n"
        else:
            context += "Full Bill Text: Not yet fetched\n"
        
        if max_length and len(context) > max_length:
            context = context[:max_length] + "\n... [truncated]"
        
        return context

    def __repr__(self):
        return f"<Bill {self.bill_number}>"


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_hidden = db.Column(db.Boolean, nullable=False, server_default='0')
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))

    def __repr__(self):
        return f"<Comment {self.id} bill={self.bill_id} user={self.user_id}>"

    @property
    def up_votes(self):
        return sum(1 for v in self.votes if v.value == 1)

    @property
    def down_votes(self):
        return sum(1 for v in self.votes if v.value == -1)

    @property
    def score(self):
        return self.up_votes - self.down_votes


class CommentSupport(db.Model):
    __tablename__ = 'comment_supports'
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    value = db.Column(db.Integer, nullable=False)  # +1 = up, -1 = down
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    comment = db.relationship('Comment', backref=db.backref('votes', lazy='dynamic', cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('comment_votes', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('comment_id', 'user_id', name='uq_comment_user_vote'),
    )

    def __repr__(self):
        return f"<CommentSupport comment={self.comment_id} user={self.user_id} value={self.value}>"


class BillSupport(db.Model):
    __tablename__ = 'bill_supports'
    id = db.Column(db.Integer, primary_key=True)
    bill_number = db.Column(db.String(20), db.ForeignKey('bills.bill_number'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    value = db.Column(db.Integer, nullable=False)  # +1 support, -1 not support
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    bill = db.relationship('Bill', backref=db.backref('votes', lazy='dynamic', cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('bill_votes', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('bill_number', 'user_id', name='uq_bill_user_vote'),
    )

    def __repr__(self):
        return f"<BillSupport bill={self.bill_number} user={self.user_id} value={self.value}>"


class RunSupport(db.Model):
    __tablename__ = 'run_supports'
    id = db.Column(db.Integer, primary_key=True)
    candidate_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    supporter_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    candidate = db.relationship('User', foreign_keys=[candidate_user_id], backref=db.backref('run_supporters', lazy='dynamic', cascade="all, delete-orphan"))
    supporter = db.relationship('User', foreign_keys=[supporter_user_id])

    __table_args__ = (
        db.UniqueConstraint('candidate_user_id', 'supporter_user_id', name='uq_candidate_supporter'),
    )

    def __repr__(self):
        return f"<RunSupport candidate={self.candidate_user_id} supporter={self.supporter_user_id}>"


class Representative(db.Model):
    __tablename__ = 'representatives'
    id = db.Column(db.Integer, primary_key=True)
    district = db.Column(db.String(10), unique=True, index=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    party = db.Column(db.String(10), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    room = db.Column(db.String(50), nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    profile_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    @property
    def name(self):
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts) if parts else None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'district': self.district,
            'party': self.party,
            'city': self.city,
            'phone': self.phone,
            'room': self.room,
            'photo_url': self.photo_url,
            'profile_url': self.profile_url
        }

    def __repr__(self):
        return f"<Representative {self.district} {self.name}>"


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_rep_name = db.Column(db.String(255), nullable=False)
    recipient_rep_district = db.Column(db.String(10), nullable=False)
    recipient_type = db.Column(db.String(20), nullable=False)  # 'representative' or 'senator'
    subject = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, server_default=db.func.now())
    read_at = db.Column(db.DateTime, nullable=True)
    
    sender = db.relationship('User', backref=db.backref('messages', lazy='dynamic'))
    
    def __repr__(self):
        return f"<Message {self.id} from User {self.sender_id} to {self.recipient_rep_name}>"


class EventTemplate(db.Model):
    __tablename__ = 'event_templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    def __repr__(self):
        return f"<EventTemplate {self.id}: {self.name}>"


class EventOption(db.Model):
    __tablename__ = 'event_options'
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('event_templates.id'), nullable=False)
    option_name = db.Column(db.String(100), nullable=False)  # e.g., 'seats', 'flags', 'meal'
    option_type = db.Column(db.String(50), nullable=False)  # 'merchandise', 'seating', 'food', 'transportation'
    price = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    template = db.relationship('EventTemplate', backref=db.backref('options', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f"<EventOption {self.id}: {self.option_name} (${self.price})>"


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    representative_id = db.Column(db.Integer, db.ForeignKey('representatives.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('event_templates.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.DateTime, nullable=False)
    event_time = db.Column(db.String(20), nullable=True)  # Optional separate time field
    location = db.Column(db.String(255), nullable=True)  # General location description
    street_address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(2), nullable=True)
    zipcode = db.Column(db.String(10), nullable=True)
    event_type = db.Column(db.String(50), nullable=True)  # 'town_hall', 'meeting', 'fundraiser', etc.
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    representative = db.relationship('Representative', backref=db.backref('events', lazy='dynamic', order_by='Event.event_date'))
    template = db.relationship('EventTemplate', backref=db.backref('events', lazy='dynamic'))
    
    def __repr__(self):
        return f"<Event {self.id}: {self.title}>"


class EventPurchase(db.Model):
    __tablename__ = 'event_purchases'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('event_options.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_paid = db.Column(db.Float, nullable=False)
    purchased_at = db.Column(db.DateTime, server_default=db.func.now())
    
    event = db.relationship('Event', backref=db.backref('purchases', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('event_purchases', lazy='dynamic'))
    option = db.relationship('EventOption', backref=db.backref('purchases', lazy='dynamic'))
    
    def __repr__(self):
        return f"<EventPurchase {self.id}: User {self.user_id} bought {self.quantity}x {self.option.option_name}>"


class EventInvitation(db.Model):
    __tablename__ = 'event_invitations'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invited_at = db.Column(db.DateTime, server_default=db.func.now())
    message = db.Column(db.Text, nullable=True)  # Optional personal message from rep
    
    event = db.relationship('Event', backref=db.backref('invitations', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('event_invitations', lazy='dynamic'))
    
    def __repr__(self):
        return f"<EventInvitation {self.id}: Event {self.event_id} -> User {self.user_id}>"


class EventRSVP(db.Model):
    __tablename__ = 'event_rsvps'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'attending', 'not_attending', 'maybe'
    responded_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    event = db.relationship('Event', backref=db.backref('rsvps', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('event_rsvps', lazy='dynamic'))
    
    # Ensure one RSVP per user per event
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', name='unique_event_user_rsvp'),)
    
    def __repr__(self):
        return f"<EventRSVP {self.id}: User {self.user_id} -> Event {self.event_id} ({self.status})>"


class EventCart(db.Model):
    __tablename__ = 'event_carts'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    event = db.relationship('Event', backref=db.backref('carts', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('event_carts', lazy='dynamic'))
    
    # Ensure one cart per user per event
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', name='unique_event_user_cart'),)
    
    def __repr__(self):
        return f"<EventCart {self.id}: User {self.user_id} for Event {self.event_id}>"


class EventCartItem(db.Model):
    __tablename__ = 'event_cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('event_carts.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('event_options.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, server_default=db.func.now())
    
    cart = db.relationship('EventCart', backref=db.backref('items', lazy='dynamic', cascade='all, delete-orphan'))
    option = db.relationship('EventOption', backref=db.backref('cart_items', lazy='dynamic'))
    
    def __repr__(self):
        return f"<EventPurchase {self.id}: User {self.user_id} bought {self.quantity}x {self.option.option_name}>"


class DraftBill(db.Model):
    """
    Bills in draft/working state created by representatives using AI bill drafting.
    Representatives can control visibility and constituents/staffers can view/comment.
    """
    __tablename__ = 'draft_bills'
    id = db.Column(db.Integer, primary_key=True)
    representative_id = db.Column(db.Integer, db.ForeignKey('representatives.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)  # The actual bill text/draft
    
    # Visibility control
    # 'hidden' = only rep and staffers can see
    # 'constituents' = rep's constituents can see
    # 'public' = everyone can see
    visibility = db.Column(db.String(20), nullable=False, default='hidden')
    
    # Optional metadata from AI generation
    topic = db.Column(db.String(100), nullable=True)
    llm_prompt_used = db.Column(db.Text, nullable=True)  # Store the prompt that generated this
    based_on_bills = db.Column(db.Text, nullable=True)  # JSON list of bill_numbers used as examples
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    representative = db.relationship('Representative', backref=db.backref('draft_bills', lazy='dynamic', cascade='all, delete-orphan'))
    
    def can_view(self, user):
        """Check if a user can view this draft bill."""
        if not user:
            return self.visibility == 'public'
        
        # Rep and their staffers can always see
        if user.representative_id == self.representative_id:
            return True
        
        if user.role == 'staffer' and user.rep_boss_id == self.representative_id:
            return True
        
        # Public drafts are visible to all
        if self.visibility == 'public':
            return True
        
        # Constituent-visible drafts
        if self.visibility == 'constituents':
            # Check if user's representative matches
            if user.representative_district == self.representative.district:
                return True
        
        return False
    
    def to_dict(self):
        """Convert to dictionary for API/template rendering."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'visibility': self.visibility,
            'topic': self.topic,
            'representative': {
                'id': self.representative.id,
                'name': self.representative.name,
                'district': self.representative.district,
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'comment_count': self.comments.count() if hasattr(self, 'comments') else 0,
        }
    
    def __repr__(self):
        return f"<DraftBill {self.id}: {self.title} ({self.visibility})>"


class DraftBillComment(db.Model):
    """Comments on draft bills - can be from constituents or staffers."""
    __tablename__ = 'draft_bill_comments'
    id = db.Column(db.Integer, primary_key=True)
    draft_bill_id = db.Column(db.Integer, db.ForeignKey('draft_bills.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    comment_text = db.Column(db.Text, nullable=False)
    is_staffer = db.Column(db.Boolean, nullable=False, default=False)  # True if comment from staffer
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    draft_bill = db.relationship('DraftBill', backref=db.backref('comments', lazy='dynamic', cascade='all, delete-orphan', order_by='DraftBillComment.created_at'))
    user = db.relationship('User', backref=db.backref('draft_comments', lazy='dynamic'))
    
    def __repr__(self):
        return f"<DraftBillComment {self.id} on DraftBill {self.draft_bill_id}>"