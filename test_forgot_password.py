#!/usr/bin/env python3
"""
Test script for forgot password functionality
"""

import requests
import sqlite3
from datetime import datetime, timedelta

def test_forgot_password():
    base_url = "http://localhost:5000"
    
    print("Testing Forgot Password Functionality")
    print("=" * 40)
    
    # Test 1: Check if forgot password page is accessible
    print("\n1. Testing forgot password page accessibility...")
    try:
        response = requests.get(f"{base_url}/forgot-password")
        if response.status_code == 200:
            print("✓ Forgot password page is accessible")
        else:
            print(f"✗ Forgot password page returned status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to the application. Make sure it's running on http://localhost:5000")
        return
    
    # Test 2: Test forgot password form submission with valid email
    print("\n2. Testing forgot password form submission...")
    test_email = "garciaraffitroy08@gmail.com"  # Using existing user email
    
    try:
        response = requests.post(f"{base_url}/forgot-password", data={
            'email': test_email
        })
        
        if response.status_code == 200:
            if 'data-reset-email-sent' in response.text:
                print("✓ Password reset email sent successfully")
            else:
                print("✗ Unexpected response format")
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"✗ Form submission failed with status code: {response.status_code}")
    except Exception as e:
        print(f"✗ Error during form submission: {e}")
    
    # Test 3: Check if reset token was created in database
    print("\n3. Checking database for reset token...")
    try:
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM password_reset_tokens WHERE used = 0 AND expires_at > ?', 
                 (datetime.now().isoformat(),))
        token_count = c.fetchone()[0]
        conn.close()
        
        if token_count > 0:
            print(f"✓ Found {token_count} active reset token(s) in database")
        else:
            print("✗ No active reset tokens found in database")
    except Exception as e:
        print(f"✗ Error checking database: {e}")
    
    # Test 4: Test with invalid email
    print("\n4. Testing with invalid email...")
    try:
        response = requests.post(f"{base_url}/forgot-password", data={
            'email': 'nonexistent@example.com'
        })
        
        if response.status_code == 200:
            if 'data-reset-email-sent' in response.text:
                print("✓ Proper response for invalid email (security: doesn't reveal if email exists)")
            else:
                print("✗ Unexpected response for invalid email")
        else:
            print(f"✗ Invalid email test failed with status code: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing invalid email: {e}")
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    test_forgot_password() 