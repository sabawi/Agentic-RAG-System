#!/usr/bin/env python3
"""
Test the simplified Google Calendar workflow (no confirmation needed)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_tools.google_calendar_scheduler import GoogleCalendarSchedulerTool

def test_simplified_calendar():
    print("🧪 Testing Simplified Google Calendar Workflow")
    print("=" * 60)
    
    # Create tool instance
    tool = GoogleCalendarSchedulerTool()
    
    # Test event description
    event_description = "Team meeting with Sarah tomorrow at 2:30 PM in conference room A"
    
    print(f"📅 Event Description: {event_description}")
    print("🔄 Testing simplified workflow...")
    
    # This should create the event immediately and return success (no confirmation)
    result = tool._schedule_calendar_event(event_description)
    
    print("📝 Result:")
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    test_simplified_calendar()