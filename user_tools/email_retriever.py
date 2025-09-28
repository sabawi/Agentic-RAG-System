"""
Email Retriever Tool for FastAPI Server
Natural language email search and retrieval with multi-provider support
Enables queries like "List my unread emails from gmail" and "Show emails from Reema about university"
"""

import os
import re
import logging
import html
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool

try:
    from ..utils.email_library_adapter import EmailLibraryAdapter, EmailSearchCriteria
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from utils.email_library_adapter import EmailLibraryAdapter, EmailSearchCriteria


class EmailRetrieverTool(BaseUserTool):
    """
    Professional email retrieval tool with natural language query support.

    Features:
    - Natural language email search queries
    - Multi-provider support (Gmail, Outlook, Yahoo, iCloud, custom)
    - Smart sender/subject/content filtering
    - Date range and status filtering (read/unread)
    - Comprehensive email information extraction
    - Secure configuration management
    """

    def __init__(self):
        super().__init__()
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'llm_config.yaml')
        self.adapter = None
        self._initialize_adapter()

    def _initialize_adapter(self):
        """Initialize EmailLibraryAdapter with server configuration"""
        try:
            logger.info(f"🚀 Initializing EmailRetrieverTool with config: {self.config_path}")

            # Check if config file exists
            if not os.path.exists(self.config_path):
                logger.error(f"❌ Configuration file not found: {self.config_path}")
                self.adapter = None
                return

            logger.debug("📁 Configuration file found, creating adapter...")
            self.adapter = EmailLibraryAdapter(self.config_path)

            providers = self.adapter.list_providers()
            default_provider = self.adapter.get_default_provider()

            logger.info(f"✅ EmailRetrieverTool initialized successfully")
            logger.info(f"📧 Available providers: {providers} (default: {default_provider})")
            logger.info(f"🔧 Configuration source: {self.config_path}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize EmailLibraryAdapter: {str(e)}")
            logger.error(f"🔍 TROUBLESHOOTING: Check config file {self.config_path} and email section")
            self.adapter = None

    @property
    def name(self) -> str:
        return "email_retriever"

    @property
    def description(self) -> str:
        return ("Retrieve emails using explicit search parameters. The LLM should map natural language requests to specific parameter values.")

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Email account to search. Use 'gmail_primary' for personal Gmail, 'gmail_work' for work Gmail, 'outlook_personal', 'outlook_work', 'yahoo_personal', 'icloud_personal'. Default is 'gmail_primary'.",
                    "enum": ["gmail_primary", "gmail_work", "outlook_personal", "outlook_work", "yahoo_personal", "icloud_personal", "custom_server"],
                    "default": "gmail_primary"
                },
                "lookback_days": {
                    "type": "integer",
                    "description": "How many days back to search from today. Examples: 1='today only', 2='yesterday and today', 7='last week', 30='last month'. For 'last N emails' requests, use default 30 days (emails will be sorted by date to get most recent).",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 30
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of emails to return. For 'last 10 emails' use 10, for 'recent 5 emails' use 5. Default is 20.",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20
                },
                "sender_keyword": {
                    "type": "string",
                    "description": "Filter by sender name or company. Examples: 'Apple', 'John Smith', 'support', 'amazon'. Case-insensitive partial matching. Leave empty for all senders."
                },
                "subject_keyword": {
                    "type": "string",
                    "description": "Filter by subject line content. Examples: 'meeting', 'invoice', 'reminder', 'shipment'. Case-insensitive partial matching. Leave empty for all subjects."
                },
                "body_keyword": {
                    "type": "string",
                    "description": "Filter by email body content. Examples: 'billing', 'payment', 'order', 'password'. Case-insensitive partial matching. Leave empty for all content."
                },
                "include_read": {
                    "type": "boolean",
                    "description": "Include read emails in results. Use True for 'all emails' or 'last N emails', False for 'unread emails only'. Default is True.",
                    "default": True
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute email retrieval using explicit parameters (no complex NLP parsing).
        The tool-calling LLM should map natural language to specific parameters.

        Args:
            provider (str, optional): Email provider to use
            lookback_days (int, optional): Days back to search (default 30)
            max_results (int, optional): Maximum results to return (default 20)
            sender_keyword (str, optional): Filter by sender name/email
            subject_keyword (str, optional): Filter by subject content
            body_keyword (str, optional): Filter by body content
            include_read (bool, optional): Include read emails (default True)

        Returns:
            Dict containing success status, results, and metadata
        """
        import time
        start_time = time.time()

        try:
            logger.info(f"🚀 EMAIL RETRIEVAL STARTED - Parameters: {dict(kwargs)}")

            # Check adapter initialization
            if not self.adapter:
                logger.error("❌ Email adapter not initialized")
                return {
                    "success": False,
                    "error": "Email adapter not initialized",
                    "results": []
                }

            # Extract and validate parameters
            provider = kwargs.get("provider")
            if not provider:
                provider = self.adapter.get_default_provider()
                logger.info(f"🔧 Using default provider: {provider}")

            if not self.adapter.validate_provider(provider):
                available_providers = self.adapter.list_providers()
                logger.error(f"❌ Invalid provider '{provider}' - Available providers: {available_providers}")
                return {
                    "success": False,
                    "error": f"Invalid provider '{provider}'. Available: {available_providers}",
                    "results": []
                }

            # Build search criteria from explicit parameters
            lookback_days = kwargs.get("lookback_days", 30)
            lookback_days = min(max(1, lookback_days), 365)  # Clamp between 1-365 days

            max_results = kwargs.get("max_results", 20)
            max_results = min(max(1, max_results), 100)  # Clamp between 1-100

            include_read = kwargs.get("include_read", True)
            sender_keyword = kwargs.get("sender_keyword")
            subject_keyword = kwargs.get("subject_keyword")
            body_keyword = kwargs.get("body_keyword")

            # Create search criteria
            search_criteria = EmailSearchCriteria(
                provider=provider,
                from_sender=sender_keyword,
                subject_contains=subject_keyword,
                content_contains=body_keyword,
                days_back=lookback_days,
                max_results=max_results,
                include_read=include_read
            )

            logger.info(f"📋 SEARCH CRITERIA - Provider: {provider}, Sender: '{sender_keyword}', Subject: '{subject_keyword}', Body: '{body_keyword}', Days: {lookback_days}, Max: {max_results}, Include Read: {include_read}")

            # Perform email search
            logger.info(f"🔍 Initiating email search...")
            search_start = time.time()

            emails = self.adapter.retrieve_emails(search_criteria)

            search_duration = time.time() - search_start
            logger.info(f"📧 Email search completed in {search_duration:.2f}s - Retrieved {len(emails) if emails else 0} emails")

            # Process and format results
            logger.debug("📝 Formatting email results...")
            format_start = time.time()
            formatted_results = self._format_email_results(emails)
            format_duration = time.time() - format_start

            total_duration = time.time() - start_time

            logger.info(f"✅ EMAIL RETRIEVAL SUCCESS - Provider: {provider}, Found: {len(formatted_results)} emails, Total Time: {total_duration:.2f}s (Search: {search_duration:.2f}s, Format: {format_duration:.3f}s)")

            return {
                "success": True,
                "results": formatted_results,
                "metadata": {
                    "provider": provider,
                    "total_found": len(formatted_results),
                    "performance": {
                        "total_duration": round(total_duration, 3),
                        "search_duration": round(search_duration, 3),
                        "format_duration": round(format_duration, 3)
                    },
                    "search_criteria": {
                        "sender_keyword": sender_keyword,
                        "subject_keyword": subject_keyword,
                        "body_keyword": body_keyword,
                        "include_read": include_read,
                        "lookback_days": lookback_days,
                        "max_results": max_results
                    }
                }
            }

        except Exception as e:
            total_duration = time.time() - start_time
            logger.error(f"❌ EMAIL RETRIEVAL FAILED - Parameters: {dict(kwargs)}, Duration: {total_duration:.2f}s, Error: {str(e)}")
            logger.error(f"🔍 TROUBLESHOOTING INFO - Adapter Status: {'OK' if self.adapter else 'NULL'}, Available Providers: {self.adapter.list_providers() if self.adapter else 'N/A'}")
            return {
                "success": False,
                "error": f"Email retrieval failed: {str(e)}",
                "results": [],
                "debug_info": {
                    "duration": round(total_duration, 3),
                    "adapter_status": "OK" if self.adapter else "NULL",
                    "parameters": dict(kwargs)
                }
            }

    def _parse_natural_language_query(self, query: str, params: Dict[str, Any]) -> EmailSearchCriteria:
        """
        Enhanced natural language query parser with sophisticated pattern recognition

        Examples:
        - "List my unread email from gmail" → unread_only=True, provider=gmail_primary
        - "emails from Reema Sabawi about university classes" → sender=Reema Sabawi, subject_contains=university classes
        - "billing notifications from Apple in last 7 days" → sender=Apple, content_contains=billing, days_back=7
        - "all emails from john regarding meeting yesterday" → sender=john, subject_contains=meeting, days_back=2
        """
        # Start with default provider (will be determined later)
        criteria = EmailSearchCriteria(provider="gmail_primary")
        query_lower = query.lower()
        original_query = query  # Keep original for case-sensitive matching

        # Enhanced provider detection with more patterns
        provider_patterns = {
            r'\bgmail\b(?!\s+work)': 'gmail_primary',
            r'\bgmail\s+work\b': 'gmail_work',
            r'\bwork\s+gmail\b': 'gmail_work',
            r'\boutlook\b(?!\s+work)': 'outlook_personal',
            r'\boutlook\s+work\b': 'outlook_work',
            r'\bwork\s+outlook\b': 'outlook_work',
            r'\byahoo\b': 'yahoo_personal',
            r'\bicloud\b': 'icloud_personal',
            r'\bcustom\b': 'custom_server'
        }

        for pattern, provider in provider_patterns.items():
            if re.search(pattern, query_lower):
                criteria.provider = provider
                break

        # Enhanced sender detection with multiple patterns
        sender_patterns = [
            # "from [email]" - email addresses (highest priority)
            r'from\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            # "from [Full Name]" - handles names like "Reema Sabawi"
            r'from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s+(?:about|regarding|in|last|from))',
            # "emails from [name]" with word boundaries - but exclude email providers
            r'emails?\s+from\s+(?!(?:' + '|'.join(['gmail', 'outlook', 'yahoo', 'icloud', 'hotmail', 'aol', 'protonmail']) + r')\b)([A-Za-z][A-Za-z0-9.\s@_-]+?)(?:\s+(?:about|regarding|in|last|from|$))',
            # "[Company] [Product] notifications" - like "Amazon Prime notifications"
            r'([A-Z][a-z]+)\s+[A-Z][a-z]+\s+(?:notifications?|emails?|messages?|alerts?)',
            # "[Company] emails" or "[Company] notifications"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:emails?|notifications?|messages?|alerts?)(?!\s+from)',
            # "from [single name/company]" or "from [Multi Word Company]" - but exclude email providers
            r'from\s+(?!(?:' + '|'.join(['gmail', 'outlook', 'yahoo', 'icloud', 'hotmail', 'aol', 'protonmail']) + r')\b)([A-Za-z][A-Za-z0-9.\s_-]+?)(?:\s+(?:about|regarding|in|last|yesterday|today|$)|$)',
        ]

        for pattern in sender_patterns:
            match = re.search(pattern, original_query)
            if match:
                sender = match.group(1).strip()
                # Clean up sender (remove trailing punctuation)
                sender = re.sub(r'[,\s]+$', '', sender)

                if len(sender) > 1:  # Avoid single character matches
                    # Exclude time-related words from being treated as sender names
                    time_words = {'today', 'yesterday', 'tomorrow', 'now', 'recent', 'lately', 'currently', 'this', 'last', 'next', 'morning', 'afternoon', 'evening', 'night'}
                    if sender.lower() not in time_words:
                        # Apply fuzzy matching for better company recognition
                        normalized_sender = self._fuzzy_match_companies(sender)
                        logger.info(f"🔍 DEBUG: Setting from_sender to: {repr(normalized_sender)} (original: {repr(sender)})")
                        criteria.from_sender = normalized_sender
                        break
                    else:
                        logger.info(f"🔍 DEBUG: Skipping time word as sender: {repr(sender)}")

        # Extract key terms/topics from the query for comprehensive search
        # This approach searches ALL fields (sender, subject, content) for the key terms
        topic_patterns = [
            # "about [topic]" or "regarding [topic]"
            r'(?:about|regarding)\s+([a-zA-Z0-9\s,.-]+?)(?:\s+(?:in|from|last|yesterday|today|$))',
            # "emails from [company/topic]" - extract the company/topic part
            r'emails?\s+from\s+([A-Za-z][A-Za-z0-9\s]+?)(?:\s+(?:in|last|yesterday|today|$))',
            # "subject: [topic]"
            r'subject:?\s*([a-zA-Z0-9\s,.-]+?)(?:\s+(?:in|from|last|yesterday|today|$))',
            # Extract topics after common prepositions
            r'(?:concerning|related\s+to|with\s+subject)\s+([a-zA-Z0-9\s,.-]+?)(?:\s+(?:in|from|last|yesterday|today|$))',
            # "[topic] emails" pattern
            r'([a-zA-Z]+)\s+emails?\b'
        ]

        # Words to exclude from topic extraction
        excluded_words = {'list', 'show', 'get', 'find', 'display', 'all', 'my', 'gmail', 'outlook', 'yahoo', 'icloud'}

        for pattern in topic_patterns:
            match = re.search(pattern, query_lower)
            if match:
                topic = match.group(1).strip()
                topic = re.sub(r'[,\s]+$', '', topic)  # Clean trailing punctuation

                # Skip if this is a command word or very short
                if len(topic) > 2 and topic.lower() not in excluded_words:
                    logger.info(f"🔍 DEBUG: Extracted topic for comprehensive search: {repr(topic)}")

                    # Split topic into individual terms for broader matching
                    # This helps match "GAULT Toyota" against emails from "Toyota" OR containing "GAULT"
                    terms = topic.split()
                    if len(terms) > 1:
                        # Use the most specific term (usually the company name)
                        # For "GAULT Toyota", prioritize "Toyota" as it's the actual company
                        main_term = None
                        for term in terms:
                            if term.lower() in ['toyota', 'apple', 'google', 'microsoft', 'amazon', 'tesla', 'ford', 'gm']:
                                main_term = term
                                break
                        if not main_term:
                            main_term = terms[-1]  # Use last term as default
                        logger.info(f"🔍 DEBUG: Using main term for search: {repr(main_term)}")
                        search_term = main_term
                    else:
                        search_term = topic

                    # Search ALL fields for the term - this is much more reliable!
                    # Make search case-insensitive and flexible
                    search_term_lower = search_term.lower()
                    criteria.from_sender = search_term_lower  # Search sender field
                    criteria.subject_contains = search_term_lower  # Search subject field
                    criteria.content_contains = search_term_lower  # Search email body
                    logger.info(f"🔍 DEBUG: Set ALL search fields to: {repr(search_term_lower)}")

                    # Also try a more flexible approach - search only in sender field first
                    # This matches the successful pattern we saw in logs
                    logger.info(f"🔍 DEBUG: Alternative - trying sender-only search for better matching")
                    break

        # Enhanced content detection with company/service recognition
        content_patterns = {
            # Billing and financial
            'billing': r'\b(?:billing|invoice|payment|charge|bill|receipt|transaction)\b',
            'payments': r'\b(?:payments?|pay|paid|billing|invoice|transaction|financial)\b',
            'bank': r'\b(?:bank|banking|account|statement|balance|transfer)\b',

            # Notifications and alerts
            'notification': r'\b(?:notifications?|alert|notice|reminder|update|announcement)\b',
            'security': r'\b(?:security|login|password|access|authentication|2fa|two.factor)\b',

            # Work and business
            'meeting': r'\b(?:meeting|appointment|call|conference|zoom|teams|schedule)\b',
            'work': r'\b(?:work|office|business|project|deadline|task)\b',

            # Education
            'university': r'\b(?:university|college|school|academic|class|course|semester|grade|exam)\b',
            'assignment': r'\b(?:assignment|homework|project|essay|report|paper|submission)\b',
            'education': r'\b(?:education|learning|study|lecture|professor|teacher|student)\b',

            # Shopping and orders
            'order': r'\b(?:order|shipping|delivery|package|tracking|shipment)\b',
            'shopping': r'\b(?:purchase|buy|bought|cart|checkout|product|item)\b',

            # Social and personal
            'social': r'\b(?:facebook|twitter|instagram|linkedin|social|friend|family)\b',
            'personal': r'\b(?:personal|private|family|friend|birthday|holiday|vacation)\b'
        }

        for category, pattern in content_patterns.items():
            if re.search(pattern, query_lower):
                if not criteria.subject_contains:
                    criteria.subject_contains = category
                else:
                    criteria.content_contains = category
                break

        # Enhanced time detection with smart date parsing
        time_patterns = [
            # Specific days
            (r'\btoday\b', 1),
            (r'\byesterday\b', 2),
            (r'\blast\s+(\d+)\s+days?\b', lambda m: int(m.group(1))),
            (r'\bin\s+(?:the\s+)?last\s+(\d+)\s+days?\b', lambda m: int(m.group(1))),

            # Weeks
            (r'\blast\s+week\b', 7),
            (r'\bthis\s+week\b', 7),
            (r'\blast\s+(\d+)\s+weeks?\b', lambda m: int(m.group(1)) * 7),
            (r'\bpast\s+week\b', 7),

            # Months
            (r'\blast\s+month\b', 30),
            (r'\bthis\s+month\b', 30),
            (r'\blast\s+(\d+)\s+months?\b', lambda m: int(m.group(1)) * 30),
            (r'\bpast\s+month\b', 30),

            # Specific month names (approximate days back from current date)
            (r'\bjanuary\b', 30),  # This is approximate - could be enhanced
            (r'\bfebruary\b', 60),
            (r'\bmarch\b', 90),
            (r'\bapril\b', 120),
            (r'\bmay\b', 150),
            (r'\bjune\b', 180),
            (r'\bjuly\b', 210),
            (r'\baugust\b', 240),
            (r'\bseptember\b', 270),
            (r'\boctober\b', 300),
            (r'\bnovember\b', 330),
            (r'\bdecember\b', 360),

            # Common time periods
            (r'\brecent(?:ly)?\b', 7),
            (r'\blately\b', 14),
            (r'\blong\s+time\s+ago\b', 365),
            (r'\bwhile\s+ago\b', 60),

            # Relative time periods
            (r'\bfew\s+days?\s+ago\b', 5),
            (r'\bcouple\s+days?\s+ago\b', 3),
            (r'\bfew\s+weeks?\s+ago\b', 21),  # 3 weeks
            (r'\bcouple\s+weeks?\s+ago\b', 14),  # 2 weeks
        ]

        # Try to match time patterns
        for pattern, days_value in time_patterns:
            match = re.search(pattern, query_lower)
            if match:
                if callable(days_value):
                    try:
                        calculated_days = days_value(match)
                        # Clamp to reasonable limits
                        criteria.days_back = min(max(1, calculated_days), 365)
                    except (ValueError, AttributeError):
                        criteria.days_back = 7  # Default fallback
                else:
                    criteria.days_back = days_value
                break

        # Smart date parsing for specific dates (basic implementation)
        # Look for patterns like "since January 1", "after March 15", etc.
        date_patterns = [
            r'\bsince\s+([a-zA-Z]+)\s+(\d{1,2})\b',  # "since March 15"
            r'\bafter\s+([a-zA-Z]+)\s+(\d{1,2})\b',  # "after January 1"
            r'\bfrom\s+([a-zA-Z]+)\s+(\d{1,2})\b',   # "from December 1"
        ]

        for pattern in date_patterns:
            match = re.search(pattern, query_lower)
            if match:
                month_name = match.group(1)
                # Simple month name to days back mapping (approximate)
                month_mapping = {
                    'january': 30, 'february': 60, 'march': 90, 'april': 120,
                    'may': 150, 'june': 180, 'july': 210, 'august': 240,
                    'september': 270, 'october': 300, 'november': 330, 'december': 360
                }
                if month_name in month_mapping:
                    criteria.days_back = month_mapping[month_name]
                    break

        # Enhanced status detection
        status_patterns = [
            (r'\bunread\b', False),  # include_read = False for unread only
            (r'\bnew\b', False),
            (r'\bunseen\b', False),
            (r'\bread\b', True),     # include_read = True for read emails
            (r'\ball\s+emails?\b', True),  # include both read and unread
        ]

        for pattern, include_read in status_patterns:
            if re.search(pattern, query_lower):
                criteria.include_read = include_read
                break
        else:
            # Default: include both read and unread
            criteria.include_read = True

        return criteria

    def _fuzzy_match_companies(self, sender_text: str) -> str:
        """
        Apply fuzzy matching for common company/service name variations

        Args:
            sender_text: The extracted sender text

        Returns:
            Normalized sender name for better matching
        """
        if not sender_text:
            return sender_text

        sender_lower = sender_text.lower()

        # Common company name variations and their normalized forms
        company_mappings = {
            # Apple variations
            'apple': ['apple', 'apple inc', 'apple.com', 'itunes', 'app store', 'icloud'],

            # Google variations
            'google': ['google', 'gmail', 'google.com', 'youtube', 'google play', 'google workspace'],

            # Microsoft variations
            'microsoft': ['microsoft', 'outlook', 'outlook.com', 'office', 'office365', 'teams'],

            # Amazon variations
            'amazon': ['amazon', 'amazon.com', 'aws', 'prime', 'kindle'],

            # Social media
            'facebook': ['facebook', 'meta', 'fb.com', 'instagram'],
            'twitter': ['twitter', 'x.com', 'twitter.com'],
            'linkedin': ['linkedin', 'linkedin.com'],

            # Financial services
            'paypal': ['paypal', 'paypal.com'],
            'stripe': ['stripe', 'stripe.com'],

            # Universities (common patterns)
            'university': ['university', 'college', 'edu', '.edu'],

            # Generic service patterns
            'support': ['support', 'customer service', 'help', 'noreply', 'no-reply'],
            'billing': ['billing', 'invoices', 'accounting', 'payments']
        }

        # Check for exact or partial matches
        for normalized_name, variations in company_mappings.items():
            for variation in variations:
                if variation in sender_lower:
                    return normalized_name

        # Handle email domains (extract company from email)
        if '@' in sender_text:
            domain_match = re.search(r'@([^.]+)', sender_text.lower())
            if domain_match:
                domain = domain_match.group(1)
                # Check if domain matches any company variations
                for normalized_name, variations in company_mappings.items():
                    if domain in variations or any(var in domain for var in variations):
                        return normalized_name

        return sender_text

    def _extract_named_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract named entities like people names, companies, and locations from query

        Args:
            query: The search query

        Returns:
            Dict with entity types and their values
        """
        entities = {
            'persons': [],
            'companies': [],
            'locations': []
        }

        # Person name patterns (capitalized words that could be names)
        person_patterns = [
            # Full names: "John Smith", "Reema Sabawi"
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
            # Single names in context: "from John", "by Sarah"
            r'(?:from|by|to)\s+([A-Z][a-z]+)\b'
        ]

        for pattern in person_patterns:
            matches = re.findall(pattern, query)
            entities['persons'].extend(matches)

        # Company patterns (often appear with certain keywords)
        company_patterns = [
            # "[Company] notifications/emails"
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s+(?:notifications?|emails?|messages?|alerts?)\b',
            # "from [Company]" where Company is capitalized
            r'from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\b'
        ]

        for pattern in company_patterns:
            matches = re.findall(pattern, query)
            entities['companies'].extend(matches)

        # Remove duplicates and clean up
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))

        return entities

    def _html_to_clean_text(self, html_content: str) -> str:
        """
        Convert HTML email content to clean, formatted text for better summarization.
        Adapted from PDF generator tool's _html_to_structured_text function.

        Args:
            html_content (str): Raw HTML content from email body

        Returns:
            str: Clean, formatted text suitable for LLM summarization
        """
        if not html_content or not html_content.strip():
            return ""

        # Remove HTML comments and CDATA sections
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<!\[CDATA\[.*?\]\]>', '', html_content, flags=re.DOTALL)

        # Remove unwanted email-specific tags and their content
        unwanted_tags = ['style', 'script', 'meta', 'link', 'title']
        for tag in unwanted_tags:
            html_content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', html_content, flags=re.IGNORECASE | re.DOTALL)

        # Convert HTML elements to structured text (email-optimized)
        conversions = [
            # Headers (keep simple for emails)
            (r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'**\1**\n'),

            # Paragraphs (add spacing)
            (r'<p[^>]*>(.*?)</p>', r'\1\n\n'),
            (r'<div[^>]*>(.*?)</div>', r'\1\n'),

            # Line breaks
            (r'<br[^>]*/?>', '\n'),

            # Bold and italic (preserve formatting)
            (r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**'),
            (r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*'),

            # Links (extract text and show URL if different)
            (r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'\2 (\1)'),

            # Lists (email-friendly format)
            (r'<ul[^>]*>', '\n'),
            (r'</ul>', '\n'),
            (r'<ol[^>]*>', '\n'),
            (r'</ol>', '\n'),
            (r'<li[^>]*>(.*?)</li>', r'• \1\n'),

            # Tables (simplified for email)
            (r'<table[^>]*>', '\n--- Table ---\n'),
            (r'</table>', '\n--- End Table ---\n'),
            (r'<tr[^>]*>', ''),
            (r'</tr>', '\n'),
            (r'<t[hd][^>]*>(.*?)</t[hd]>', r'\1 | '),

            # Blockquotes
            (r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1\n'),

            # Image alt text (preserve for context)
            (r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*>', r'[Image: \1]'),
            (r'<img[^>]*>', '[Image]'),

            # Span and other inline elements (keep content only)
            (r'<span[^>]*>(.*?)</span>', r'\1'),
            (r'<font[^>]*>(.*?)</font>', r'\1'),
        ]

        # Apply all conversions
        for pattern, replacement in conversions:
            html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE | re.DOTALL)

        # Remove any remaining HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)

        # Decode HTML entities (e.g., &nbsp;, &amp;, etc.)
        html_content = html.unescape(html_content)

        # Clean up whitespace and formatting
        # Remove multiple consecutive newlines
        html_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', html_content)
        # Remove multiple spaces
        html_content = re.sub(r' {2,}', ' ', html_content)
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in html_content.split('\n')]
        html_content = '\n'.join(lines)

        return html_content.strip()

    def _format_email_results(self, emails: List[Any]) -> List[Dict[str, Any]]:
        """
        Format email results for consistent output

        Args:
            emails: List of email objects from email library

        Returns:
            List of formatted email dictionaries
        """
        formatted = []

        for email in emails:
            try:
                # Handle different email object types/formats
                if hasattr(email, '__dict__'):
                    email_dict = email.__dict__
                elif isinstance(email, dict):
                    email_dict = email
                else:
                    # Try to convert to dict
                    email_dict = vars(email) if hasattr(email, '__dict__') else {}

                # Get body content with intelligent HTML cleaning
                body_text = email_dict.get("body_text", "")
                body_html = email_dict.get("body_html", "")
                fallback_body = email_dict.get("body") or email_dict.get("content", "")

                # Determine the best body content and clean if needed
                if body_text:
                    # Plain text is preferred - use as-is
                    clean_body_content = body_text
                elif body_html:
                    # HTML content - convert to clean text
                    clean_body_content = self._html_to_clean_text(body_html)
                    logger.debug(f"Converted HTML email body to clean text: {len(body_html)} chars -> {len(clean_body_content)} chars")
                elif fallback_body:
                    # Check if fallback content is HTML
                    if '<' in fallback_body and '>' in fallback_body:
                        # Looks like HTML - clean it
                        clean_body_content = self._html_to_clean_text(fallback_body)
                        logger.debug(f"Converted fallback HTML content to clean text")
                    else:
                        # Plain text fallback
                        clean_body_content = fallback_body
                else:
                    clean_body_content = ""

                formatted_email = {
                    "subject": email_dict.get("subject", "No Subject"),
                    "sender": email_dict.get("sender", email_dict.get("from", "Unknown Sender")),
                    "date": self._format_date(email_dict.get("date", email_dict.get("received_date"))),
                    "is_read": email_dict.get("is_read", True),
                    "preview": self._get_email_preview(clean_body_content),
                    "body_content": clean_body_content,  # Clean, formatted body content for summarization
                    "email_id": email_dict.get("id", email_dict.get("email_id", "unknown")),
                    "has_attachments": bool(email_dict.get("attachments", [])),
                    "size": email_dict.get("size", 0)
                }

                formatted.append(formatted_email)

            except Exception as e:
                logger.warning(f"Failed to format email: {e}")
                # Add minimal fallback entry
                formatted.append({
                    "subject": "Email formatting error",
                    "sender": "unknown",
                    "date": "unknown",
                    "is_read": True,
                    "preview": f"Error formatting email: {str(e)}",
                    "email_id": "error",
                    "has_attachments": False,
                    "size": 0
                })

        return formatted

    def _format_date(self, date_value: Any) -> str:
        """Format date value to readable string"""
        if not date_value:
            return "Unknown date"

        try:
            if isinstance(date_value, datetime):
                return date_value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(date_value, str):
                # Try to parse common date formats
                try:
                    dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    return date_value
            else:
                return str(date_value)
        except Exception:
            return "Date format error"

    def _get_email_preview(self, body: str, max_length: int = 200) -> str:
        """Get preview text from email body"""
        if not body:
            return "No content"

        try:
            # Strip HTML tags if present
            import re
            clean_text = re.sub(r'<[^>]+>', ' ', str(body))

            # Clean up whitespace
            clean_text = ' '.join(clean_text.split())

            # Truncate to preview length
            if len(clean_text) > max_length:
                return clean_text[:max_length] + "..."

            return clean_text

        except Exception:
            return "Preview unavailable"