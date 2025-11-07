#!/usr/bin/env python3
"""
Script to confirm and update representative information for users.

This script:
1. Finds users who don't have rep info or have stale data
2. Looks up their representatives using their address
3. Updates their profile with the current rep info
4. Shows a summary of what was found

Usage:
    python confirm_user_reps.py [--user-id USER_ID] [--force] [--all]
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from extensions import db
from models import User
from rep_lookup import RepresentativeLookup
from address_verification import format_address


def create_app():
    """Create minimal Flask app for database access."""
    app = Flask(__name__)
    from config import config
    app.config.from_object(config['default'])
    db.init_app(app)
    return app


def confirm_reps_for_user(user, force=False):
    """Look up and update representative information for a single user.
    
    Args:
        user: User model instance
        force: If True, update even if reps_last_updated is recent
    
    Returns:
        dict: Result with status, message, and rep_info
    """
    # Check if update is needed
    if not force and user.reps_last_updated:
        days_old = (datetime.utcnow() - user.reps_last_updated).days
        if days_old < 30:
            return {
                'status': 'skip',
                'message': f'Rep info updated {days_old} days ago (use --force to refresh)',
                'rep_info': user.get_representatives_display()
            }
    
    # Format address for lookup
    address_str = format_address(
        user.street_address,
        user.city,
        user.state,
        user.zipcode,
        user.apt_unit
    )
    
    print(f"\n🔍 Looking up representatives for: {user.username}")
    print(f"   Address: {address_str}")
    
    # Perform lookup
    rep_info = RepresentativeLookup.lookup_representatives(
        user.street_address,
        user.city,
        user.zipcode
    )
    
    if not rep_info:
        return {
            'status': 'error',
            'message': 'Failed to look up representatives (API error)',
            'rep_info': None
        }
    
    # Check if we got any results
    has_senator = rep_info.get('state_senator') and rep_info['state_senator'].get('name')
    has_rep = rep_info.get('state_representative') and rep_info['state_representative'].get('name')
    
    if not has_senator and not has_rep:
        return {
            'status': 'error',
            'message': 'No representatives found for this address',
            'rep_info': None
        }
    
    # Update user record
    success = user.update_representatives(rep_info)
    
    if success:
        try:
            db.session.commit()
            display = user.get_representatives_display()
            return {
                'status': 'success',
                'message': 'Representatives updated successfully',
                'rep_info': display
            }
        except Exception as e:
            db.session.rollback()
            return {
                'status': 'error',
                'message': f'Database error: {str(e)}',
                'rep_info': None
            }
    else:
        return {
            'status': 'error',
            'message': 'Failed to update user record',
            'rep_info': None
        }


def print_rep_info(display_info):
    """Pretty print representative information."""
    if not display_info or not display_info.get('has_data'):
        print("   ❌ No representative data")
        return
    
    if display_info.get('senator'):
        sen = display_info['senator']
        print(f"   👔 State Senator: {sen['name']}")
        print(f"      District: {sen['district']}, Party: {sen['party']}")
    
    if display_info.get('representative'):
        rep = display_info['representative']
        print(f"   🏛️  State Representative: {rep['name']}")
        print(f"      District: {rep['district']}, Party: {rep['party']}")


def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(
        description='Confirm and update representative information for users'
    )
    parser.add_argument(
        '--user-id',
        type=int,
        help='Update specific user by ID'
    )
    parser.add_argument(
        '--username',
        type=str,
        help='Update specific user by username'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update even if data is recent'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Update all users (default: only users without rep info or stale data)'
    )
    parser.add_argument(
        '--stale-days',
        type=int,
        default=90,
        help='Consider rep info stale after N days (default: 90)'
    )
    
    args = parser.parse_args()
    
    # Create app and get database access
    app = create_app()
    
    with app.app_context():
        # Determine which users to process
        if args.user_id:
            users = [User.query.get(args.user_id)]
            if not users[0]:
                print(f"❌ User with ID {args.user_id} not found")
                return 1
        elif args.username:
            users = [User.query.filter_by(username=args.username).first()]
            if not users[0]:
                print(f"❌ User '{args.username}' not found")
                return 1
        elif args.all:
            users = User.query.all()
        else:
            # Default: users without rep info or with stale data
            cutoff_date = datetime.utcnow() - timedelta(days=args.stale_days)
            users = User.query.filter(
                db.or_(
                    User.reps_last_updated == None,
                    User.reps_last_updated < cutoff_date,
                    User.representative_name == None
                )
            ).all()
        
        if not users:
            print("✅ No users need representative updates")
            return 0
        
        print(f"\n{'='*60}")
        print(f"REPRESENTATIVE CONFIRMATION REPORT")
        print(f"{'='*60}")
        print(f"Processing {len(users)} user(s)...")
        
        # Process each user
        results = {
            'success': 0,
            'skip': 0,
            'error': 0
        }
        
        for user in users:
            result = confirm_reps_for_user(user, force=args.force)
            results[result['status']] += 1
            
            # Print result
            status_icon = {
                'success': '✅',
                'skip': '⏭️ ',
                'error': '❌'
            }[result['status']]
            
            print(f"\n{status_icon} User: {user.username} (ID: {user.id})")
            print(f"   {result['message']}")
            
            if result.get('rep_info'):
                print_rep_info(result['rep_info'])
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful updates: {results['success']}")
        print(f"⏭️  Skipped (recent):   {results['skip']}")
        print(f"❌ Errors:             {results['error']}")
        print(f"{'='*60}\n")
        
        return 0 if results['error'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
