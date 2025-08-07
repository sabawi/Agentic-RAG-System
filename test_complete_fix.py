#!/usr/bin/env python3

import requests
import time
import subprocess
import os

def test_complete_workflow():
    """Test the complete workflow with proper HTML-to-PDF conversion"""
    
    # Create a comprehensive request that would generate HTML content
    test_request = {
        "prompt": "Create a PDF report called comprehensive_test.pdf about artificial intelligence and machine learning trends, include sections about transformers, computer vision, and natural language processing, then email it to sabawi@gmail.com",
        "model": "qwen3:8b", 
        "stream": False
    }
    
    print("🚀 Testing complete HTML-to-PDF conversion workflow...")
    print(f"Request: {test_request['prompt']}")
    print()
    
    start_time = time.time()
    
    try:
        # Send request
        response = requests.post(
            "http://localhost:5000/llama3_1b/stream",
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout
        )
        
        end_time = time.time()
        
        print(f"⏱️ Request completed in {end_time - start_time:.1f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request successful")
            
            # Check if PDF was created
            pdf_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/comprehensive_test.pdf"
            if os.path.exists(pdf_path):
                print(f"✅ PDF file exists: {pdf_path}")
                
                # Check file type
                result = subprocess.run(['file', pdf_path], capture_output=True, text=True)
                print(f"📄 File type: {result.stdout.strip()}")
                
                # Check file size
                size = os.path.getsize(pdf_path)
                print(f"📏 File size: {size} bytes")
                
                if "PDF document" in result.stdout and size > 1000:
                    print("✅ Valid PDF with substantial content!")
                    
                    # Check for latest email debug file
                    import glob
                    email_files = glob.glob("/tmp/email_debug_*.eml")
                    if email_files:
                        latest_email = max(email_files, key=os.path.getctime)
                        email_time = os.path.getctime(latest_email)
                        if email_time > start_time - 60:  # Within the last minute plus buffer
                            print(f"✅ Email debug file created: {latest_email}")
                            
                            # Check email content briefly
                            with open(latest_email, 'r') as f:
                                email_content = f.read()
                                if "comprehensive_test.pdf" in email_content:
                                    print("✅ Email contains correct attachment reference")
                                else:
                                    print("⚠️ Email might not contain correct attachment")
                        else:
                            print("⚠️ No recent email debug file found")
                    else:
                        print("⚠️ No email debug files found")
                        
                else:
                    print("❌ Invalid PDF or too small")
            else:
                print(f"❌ PDF file not found: {pdf_path}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except requests.exceptions.Timeout:
        print("⏱️ Request timed out (this might be normal for complex requests)")
        
        # Still check if files were created
        pdf_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/comprehensive_test.pdf"
        if os.path.exists(pdf_path):
            print("✅ PDF was created despite timeout")
            result = subprocess.run(['file', pdf_path], capture_output=True, text=True)
            print(f"📄 File type: {result.stdout.strip()}")
            size = os.path.getsize(pdf_path)
            print(f"📏 File size: {size} bytes")
        else:
            print("❌ No PDF created")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_complete_workflow()