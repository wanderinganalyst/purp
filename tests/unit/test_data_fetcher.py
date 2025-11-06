"""
Unit tests for utils/data_fetcher.py
"""

import pytest
import json
import os
from pathlib import Path
from utils.data_fetcher import DataFetcher, get_data_fetcher


class TestDataFetcher:
    """Test the DataFetcher class."""
    
    def test_singleton_pattern(self):
        """Test that get_data_fetcher returns the same instance."""
        fetcher1 = get_data_fetcher()
        fetcher2 = get_data_fetcher()
        assert fetcher1 is fetcher2
    
    def test_development_mode_detection(self):
        """Test that development mode is detected correctly."""
        os.environ['FLASK_ENV'] = 'development'
        fetcher = DataFetcher()
        assert fetcher.is_production is False
    
    def test_production_mode_detection(self):
        """Test that production mode is detected correctly."""
        os.environ['FLASK_ENV'] = 'production'
        fetcher = DataFetcher()
        assert fetcher.is_production is True
    
    def test_fetch_bills_development(self):
        """Test fetching bills in development mode."""
        os.environ['FLASK_ENV'] = 'development'
        fetcher = DataFetcher()
        bills = fetcher.fetch_bills()
        
        assert isinstance(bills, list)
        assert len(bills) > 0
        
        # Check bill structure
        bill = bills[0]
        assert 'number' in bill
        assert 'sponsor' in bill
        assert 'title' in bill
        assert 'status' in bill
    
    def test_fetch_representatives_development(self):
        """Test fetching representatives in development mode."""
        os.environ['FLASK_ENV'] = 'development'
        fetcher = DataFetcher()
        
        address_data = {
            'street': '201 W Capitol Ave',
            'city': 'Jefferson City',
            'state': 'MO',
            'zip': '65101'
        }
        
        reps = fetcher.fetch_representatives(address_data)
        
        assert 'senator' in reps
        assert 'representative' in reps
        assert 'name' in reps['senator']
        assert 'district' in reps['senator']
        assert 'party' in reps['senator']
    
    def test_mock_data_file_creation(self):
        """Test that mock data file is created."""
        os.environ['FLASK_ENV'] = 'development'
        fetcher = DataFetcher()
        fetcher._ensure_mock_data()
        
        assert fetcher.MOCK_DATA_FILE.exists()
    
    def test_mock_data_structure(self):
        """Test that mock data has correct structure."""
        os.environ['FLASK_ENV'] = 'development'
        fetcher = DataFetcher()
        fetcher._ensure_mock_data()
        
        with open(fetcher.MOCK_DATA_FILE, 'r') as f:
            mock_data = json.load(f)
        
        assert 'generated_at' in mock_data
        assert 'bills' in mock_data
        assert 'representatives' in mock_data
        assert isinstance(mock_data['bills'], list)
        assert isinstance(mock_data['representatives'], dict)
    
    def test_zip_code_lookup(self):
        """Test representative lookup by zip code."""
        os.environ['FLASK_ENV'] = 'development'
        fetcher = DataFetcher()
        
        # Test Jefferson City
        reps_jc = fetcher.fetch_representatives({'zip': '65101', 'city': 'Jefferson City', 'state': 'MO', 'street': '201 W Capitol'})
        
        # Test St. Louis
        reps_stl = fetcher.fetch_representatives({'zip': '63101', 'city': 'St. Louis', 'state': 'MO', 'street': '123 Main'})
        
        # Should be different reps
        assert reps_jc['senator']['name'] != reps_stl['senator']['name']
    
    def test_unknown_zip_fallback(self):
        """Test fallback for unknown zip code."""
        os.environ['FLASK_ENV'] = 'development'
        fetcher = DataFetcher()
        
        reps = fetcher.fetch_representatives({
            'zip': '99999',
            'city': 'Unknown',
            'state': 'MO',
            'street': '999 Unknown St'
        })
        
        assert reps is not None
        assert 'senator' in reps
        assert 'representative' in reps
    
    def test_refresh_mock_data(self):
        """Test refreshing mock data."""
        os.environ['FLASK_ENV'] = 'development'
        fetcher = DataFetcher()
        
        # Get initial data
        initial_data = fetcher.fetch_bills()
        
        # Refresh
        fetcher.refresh_mock_data()
        
        # Get new data
        new_data = fetcher.fetch_bills()
        
        # Should still have data
        assert len(new_data) > 0
