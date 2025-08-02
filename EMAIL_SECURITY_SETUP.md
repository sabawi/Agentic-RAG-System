# 🔒 Email Tool Security Setup Guide

## Overview
The Secure Email Sender Tool implements enterprise-grade security measures for AI agent email functionality. This guide covers proper configuration and security best practices.

## 🛡️ Security Features

### 1. Credential Management
- **Environment Variables**: Credentials stored in environment variables (never in code)
- **App Passwords**: Supports modern app-specific passwords for Gmail/Outlook
- **Config File Support**: Optional JSON config with environment variable override
- **No Plain Text Storage**: Passwords never stored in plain text files

### 2. Email Validation
- **RFC 5322 Compliant**: Proper email format validation
- **Domain Validation**: Checks for valid domain structure
- **Sanitization**: Automatic cleaning of email inputs

### 3. Attachment Security
- **File Type Filtering**: Only allows safe file types
- **Size Limits**: Maximum 25MB per attachment
- **Path Validation**: Prevents directory traversal attacks
- **Existence Check**: Validates files exist before processing

### 4. Connection Security
- **TLS/SSL Encryption**: All SMTP connections use encryption
- **Secure Context**: Modern SSL context with security defaults
- **Timeout Protection**: Prevents hanging connections

## 🔧 Configuration Setup

### Method 1: Environment Variables (Recommended)

Create a `.env` file or set environment variables:

```bash
# Gmail Configuration
export GMAIL_SENDER_EMAIL="your-agent@gmail.com"
export GMAIL_APP_PASSWORD="your-16-char-app-password"

# Outlook Configuration  
export OUTLOOK_SENDER_EMAIL="your-agent@outlook.com"
export OUTLOOK_APP_PASSWORD="your-outlook-app-password"

# Custom SMTP Configuration
export CUSTOM_SMTP_SERVER="smtp.yourcompany.com"
export CUSTOM_SMTP_PORT="587"
export CUSTOM_SENDER_EMAIL="agent@yourcompany.com"
export CUSTOM_SMTP_PASSWORD="your-smtp-password"

# Default sender for sendmail
export DEFAULT_SENDER_EMAIL="agent@localhost"
```

### Method 2: Configuration File (Optional)

Create `email_config.json` in the server directory:

```json
{
  "gmail": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-agent@gmail.com",
    "app_password": "your-16-char-app-password"
  },
  "outlook": {
    "smtp_server": "smtp-mail.outlook.com",
    "smtp_port": 587, 
    "sender_email": "your-agent@outlook.com",
    "app_password": "your-outlook-app-password"
  },
  "custom": {
    "smtp_server": "smtp.yourcompany.com",
    "smtp_port": 587,
    "sender_email": "agent@yourcompany.com", 
    "app_password": "your-smtp-password"
  }
}
```

**⚠️ Important**: If using config file, set restrictive permissions:
```bash
chmod 600 email_config.json
```

## 🔑 Getting App Passwords

### Gmail Setup
1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account Settings → Security → App Passwords
3. Generate app password for "Mail" application
4. Use the 16-character password (spaces removed)

### Outlook/Hotmail Setup  
1. Enable 2-Factor Authentication on Microsoft account
2. Go to Security Settings → App Passwords
3. Generate app password for email application
4. Use the generated password

### Custom SMTP
- Contact your email administrator for SMTP credentials
- Ensure STARTTLS or SSL/TLS is supported
- Use authentication credentials provided

## 🛡️ Security Best Practices

### 1. Credential Protection
```bash
# Set environment variables securely
source /secure/path/email_credentials.env

# Or use systemd service environment
sudo systemctl edit your-service
# Add:
# [Service]
# EnvironmentFile=/secure/path/email_credentials.env
```

### 2. File Permissions
```bash
# Secure credential files
chmod 600 email_credentials.env
chmod 600 email_config.json

# Secure directories
chmod 700 /secure/path/
```

### 3. Network Security
- Use firewall rules to restrict SMTP outbound connections
- Consider SMTP relay through internal mail server
- Monitor email sending for anomalies

### 4. Monitoring and Logging
```bash
# Monitor email sending
tail -f /var/log/email_agent.log

# Check for suspicious activity
grep "Email sent" /var/log/email_agent.log | tail -20
```

## 🔧 Testing Configuration

Test your setup with this command:
```bash
cd /home/sabawi/Development/flaskserver/user_tools
python3 secure_email_sender.py
```

## ⚡ Usage Examples

### Basic Email
```json
{
  "to_email": "recipient@example.com",
  "subject": "Agent Report", 
  "body": "This is an automated message from your AI agent.",
  "provider": "gmail"
}
```

### Email with Attachments
```json
{
  "to_email": "manager@company.com",
  "subject": "Weekly Analysis Report",
  "body": "Please find the weekly analysis attached.",
  "attachments": "/path/to/report.pdf,/path/to/data.csv",
  "cc_emails": "team@company.com",
  "priority": "high",
  "provider": "outlook"
}
```

### HTML Email
```json
{
  "to_email": "client@company.com", 
  "subject": "Dashboard Update",
  "body": "<html><body><h1>System Status</h1><p>All systems operational.</p></body></html>",
  "provider": "custom"
}
```

## 🚨 Security Warnings

1. **Never commit credentials** to version control
2. **Use app passwords**, not account passwords
3. **Restrict attachment types** - modify allowed_attachment_types if needed
4. **Monitor usage** - implement rate limiting if necessary
5. **Regular rotation** - change app passwords periodically
6. **Network isolation** - consider VPN or internal SMTP relay

## 🔍 Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Verify app password is correct
   - Check 2FA is enabled
   - Ensure environment variables are set

2. **"Connection timeout"**
   - Check firewall settings
   - Verify SMTP server and port
   - Test network connectivity

3. **"Attachment too large"**
   - Files must be < 25MB
   - Consider compression or cloud links

4. **"Invalid email format"**
   - Check email address format
   - Remove extra spaces or characters

### Debug Mode
Enable debug logging by setting:
```bash
export EMAIL_DEBUG=true
```

## 📞 Support

For security concerns or configuration issues:
1. Check server logs for detailed error messages
2. Verify all environment variables are correctly set
3. Test with minimal configuration first
4. Ensure network connectivity to SMTP servers