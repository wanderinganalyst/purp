#!/usr/bin/env python3
"""
Script to fetch and store full bill text in the database.

This script:
1. Fetches bill text PDFs from Missouri Legislature
2. Extracts text from PDFs
3. Stores in database for LLM processing

Usage:
    python fetch_bill_text.py                    # Fetch text for all bills
    python fetch_bill_text.py HB101 HB102       # Fetch specific bills
    python fetch_bill_text.py --limit 10        # Fetch first 10 bills
    python fetch_bill_text.py --refetch         # Re-fetch all bills even if already fetched
"""
import sys
import argparse
from datetime import datetime
from extensions import db
from models import Bill
from services.bill_text_fetcher import fetch_bill_full_text
from main import app


def fetch_text_for_bill(bill, refetch=False):
    """Fetch and store text for a single bill."""
    if not refetch and bill.full_text and bill.text_fetched_at:
        print(f"  ✓ {bill.bill_number} already has text (fetched {bill.text_fetched_at})")
        return False
    
    print(f"  Fetching text for {bill.bill_number}...")
    
    try:
        full_text, text_pdf_url, summary_pdf_url = fetch_bill_full_text(bill.bill_number)
        
        if full_text:
            bill.full_text = full_text
            bill.text_pdf_url = text_pdf_url
            bill.summary_pdf_url = summary_pdf_url
            bill.text_fetched_at = datetime.utcnow()
            
            word_count = len(full_text.split())
            print(f"  ✓ {bill.bill_number}: Fetched {word_count} words")
            return True
        else:
            print(f"  ✗ {bill.bill_number}: No text found")
            # Still update URLs even if text extraction failed
            bill.text_pdf_url = text_pdf_url
            bill.summary_pdf_url = summary_pdf_url
            return False
            
    except Exception as e:
        print(f"  ✗ {bill.bill_number}: Error - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Fetch bill text for database')
    parser.add_argument('bills', nargs='*', help='Specific bill numbers to fetch (e.g., HB101)')
    parser.add_argument('--limit', type=int, help='Limit number of bills to fetch')
    parser.add_argument('--refetch', action='store_true', help='Re-fetch bills that already have text')
    parser.add_argument('--year', default='2025', help='Legislative year (default: 2025)')
    
    args = parser.parse_args()
    
    with app.app_context():
        # Determine which bills to fetch
        if args.bills:
            # Specific bills requested
            bills = Bill.query.filter(Bill.bill_number.in_(args.bills)).all()
            if not bills:
                print(f"No bills found matching: {', '.join(args.bills)}")
                return
            print(f"Fetching text for {len(bills)} specified bills...")
        else:
            # All bills (or limited)
            query = Bill.query.order_by(Bill.bill_number)
            if args.limit:
                query = query.limit(args.limit)
            bills = query.all()
            
            if not bills:
                print("No bills found in database. Run sync_bills.py first.")
                return
            
            limit_msg = f" (limited to {args.limit})" if args.limit else ""
            print(f"Fetching text for {len(bills)} bills{limit_msg}...")
        
        # Fetch text for each bill
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for bill in bills:
            result = fetch_text_for_bill(bill, refetch=args.refetch)
            if result:
                success_count += 1
            elif bill.full_text:
                skip_count += 1
            else:
                fail_count += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✓ Database updated successfully")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error saving to database: {e}")
            return
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total bills processed: {len(bills)}")
        print(f"Successfully fetched:  {success_count}")
        print(f"Already had text:      {skip_count}")
        print(f"Failed/No text:        {fail_count}")
        print()
        
        # Show stats
        total_with_text = Bill.query.filter(Bill.full_text.isnot(None)).count()
        total_bills = Bill.query.count()
        coverage_pct = (total_with_text / total_bills * 100) if total_bills > 0 else 0
        
        print(f"Database coverage: {total_with_text}/{total_bills} bills ({coverage_pct:.1f}%) have full text")
        
        # Calculate total words
        bills_with_text = Bill.query.filter(Bill.full_text.isnot(None)).all()
        total_words = sum(len(b.full_text.split()) for b in bills_with_text)
        print(f"Total text stored: {total_words:,} words")
        print()


if __name__ == '__main__':
    main()
