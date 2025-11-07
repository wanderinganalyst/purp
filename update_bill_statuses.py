#!/usr/bin/env python3
"""
Script to update bill statuses for testing the bill drafting feature.
This adds realistic passed/failed statuses to bills for demonstration.
"""
from models import Bill
from extensions import db
from main import app

def update_bill_statuses():
    """Update some bills with passed/failed statuses for testing."""
    with app.app_context():
        bills = Bill.query.all()
        
        if not bills:
            print("No bills found. Run sync_bills.py first.")
            return
        
        print(f"Updating statuses for {len(bills)} bills...")
        
        # Update some bills as passed
        passed_statuses = ['Signed by Governor', 'Enacted', 'Passed', 'Signed into Law']
        for i, bill in enumerate(bills[::5]):  # Every 5th bill
            if i < len(passed_statuses):
                bill.status = passed_statuses[i % len(passed_statuses)]
                bill.last_action = f'Signed - {bill.bill_number} became law'
                print(f"  ✓ {bill.bill_number}: {bill.status}")
        
        # Update some bills as failed
        failed_statuses = ['Defeated', 'Rejected', 'Vetoed', 'Failed']
        for i, bill in enumerate(bills[1::7]):  # Every 7th bill starting at 1
            if i < len(failed_statuses):
                bill.status = failed_statuses[i % len(failed_statuses)]
                bill.last_action = f'Motion to pass failed'
                print(f"  ✗ {bill.bill_number}: {bill.status}")
        
        db.session.commit()
        
        # Show summary
        from services.bill_drafting import categorize_bill_status
        
        passed_count = sum(1 for b in bills if categorize_bill_status(b.status) == 'passed')
        failed_count = sum(1 for b in bills if categorize_bill_status(b.status) == 'failed')
        active_count = sum(1 for b in bills if categorize_bill_status(b.status) == 'active')
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Passed bills: {passed_count}")
        print(f"Failed bills: {failed_count}")
        print(f"Active bills: {active_count}")
        print(f"Total bills:  {len(bills)}")
        print()
        print("✓ Bill statuses updated successfully!")
        print()

if __name__ == '__main__':
    update_bill_statuses()
