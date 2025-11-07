"""
Seed script to create Rally and Dinner event templates with predefined options.
Run this script to populate the database with the two initial templates.
"""
from main import create_app
from extensions import db
from models import EventTemplate, EventOption

def seed_templates():
    app = create_app()
    
    with app.app_context():
        # Check if templates already exist
        existing_rally = EventTemplate.query.filter_by(name='Rally Template').first()
        existing_dinner = EventTemplate.query.filter_by(name='Dinner Event Template').first()
        
        if existing_rally:
            print('⚠️  Rally Template already exists. Skipping...')
        else:
            # Create Rally Template
            rally_template = EventTemplate(
                name='Rally Template',
                description='Political rally with seating, merchandise, and transportation options'
            )
            db.session.add(rally_template)
            db.session.flush()  # Get the ID
            
            # Rally options
            rally_options = [
                # Seating
                EventOption(template_id=rally_template.id, option_name='Front Row Seat', option_type='seating', price=50.00, description='Premium seating in the front row'),
                EventOption(template_id=rally_template.id, option_name='Standard Seat', option_type='seating', price=25.00, description='General admission seating'),
                EventOption(template_id=rally_template.id, option_name='VIP Section', option_type='seating', price=100.00, description='VIP section with meet & greet'),
                
                # Merchandise
                EventOption(template_id=rally_template.id, option_name='Campaign Flag', option_type='merchandise', price=15.00, description='Official campaign flag'),
                EventOption(template_id=rally_template.id, option_name='Rally Hat', option_type='merchandise', price=20.00, description='Embroidered campaign hat'),
                EventOption(template_id=rally_template.id, option_name='Rally Towel', option_type='merchandise', price=10.00, description='Rally towel with campaign logo'),
                EventOption(template_id=rally_template.id, option_name='Campaign Pin', option_type='merchandise', price=5.00, description='Collectible campaign pin'),
                EventOption(template_id=rally_template.id, option_name='Campaign Sticker', option_type='merchandise', price=2.00, description='Weatherproof campaign sticker'),
                
                # Transportation
                EventOption(template_id=rally_template.id, option_name='Bus Transportation', option_type='transportation', price=10.00, description='Round-trip bus transportation to the rally'),
            ]
            db.session.add_all(rally_options)
            print('✅ Rally Template created with 9 options')
        
        if existing_dinner:
            print('⚠️  Dinner Event Template already exists. Skipping...')
        else:
            # Create Dinner Event Template
            dinner_template = EventTemplate(
                name='Dinner Event Template',
                description='Fundraising dinner with catered meals, drinks, and seating options'
            )
            db.session.add(dinner_template)
            db.session.flush()  # Get the ID
            
            # Dinner options
            dinner_options = [
                # Seating
                EventOption(template_id=dinner_template.id, option_name='Head Table Seat', option_type='seating', price=200.00, description='Reserved seat at the head table'),
                EventOption(template_id=dinner_template.id, option_name='Full Table (8 seats)', option_type='seating', price=1000.00, description='Reserve an entire table for 8 people'),
                EventOption(template_id=dinner_template.id, option_name='Single Seat', option_type='seating', price=150.00, description='Individual dinner seat'),
                
                # Food & Drinks
                EventOption(template_id=dinner_template.id, option_name='Catered Meal', option_type='food', price=75.00, description='Three-course catered meal'),
                EventOption(template_id=dinner_template.id, option_name='Vegetarian Meal', option_type='food', price=75.00, description='Vegetarian three-course meal'),
                EventOption(template_id=dinner_template.id, option_name='Wine Pairing', option_type='food', price=30.00, description='Wine pairing for your meal'),
                EventOption(template_id=dinner_template.id, option_name='Premium Bar Package', option_type='food', price=50.00, description='Unlimited premium drinks'),
                
                # Merchandise
                EventOption(template_id=dinner_template.id, option_name='Event Flag', option_type='merchandise', price=15.00, description='Commemorative event flag'),
                EventOption(template_id=dinner_template.id, option_name='Event Hat', option_type='merchandise', price=20.00, description='Embroidered event hat'),
                EventOption(template_id=dinner_template.id, option_name='Event Towel', option_type='merchandise', price=10.00, description='Event towel with logo'),
                EventOption(template_id=dinner_template.id, option_name='Commemorative Pin', option_type='merchandise', price=5.00, description='Collectible event pin'),
                EventOption(template_id=dinner_template.id, option_name='Event Sticker', option_type='merchandise', price=2.00, description='Event sticker'),
                
                # Transportation
                EventOption(template_id=dinner_template.id, option_name='Valet Parking', option_type='transportation', price=25.00, description='Premium valet parking service'),
                EventOption(template_id=dinner_template.id, option_name='Shuttle Service', option_type='transportation', price=15.00, description='Round-trip shuttle from designated locations'),
            ]
            db.session.add_all(dinner_options)
            print('✅ Dinner Event Template created with 14 options')
        
        try:
            db.session.commit()
            print('\n🎉 Template seeding completed successfully!')
            print('\nTemplates created:')
            templates = EventTemplate.query.all()
            for template in templates:
                print(f'  - {template.name} ({template.options.count()} options)')
        except Exception as e:
            db.session.rollback()
            print(f'❌ Error seeding templates: {e}')

if __name__ == '__main__':
    seed_templates()
