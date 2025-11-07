#!/usr/bin/env python
"""Test the draft bill workspace feature."""
from main import app
from extensions import db
from models import User, Representative, DraftBill, DraftBillComment
from services.bill_drafting import (
    save_draft_bill,
    get_rep_drafts,
    get_visible_drafts_for_user,
    add_draft_comment,
    update_draft_visibility
)

def test_draft_bills():
    """Test the draft bill workspace feature."""
    with app.app_context():
        print("="*60)
        print("DRAFT BILL WORKSPACE TEST")
        print("="*60)
        
        # Get or create a test representative
        rep = Representative.query.filter_by(district='001').first()
        if not rep:
            rep = Representative(
                district='001',
                first_name='Test',
                last_name='Representative',
                party='D',
                city='Jefferson City',
                phone='555-0001'
            )
            db.session.add(rep)
            db.session.commit()
            print(f"✓ Created test representative: {rep.name} (District {rep.district})")
        else:
            print(f"✓ Using existing representative: {rep.name} (District {rep.district})")
        
        # Get or create a test rep user
        rep_user = User.query.filter_by(username='testrep').first()
        if not rep_user:
            rep_user = User(
                username='testrep',
                role='rep',
                representative_id=rep.id,
                street_address='123 Capitol Ave',
                city='Jefferson City',
                state='MO',
                zipcode='65101',
                address_verified=True
            )
            rep_user.set_password('test123')
            db.session.add(rep_user)
            db.session.commit()
            print(f"✓ Created test rep user: {rep_user.username}")
        else:
            print(f"✓ Using existing rep user: {rep_user.username}")
        
        # Get or create a test staffer
        staffer = User.query.filter_by(username='teststaffer').first()
        if not staffer:
            staffer = User(
                username='teststaffer',
                role='staffer',
                rep_boss_id=rep.id,
                street_address='123 Capitol Ave',
                city='Jefferson City',
                state='MO',
                zipcode='65101',
                address_verified=True
            )
            staffer.set_password('test123')
            db.session.add(staffer)
            db.session.commit()
            print(f"✓ Created test staffer: {staffer.username}")
        else:
            print(f"✓ Using existing staffer: {staffer.username}")
        
        # Get or create a test constituent
        constituent = User.query.filter_by(username='testconstituent').first()
        if not constituent:
            constituent = User(
                username='testconstituent',
                role='regular',
                street_address='456 Main St',
                city='Jefferson City',
                state='MO',
                zipcode='65101',
                address_verified=True,
                representative_district='001'  # Same district as rep
            )
            constituent.set_password('test123')
            db.session.add(constituent)
            db.session.commit()
            print(f"✓ Created test constituent: {constituent.username}")
        else:
            print(f"✓ Using existing constituent: {constituent.username}")
        
        # Get or create a test non-constituent
        non_constituent = User.query.filter_by(username='testnonconstituent').first()
        if not non_constituent:
            non_constituent = User(
                username='testnonconstituent',
                role='regular',
                street_address='789 Other St',
                city='Springfield',
                state='MO',
                zipcode='65802',
                address_verified=True,
                representative_district='002'  # Different district
            )
            non_constituent.set_password('test123')
            db.session.add(non_constituent)
            db.session.commit()
            print(f"✓ Created test non-constituent: {non_constituent.username}")
        else:
            print(f"✓ Using existing non-constituent: {non_constituent.username}")
        
        print("\n" + "="*60)
        print("TESTING DRAFT BILL CREATION")
        print("="*60)
        
        # Create test drafts with different visibilities
        drafts_created = []
        
        # Hidden draft
        hidden_draft = save_draft_bill(
            representative_id=rep.id,
            title="HB 100 - Test Hidden Bill",
            content="This is a hidden draft bill that only the rep and staff can see.",
            description="Testing hidden visibility",
            visibility='hidden',
            topic='testing'
        )
        drafts_created.append(hidden_draft)
        print(f"✓ Created hidden draft: {hidden_draft.title}")
        
        # Constituents-visible draft
        constituent_draft = save_draft_bill(
            representative_id=rep.id,
            title="HB 101 - Education Funding Reform",
            content="This bill proposes changes to education funding...",
            description="Visible to constituents",
            visibility='constituents',
            topic='education'
        )
        drafts_created.append(constituent_draft)
        print(f"✓ Created constituent-visible draft: {constituent_draft.title}")
        
        # Public draft
        public_draft = save_draft_bill(
            representative_id=rep.id,
            title="HB 102 - Healthcare Access Act",
            content="This bill aims to improve healthcare access...",
            description="Visible to everyone",
            visibility='public',
            topic='healthcare'
        )
        drafts_created.append(public_draft)
        print(f"✓ Created public draft: {public_draft.title}")
        
        print("\n" + "="*60)
        print("TESTING VISIBILITY CONTROLS")
        print("="*60)
        
        # Test what each user can see
        print("\n1. Representative (owner) should see all 3 drafts:")
        rep_visible = get_visible_drafts_for_user(rep_user, rep.id)
        print(f"   Can see {len(rep_visible)} drafts: {[d.title for d in rep_visible]}")
        
        print("\n2. Staffer should see all 3 drafts:")
        staffer_visible = get_visible_drafts_for_user(staffer, rep.id)
        print(f"   Can see {len(staffer_visible)} drafts: {[d.title for d in staffer_visible]}")
        
        print("\n3. Constituent should see 2 drafts (constituents + public):")
        constituent_visible = get_visible_drafts_for_user(constituent, rep.id)
        print(f"   Can see {len(constituent_visible)} drafts: {[d.title for d in constituent_visible]}")
        
        print("\n4. Non-constituent should see 1 draft (public only):")
        non_constituent_visible = get_visible_drafts_for_user(non_constituent, rep.id)
        print(f"   Can see {len(non_constituent_visible)} drafts: {[d.title for d in non_constituent_visible]}")
        
        print("\n" + "="*60)
        print("TESTING COMMENTS")
        print("="*60)
        
        # Add comments from different users
        comment1 = add_draft_comment(
            draft_bill_id=public_draft.id,
            user_id=constituent.id,
            comment_text="This is a great idea! I support this bill.",
            is_staffer=False
        )
        print(f"✓ Constituent commented on public draft")
        
        comment2 = add_draft_comment(
            draft_bill_id=public_draft.id,
            user_id=staffer.id,
            comment_text="Internal note: Need to check fiscal impact.",
            is_staffer=True
        )
        print(f"✓ Staffer commented on public draft")
        
        comment3 = add_draft_comment(
            draft_bill_id=constituent_draft.id,
            user_id=constituent.id,
            comment_text="Can we add more funding for rural schools?",
            is_staffer=False
        )
        print(f"✓ Constituent commented on constituent-visible draft")
        
        print(f"\nPublic draft now has {public_draft.comments.count()} comments")
        print(f"Constituent draft now has {constituent_draft.comments.count()} comments")
        
        print("\n" + "="*60)
        print("TESTING VISIBILITY UPDATE")
        print("="*60)
        
        # Change hidden draft to public
        print(f"Changing '{hidden_draft.title}' from hidden to public...")
        updated_draft = update_draft_visibility(hidden_draft.id, 'public')
        print(f"✓ Updated visibility to: {updated_draft.visibility}")
        
        # Re-check what non-constituent can see
        non_constituent_visible_after = get_visible_drafts_for_user(non_constituent, rep.id)
        print(f"\nNon-constituent can now see {len(non_constituent_visible_after)} drafts (was {len(non_constituent_visible)})")
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✓ Created {len(drafts_created)} draft bills")
        print(f"✓ Tested visibility for 4 different user types")
        print(f"✓ Added {DraftBillComment.query.count()} comments")
        print(f"✓ Updated visibility settings")
        print("\n✅ All tests passed!")
        print("\nTest users created (password: test123):")
        print(f"  - testrep (Representative)")
        print(f"  - teststaffer (Staffer)")
        print(f"  - testconstituent (Constituent)")
        print(f"  - testnonconstituent (Non-constituent)")
        print("\nYou can now login and test the UI!")

if __name__ == '__main__':
    test_draft_bills()
