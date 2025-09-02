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
import logging
from pathlib import Path
from email.message import EmailMessage
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

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
        # Security: Use blacklist approach - only restrict genuinely dangerous file types
        # On macOS/Linux, files aren't executable by default and require explicit chmod +x
        self.forbidden_attachment_types = {
            '.exe',    # Windows executables
            '.bat',    # Windows batch files  
            '.cmd',    # Windows command files
            '.com',    # Windows command files
            '.scr',    # Windows screen savers (often malware)
            '.pif',    # Windows program information files
            '.msi',    # Windows installer packages
            '.dll',    # Dynamic link libraries (can be malicious)
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
                    "description": "Optional comma-separated file paths to attach (max 25MB per file, excludes dangerous executable types)"
                },
                "priority": {
                    "type": "string",
                    "description": "Email priority: 'low', 'normal', or 'high'",
                    "enum": ["low", "normal", "high"]
                },
                "provider": {
                    "type": "string", 
                    "description": "Email provider: 'sendmail' (default, uses mailx/mutt/msmtp), 'gmail', 'outlook', or 'custom'",
                    "enum": ["sendmail", "gmail", "outlook", "custom"]
                },
                "wait_for_attachments": {
                    "type": "boolean",
                    "description": "Whether to wait for attachment files to be created (default: true)"
                },
                "attachment_timeout": {
                    "type": "integer", 
                    "description": "Maximum seconds to wait for attachments (default: 45)"
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
        """Resolve attachment file path, checking sandbox workspace for relative paths with fuzzy matching"""
        path = Path(file_path)
        
        # If absolute path exists, return it
        if path.is_absolute() and path.exists():
            return path
        
        # If relative path exists in current directory, return it
        if not path.is_absolute() and path.exists():
            return path
        
        # Check sandbox workspace for relative paths with retry mechanism
        if not path.is_absolute():
            sandbox_path = Path.cwd() / "sandbox_workspace" / file_path
            
            # 🔧 ENHANCED: Advanced file creation waiting mechanism
            import time
            
            # Smart waiting based on file type and context
            if file_path.lower().endswith('.pdf'):
                max_wait_time = 30  # 30 seconds for PDF generation
                check_interval = 0.5  # 500ms between checks
            else:
                max_wait_time = 10  # 10 seconds for other files  
                check_interval = 0.2  # 200ms between checks
                
            max_retries = int(max_wait_time / check_interval)
            printed_waiting_message = False
            
            for retry in range(max_retries):
                exists = sandbox_path.exists()
                
                if exists:
                    # Enhanced file completeness check
                    try:
                        stat_info = sandbox_path.stat()
                        if stat_info.st_size > 0:
                            # Additional check: ensure file is not still being written
                            # Wait a bit and check if file size changed
                            initial_size = stat_info.st_size
                            time.sleep(0.1)  # Brief pause
                            
                            try:
                                new_size = sandbox_path.stat().st_size
                                if new_size == initial_size and new_size > 100:  # File stable and substantial
                                    if printed_waiting_message:
                                        print(f"✅ File ready: {file_path} ({new_size} bytes)")
                                    return sandbox_path
                                elif not printed_waiting_message:
                                    print(f"⏳ Waiting for {file_path} to be fully written... (current size: {initial_size} bytes)")
                                    printed_waiting_message = True
                            except:
                                # File might be locked, keep waiting
                                pass
                        else:
                            if not printed_waiting_message:
                                print(f"⏳ Waiting for {file_path} to be created and written...")
                                printed_waiting_message = True
                    except Exception as e:
                        if not printed_waiting_message:
                            print(f"⏳ Waiting for {file_path} to be accessible... ({str(e)[:50]})")
                            printed_waiting_message = True
                
                if retry < max_retries - 1:  # Don't sleep on last iteration
                    time.sleep(check_interval)
                    
            # If we get here, we've exhausted retries
            if printed_waiting_message:
                print(f"⚠️ Timeout waiting for {file_path} after {max_wait_time} seconds")
        
        # 🆕 NEW: Fuzzy matching for attachment files
        if not path.is_absolute():
            fuzzy_match = self._find_fuzzy_attachment_match(file_path)
            if fuzzy_match:
                print(f"🔍 FUZZY MATCH: '{file_path}' -> '{fuzzy_match.name}'")
                return fuzzy_match
        
        return None
    
    def _find_fuzzy_attachment_match(self, requested_file: str) -> Optional[Path]:
        """Find fuzzy matches for attachment files in sandbox workspace"""
        try:
            sandbox_path = Path.cwd() / "sandbox_workspace"
            if not sandbox_path.exists():
                return None
            
            requested_lower = requested_file.lower()
            requested_stem = Path(requested_file).stem.lower()
            requested_suffix = Path(requested_file).suffix.lower()
            
            # Look for fuzzy matches
            candidates = []
            
            for file_path in sandbox_path.glob("*"):
                if not file_path.is_file():
                    continue
                    
                file_lower = file_path.name.lower()
                file_stem = file_path.stem.lower()
                file_suffix = file_path.suffix.lower()
                
                # Exact match (case insensitive)
                if file_lower == requested_lower:
                    return file_path
                
                # Stem match with same extension
                if file_stem == requested_stem and file_suffix == requested_suffix:
                    candidates.append((file_path, 100))  # High priority
                
                # Handle common patterns
                # "Cover Letter.pdf" -> "cover_letter.pdf"
                normalized_requested = requested_stem.replace(' ', '_').replace('-', '_')
                normalized_file = file_stem.replace(' ', '_').replace('-', '_')
                
                if normalized_file == normalized_requested and file_suffix == requested_suffix:
                    candidates.append((file_path, 90))
                
                # "Resume.pdf" -> "resume_john_doe.pdf" (contains keyword)
                if requested_suffix == file_suffix:
                    if requested_stem in file_stem or file_stem.startswith(requested_stem):
                        candidates.append((file_path, 80))
                    elif any(word in file_stem for word in requested_stem.split('_')):
                        candidates.append((file_path, 70))
            
            # Return best match
            if candidates:
                candidates.sort(key=lambda x: x[1], reverse=True)
                return candidates[0][0]
                
        except Exception as e:
            print(f"Warning: Fuzzy matching failed: {e}")
        
        return None
    
    def _wait_for_all_attachments(self, attachment_paths: List[str], timeout_seconds: int = 60) -> Dict[str, Any]:
        """Wait for all attachment files to be created and return status"""
        if not attachment_paths:
            return {"all_ready": True, "ready_files": [], "missing_files": [], "timeout": False}
        
        import time
        start_time = time.time()
        ready_files = []
        missing_files = []
        
        print(f"🔄 Pre-flight check: Waiting for {len(attachment_paths)} attachment(s)...")
        
        while time.time() - start_time < timeout_seconds:
            current_missing = []
            current_ready = []
            
            for file_path in attachment_paths:
                resolved_path = self._resolve_attachment_path(file_path)
                if resolved_path and self._validate_attachment(file_path):
                    if file_path not in ready_files:
                        print(f"✅ Ready: {file_path}")
                    current_ready.append(file_path)
                else:
                    current_missing.append(file_path)
            
            ready_files = current_ready
            missing_files = current_missing
            
            if not missing_files:
                print(f"🎉 All {len(attachment_paths)} attachment(s) ready!")
                return {"all_ready": True, "ready_files": ready_files, "missing_files": [], "timeout": False}
            
            # Wait before next check
            time.sleep(1.0)
        
        # Timeout reached
        print(f"⚠️ Timeout after {timeout_seconds}s: {len(missing_files)} attachment(s) still missing")
        for missing in missing_files:
            print(f"   ❌ Missing: {missing}")
        
        return {
            "all_ready": False, 
            "ready_files": ready_files, 
            "missing_files": missing_files, 
            "timeout": True
        }
    
    def _detect_recent_reports(self, max_age_minutes: int = 10) -> List[str]:
        """Detect recently created report files in sandbox workspace"""
        try:
            sandbox_path = Path.cwd() / "sandbox_workspace"
            if not sandbox_path.exists():
                return []
            
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            recent_reports = []
            
            # Look for common report file patterns
            report_patterns = ['*report*.pdf', '*report*.html', '*analysis*.pdf', '*analysis*.html', 
                             '*_report.pdf', '*_report.html', '*stock*.pdf', '*stock*.html']
            
            for pattern in report_patterns:
                for file_path in sandbox_path.glob(pattern):
                    if file_path.is_file():
                        # Check if file was modified recently
                        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mod_time > cutoff_time:
                            recent_reports.append(file_path.name)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_reports = []
            for report in recent_reports:
                if report not in seen:
                    seen.add(report)
                    unique_reports.append(report)
            
            return unique_reports[:3]  # Limit to 3 most recent
            
        except Exception as e:
            print(f"Warning: Could not detect recent reports: {e}")
            return []
    
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
        
        # Check file type - use blacklist approach for security
        if path.suffix.lower() in self.forbidden_attachment_types:
            print(f"Warning: Attachment type forbidden for security: {file_path} (type: {path.suffix.lower()})")
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
            # 🔧 CRITICAL FIX: Clean up HTML tags and formatting in plain text email body
            import re
            clean_body = body
            
            # First, handle literal \n strings that should be actual newlines
            clean_body = clean_body.replace('\\n', '\n')  # Convert literal \n to actual newlines
            
            # Convert common HTML tags to plain text equivalents
            clean_body = re.sub(r'<br\s*/?>', '\n', clean_body)  # <br> -> newline
            clean_body = re.sub(r'<br><br>', '\n\n', clean_body)  # <br><br> -> double newline
            clean_body = re.sub(r'<p>', '\n', clean_body)  # <p> -> newline
            clean_body = re.sub(r'</p>', '\n', clean_body)  # </p> -> newline
            
            # Remove any other HTML tags that might be left
            clean_body = re.sub(r'<[^>]+>', '', clean_body)
            
            # Clean up multiple consecutive newlines
            clean_body = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_body)
            
            # 🔧 FIX: Prevent quoted-printable encoding by keeping lines under 76 characters
            # Split long lines to avoid quoted-printable encoding
            lines = clean_body.split('\n')
            formatted_lines = []
            for line in lines:
                if len(line) > 70:  # Keep some margin under 76 char limit
                    # Split long lines at word boundaries
                    words = line.split(' ')
                    current_line = []
                    current_length = 0
                    
                    for word in words:
                        if current_length + len(word) + 1 <= 70:
                            current_line.append(word)
                            current_length += len(word) + 1
                        else:
                            if current_line:
                                formatted_lines.append(' '.join(current_line))
                            current_line = [word]
                            current_length = len(word)
                    
                    if current_line:
                        formatted_lines.append(' '.join(current_line))
                else:
                    formatted_lines.append(line)
            
            clean_body = '\n'.join(formatted_lines)
            
            msg.set_content(clean_body.strip())
        
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
        """Send email via system sendmail or alternatives"""
        try:
            # 🔧 NEW: Try alternative mail transfer agents for better MIME support
            has_attachments = any(part.get_filename() for part in msg.walk())
            
            if has_attachments:
                print("📎 Attachments detected - trying alternative mail agents...")
                self._save_email_to_file(msg)
                
                # 🚀 ENHANCED: Prioritize mutt for multiple attachments, then try others
                attachments_count = len([part for part in msg.walk() if part.get_filename()])
                
                if attachments_count > 1:
                    # For multiple attachments, prefer mutt (best MIME support) then msmtp
                    alternatives = [
                        ("mutt", self._send_via_mutt),
                        ("msmtp", self._send_via_msmtp),
                        ("mailx", self._send_via_mailx)
                    ]
                    print(f"🔧 Multiple attachments ({attachments_count}) detected - prioritizing mutt")
                else:
                    # For single attachments, standard order
                    alternatives = [
                        ("msmtp", self._send_via_msmtp),
                        ("mailx", self._send_via_mailx), 
                        ("mutt", self._send_via_mutt)
                    ]
                
                for tool_name, send_func in alternatives:
                    if self._find_mail_tool(tool_name):
                        print(f"🔧 Trying {tool_name} for better MIME attachment support...")
                        if send_func(msg):
                            print(f"✅ Email sent successfully via {tool_name}")
                            return True
                        else:
                            print(f"❌ {tool_name} failed, trying next option...")
                
                # 🚀 ULTIMATE FALLBACK: If multiple attachments failed, try ZIP approach
                if attachments_count > 1:
                    print("🔧 All mail agents failed with multiple attachments - trying ZIP fallback...")
                    if self._send_with_zip_fallback(msg):
                        print("✅ Email sent successfully with ZIP fallback")
                        return True
            
            # Fallback to sendmail/sSMTP
            sendmail_path = "/usr/sbin/sendmail"
            if not os.path.exists(sendmail_path):
                sendmail_path = "/usr/bin/sendmail"
                
            if not os.path.exists(sendmail_path):
                print("❌ No mail transfer agents found on system")
                return False
            
            # Check if this is sSMTP and warn about issues
            import subprocess
            try:
                version_result = subprocess.run([sendmail_path, "-V"], capture_output=True, text=True, timeout=5)
                if "sSMTP" in version_result.stderr:
                    print("⚠️ Falling back to sSMTP - known issues with attachments.")
                    print("🔧 Alternative mail agents not available or failed.")
                    if has_attachments:
                        print("📧 Debug files saved to /tmp/ for verification.")
            except:
                pass
            
            # Send via sendmail/sSMTP  
            with os.popen(f"{sendmail_path} -t -oi", "w") as p:
                email_content = msg.as_string()
                p.write(email_content)
                print(f"📧 Sent {len(email_content)} bytes to {sendmail_path}")
            
            # 🧹 AUTO-CLEANUP: Remove successfully emailed generated files  
            # Extract attachment paths from the message
            attachment_paths = []
            for part in msg.walk():
                if part.get_filename():
                    # This is a fallback cleanup - we don't have the original paths
                    # but we can clean common generated file patterns
                    filename = part.get_filename()
                    attachment_paths.append(filename)
            if attachment_paths:
                self._cleanup_generated_files(attachment_paths)
            
            return True
            
        except Exception as e:
            print(f"Mail sending failed: {e}")
            return False
    
    def _find_mail_tool(self, tool_name: str) -> str:
        """Find mail tool in system PATH"""
        import shutil
        return shutil.which(tool_name)
    
    def _send_via_msmtp(self, msg: EmailMessage) -> bool:
        """Send email via msmtp"""
        try:
            msmtp_path = self._find_mail_tool("msmtp")
            if not msmtp_path:
                return False
            
            import subprocess
            
            # Extract recipients
            recipients = []
            if msg["To"]:
                recipients.extend([addr.strip() for addr in msg["To"].split(",")])
            if msg["Cc"]:
                recipients.extend([addr.strip() for addr in msg["Cc"].split(",")])
            if msg["Bcc"]:
                recipients.extend([addr.strip() for addr in msg["Bcc"].split(",")])
            
            # Build msmtp command
            cmd = [msmtp_path, "-t"] + recipients
            
            # Send email
            result = subprocess.run(
                cmd,
                input=msg.as_string(),
                text=True,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True
            else:
                print(f"msmtp error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"msmtp failed: {e}")
            return False
    
    def _send_via_mailx(self, msg: EmailMessage) -> bool:
        """Send email via mailx"""
        try:
            mailx_path = self._find_mail_tool("mailx") or self._find_mail_tool("mail")
            if not mailx_path:
                return False
            
            import subprocess
            import tempfile
            
            # Extract recipients and subject
            recipients = msg["To"]
            subject = msg["Subject"] or "Email with attachment"
            
            # Build mailx command
            cmd = [mailx_path, "-s", subject]
            
            # 🔧 FIX: Add CC support for mailx
            if msg["Cc"]:
                cc_recipients = msg["Cc"]
                cmd.extend(["-c", cc_recipients])
                print(f"📧 Adding CC recipients: {cc_recipients}")
                
            if msg["Bcc"]:
                bcc_recipients = msg["Bcc"]
                cmd.extend(["-b", bcc_recipients])
                print(f"📧 Adding BCC recipients: {bcc_recipients}")
            
            # Handle attachments properly - save to actual files that mailx can access
            attachments = [part for part in msg.walk() if part.get_filename()]
            temp_files = []
            
            try:
                if attachments:
                    for part in attachments:
                        if part.get_filename():
                            # Save attachment to temp file with proper name
                            attachment_data = part.get_payload(decode=True)
                            temp_file = f"/tmp/mailx_attachment_{part.get_filename()}"
                            
                            with open(temp_file, 'wb') as af:
                                af.write(attachment_data)
                            
                            temp_files.append(temp_file)
                            cmd.extend(["-A", temp_file])
                            print(f"📎 Added attachment: {temp_file} ({len(attachment_data)} bytes)")
                
                # Get email body (plain text)
                body = ""
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload()
                        break
                
                if not body:
                    # Extract text from HTML if no plain text
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            import re
                            html_content = part.get_payload()
                            # Basic HTML to text conversion
                            body = re.sub(r'<[^>]+>', '', html_content)
                            break
                
                if not body:
                    body = "Please see attached file."
                
                # 🔧 CRITICAL FIX: mailx needs recipient in both command line AND proper body format
                # Add recipient to command AFTER all attachments
                cmd.append(recipients)
                
                # Create proper email body format for mailx
                email_body = body
                
                print(f"📧 Sending via mailx: {' '.join(cmd)}")
                print(f"📝 Email body length: {len(email_body)} chars")
                
                result = subprocess.run(
                    cmd,
                    input=email_body,
                    text=True,
                    capture_output=True,
                    timeout=30
                )
                
                print(f"📧 mailx return code: {result.returncode}")
                if result.stdout:
                    print(f"📧 mailx stdout: {result.stdout}")
                if result.stderr:
                    print(f"📧 mailx stderr: {result.stderr}")
                
                return result.returncode == 0
                
            finally:
                # Clean up temp files
                for temp_file in temp_files:
                    try:
                        os.unlink(temp_file)
                        print(f"🗑️ Cleaned up: {temp_file}")
                    except:
                        pass
                        
        except Exception as e:
            print(f"mailx failed: {e}")
            return False
    
    def _send_via_mutt(self, msg: EmailMessage) -> bool:
        """Send email via mutt"""
        try:
            mutt_path = self._find_mail_tool("mutt")
            if not mutt_path:
                return False
            
            import subprocess
            import tempfile
            
            # Extract recipients and subject
            recipients = msg["To"]
            subject = msg["Subject"] or "Email with attachment"
            
            # Build mutt command
            cmd = [mutt_path, "-s", subject]
            
            # Add attachments
            attachments = [part for part in msg.walk() if part.get_filename()]
            temp_files = []
            
            try:
                if attachments:
                    for part in attachments:
                        if part.get_filename():
                            # Save attachment to temp file with proper name
                            attachment_data = part.get_payload(decode=True)
                            temp_file = f"/tmp/mutt_attachment_{part.get_filename()}"
                            
                            with open(temp_file, 'wb') as af:
                                af.write(attachment_data)
                            
                            temp_files.append(temp_file)
                            cmd.extend(["-a", temp_file])
                            print(f"📎 Added mutt attachment: {temp_file} ({len(attachment_data)} bytes)")
                
                cmd.append(recipients)
                
                # Get email body
                body = ""
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload()
                        break
                
                if not body:
                    # Extract text from HTML if no plain text
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            import re
                            html_content = part.get_payload()
                            # Basic HTML to text conversion
                            body = re.sub(r'<[^>]+>', '', html_content)
                            break
                
                if not body:
                    body = "Please see attached file."
                
                print(f"📧 Sending via mutt: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    input=body,
                    text=True,
                    capture_output=True,
                    timeout=30
                )
                
                print(f"📧 mutt return code: {result.returncode}")
                if result.stderr:
                    print(f"📧 mutt stderr: {result.stderr}")
                
                return result.returncode == 0
                
            finally:
                # Clean up temp files
                for temp_file in temp_files:
                    try:
                        os.unlink(temp_file)
                        print(f"🗑️ Cleaned up: {temp_file}")
                    except:
                        pass
                        
        except Exception as e:
            print(f"mutt failed: {e}")
            return False
    
    def _send_via_localhost_smtp(self, msg: EmailMessage) -> bool:
        """Send email via localhost SMTP as fallback for sSMTP issues"""
        try:
            print("🔧 Attempting localhost SMTP fallback...")
            import smtplib
            
            # Try localhost SMTP first
            try:
                with smtplib.SMTP('localhost', 25) as server:
                    server.send_message(msg)
                print("✅ Email sent via localhost SMTP")
                return True
            except:
                pass
            
            # Try alternative ports
            for port in [587, 25, 2525]:
                try:
                    with smtplib.SMTP('localhost', port) as server:
                        server.send_message(msg)
                    print(f"✅ Email sent via localhost SMTP port {port}")
                    return True
                except:
                    continue
            
            print("❌ All localhost SMTP attempts failed")
            return False
            
        except Exception as e:
            print(f"Localhost SMTP failed: {e}")
            return False
    
    def _save_email_to_file(self, msg: EmailMessage, filename: str = None) -> bool:
        """Save email to file for debugging or manual delivery"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"/tmp/email_debug_{timestamp}.eml"
            
            with open(filename, 'w') as f:
                f.write(msg.as_string())
            
            print(f"📧 Email saved to: {filename}")
            print(f"📧 File size: {os.path.getsize(filename)} bytes")
            
            # Also save attachment separately for verification
            for part in msg.walk():
                if part.get_filename():
                    attachment_filename = part.get_filename()
                    payload = part.get_payload(decode=True)
                    
                    debug_attachment_path = f"/tmp/attachment_debug_{attachment_filename}"
                    with open(debug_attachment_path, 'wb') as af:
                        af.write(payload)
                    
                    print(f"📎 Attachment saved to: {debug_attachment_path}")
                    print(f"📎 Attachment size: {len(payload)} bytes")
            
            return True
            
        except Exception as e:
            print(f"Failed to save email to file: {e}")
            return False

    def _cleanup_generated_files(self, attachment_paths):
        """
        🧹 AUTO-CLEANUP: Remove successfully emailed generated files from sandbox workspace
        
        Only removes files that were generated in the sandbox workspace, not user source files.
        This prevents file accumulation and ensures clean state for future requests.
        """
        try:
            import os
            sandbox_base = str(Path.cwd() / "sandbox_workspace")
            files_cleaned = []
            files_preserved = []
            
            for file_path in attachment_paths:
                try:
                    # Resolve the full path
                    if os.path.isabs(file_path):
                        full_path = file_path
                    else:
                        full_path = os.path.join(sandbox_base, file_path)
                    
                    # Only clean up files in the sandbox workspace (generated files)
                    if full_path.startswith(sandbox_base) and os.path.exists(full_path):
                        # Additional safety: Only remove common generated file types
                        if any(full_path.lower().endswith(ext) for ext in [
                            '.html', '.txt', '.md', '.csv', '.json', '.xml', '.log'
                        ]):
                            os.remove(full_path)
                            files_cleaned.append(os.path.basename(full_path))
                            print(f"🧹 AUTO-CLEANUP: Removed generated file: {os.path.basename(full_path)}")
                        else:
                            files_preserved.append(os.path.basename(full_path))
                            print(f"🛡️ AUTO-CLEANUP: Preserved file (not a typical generated file): {os.path.basename(full_path)}")
                    else:
                        files_preserved.append(os.path.basename(file_path))
                        print(f"🛡️ AUTO-CLEANUP: Preserved source file (outside sandbox): {os.path.basename(file_path)}")
                        
                except Exception as e:
                    print(f"⚠️ AUTO-CLEANUP: Error processing {file_path}: {e}")
                    files_preserved.append(os.path.basename(file_path))
            
            if files_cleaned:
                print(f"🧹 AUTO-CLEANUP: Successfully removed {len(files_cleaned)} generated files: {', '.join(files_cleaned)}")
            if files_preserved:
                print(f"🛡️ AUTO-CLEANUP: Preserved {len(files_preserved)} files: {', '.join(files_preserved)}")
                
        except Exception as e:
            print(f"⚠️ AUTO-CLEANUP: Error during cleanup: {e}")
            # Don't fail email sending if cleanup fails

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the email sending tool"""
        try:
            # Use kwargs directly as parameters
            parsed_args = kwargs
            
            # 🎯 CHECK FOR HTML EMAIL FORMAT PARAMETERS
            format_type = parsed_args.get("format", "").strip().lower()
            source_type = parsed_args.get("source", "").strip().lower()
            style_params = parsed_args.get("style", "").strip()
            
            # Continue with normal processing - no special HTML handling
            
            # Extract and validate required parameters (regular processing)
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
            provider = parsed_args.get("provider", "sendmail").lower()
            
            # Parse attachments with security sanitization
            attachment_paths = []
            if parsed_args.get("attachments"):
                raw_paths = [
                    path.strip() for path in parsed_args["attachments"].split(',')
                    if path.strip()
                ]
                # 🔧 SECURITY FIX: Sanitize attachment paths to prevent pipe character issues
                for path in raw_paths:
                    # Remove any potential shell injection characters
                    sanitized_path = path.replace('|', '').replace(';', '').replace('&', '').replace('$', '')
                    if sanitized_path and sanitized_path != path:
                        print(f"🔧 SECURITY: Sanitized attachment path: {path} -> {sanitized_path}")
                    if sanitized_path:
                        attachment_paths.append(sanitized_path)
            elif parsed_args.get("attachment_path"):
                # Handle single attachment_path parameter
                raw_path = parsed_args["attachment_path"].strip()
                sanitized_path = raw_path.replace('|', '').replace(';', '').replace('&', '').replace('$', '')
                if sanitized_path:
                    attachment_paths = [sanitized_path]
            else:
                # 🆕 ENHANCED: Support plain text emails without attachments
                # Only auto-detect files if user explicitly mentions attachments, files, or reports
                if any(keyword in body.lower() for keyword in ["attach", "file", "report", "document", "pdf"]) and \
                   not any(exclude in body.lower() for exclude in ["summarize", "summary", "conversation"]):
                    # Auto-detect recent report files if no attachments specified
                    recent_reports = self._detect_recent_reports()
                    if recent_reports:
                        print(f"🔍 AUTO-DETECT: Found {len(recent_reports)} recent report(s): {', '.join(recent_reports)}")
                        attachment_paths = recent_reports
                    else:
                        print(f"📧 PLAIN TEXT EMAIL: No files detected, sending text-only email")
                else:
                    print(f"📧 PLAIN TEXT EMAIL: Sending text summary without file attachments")
            
            # 🆕 NEW: Wait for all attachments to be ready before proceeding
            wait_for_attachments = parsed_args.get("wait_for_attachments", True)
            attachment_timeout = parsed_args.get("attachment_timeout", 45)
            
            if attachment_paths and wait_for_attachments:
                wait_result = self._wait_for_all_attachments(attachment_paths, timeout_seconds=attachment_timeout)
                
                if not wait_result["all_ready"]:
                    if wait_result["timeout"]:
                        error_msg = f"Timeout waiting for attachments after {attachment_timeout}s: {', '.join(wait_result['missing_files'])}"
                        return {"success": False, "error": error_msg, "result": None}
                    else:
                        error_msg = f"Attachments not found: {', '.join(wait_result['missing_files'])}"
                        return {"success": False, "error": error_msg, "result": None}
                
                print(f"🚀 All attachments verified - proceeding with email sending")
            elif attachment_paths and not wait_for_attachments:
                print(f"⚡ Skipping attachment wait (wait_for_attachments=False) - proceeding immediately")
            
            # Get provider configuration
            if provider == "sendmail":
                # Use sendmail method
                sender_email = os.getenv("DEFAULT_SENDER_EMAIL", "agent@localhost")
                msg = self._create_email_message(
                    to_email, subject, body, cc_emails, bcc_emails,
                    attachment_paths, priority, sender_email
                )
                
                if self._send_via_sendmail(msg):
                    # 🔧 RECORD EMAIL SEND TIME for duplicate prevention
                    try:
                        from datetime import datetime
                        with open("/tmp/last_email_sent.txt", "w") as f:
                            f.write(datetime.now().isoformat())
                    except:
                        pass  # Don't fail email sending if timestamp recording fails
                    
                    # 🧹 AUTO-CLEANUP: Remove successfully emailed generated files
                    self._cleanup_generated_files(attachment_paths)
                    
                    recipients = [to_email] + cc_emails + bcc_emails
                    # 📧 DETAILED EMAIL LOG: Show full email details for debugging
                    attachment_summary = []
                    if attachment_paths:
                        for path in attachment_paths:
                            if os.path.exists(path):
                                size = os.path.getsize(path)
                                attachment_summary.append(f"{path} ({size}B)")
                            else:
                                attachment_summary.append(f"{path} (NOT FOUND)")
                    
                    message = f"✅ Email sent successfully via sendmail\n📧 TO: {to_email}\n📧 SUBJECT: {subject}\n📧 BODY: {body[:100]}...\n📎 ATTACHMENTS: {attachment_summary if attachment_summary else 'None'}\n📊 RECIPIENTS: {len(recipients)}"
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
                        # 🧹 AUTO-CLEANUP: Remove successfully emailed generated files
                        self._cleanup_generated_files(attachment_paths)
                        
                        recipients = [to_email] + cc_emails + bcc_emails
                        # 📧 DETAILED EMAIL LOG: Show full email details for debugging
                        attachment_summary = []
                        if attachment_paths:
                            for path in attachment_paths:
                                if os.path.exists(path):
                                    size = os.path.getsize(path)
                                    attachment_summary.append(f"{path} ({size}B)")
                                else:
                                    attachment_summary.append(f"{path} (NOT FOUND)")
                        
                        message = f"✅ Email sent successfully via sendmail (fallback)\n📧 TO: {to_email}\n📧 SUBJECT: {subject}\n📧 BODY: {body[:100]}...\n📎 ATTACHMENTS: {attachment_summary if attachment_summary else 'None'}\n📊 RECIPIENTS: {len(recipients)}"
                        return {"success": True, "result": message, "error": None}
                    else:
                        return {"success": False, "error": f"No sender email configured for provider: {provider} and sendmail fallback failed", "result": None}
                
                msg = self._create_email_message(
                    to_email, subject, body, cc_emails, bcc_emails,
                    attachment_paths, priority, sender_email
                )
                
                if self._send_via_smtp(msg, provider_config):
                    # 🔧 RECORD EMAIL SEND TIME for duplicate prevention
                    try:
                        from datetime import datetime
                        with open("/tmp/last_email_sent.txt", "w") as f:
                            f.write(datetime.now().isoformat())
                    except:
                        pass  # Don't fail email sending if timestamp recording fails
                    
                    # 🧹 AUTO-CLEANUP: Remove successfully emailed generated files
                    self._cleanup_generated_files(attachment_paths)
                        
                    recipients = [to_email] + cc_emails + bcc_emails
                    message = f"✅ Email sent successfully via {provider} to {len(recipients)} recipient(s)"
                    return {"success": True, "result": message, "error": None}
                else:
                    return {"success": False, "error": f"Failed to send email via {provider} SMTP", "result": None}
            
        except Exception as e:
            return {"success": False, "error": f"Email sending failed: {str(e)}", "result": None}
    
    def _send_with_zip_fallback(self, msg: EmailMessage) -> bool:
        """🚀 ULTIMATE FALLBACK: Create ZIP file with all attachments and send single ZIP"""
        try:
            import zipfile
            import tempfile
            import os
            
            # Create temporary ZIP file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f"attachments_{timestamp}.zip"
            zip_path = f"/tmp/{zip_filename}"
            
            print(f"🗂️ Creating ZIP file: {zip_filename}")
            
            # Create ZIP with all attachments
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                attachments = [part for part in msg.walk() if part.get_filename()]
                
                for part in attachments:
                    filename = part.get_filename()
                    attachment_data = part.get_payload(decode=True)
                    
                    # Add file to ZIP
                    zipf.writestr(filename, attachment_data)
                    print(f"📎 Added to ZIP: {filename} ({len(attachment_data)} bytes)")
            
            zip_size = os.path.getsize(zip_path)
            print(f"🗂️ ZIP created: {zip_size} bytes containing {len(attachments)} files")
            
            # Create new message with single ZIP attachment
            from email.message import EmailMessage
            zip_msg = EmailMessage()
            zip_msg['From'] = msg['From']
            zip_msg['To'] = msg['To']
            zip_msg['Subject'] = msg['Subject']
            if msg['Cc']:
                zip_msg['Cc'] = msg['Cc']
            if msg['Bcc']:
                zip_msg['Bcc'] = msg['Bcc']
            
            # Update body to mention ZIP
            original_body = msg.get_body(preferencelist=('plain', 'html'))
            if original_body:
                body_text = original_body.get_content()
                zip_msg.set_content(f"""{body_text}

Note: All files have been combined into a single ZIP archive for reliable delivery.
ZIP contains: {', '.join([part.get_filename() for part in attachments])}""")
            else:
                zip_msg.set_content(f"Please find attached ZIP file containing {len(attachments)} files.")
            
            # Add ZIP as single attachment
            with open(zip_path, 'rb') as zf:
                zip_data = zf.read()
                zip_msg.add_attachment(zip_data, 
                                     maintype='application', 
                                     subtype='zip',
                                     filename=zip_filename)
            
            print(f"📧 Sending ZIP fallback via best available mail agent...")
            
            # Try to send via the best available single-attachment method
            alternatives = [
                ("mutt", self._send_via_mutt),
                ("mailx", self._send_via_mailx),
                ("msmtp", self._send_via_msmtp)
            ]
            
            for tool_name, send_func in alternatives:
                if self._find_mail_tool(tool_name):
                    print(f"🔧 Trying ZIP via {tool_name}...")
                    if send_func(zip_msg):
                        print(f"✅ ZIP sent successfully via {tool_name}")
                        return True
                    else:
                        print(f"❌ ZIP via {tool_name} failed")
            
            return False
            
        except Exception as e:
            print(f"❌ ZIP fallback failed: {e}")
            return False
        finally:
            # Clean up ZIP file
            try:
                if 'zip_path' in locals() and os.path.exists(zip_path):
                    os.unlink(zip_path)
                    print(f"🗑️ Cleaned up ZIP: {zip_path}")
            except:
                pass


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