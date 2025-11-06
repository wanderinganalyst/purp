"""
Models package for database models.
"""
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='regular')
    
    # Address fields
    street_address = db.Column(db.String(255), nullable=False)
    apt_unit = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    zipcode = db.Column(db.String(10), nullable=False)
    address_verified = db.Column(db.Boolean, nullable=False, default=False)
    
    # Representative information
    senator_name = db.Column(db.String(255), nullable=True)
    senator_district = db.Column(db.String(10), nullable=True)
    senator_party = db.Column(db.String(50), nullable=True)
    representative_name = db.Column(db.String(255), nullable=True)
    representative_district = db.Column(db.String(10), nullable=True)
    representative_party = db.Column(db.String(50), nullable=True)
    reps_last_updated = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_representatives(self, rep_info):
        """Update representative information from lookup result."""
        from datetime import datetime
        
        if not rep_info:
            return False
        
        # Update senator info
        if rep_info.get('state_senator'):
            senator = rep_info['state_senator']
            self.senator_name = senator.get('name')
            self.senator_district = senator.get('district')
            self.senator_party = senator.get('party')
        
        # Update representative info
        if rep_info.get('state_representative'):
            rep = rep_info['state_representative']
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