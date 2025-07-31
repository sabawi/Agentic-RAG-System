"""
Google Calendar Event Scheduler Tool for FastAPI Server
Adapted from open-webui-tools with enhanced parsing and server-friendly authentication
Simplified version for server environments
"""

import os
import json
import re
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import quote

try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool

# Google Calendar API imports (check at runtime for better error handling)
GOOGLE_CALENDAR_AVAILABLE = True
try:
    import google.oauth2.credentials
    import google_auth_oauthlib.flow
    import google.auth.transport.requests
    import googleapiclient.discovery
    import googleapiclient.errors
    print("✅ Google Calendar API modules available")
except ImportError as e:
    print(f"⚠️ Google Calendar API modules not available: {e}")
    GOOGLE_CALENDAR_AVAILABLE = False


class GoogleCalendarSchedulerTool(BaseUserTool):
    """
    A comprehensive Google Calendar event scheduler with enhanced natural language parsing.
    Handles event scheduling with user confirmation workflow.
    """
    
    def __init__(self):
        super().__init__()
        self.service = None
        self.scopes = ["https://www.googleapis.com/auth/calendar"]
        self.pending_events = {}  # Store pending events for confirmation
        self.authenticated = False
        
        # Configuration
        self.credentials_path = "./credentials.json"
        self.token_path = "./token.pickle"
        self.default_timezone = "America/New_York"
        self.default_duration = 60  # minutes
    
    @property
    def name(self) -> str:
        return "google_calendar_scheduler"
    
    @property
    def description(self) -> str:
        return "Schedule Google Calendar events from natural language prompts with intelligent parsing and user confirmation. Handles complex date/time expressions, locations, and recurring events."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "event_description": {
                    "type": "string",
                    "description": "Natural language description of the event to schedule, including title, date, time, and any other details. Examples: 'Meeting with Bob tomorrow at 2 PM', 'Doctor appointment next Tuesday 10 AM', 'Weekly team standup every Monday 9 AM'"
                }
            },
            "required": ["event_description"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute calendar event scheduling from natural language description.
        """
        try:
            event_description = kwargs.get("event_description", "").strip()
            
            if not event_description:
                return {
                    "success": False,
                    "error": "Event description is required",
                    "result": None
                }
            
            # Process the calendar event (libraries are available)
            result = self._schedule_calendar_event(event_description)
            
            return {
                "success": True,
                "result": result,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Calendar scheduling error: {str(e)}",
                "result": None
            }
    
    def _schedule_calendar_event(self, event_description: str) -> str:
        """Schedule a calendar event from natural language description."""
        try:
            # Parse the event details
            event_data = self._parse_event_details(event_description)
            
            # Check authentication status
            if not self._check_authentication():
                return self._format_auth_setup_message()
            
            # AUTHENTICATE AND CREATE EVENT IMMEDIATELY
            auth_success = self._authenticate_google_calendar()
            if not auth_success:
                return self._format_auth_setup_message()
            
            # CREATE EVENT IN GOOGLE CALENDAR (IMMEDIATELY SCHEDULED)
            result = self._create_calendar_event(event_data)
            if not result["success"]:
                return f"❌ **Failed to Create Event**: {result['message']}"
            
            # Event successfully created - return success message without confirmation
            google_event_id = result["event_id"]
            google_event_link = result.get("event_link", "")
            
            # Return immediate success confirmation
            return self._format_success_confirmation(event_data, google_event_id, google_event_link)
            
        except Exception as e:
            return f"❌ **Error**: {str(e)}"
    
    
    def _parse_event_details(self, prompt: str) -> Dict[str, Any]:
        """Parse event details from natural language prompt with enhanced flexibility."""
        
        event_data = {
            "summary": "",
            "description": "",
            "date_string": "",
            "time_string": "",
            "location": "",
            "all_day": False,
            "recurrence": None,
            "parsed_datetime": None,
            "parsed_end_datetime": None
        }
        
        # Parse datetime using enhanced method
        try:
            start_dt, end_dt, date_desc, time_desc = self._parse_flexible_datetime(prompt)
            event_data["parsed_datetime"] = start_dt
            event_data["parsed_end_datetime"] = end_dt
            event_data["date_string"] = date_desc
            event_data["time_string"] = time_desc
        except Exception as e:
            # Fallback to current approach  
            now = datetime.now()
            event_data["parsed_datetime"] = now.replace(hour=9, minute=0, second=0, microsecond=0)
            event_data["parsed_end_datetime"] = event_data["parsed_datetime"] + timedelta(minutes=self.default_duration)
            event_data["date_string"] = "today"
            event_data["time_string"] = "9:00 AM"
        
        # Extract summary - everything before time/date indicators
        summary_patterns = [
            r"^(.*?)\s+(?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|at\s+\d|on\s+\w|\d{1,2}:\d{2}|\d{1,2}\s*(?:AM|PM))",
            r"^(.*?)\s+(?:next\s+\w+|\d{1,2}\/\d{1,2})",
        ]
        
        summary_found = False
        for pattern in summary_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                event_data["summary"] = match.group(1).strip()
                summary_found = True
                break
        
        if not summary_found:
            # Extract everything before common time indicators
            parts = re.split(r"\s+(?:at|on|for|from)\s+", prompt, maxsplit=1, flags=re.IGNORECASE)
            event_data["summary"] = parts[0].strip()
        
        # Clean up summary
        if event_data["summary"]:
            # Remove common scheduling words
            event_data["summary"] = re.sub(
                r"^(schedule|book|create|add|set up|plan)\s+",
                "",
                event_data["summary"],
                flags=re.IGNORECASE,
            ).strip()
        
        if not event_data["summary"]:
            event_data["summary"] = "Meeting"  # Default fallback
        
        # Extract location (optional)
        location_patterns = [
            r"(?:at|to)\s+([^,.\n]+(?:doctor|hospital|clinic|office|center|gym|restaurant))",
            r"(?:trip to|visit to|go to)\s+([^,.\n]+)",
            r"(?:at|to)\s+([A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd))",
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                event_data["location"] = match.group(1).strip()
                break
        
        # Check for all day events
        full_day_patterns = [
            r"(full day|all day|entire day)",
            r"(block.*day)",
        ]
        
        for pattern in full_day_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                event_data["all_day"] = True
                break
        
        # Check for recurrence
        recurrence_patterns = [
            (r"(daily|every day)", ["RRULE:FREQ=DAILY"]),
            (r"(weekly|every week)", ["RRULE:FREQ=WEEKLY"]),
            (r"(monthly|every month)", ["RRULE:FREQ=MONTHLY"]),
            (r"(yearly|every year)", ["RRULE:FREQ=YEARLY"]),
        ]
        
        for pattern, rule in recurrence_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                event_data["recurrence"] = rule
                break
        
        return event_data
    
    def _parse_flexible_datetime(self, prompt: str) -> Tuple[datetime, datetime, str, str]:
        """Enhanced datetime parsing with better flexibility."""
        
        now = datetime.now()
        current_year = now.year
        
        # Initialize variables
        start_datetime = None
        end_datetime = None
        date_description = ""
        time_description = ""
        
        # Enhanced time patterns
        time_patterns = [
            (r"(?:at\s+)?(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))", "12-hour with minutes"),
            (r"(?:at\s+)?(\d{1,2}\s*(?:AM|PM|am|pm))", "12-hour"),
            (r"(?:at\s+)?(\d{1,2}:\d{2})", "24-hour with minutes"),
            (r"(?:at\s+)?(\d{1,2})\s*(?:o'?clock)?(?:\s+(?:AM|PM|am|pm))?", "simple hour"),
        ]
        
        # Enhanced date patterns
        date_patterns = [
            # Relative dates
            (r"\b(today)\b", "relative", "today"),
            (r"\b(tomorrow)\b", "relative", "tomorrow"),
            # Weekdays
            (r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b", "weekday", None),
            # Next + weekday
            (r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", "next_weekday", None),
            # Month day patterns
            (r"\b([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\b", "month_day", None),
            (r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]+)\b", "day_month", None),
            # Numeric patterns
            (r"\b(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)\b", "slash_date", None),
            (r"\b(\d{1,2}-\d{1,2}(?:-\d{2,4})?)\b", "dash_date", None),
        ]
        
        # Extract time first
        extracted_time = None
        time_match = None
        for pattern, description in time_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                extracted_time = match.group(1)
                time_description = description
                time_match = match
                break
        
        # Extract date
        extracted_date = None
        date_type = None
        date_match = None
        
        for pattern, date_type, fixed_value in date_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                if fixed_value:
                    extracted_date = fixed_value
                else:
                    extracted_date = match.group(0) if date_type == "weekday" else match.groups()
                date_match = match
                break
        
        # Parse the date into a datetime object
        if date_type == "relative":
            if extracted_date == "today":
                start_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
                date_description = "today"
            elif extracted_date == "tomorrow":
                start_datetime = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                date_description = "tomorrow"
        
        elif date_type == "weekday":
            weekday_dt = self._find_next_weekday(extracted_date)
            if weekday_dt:
                start_datetime = weekday_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                date_description = f"next {extracted_date.title()}"
        
        elif date_type == "next_weekday":
            weekday = extracted_date[1] if isinstance(extracted_date, tuple) else extracted_date
            weekday_dt = self._find_next_weekday(weekday)
            if weekday_dt:
                # For "next Monday", always go to the following week
                start_datetime = (weekday_dt + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
                date_description = f"next {weekday.title()}"
        
        elif date_type == "month_day":
            try:
                month_name, day = extracted_date
                month_day_str = f"{month_name} {day}, {current_year}"
                start_datetime = datetime.strptime(month_day_str, "%B %d, %Y")
                date_description = f"{month_name} {day}"
            except (ValueError, TypeError):
                pass
        
        elif date_type == "day_month":
            try:
                day, month_name = extracted_date
                month_day_str = f"{month_name} {day}, {current_year}"
                start_datetime = datetime.strptime(month_day_str, "%B %d, %Y")
                date_description = f"{month_name} {day}"
            except (ValueError, TypeError):
                pass
        
        elif date_type == "slash_date":
            try:
                date_str = extracted_date
                if date_str.count("/") == 1:
                    date_str += f"/{current_year}"
                start_datetime = datetime.strptime(date_str, "%m/%d/%Y")
                date_description = date_str
            except ValueError:
                pass
        
        elif date_type == "dash_date":
            try:
                date_str = extracted_date
                if date_str.count("-") == 1:
                    date_str += f"-{current_year}"
                start_datetime = datetime.strptime(date_str, "%m-%d-%Y")
                date_description = date_str
            except ValueError:
                pass
        
        # If no date found, default to today
        if start_datetime is None:
            start_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_description = "today"
        
        # Parse and apply time
        if extracted_time:
            try:
                # Clean up the time string
                time_str = extracted_time.strip()
                
                # Parse different time formats
                if ":" in time_str:
                    if any(x in time_str.upper() for x in ["AM", "PM"]):
                        time_obj = datetime.strptime(time_str.upper(), "%I:%M %p")
                    else:
                        time_obj = datetime.strptime(time_str, "%H:%M")
                else:
                    # Handle cases like "1PM", "13", "1 PM"
                    time_str_clean = re.sub(r"\s+", " ", time_str)
                    if any(x in time_str_clean.upper() for x in ["AM", "PM"]):
                        time_obj = datetime.strptime(time_str_clean.upper(), "%I %p")
                    else:
                        # Assume 24-hour format or add PM if it's afternoon-ish
                        hour = int(re.search(r"\d+", time_str).group())
                        if hour <= 12 and hour >= 1:
                            time_obj = datetime.strptime(f"{hour} PM", "%I %p")
                        else:
                            time_obj = datetime.strptime(f"{hour}", "%H")
                
                start_datetime = start_datetime.replace(hour=time_obj.hour, minute=time_obj.minute)
                time_description = extracted_time
                
            except ValueError:
                # Default to 9 AM if time parsing fails
                start_datetime = start_datetime.replace(hour=9, minute=0)
                time_description = "9:00 AM (default)"
        else:
            # No time specified, default to 9 AM
            start_datetime = start_datetime.replace(hour=9, minute=0)
            time_description = "9:00 AM (default)"
        
        # Calculate end time
        end_datetime = start_datetime + timedelta(minutes=self.default_duration)
        
        return start_datetime, end_datetime, date_description, time_description
    
    def _find_next_weekday(self, weekday_name: str) -> Optional[datetime]:
        """Find the next occurrence of a specific weekday."""
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
            "mon": 0, "tue": 1, "wed": 2, "thu": 3,
            "fri": 4, "sat": 5, "sun": 6,
        }
        
        today = datetime.now()
        target_weekday = weekdays.get(weekday_name.lower())
        
        if target_weekday is None:
            return None
        
        days_ahead = target_weekday - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        return today + timedelta(days=days_ahead)
    
    def _check_authentication(self) -> bool:
        """Check if Google Calendar API is authenticated."""
        # Only require credentials.json - token.pickle will be created if needed
        return os.path.exists(self.credentials_path)
    
    def _authenticate_google_calendar(self) -> bool:
        """Authenticate with Google Calendar API using existing credentials."""
        try:
            # Try importing Google modules at runtime
            try:
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                from googleapiclient.discovery import build
                print("✅ Google API modules imported successfully")
            except ImportError as import_error:
                print(f"❌ Google API import error: {import_error}")
                return False
            
            creds = None
            
            # Load existing token if available
            if os.path.exists(self.token_path):
                print(f"✅ Found token file: {self.token_path}")
                with open(self.token_path, "rb") as token:
                    creds = pickle.load(token)
                print(f"✅ Loaded credentials from token file")
            else:
                print(f"⚠️ Token file not found: {self.token_path}")
                creds = None
            
            # Check credentials validity and refresh/create if needed
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        print("🔄 Attempting to refresh expired credentials...")
                        creds.refresh(Request())
                        # Save refreshed credentials
                        with open(self.token_path, "wb") as token:
                            pickle.dump(creds, token)
                        print("✅ Credentials refreshed and saved")
                    except Exception as refresh_error:
                        print(f"❌ Token refresh failed: {refresh_error}")
                        print("🔄 Will attempt to create new credentials...")
                        creds = None
                
                # If refresh failed or no refresh token, create new credentials
                if not creds:
                    if not os.path.exists(self.credentials_path):
                        print(f"❌ Credentials file not found: {self.credentials_path}")
                        return False
                    
                    print("🔄 Automatically generating new OAuth token...")
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    
                    try:
                        # Create the flow using the client secrets file
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, self.scopes
                        )
                        
                        # For server environment, use run_local_server with dynamic port
                        print("🌐 Starting local OAuth server...")
                        creds = flow.run_local_server(
                            port=0,  # Use dynamic port to avoid conflicts
                            access_type='offline',
                            include_granted_scopes='true'
                        )
                        
                        # Save the credentials for future use
                        with open(self.token_path, 'wb') as token:
                            pickle.dump(creds, token)
                        
                        print("✅ New OAuth token generated and saved successfully!")
                        
                    except Exception as oauth_error:
                        print(f"❌ OAuth flow failed: {oauth_error}")
                        # Fallback to manual instructions
                        return False
            else:
                print("✅ Credentials are valid")
            
            # Build the service
            print("🔨 Building Google Calendar service...")
            self.service = build("calendar", "v3", credentials=creds)
            self.authenticated = True
            print("✅ Google Calendar service authenticated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False
    
    def _format_auth_setup_message(self) -> str:
        """Format authentication setup instructions."""
        return f"""🔐 **Google Calendar Authentication Required**

To use the Google Calendar scheduler, you need to set up authentication:

**Setup Steps:**

1. **Get Google Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials (Desktop Application)
   - Download the JSON file as 'credentials.json'

2. **File Locations:**
   - Place credentials.json at: `{self.credentials_path}`
   - Token will be saved at: `{self.token_path}`

3. **Initial Authentication:**
   - Complete OAuth flow (requires browser access)
   - Token will be saved for future use

**Current Status:** Not authenticated

**Alternative:** For now, I can provide a Google Calendar link you can use to manually create the event."""
    
    def _format_success_confirmation(self, event_data: Dict[str, Any], google_event_id: str, google_event_link: str) -> str:
        """Create a success message for completed calendar event."""
        
        # Format the datetime nicely
        if event_data["parsed_datetime"]:
            date_formatted = event_data["parsed_datetime"].strftime("%A, %B %d")
            if event_data["all_day"]:
                time_formatted = "all day"
            else:
                time_formatted = event_data["parsed_datetime"].strftime("%I:%M %p").lstrip("0")
        else:
            date_formatted = event_data["date_string"]
            time_formatted = event_data["time_string"]
        
        # Create success message
        confirmation = f"✅ **EVENT SUCCESSFULLY SCHEDULED!** ✅\\n\\n"
        confirmation += f"**📅 Event Details:**\\n"
        confirmation += f"• **Title:** {event_data['summary']}\\n"
        confirmation += f"• **Date:** {date_formatted}\\n"
        confirmation += f"• **Time:** {time_formatted}\\n"
        
        if event_data["location"]:
            confirmation += f"• **Location:** {event_data['location']}\\n"
        
        confirmation += f"\\n🎯 **Event Status:** CONFIRMED & LIVE\\n"
        confirmation += f"📍 **Google Event ID:** {google_event_id}\\n"
        confirmation += f"🔗 **View in Google Calendar:** {google_event_link}\\n\\n"
        confirmation += f"🎉 **Your event is now active in your Google Calendar!**"
        
        return confirmation

    def _format_booking_confirmation(self, event_data: Dict[str, Any], event_token: str, google_result: Dict[str, Any]) -> str:
        """Create a user-friendly confirmation message."""
        
        # Format the datetime nicely
        if event_data["parsed_datetime"]:
            date_formatted = event_data["parsed_datetime"].strftime("%A, %B %d")
            if event_data["all_day"]:
                time_formatted = "all day"
            else:
                time_formatted = event_data["parsed_datetime"].strftime("%I:%M %p").lstrip("0")
        else:
            date_formatted = event_data["date_string"]
            time_formatted = event_data["time_string"]
        
        # Generate calendar link for manual creation
        calendar_link = self._generate_calendar_link(event_data)
        
        # Create booking confirmation message
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        google_event_id = google_result.get("event_id", "N/A")
        google_event_link = google_result.get("event_link", "N/A")
        
        confirmation = f"✅ **EVENT CREATED IN GOOGLE CALENDAR** ✅\n\n"
        confirmation += f"**📅 Event Details:**\n"
        confirmation += f"• **Title:** {event_data['summary']}\n"
        confirmation += f"• **Date:** {date_formatted}\n"
        confirmation += f"• **Time:** {time_formatted}\n"
        
        if event_data["location"]:
            confirmation += f"• **Location:** {event_data['location']}\n"
        
        confirmation += f"\n📍 **Event Status:**\n"
        confirmation += f"• **Status:** CREATED (awaiting confirmation)\n"
        confirmation += f"• **Google Event ID:** {google_event_id}\n"
        confirmation += f"• **Google Event Link:** {google_event_link}\n"
        
        # CRITICAL: Instructions for primary LLM to pass information verbatim
        confirmation += f"\n" + "="*60 + "\n"
        confirmation += f"🚨 **CRITICAL INSTRUCTIONS FOR PRIMARY LLM** 🚨\n"
        confirmation += f"="*60 + "\n"
        confirmation += f"PASS THIS MESSAGE TO THE USER EXACTLY AS WRITTEN:\n\n"
        
        confirmation += f"🎯 **YOUR EVENT HAS BEEN CREATED!**\n\n"
        confirmation += f"📅 **'{event_data['summary']}'** is now in your Google Calendar\n"
        confirmation += f"📍 **When:** {date_formatted} at {time_formatted}\n"
        if event_data["location"]:
            confirmation += f"📍 **Where:** {event_data['location']}\n"
        
        confirmation += f"\n🔗 **View in Google Calendar:** {google_event_link}\n\n"
        confirmation += f"⚠️ **IMPORTANT:** To CONFIRM this event, simply reply with:\n"
        confirmation += f"• **'yes'** or **'confirm'** or **'book it'**\n\n"
        confirmation += f"🎫 **Booking Token:** {event_token}\n\n"
        confirmation += f"🚨 **The event is created but needs your confirmation to be finalized!**\n"
        
        confirmation += f"\n" + "="*60
        
        return confirmation
    
    def _generate_calendar_link(self, event_data: Dict[str, Any]) -> str:
        """Generate a clickable Google Calendar link."""
        try:
            base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
            
            # Use parsed datetime
            if event_data["parsed_datetime"] and event_data["parsed_end_datetime"]:
                start_dt = event_data["parsed_datetime"]
                end_dt = event_data["parsed_end_datetime"]
            else:
                # Fallback
                now = datetime.now()
                start_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
                end_dt = start_dt + timedelta(minutes=self.default_duration)
            
            if event_data["all_day"]:
                dates = f"{start_dt.strftime('%Y%m%d')}/{end_dt.strftime('%Y%m%d')}"
            else:
                dates = f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"
            
            params = {
                "text": event_data["summary"],
                "dates": dates,
                "location": event_data["location"],
                "details": event_data["description"],
            }
            
            # Build URL
            url_parts = [base_url]
            for key, value in params.items():
                if value:
                    url_parts.append(f"{key}={quote(str(value))}")
            
            return "&".join(url_parts)
            
        except Exception as e:
            return f"Error generating calendar link: {e}"
    
    def _create_calendar_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create event in Google Calendar using API."""
        try:
            if not self.authenticated or not self.service:
                return {
                    "success": False,
                    "message": "❌ Not authenticated with Google Calendar",
                    "event_link": None
                }
            
            # Use parsed datetime
            if event_data["parsed_datetime"] and event_data["parsed_end_datetime"]:
                start_dt = event_data["parsed_datetime"]
                end_dt = event_data["parsed_end_datetime"]
            else:
                # Fallback
                now = datetime.now()
                start_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
                end_dt = start_dt + timedelta(minutes=self.default_duration)
            
            # Prepare event object
            event = {
                "summary": event_data["summary"],
                "location": event_data["location"],
                "description": event_data["description"],
            }
            
            # Set start and end times
            if event_data["all_day"]:
                event["start"] = {"date": start_dt.strftime("%Y-%m-%d")}
                event["end"] = {"date": end_dt.strftime("%Y-%m-%d")}
            else:
                event["start"] = {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": self.default_timezone,
                }
                event["end"] = {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": self.default_timezone,
                }
            
            # Add recurrence if specified
            if event_data["recurrence"]:
                event["recurrence"] = event_data["recurrence"]
            
            # Create the event
            created_event = self.service.events().insert(calendarId="primary", body=event).execute()
            
            return {
                "success": True,
                "event_id": created_event["id"],
                "event_link": created_event.get("htmlLink", ""),
                "message": f"✅ Event '{event_data['summary']}' scheduled successfully!",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ Failed to create calendar event: {e}",
                "event_link": None
            }