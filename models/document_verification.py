"""
Document verification model for address verification through uploaded documents.
"""
from extensions import db
from datetime import datetime


class DocumentVerification(db.Model):
    """Model for user-uploaded documents for address verification (ID, utility bills, passport, etc.)."""
    __tablename__ = 'document_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Document details
    file_path = db.Column(db.String(500), nullable=False)  # Path to uploaded file
    original_filename = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # 'id', 'utility_bill', 'passport', 'lease', 'mortgage', 'other'
    
    # Verification status
    verification_status = db.Column(db.String(50), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'
    rejection_reason = db.Column(db.Text, nullable=True)  # Reason if rejected
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Admin who verified
    verified_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('verification_documents', lazy='dynamic'), foreign_keys=[user_id])
    verified_by = db.relationship('User', foreign_keys=[verified_by_admin_id])
    
    def approve(self, admin_id):
        """Approve the document and update user's address_verified status."""
        self.verification_status = 'approved'
        self.verified_at = datetime.utcnow()
        self.verified_by_admin_id = admin_id
        
        # Update user's address verification status
        if self.user:
            self.user.address_verified = True
    
    def reject(self, admin_id, reason):
        """Reject the document with a reason."""
        self.verification_status = 'rejected'
        self.verified_at = datetime.utcnow()
        self.verified_by_admin_id = admin_id
        self.rejection_reason = reason
    
    def to_dict(self):
        """Convert to dictionary for API/template rendering."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'original_filename': self.original_filename,
            'document_type': self.document_type,
            'verification_status': self.verification_status,
            'rejection_reason': self.rejection_reason,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified_by': self.verified_by.username if self.verified_by else None,
        }
    
    def __repr__(self):
        return f"<DocumentVerification {self.id}: {self.document_type} for User {self.user_id} ({self.verification_status})>"
