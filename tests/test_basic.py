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
    
    def test_basic_imports(self):
        """Test that basic Python modules can be imported"""
        try:
            import sqlite3
            import json
            import logging
            import requests
            self.assertTrue(True, "Basic modules imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import basic modules: {e}")
    
    def test_flask_import(self):
        """Test that Flask can be imported"""
        try:
            import flask
            self.assertTrue(True, "Flask imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import Flask: {e}")
    
    def test_requirements_met(self):
        """Test that required packages are available"""
        required_packages = [
            'flask', 'requests', 'sqlite3', 'json', 'logging'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                self.fail(f"Required package {package} is not available")

if __name__ == '__main__':
    unittest.main()
