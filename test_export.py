#!/usr/bin/env python3
"""
Test script for the export functionality
"""

import requests
import json

def test_export_functionality():
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Export Functionality")
    print("=" * 40)
    
    # Test 1: Check if export endpoint is accessible
    print("\n1️⃣ Testing export endpoint...")
    try:
        # First, we need to login to get a session
        login_data = {
            'username': 'troy123',
            'password': 'password123'
        }
        
        session = requests.Session()
        login_response = session.post(f"{base_url}/login", data=login_data)
        
        if login_response.status_code == 200:
            print("✅ Login successful")
        else:
            print("❌ Login failed")
            return
        
        # Test export with some task IDs (assuming they exist)
        export_data = {
            'task_ids': [1, 2, 3]  # Test with some task IDs
        }
        
        export_response = session.post(f"{base_url}/api/export-tasks", 
                                     json=export_data)
        
        if export_response.status_code == 200:
            result = export_response.json()
            if result.get('success'):
                print("✅ Export endpoint working correctly")
                print(f"   Generated filename: {result.get('filename')}")
                print(f"   Report length: {len(result.get('report', ''))} characters")
                
                # Show a preview of the report
                report = result.get('report', '')
                if report:
                    print("\n📄 Report Preview:")
                    print("-" * 40)
                    lines = report.split('\n')[:20]  # Show first 20 lines
                    for line in lines:
                        print(line)
                    if len(report.split('\n')) > 20:
                        print("... (truncated)")
            else:
                print(f"❌ Export failed: {result.get('error')}")
        else:
            print(f"❌ Export endpoint returned status code: {export_response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the application")
        print("   Make sure the Flask app is running: python app.py")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 40)
    print("🎉 Export functionality test completed!")

if __name__ == "__main__":
    test_export_functionality() 