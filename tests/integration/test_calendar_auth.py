#!/usr/bin/env python3
"""
Test Google Calendar authentication with automatic token regeneration
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from user_tools.google_calendar_scheduler import GoogleCalendarSchedulerTool

def test_calendar_auth():
    print("🧪 Testing Google Calendar Authentication with Auto-Regeneration")
    print("=" * 60)
    
    # Create tool instance
    tool = GoogleCalendarSchedulerTool()
    
    # Test event description
    event_description = "Test dinner with Diana at Loleta Italian Restaurant this Sunday at 7:20 PM"
    
    print(f"📅 Event Description: {event_description}")
    print("🔄 Testing authentication and event creation...")
    
    # This should trigger the authentication method which includes auto-regeneration
    result = tool._schedule_calendar_event(event_description)
    
    print("📝 Result:")
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    test_calendar_auth()