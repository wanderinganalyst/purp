"""
Create a Candidate Representative placeholder for candidates to use.
"""
from main import create_app
from extensions import db
from models import Representative

app = create_app()

with app.app_context():
    # Check if Candidate Representative already exists
    candidate_rep = Representative.query.filter_by(
        last_name='Candidate',
        first_name='Campaign'
    ).first()
    
    if candidate_rep:
        print(f'✓ Candidate Representative already exists: ID {candidate_rep.id}')
    else:
        # Create the candidate representative placeholder
        candidate_rep = Representative(
            first_name='Campaign',
            last_name='Candidate',
            district='Candidate',
            party='Independent',
            city='Providence',
            phone='000-000-0000',
            room='N/A'
        )
        db.session.add(candidate_rep)
        db.session.commit()
        print(f'✓ Created Candidate Representative with ID: {candidate_rep.id}')
        print(f'  Name: {candidate_rep.first_name} {candidate_rep.last_name}')
        print(f'  District: {candidate_rep.district}')
        print(f'\nCandidates can now use this representative for creating events.')
