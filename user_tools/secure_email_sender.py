"""
Secure Email Sender Tool for FastAPI Server
Professional-grade email functionality with comprehensive security measures
Adapted for agent/AI tool calling with robust error handling and credential management
"""

import os
import json
import smtplib
import ssl
import re
from pathlib import Path
from email.message import EmailMessage
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool


class SecureEmailSenderTool(BaseUserTool):
    """
    A secure, professional email sending tool with comprehensive security measures.
    
    Features:
    - Secure credential management with environment variables
    - Multiple SMTP provider support (Gmail, Outlook, custom)
    - Attachment handling with security validation
    - Email validation and sanitization
    - Comprehensive error handling and logging
    - Fallback to system sendmail if configured
    """
    
    def __init__(self):
        super().__init__()
        self.config_file = Path("email_config.json")
        self.max_attachment_size = 25 * 1024 * 1024  # 25MB limit
        self.allowed_attachment_types = {
            '.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx', '.png', 
            '.jpg', '.jpeg', '.gif', '.zip', '.json', '.xml', '.html'
        }
        
        # Load configuration
        self._load_email_config()
    
    @property
    def name(self) -> str:
        return "secure_email_sender"
    
    @property
    def description(self) -> str:
        return "Send professional emails with optional attachments. Supports multiple recipients, CC/BCC, file attachments, and various email providers. Includes comprehensive security validation and error handling."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to_email": {
                    "type": "string",
                    "description": "Primary recipient email address"
                },
                "subject": {
                    "type": "string", 
                    "description": "Email subject line"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content (supports plain text and basic HTML)"
                },
                "cc_emails": {
                    "type": "string",
                    "description": "Optional comma-separated CC email addresses"
                },
                "bcc_emails": {
                    "type": "string", 
                    "description": "Optional comma-separated BCC email addresses"
                },
                "attachments": {
                    "type": "string",
                    "description": "Optional comma-separated file paths to attach (max 25MB per file)"
                },
                "priority": {
                    "type": "string",
                    "description": "Email priority: 'low', 'normal', or 'high'",
                    "enum": ["low", "normal", "high"]
                },
                "provider": {
                    "type": "string", 
                    "description": "Email provider: 'gmail', 'outlook', 'custom', or 'sendmail'",
                    "enum": ["gmail", "outlook", "custom", "sendmail"]
                }
            },
            "required": ["to_email", "subject", "body"]
        }
    
    def _load_email_config(self):
        """Load email configuration from file or environment variables"""
        self.config = {
            "gmail": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": os.getenv("GMAIL_SENDER_EMAIL"),
                "app_password": os.getenv("GMAIL_APP_PASSWORD")
            },
            "outlook": {
                "smtp_server": "smtp-mail.outlook.com", 
                "smtp_port": 587,
                "sender_email": os.getenv("OUTLOOK_SENDER_EMAIL"),
                "app_password": os.getenv("OUTLOOK_APP_PASSWORD")
            },
            "custom": {
                "smtp_server": os.getenv("CUSTOM_SMTP_SERVER"),
                "smtp_port": int(os.getenv("CUSTOM_SMTP_PORT", "587")),
                "sender_email": os.getenv("CUSTOM_SENDER_EMAIL"),
                "app_password": os.getenv("CUSTOM_SMTP_PASSWORD")
            }
        }
        
        # Load from config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    # Only update if environment variables aren't set
                    for provider, settings in file_config.items():
                        if provider in self.config:
                            for key, value in settings.items():
                                if not self.config[provider].get(key):
                                    self.config[provider][key] = value
            except Exception as e:
                print(f"Warning: Could not load email config file: {e}")
    
    def _validate_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
    
    def _parse_email_list(self, email_string: str) -> List[str]:
        """Parse comma-separated email list and validate each"""
        if not email_string:
            return []
        
        emails = [email.strip() for email in email_string.split(',')]
        valid_emails = []
        
        for email in emails:
            if email and self._validate_email(email):
                valid_emails.append(email)
            elif email:
                print(f"Warning: Invalid email address skipped: {email}")
        
        return valid_emails
    
    def _resolve_attachment_path(self, file_path: str) -> Optional[Path]:
        """Resolve attachment file path, checking sandbox workspace for relative paths"""
        path = Path(file_path)
        
        # If absolute path exists, return it
        if path.is_absolute() and path.exists():
            return path
        
        # If relative path exists in current directory, return it
        if not path.is_absolute() and path.exists():
            return path
        
        # Check sandbox workspace for relative paths
        if not path.is_absolute():
            sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace") / file_path
            if sandbox_path.exists():
                return sandbox_path
        
        return None
    
    def _validate_attachment(self, file_path: str) -> bool:
        """Validate attachment file"""
        path = self._resolve_attachment_path(file_path)
        
        # Check if file exists
        if not path:
            print(f"Warning: Attachment file not found: {file_path} (checked current dir and sandbox)")
            return False
        
        # Check file size
        if path.stat().st_size > self.max_attachment_size:
            print(f"Warning: Attachment too large (>25MB): {file_path}")
            return False
        
        # Check file type
        if path.suffix.lower() not in self.allowed_attachment_types:
            print(f"Warning: Attachment type not allowed: {file_path}")
            return False
        
        return True
    
    def _create_email_message(self, to_email: str, subject: str, body: str, 
                            cc_emails: List[str], bcc_emails: List[str], 
                            attachments: List[str], priority: str, 
                            sender_email: str) -> EmailMessage:
        """Create email message with all components"""
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Add CC and BCC
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
        if bcc_emails:
            msg["Bcc"] = ", ".join(bcc_emails)
        
        # Set priority
        priority_headers = {
            "high": ("1", "high"),
            "normal": ("3", "normal"), 
            "low": ("5", "low")
        }
        if priority in priority_headers:
            p_num, p_text = priority_headers[priority]
            msg["X-Priority"] = p_num
            msg["X-MSMail-Priority"] = p_text.capitalize()
        
        # Set content (detect HTML vs plain text)
        if "<html>" in body.lower() or "<body>" in body.lower():
            msg.set_content(body, subtype='html')
        else:
            msg.set_content(body)
        
        # Add attachments
        for file_path in attachments:
            resolved_path = self._resolve_attachment_path(file_path)
            if resolved_path and self._validate_attachment(file_path):
                try:
                    with open(resolved_path, "rb") as f:
                        data = f.read()
                        msg.add_attachment(
                            data,
                            maintype="application",
                            subtype="octet-stream", 
                            filename=resolved_path.name
                        )
                except Exception as e:
                    print(f"Warning: Could not attach file {file_path}: {e}")
        
        return msg
    
    def _send_via_smtp(self, msg: EmailMessage, provider_config: Dict[str, Any]) -> bool:
        """Send email via SMTP"""
        try:
            smtp_server = provider_config["smtp_server"]
            smtp_port = provider_config["smtp_port"] 
            sender_email = provider_config["sender_email"]
            app_password = provider_config["app_password"]
            
            if not all([smtp_server, sender_email, app_password]):
                raise ValueError("Missing SMTP configuration")
            
            # Create secure connection
            context = ssl.create_default_context()
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, app_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"SMTP sending failed: {e}")
            return False
    
    def _send_via_sendmail(self, msg: EmailMessage) -> bool:
        """Send email via system sendmail"""
        try:
            sendmail_path = "/usr/sbin/sendmail"
            if not os.path.exists(sendmail_path):
                sendmail_path = "/usr/bin/sendmail"
                
            if not os.path.exists(sendmail_path):
                print("Sendmail not found on system")
                return False
            
            with os.popen(f"{sendmail_path} -t -oi", "w") as p:
                p.write(msg.as_string())
            
            return True
            
        except Exception as e:
            print(f"Sendmail failed: {e}")
            return False

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the email sending tool"""
        try:
            # Use kwargs directly as parameters
            parsed_args = kwargs
            
            # Extract and validate required parameters
            to_email = parsed_args.get("to_email", "").strip()
            subject = parsed_args.get("subject", "").strip()
            body = parsed_args.get("body", "").strip()
            
            if not all([to_email, subject, body]):
                return {"success": False, "error": "Missing required fields: to_email, subject, body", "result": None}
            
            if not self._validate_email(to_email):
                return {"success": False, "error": f"Invalid recipient email address: {to_email}", "result": None}
            
            # Parse optional parameters
            cc_emails = self._parse_email_list(parsed_args.get("cc_emails", ""))
            bcc_emails = self._parse_email_list(parsed_args.get("bcc_emails", ""))
            priority = parsed_args.get("priority", "normal").lower()
            provider = parsed_args.get("provider", "gmail").lower()
            
            # Parse attachments
            attachment_paths = []
            if parsed_args.get("attachments"):
                attachment_paths = [
                    path.strip() for path in parsed_args["attachments"].split(',')
                    if path.strip()
                ]
            
            # Get provider configuration
            if provider == "sendmail":
                # Use sendmail method
                sender_email = os.getenv("DEFAULT_SENDER_EMAIL", "agent@localhost")
                msg = self._create_email_message(
                    to_email, subject, body, cc_emails, bcc_emails,
                    attachment_paths, priority, sender_email
                )
                
                if self._send_via_sendmail(msg):
                    recipients = [to_email] + cc_emails + bcc_emails
                    message = f"✅ Email sent successfully via sendmail to {len(recipients)} recipient(s)"
                    return {"success": True, "result": message, "error": None}
                else:
                    return {"success": False, "error": "Failed to send email via sendmail", "result": None}
            
            else:
                # Use SMTP method
                if provider not in self.config:
                    return {"success": False, "error": f"Unknown email provider: {provider}", "result": None}
                
                provider_config = self.config[provider]
                sender_email = provider_config.get("sender_email")
                
                if not sender_email:
                    # Fallback to sendmail if no SMTP configuration
                    print(f"Warning: No sender email configured for {provider}, falling back to sendmail")
                    sender_email = os.getenv("DEFAULT_SENDER_EMAIL", "agent@localhost")
                    msg = self._create_email_message(
                        to_email, subject, body, cc_emails, bcc_emails,
                        attachment_paths, priority, sender_email
                    )
                    
                    if self._send_via_sendmail(msg):
                        recipients = [to_email] + cc_emails + bcc_emails
                        message = f"✅ Email sent successfully via sendmail (fallback) to {len(recipients)} recipient(s)"
                        return {"success": True, "result": message, "error": None}
                    else:
                        return {"success": False, "error": f"No sender email configured for provider: {provider} and sendmail fallback failed", "result": None}
                
                msg = self._create_email_message(
                    to_email, subject, body, cc_emails, bcc_emails,
                    attachment_paths, priority, sender_email
                )
                
                if self._send_via_smtp(msg, provider_config):
                    recipients = [to_email] + cc_emails + bcc_emails
                    message = f"✅ Email sent successfully via {provider} to {len(recipients)} recipient(s)"
                    return {"success": True, "result": message, "error": None}
                else:
                    return {"success": False, "error": f"Failed to send email via {provider} SMTP", "result": None}
            
        except Exception as e:
            return {"success": False, "error": f"Email sending failed: {str(e)}", "result": None}


# Register the tool
def get_user_tool():
    """Factory function to create tool instance"""
    return SecureEmailSenderTool()


if __name__ == "__main__":
    # Test the tool
    tool = SecureEmailSenderTool()
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print("Parameters:", json.dumps(tool.parameters, indent=2))