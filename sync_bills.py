#!/usr/bin/env python3
"""
Script to sync bills from Missouri House website to the database.
Run this to populate/update the bills table.
"""
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup
from extensions import db
from models import Bill
from main import app

def fetch_bills_from_mo_house():
    """Fetch and parse bills from Missouri House website."""
    url = "https://house.mo.gov/BillList.aspx"
    
    try:
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request, timeout=15) as response:
            html = response.read().decode('utf-8')
    except (URLError, HTTPError) as e:
        print(f"Error fetching bills: {e}")
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('tr')
    
    bills = []
    for i in range(0, len(rows) - 1, 2):  # Process pairs of rows
        try:
            row1 = rows[i]
            row2 = rows[i + 1]
            
            cols1 = row1.find_all('td')
            cols2 = row2.find_all('td')
            
            if len(cols1) >= 2 and len(cols2) >= 1:
                # First row has bill number and sponsor
                bill_number = cols1[0].get_text(strip=True)
                sponsor = cols1[1].get_text(strip=True) if len(cols1) > 1 else 'Unknown'
                
                # Second row has description
                description = cols2[0].get_text(strip=True) if cols2 else ''
                
                # Only process House Bills
                if bill_number and bill_number.startswith('HB'):
                    bills.append({
                        'number': bill_number,
                        'sponsor': sponsor,
                        'description': description,
                        'title': description[:200] if len(description) > 200 else description,
                        'status': 'Active',
                        'last_action': 'Filed'
                    })
                    
                    # Limit to 100 bills to keep database manageable
                    if len(bills) >= 100:
                        break
        except Exception as e:
            print(f"Error parsing row {i}: {e}")
            continue
    
    return bills

def sync_bills_to_database():
    """Sync bills from MO House to database."""
    print("Fetching bills from Missouri House website...")
    bills_data = fetch_bills_from_mo_house()
    
    if not bills_data:
        print("No bills fetched. Exiting.")
        return
    
    print(f"Fetched {len(bills_data)} bills. Syncing to database...")
    
    with app.app_context():
        # Track stats
        added = 0
        updated = 0
        
        for bill_data in bills_data:
            # Check if bill already exists
            existing_bill = Bill.query.filter_by(bill_number=bill_data['number']).first()
            
            if existing_bill:
                # Update existing bill
                existing_bill.sponsor = bill_data['sponsor']
                existing_bill.title = bill_data['title']
                existing_bill.description = bill_data['description']
                existing_bill.status = bill_data['status']
                existing_bill.last_action = bill_data['last_action']
                updated += 1
            else:
                # Create new bill
                new_bill = Bill(
                    bill_number=bill_data['number'],
                    sponsor=bill_data['sponsor'],
                    title=bill_data['title'],
                    description=bill_data['description'],
                    status=bill_data['status'],
                    last_action=bill_data['last_action']
                )
                db.session.add(new_bill)
                added += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"✓ Successfully synced bills!")
            print(f"  - Added: {added}")
            print(f"  - Updated: {updated}")
            print(f"  - Total in database: {Bill.query.count()}")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error committing to database: {e}")
            sys.exit(1)

if __name__ == '__main__':
    sync_bills_to_database()
