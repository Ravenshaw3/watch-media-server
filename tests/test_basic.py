#!/usr/bin/env python3
"""
Basic tests for Watch Media Server
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestBasicFunctionality(unittest.TestCase):
    """Basic functionality tests"""
    
    def test_imports(self):
        """Test that all modules can be imported"""
        try:
            import app
            import console
            import media_formatter
            self.assertTrue(True, "All modules imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import modules: {e}")
    
    def test_app_creation(self):
        """Test that the Flask app can be created"""
        try:
            from app import app
            self.assertIsNotNone(app, "Flask app should be created")
        except Exception as e:
            self.fail(f"Failed to create Flask app: {e}")
    
    def test_media_manager_creation(self):
        """Test that MediaManager can be created"""
        try:
            from app import MediaManager
            # Create a temporary database for testing
            manager = MediaManager()
            self.assertIsNotNone(manager, "MediaManager should be created")
        except Exception as e:
            self.fail(f"Failed to create MediaManager: {e}")

if __name__ == '__main__':
    unittest.main()
