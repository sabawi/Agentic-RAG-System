"""
Universal Email Library
A comprehensive Python library for email operations with YAML configuration support.
Supports Gmail, Yahoo Mail, Outlook, and other email providers.
"""

import imaplib
import smtplib
import ssl
import email
import email.mime.multipart
import email.mime.text
import email.mime.base
import email.encoders
import yaml
import os
import socket
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from email.header import decode_header
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Data class for email message representation"""

    message_id: str
    subject: str
    sender: str
    recipient: str
    date: datetime
    body_text: str = ""
    body_html: str = ""
    attachments: List[Dict[str, Any]] = None
    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.headers is None:
            self.headers = {}


class EmailLibrary:
    """
    Universal Email Library for reading YAML configuration and managing email operations.

    Supports multiple email providers with IMAP, POP3, and SMTP protocols.
    """

    def __init__(self, config_path: str):
        """
        Initialize the email library with configuration file.

        Args:
            config_path (str): Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._connections = {}

    def _load_config(self) -> Dict[str, Any]:
        """Load and validate YAML configuration file"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
                self._validate_config(config)
                return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")

    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration structure"""
        required_sections = ["providers"]
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")

        for provider_alias, provider_config in config["providers"].items():
            required_fields = ["email", "password"]
            for field in required_fields:
                if field not in provider_config:
                    raise ValueError(
                        f"Missing required field '{field}' for provider '{provider_alias}'"
                    )

    def _get_provider_config(self, provider_alias: str) -> Dict[str, Any]:
        """Get configuration for specific provider"""
        if provider_alias not in self.config["providers"]:
            raise ValueError(f"Provider '{provider_alias}' not found in configuration")
        return self.config["providers"][provider_alias]

    def _get_imap_connection(self, provider_alias: str) -> imaplib.IMAP4_SSL:
        """Establish IMAP connection for provider"""
        config = self._get_provider_config(provider_alias)

        if f"{provider_alias}_imap" in self._connections:
            return self._connections[f"{provider_alias}_imap"]

        try:
            # Get IMAP settings
            imap_server = config.get("imap", {}).get("server")
            imap_port = config.get("imap", {}).get("port", 993)

            if not imap_server:
                raise ValueError(f"IMAP server not configured for {provider_alias}")

            # Create SSL context with relaxed settings compatible with OpenSSL 3.x
            # Note: Mutt uses GnuTLS which has different SSL handshake behavior
            context = ssl.create_default_context()

            # Set minimum TLS version (Gmail supports TLS 1.2+)
            context.minimum_version = ssl.TLSVersion.TLSv1_2

            # Use relaxed cipher settings for compatibility
            # SECLEVEL=1 allows older ciphers that Gmail might use
            context.set_ciphers('DEFAULT@SECLEVEL=1')

            # Relax certificate verification for OpenSSL 3.x compatibility
            # This matches behavior of GnuTLS-based clients like Mutt
            context.check_hostname = True  # Still verify hostname
            context.verify_mode = ssl.CERT_REQUIRED  # But require valid cert

            # Load default CA certificates
            context.load_default_certs()

            logger.info(f"Attempting IMAP connection to {imap_server}:{imap_port}")

            # Connect to IMAP server with timeout
            try:
                mail = imaplib.IMAP4_SSL(
                    imap_server,
                    imap_port,
                    ssl_context=context,
                    timeout=30  # 30 second timeout
                )
            except ssl.SSLError as ssl_err:
                logger.error(f"SSL handshake failed: {ssl_err}")
                logger.info("Retrying with even more relaxed SSL settings...")

                # Retry with minimal SSL restrictions
                context_relaxed = ssl.create_default_context()
                context_relaxed.check_hostname = False  # Disable hostname check
                context_relaxed.verify_mode = ssl.CERT_NONE  # Disable cert verification
                context_relaxed.set_ciphers('DEFAULT@SECLEVEL=0')  # Most permissive

                mail = imaplib.IMAP4_SSL(
                    imap_server,
                    imap_port,
                    ssl_context=context_relaxed,
                    timeout=30
                )
                logger.warning("Connected with relaxed SSL settings - consider checking certificates")

            # Login with credentials
            email_addr = config.get("email", "")
            password = config.get("password", "")

            # Debug: Check if credentials are actually set
            if not email_addr or not password:
                logger.error(f"❌ CREDENTIALS MISSING!")
                logger.error(f"  Email set: {'YES' if email_addr else 'NO'}")
                logger.error(f"  Password set: {'YES' if password else 'NO'}")
                logger.error(f"  Config keys: {list(config.keys())}")
                raise ValueError(f"Email credentials not configured for {provider_alias}")

            logger.info(f"Logging in as {email_addr[:5]}...@{email_addr.split('@')[1] if '@' in email_addr else '???'}")
            logger.debug(f"Password length: {len(password)}")

            mail.login(email_addr, password)

            self._connections[f"{provider_alias}_imap"] = mail
            logger.info(f"✅ IMAP connection established for {provider_alias}")

            return mail

        except imaplib.IMAP4.error as imap_err:
            logger.error(f"IMAP protocol error for {provider_alias}: {imap_err}")
            raise ConnectionError(f"IMAP authentication failed for {provider_alias}: {imap_err}")
        except ssl.SSLError as ssl_err:
            logger.error(f"SSL error for {provider_alias}: {ssl_err}")
            logger.error(f"SSL details: {ssl_err.__class__.__name__}: {str(ssl_err)}")
            raise ConnectionError(f"SSL connection failed for {provider_alias}. Check credentials and network. Details: {ssl_err}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to IMAP for {provider_alias}: {e}")
            logger.error(f"Error type: {e.__class__.__name__}")
            raise ConnectionError(f"Failed to connect to IMAP server for {provider_alias}: {e}")

    def _get_smtp_connection(self, provider_alias: str) -> smtplib.SMTP_SSL:
        """Establish SMTP connection for provider"""
        config = self._get_provider_config(provider_alias)

        try:
            # Get SMTP settings
            smtp_server = config.get("smtp", {}).get("server")
            smtp_port = config.get("smtp", {}).get("port", 587)
            use_tls = config.get("smtp", {}).get("use_tls", True)

            if not smtp_server:
                raise ValueError(f"SMTP server not configured for {provider_alias}")

            # Create SSL context with Gmail-compatible settings
            context = ssl.create_default_context()
            context.minimum_version = ssl.TLSVersion.TLSv1_2  # Gmail requires TLS 1.2+
            context.set_ciphers('DEFAULT@SECLEVEL=1')  # Adjust for Gmail compatibility

            # Create SMTP connection
            if use_tls:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls(context=context)

            server.login(config["email"], config["password"])
            logger.info(f"SMTP connection established for {provider_alias}")

            return server

        except Exception as e:
            raise ConnectionError(f"Failed to connect to SMTP server for {provider_alias}: {e}")

    def _parse_email_message(
        self, raw_message: bytes, retrieval_type: str = "full"
    ) -> EmailMessage:
        """Parse raw email message into EmailMessage object"""
        try:
            msg = email.message_from_bytes(raw_message)

            # Extract basic headers
            subject = self._decode_header_value(msg.get("Subject", ""))
            sender = self._decode_header_value(msg.get("From", ""))
            recipient = self._decode_header_value(msg.get("To", ""))
            date_str = msg.get("Date", "")
            message_id = msg.get("Message-ID", "")

            # Parse date
            try:
                date_obj = email.utils.parsedate_to_datetime(date_str)
            except (ValueError, TypeError):
                date_obj = datetime.now()

            # Create EmailMessage object
            email_msg = EmailMessage(
                message_id=message_id,
                subject=subject,
                sender=sender,
                recipient=recipient,
                date=date_obj,
            )

            if retrieval_type == "headers":
                # Only populate headers for header-only retrieval
                email_msg.headers = dict(msg.items())
                return email_msg

            # Extract body and attachments for full retrieval
            self._extract_body_and_attachments(msg, email_msg)
            email_msg.headers = dict(msg.items())

            return email_msg

        except Exception as e:
            logger.error(f"Error parsing email message: {e}")
            raise ValueError(f"Failed to parse email message: {e}")

    def _decode_header_value(self, header_value: str) -> str:
        """Decode email header value"""
        if not header_value:
            return ""

        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode("utf-8", errors="ignore")
                else:
                    decoded_string += part

            return decoded_string
        except (UnicodeDecodeError, LookupError):
            return str(header_value)

    def _extract_body_and_attachments(self, msg: email.message.Message, email_msg: EmailMessage):
        """Extract email body and attachments"""
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition"))
                content_type = part.get_content_type()

                # Skip multipart containers
                if part.get_content_maintype() == "multipart":
                    continue

                # Handle attachments
                if "attachment" in content_disposition:
                    self._process_attachment(part, email_msg)

                # Handle body content
                elif content_type == "text/plain" and not email_msg.body_text:
                    email_msg.body_text = self._get_part_content(part)
                elif content_type == "text/html" and not email_msg.body_html:
                    email_msg.body_html = self._get_part_content(part)
        else:
            # Single part message
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                email_msg.body_text = self._get_part_content(msg)
            elif content_type == "text/html":
                email_msg.body_html = self._get_part_content(msg)

    def _get_part_content(self, part: email.message.Message) -> str:
        """Extract content from email part"""
        try:
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="ignore")
            return ""
        except (UnicodeDecodeError, LookupError, AttributeError):
            return ""

    def _process_attachment(self, part: email.message.Message, email_msg: EmailMessage):
        """Process email attachment"""
        try:
            filename = part.get_filename()
            if filename:
                filename = self._decode_header_value(filename)
                content = part.get_payload(decode=True)

                attachment = {
                    "filename": filename,
                    "content_type": part.get_content_type(),
                    "size": len(content) if content else 0,
                    "content": content,
                }
                email_msg.attachments.append(attachment)
        except Exception as e:
            logger.warning(f"Error processing attachment: {e}")

    def _build_search_criteria(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        search_key: Optional[str] = None,
        include_read: bool = True,
    ) -> str:
        """Build IMAP search criteria"""
        criteria = []

        # Add read/unread filter based on include_read parameter
        if not include_read:
            criteria.append("UNSEEN")  # Only unread emails

        if from_date:
            date_str = from_date.strftime("%d-%b-%Y")
            criteria.append(f'SINCE "{date_str}"')

        if to_date:
            date_str = to_date.strftime("%d-%b-%Y")
            criteria.append(f'BEFORE "{date_str}"')

        if search_key:
            # Search in subject, body, and sender
            search_criteria = (
                f'(OR (OR SUBJECT "{search_key}" BODY "{search_key}") FROM "{search_key}")'
            )
            criteria.append(search_criteria)

        return " ".join(criteria)

    def retrieve_email(
        self,
        provider_alias: str,
        retrieval_type: str = "full",
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        search_key: Optional[str] = None,
        include_read: bool = True,
        timeout: int = 30,
    ) -> List[EmailMessage]:
        """
        Retrieve emails from specified provider.

        Args:
            provider_alias (str): Provider alias from configuration
            retrieval_type (str): "headers" or "full"
            from_date (datetime, optional): Start date for email search
            to_date (datetime, optional): End date for email search
            search_key (str, optional): Search text in subject, body, or sender
            timeout (int): Connection timeout in seconds

        Returns:
            List[EmailMessage]: List of retrieved emails
        """
        if retrieval_type not in ["headers", "full"]:
            raise ValueError("retrieval_type must be 'headers' or 'full'")

        try:
            # Set socket timeout
            socket.setdefaulttimeout(timeout)

            # Get IMAP connection
            mail = self._get_imap_connection(provider_alias)

            # Select inbox
            mail.select("inbox")

            # Build search criteria
            search_criteria = self._build_search_criteria(from_date, to_date, search_key, include_read)

            # Search for emails
            status, messages = mail.search(None, search_criteria)

            if status != "OK":
                raise RuntimeError("Failed to search emails")

            email_ids = messages[0].split()
            emails = []

            # Retrieve emails
            for email_id in email_ids:
                try:
                    # Fetch email using PEEK to avoid marking as read
                    if retrieval_type == "headers":
                        status, msg_data = mail.fetch(email_id, "(BODY.PEEK[HEADER])")
                    else:
                        status, msg_data = mail.fetch(email_id, "(BODY.PEEK[])")

                    if status == "OK" and msg_data[0]:
                        raw_email = msg_data[0][1]
                        parsed_email = self._parse_email_message(raw_email, retrieval_type)
                        emails.append(parsed_email)

                except Exception as e:
                    logger.warning(f"Error processing email {email_id}: {e}")
                    continue

            logger.info(f"Retrieved {len(emails)} emails from {provider_alias}")
            return emails

        except Exception as e:
            logger.error(f"Error retrieving emails: {e}")
            raise RuntimeError(f"Failed to retrieve emails: {e}")

        finally:
            # Reset socket timeout
            socket.setdefaulttimeout(None)

    def send_email(
        self,
        provider_alias: str,
        to: str,
        from_email: Optional[str] = None,
        subject: str = "",
        email_content: str = "",
        content_type: str = "text",
        attachments: Optional[List[str]] = None,
        timeout: int = 30,
    ) -> bool:
        """
        Send email using specified provider.

        Args:
            provider_alias (str): Provider alias from configuration
            to (str): Recipient email address
            from_email (str, optional): Sender email (uses config default if not provided)
            subject (str): Email subject
            email_content (str): Email body content
            content_type (str): "text" or "html"
            attachments (List[str], optional): List of file paths to attach
            timeout (int): Connection timeout in seconds

        Returns:
            bool: True if email sent successfully
        """
        try:
            # Set socket timeout
            socket.setdefaulttimeout(timeout)

            # Get provider configuration
            config = self._get_provider_config(provider_alias)

            # Use configured email as sender if not provided
            if not from_email:
                from_email = config["email"]

            # Create message
            msg = email.mime.multipart.MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to
            msg["Subject"] = subject

            # Add body
            if content_type.lower() == "html":
                body = email.mime.text.MIMEText(email_content, "html")
            else:
                body = email.mime.text.MIMEText(email_content, "plain")

            msg.attach(body)

            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        self._add_attachment(msg, file_path)
                    else:
                        logger.warning(f"Attachment file not found: {file_path}")

            # Get SMTP connection and send
            server = self._get_smtp_connection(provider_alias)

            # Send email
            text = msg.as_string()
            server.sendmail(from_email, to, text)
            server.quit()

            logger.info(f"Email sent successfully from {from_email} to {to}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise RuntimeError(f"Failed to send email: {e}")

        finally:
            # Reset socket timeout
            socket.setdefaulttimeout(None)

    def _add_attachment(self, msg: email.mime.multipart.MIMEMultipart, file_path: str):
        """Add file attachment to email message"""
        try:
            with open(file_path, "rb") as attachment:
                part = email.mime.base.MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            # Encode attachment
            email.encoders.encode_base64(part)

            # Add header
            filename = os.path.basename(file_path)
            part.add_header("Content-Disposition", f"attachment; filename= {filename}")

            msg.attach(part)

        except Exception as e:
            logger.error(f"Error adding attachment {file_path}: {e}")
            raise

    def close_connections(self):
        """Close all active connections"""
        for connection_key, connection in self._connections.items():
            try:
                if "imap" in connection_key:
                    connection.close()
                    connection.logout()
                elif "smtp" in connection_key:
                    connection.quit()
                logger.info(f"Closed connection: {connection_key}")
            except Exception as e:
                logger.warning(f"Error closing connection {connection_key}: {e}")

        self._connections.clear()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_connections()


# Example usage and configuration
if __name__ == "__main__":
    # Example configuration creation
    example_config = {
        "providers": {
            "gmail_personal": {
                "email": "your.email@gmail.com",
                "password": "your_app_password",
                "imap": {"server": "imap.gmail.com", "port": 993},
                "smtp": {"server": "smtp.gmail.com", "port": 587, "use_tls": True},
            },
            "outlook_work": {
                "email": "your.email@outlook.com",
                "password": "your_password",
                "imap": {"server": "outlook.office365.com", "port": 993},
                "smtp": {"server": "smtp.office365.com", "port": 587, "use_tls": True},
            },
            "yahoo_personal": {
                "email": "your.email@yahoo.com",
                "password": "your_app_password",
                "imap": {"server": "imap.mail.yahoo.com", "port": 993},
                "smtp": {"server": "smtp.mail.yahoo.com", "port": 587, "use_tls": True},
            },
        }
    }

    # Save example configuration
    with open("email_config.yaml", "w") as f:
        yaml.dump(example_config, f, default_flow_style=False)

    print("Example configuration saved to 'email_config.yaml'")
    print("Please update with your actual email credentials before using.")

    # Example usage (commented out for safety)
    """
    # Initialize library
    with EmailLibrary('email_config.yaml') as email_lib:

        # Retrieve unread emails from last 7 days
        from_date = datetime.now() - timedelta(days=7)
        emails = email_lib.retrieve_email(
            provider_alias='gmail_personal',
            retrieval_type='full',
            from_date=from_date,
            search_key='important'
        )

        print(f"Retrieved {len(emails)} emails")

        for email_msg in emails:
            print(f"From: {email_msg.sender}")
            print(f"Subject: {email_msg.subject}")
            print(f"Date: {email_msg.date}")
            print(f"Attachments: {len(email_msg.attachments)}")
            print("-" * 50)

        # Send an email
        success = email_lib.send_email(
            provider_alias='gmail_personal',
            to='recipient@example.com',
            subject='Test Email',
            email_content='This is a test email from the universal email library.',
            content_type='text',
            attachments=['document.pdf']
        )

        if success:
            print("Email sent successfully!")
    """
