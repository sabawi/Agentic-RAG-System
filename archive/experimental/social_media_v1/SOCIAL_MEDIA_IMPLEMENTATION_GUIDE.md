# Social Media Plugin System - Implementation Guide

**Version**: 1.0.3.11
**Last Updated**: October 18, 2025
**Target Audience**: Developers

---

## Overview

This document provides technical details about the social media publishing plugin system architecture, implementation, and extension guidelines for developers who want to understand the codebase or add new platform support.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Directory Structure](#directory-structure)
3. [Core Components](#core-components)
4. [Configuration System](#configuration-system)
5. [Plugin Development](#plugin-development)
6. [Integration with Tool System](#integration-with-tool-system)
7. [Testing Strategy](#testing-strategy)
8. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

### Design Principles

1. **Plugin Architecture**: Each platform is a separate plugin inheriting from base class
2. **Configuration-Driven**: All settings in YAML, secrets in `.env`
3. **Extensible**: Easy to add new platforms without modifying core code
4. **Fail-Safe**: Graceful degradation when platforms unavailable
5. **Secure**: Credentials isolated in environment variables

### Component Diagram

```
┌─────────────────────────────────────────────┐
│         fastapi_server_complete.py          │
│              (Tool Manager)                  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│      user_tools/social_media_publisher.py   │
│           (Main Tool Interface)              │
└──────────────────┬──────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌──────────────┐      ┌─────────────────┐
│ config_loader│      │  Base Publisher  │
│  (Config)    │      │    (Abstract)    │
└──────────────┘      └────────┬─────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │  Substack    │ │   Medium     │ │   Twitter    │
      │  Publisher   │ │  Publisher   │ │  Publisher   │
      │ (Implemented)│ │ (Planned)    │ │ (Planned)    │
      └──────────────┘ └──────────────┘ └──────────────┘
```

### Data Flow

```
1. User Prompt
   ↓
2. Tool Calling LLM detects social_media_publisher tool
   ↓
3. social_media_publisher() main function called
   ↓
4. Configuration loaded from YAML + .env
   ↓
5. Platform-specific publisher instantiated
   ↓
6. Publisher authenticates with platform
   ↓
7. Content published to platform
   ↓
8. Result returned (success/failure + URL)
   ↓
9. Result logged to posts log file
   ↓
10. Response sent to user
```

---

## Directory Structure

```
/home/sabawi/Development/flaskserver/
├── config/
│   └── social_media_accounts.yaml      # Account configurations
├── user_tools/
│   ├── social_media_publisher.py       # Main tool interface
│   └── social_media/
│       ├── __init__.py
│       ├── base.py                     # Abstract base class
│       ├── config_loader.py            # Configuration loader
│       └── publishers/
│           ├── __init__.py
│           ├── substack_publisher.py   # Substack implementation
│           ├── medium_publisher.py     # (Future)
│           └── twitter_publisher.py    # (Future)
├── drafts/
│   └── social_media/                   # Draft backups
├── logs/
│   └── social_media_posts.json         # Published posts log
├── docs/
│   ├── SOCIAL_MEDIA_PLUGINS_RESEARCH.md        # Research findings
│   ├── SOCIAL_MEDIA_IMPLEMENTATION_GUIDE.md    # This document
│   └── production/
│       └── SOCIAL_MEDIA_PUBLISHING_GUIDE.md    # User guide
└── .env                                 # Credentials (not in git)
```

---

## Core Components

### 1. Base Publisher Class (`user_tools/social_media/base.py`)

**Purpose**: Abstract base class that all platform publishers inherit from.

**Key Classes**:

#### `PublishResult`

Standardized result object for publishing operations.

```python
class PublishResult:
    def __init__(
        self,
        success: bool,
        platform: str,
        account: str,
        post_url: Optional[str] = None,
        post_id: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        ...
```

**Attributes**:
- `success`: Whether operation succeeded
- `platform`: Platform name (substack, medium, twitter)
- `account`: Account name used
- `post_url`: URL of published post
- `post_id`: Platform-specific post ID
- `error`: Error message if failed
- `metadata`: Additional platform-specific metadata
- `timestamp`: Auto-generated ISO timestamp

**Methods**:
- `to_dict()`: Convert to dictionary for JSON serialization
- `__str__()`: Human-readable string representation

#### `SocialMediaPublisher`

Abstract base class for all publishers.

```python
class SocialMediaPublisher(ABC):
    def __init__(
        self,
        platform_name: str,
        account_config: Dict[str, Any],
        settings: Dict[str, Any]
    ):
        ...

    @abstractmethod
    def authenticate(self) -> bool:
        """Platform-specific authentication"""
        pass

    @abstractmethod
    def publish_post(
        self,
        title: str,
        content: str,
        **kwargs
    ) -> PublishResult:
        """Platform-specific publishing"""
        pass
```

**Abstract Methods** (must be implemented by subclasses):
- `authenticate()`: Authenticate with platform
- `publish_post()`: Publish content to platform

**Helper Methods** (inherited by all publishers):
- `get_credential(env_var_name)`: Retrieve credential from environment
- `save_draft(title, content, metadata)`: Save draft before publishing
- `log_post(result)`: Log published post to JSON file
- `validate_account_enabled()`: Check if account is enabled

**Properties**:
- `is_authenticated`: Check authentication status
- `description`: Get account description from config

---

### 2. Configuration Loader (`user_tools/social_media/config_loader.py`)

**Purpose**: Load and manage social media account configurations from YAML.

**Key Class**: `SocialMediaConfig`

```python
class SocialMediaConfig:
    def __init__(self, config_path: Optional[str] = None):
        """Load configuration from YAML file"""
        ...

    def get_account(
        self,
        platform: str,
        account_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get account config (default if name not specified)"""
        ...

    def get_platform_settings(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific settings"""
        ...

    def validate_account(
        self,
        platform: str,
        account_name: Optional[str] = None
    ) -> bool:
        """Validate account exists, enabled, and has credentials"""
        ...
```

**Key Methods**:
- `get_account()`: Get account configuration
- `get_platform_settings()`: Get platform settings
- `get_defaults()`: Get global defaults
- `get_feature_flag()`: Check feature enabled
- `list_accounts()`: List all accounts for platform
- `is_platform_enabled()`: Check platform enabled
- `validate_account()`: Comprehensive validation
- `reload()`: Reload config from file

**Usage Example**:

```python
from user_tools.social_media.config_loader import SocialMediaConfig

config = SocialMediaConfig()

# Get default Substack account
account = config.get_account("substack")

# Get specific account
account = config.get_account("substack", "agentic-developer")

# Validate account ready
if config.validate_account("substack", "agentic-developer"):
    # Proceed with publishing
    pass
```

---

### 3. Platform Publishers

#### Substack Publisher (`user_tools/social_media/publishers/substack_publisher.py`)

**Status**: ✅ Implemented (v1.0.3.11)

**Key Features**:
- Email/password authentication
- HTML content publishing
- Visibility control (everyone, paid subscribers, founding members)
- Email notification control
- Draft saving
- Post logging

**Dependencies**:
```python
from substack import Api as SubstackApi
```

**Implementation**:

```python
class SubstackPublisher(SocialMediaPublisher):
    def authenticate(self) -> bool:
        """Authenticate with Substack using email/password"""
        email = self.get_credential(self.account_config.get("email_env"))
        password = self.get_credential(self.account_config.get("password_env"))

        self.client = SubstackApi(email=email, password=password)
        self.authenticated = True
        return True

    def publish_post(
        self,
        title: str,
        content: str,
        subtitle: Optional[str] = None,
        visibility: Optional[str] = None,
        send_email: Optional[bool] = None,
        **kwargs
    ) -> PublishResult:
        """Publish post to Substack"""
        # ... implementation ...
        response = self.client.post.create(
            publication_slug=self.publication_id,
            title=title,
            subtitle=subtitle,
            body_html=content,
            audience=visibility,
            send_email=send_email
        )
        return PublishResult(
            success=True,
            platform="substack",
            account=self.account_name,
            post_url=response.get("url")
        )
```

**IMPORTANT**: Uses unofficial `python-substack` library. API may change without notice.

#### Medium Publisher (Planned)

**Status**: 🔜 Coming soon

**Planned Features**:
- Integration token authentication
- Markdown or HTML content
- Publication association
- Tags support
- License selection

**API Note**: Medium API is official but closed to new applications. Existing integration tokens still work.

#### Twitter Publisher (Planned)

**Status**: 🔜 Coming soon

**Planned Features**:
- OAuth 2.0 PKCE authentication
- Tweet posting (280 characters)
- Thread support for longer content
- Media upload
- Reply/retweet/quote options

**API Note**: Twitter API v2 requires paid subscription ($100/month for reasonable usage).

---

### 4. Main Tool Interface (`user_tools/social_media_publisher.py`)

**Purpose**: Main entry point for social media publishing tool.

**Key Function**:

```python
def social_media_publisher(
    platform: str,
    content: str,
    title: Optional[str] = None,
    account: Optional[str] = None,
    subtitle: Optional[str] = None,
    visibility: Optional[str] = None,
    tags: Optional[str] = None,
    send_email: Optional[bool] = None,
    **kwargs
) -> str:
    """
    Main tool function called by Tool Calling LLM.

    Returns: JSON string with result
    """
```

**Workflow**:

1. **Validate Platform**:
   ```python
   supported_platforms = ["substack", "medium", "twitter"]
   if platform not in supported_platforms:
       return error
   ```

2. **Load Configuration**:
   ```python
   config = SocialMediaConfig()
   if not config.is_platform_enabled(platform):
       return error
   ```

3. **Validate Account**:
   ```python
   if not config.validate_account(platform, account):
       return error
   ```

4. **Create Publisher**:
   ```python
   account_config = config.get_account(platform, account)
   settings = config.get_platform_settings(platform)

   if platform == "substack":
       publisher = SubstackPublisher(account_config, settings)
   ```

5. **Publish Content**:
   ```python
   result = publisher.publish_post(
       title=title,
       content=content,
       **kwargs
   )
   ```

6. **Return Result**:
   ```python
   return json.dumps(result.to_dict())
   ```

**Tool Metadata** (for Tool Calling LLM):

```python
TOOL_METADATA = {
    "name": "social_media_publisher",
    "description": "Publish content to social media platforms",
    "parameters": {
        "type": "object",
        "properties": {
            "platform": {"type": "string", "enum": ["substack", "medium", "twitter"]},
            "content": {"type": "string"},
            "title": {"type": "string"},
            # ... more parameters ...
        },
        "required": ["platform", "content"]
    }
}
```

---

## Configuration System

### YAML Configuration (`config/social_media_accounts.yaml`)

**Structure**:

```yaml
# Account definitions
accounts:
  <platform_name>:
    - name: <account_identifier>
      description: <human_readable_description>
      <platform_specific_fields>
      enabled: <true|false>
      default: <true|false>

# Platform-specific settings
settings:
  <platform_name>:
    <setting_key>: <setting_value>

# Global defaults
defaults:
  save_drafts: <true|false>
  drafts_directory: <path>
  require_confirmation: <true|false>
  log_posts: <true|false>
  posts_log_file: <path>

# Feature flags
features:
  enable_<platform>: <true|false>
```

**Example**:

```yaml
accounts:
  substack:
    - name: "tech-blog"
      description: "Technical writing blog"
      publication_url: "https://tech-blog.substack.com"
      email_env: "SUBSTACK_TECH_EMAIL"
      password_env: "SUBSTACK_TECH_PASSWORD"
      enabled: true
      default: true

settings:
  substack:
    default_visibility: "everyone"
    default_send_email: true

defaults:
  save_drafts: true
  drafts_directory: "./drafts/social_media"
  log_posts: true
  posts_log_file: "./logs/social_media_posts.json"

features:
  enable_substack: true
  enable_medium: false
  enable_twitter: false
```

### Environment Variables (`.env`)

**Security Model**:
- YAML files: Configuration, references to environment variables
- `.env` file: Actual credentials, NOT in version control

**Naming Convention**: `<PLATFORM>_<ACCOUNT>_<CREDENTIAL_TYPE>`

**Examples**:
```bash
# Substack
SUBSTACK_TECH_EMAIL=tech@example.com
SUBSTACK_TECH_PASSWORD=secure_password_here

# Medium
MEDIUM_TECH_TOKEN=integration_token_here

# Twitter
TWITTER_TECH_API_KEY=api_key_here
TWITTER_TECH_API_SECRET=api_secret_here
TWITTER_TECH_ACCESS_TOKEN=access_token_here
TWITTER_TECH_ACCESS_SECRET=access_secret_here
```

**Access in Code**:
```python
email = os.getenv("SUBSTACK_TECH_EMAIL")
```

---

## Plugin Development

### Adding a New Platform

**Step-by-Step Guide**:

#### 1. Create Publisher Class

Create `user_tools/social_media/publishers/<platform>_publisher.py`:

```python
from user_tools.social_media.base import SocialMediaPublisher, PublishResult
from typing import Dict, Any, Optional

class NewPlatformPublisher(SocialMediaPublisher):
    def __init__(self, account_config: Dict[str, Any], settings: Dict[str, Any]):
        super().__init__("<platform_name>", account_config, settings)
        self.client = None

    def authenticate(self) -> bool:
        """Implement platform-specific authentication"""
        # 1. Get credentials from environment
        api_key = self.get_credential(self.account_config.get("api_key_env"))

        # 2. Authenticate with platform SDK
        self.client = PlatformSDK(api_key=api_key)

        # 3. Set authenticated flag
        self.authenticated = True
        return True

    def publish_post(
        self,
        title: str,
        content: str,
        **kwargs
    ) -> PublishResult:
        """Implement platform-specific publishing"""
        # 1. Ensure authenticated
        if not self.authenticated:
            if not self.authenticate():
                return PublishResult(
                    success=False,
                    platform="<platform>",
                    account=self.account_name,
                    error="Authentication failed"
                )

        # 2. Save draft if configured
        if self.settings.get("save_drafts", True):
            self.save_draft(title, content, kwargs)

        # 3. Publish using platform SDK
        try:
            response = self.client.publish(
                title=title,
                content=content,
                **kwargs
            )

            # 4. Create success result
            result = PublishResult(
                success=True,
                platform="<platform>",
                account=self.account_name,
                post_url=response.url,
                post_id=response.id
            )

            # 5. Log the post
            self.log_post(result)

            return result

        except Exception as e:
            # 6. Return failure result
            return PublishResult(
                success=False,
                platform="<platform>",
                account=self.account_name,
                error=str(e)
            )
```

#### 2. Update Main Tool Interface

Edit `user_tools/social_media_publisher.py`:

```python
from user_tools.social_media.publishers.newplatform_publisher import NewPlatformPublisher

def social_media_publisher(...):
    ...
    if platform == "newplatform":
        publisher = NewPlatformPublisher(account_config, settings)
        result = publisher.publish_post(...)
    ...
```

#### 3. Update Configuration

Add to `config/social_media_accounts.yaml`:

```yaml
accounts:
  newplatform:
    - name: "account1"
      description: "My account"
      <platform_specific_fields>
      enabled: true
      default: true

settings:
  newplatform:
    <platform_specific_settings>

features:
  enable_newplatform: true
```

#### 4. Add Credentials Template

Update `.env.example`:

```bash
# New Platform Credentials
NEWPLATFORM_ACCOUNT1_API_KEY=your_api_key_here
```

#### 5. Add Dependencies

Update `requirements.txt`:

```
# New Platform SDK
newplatform-sdk>=1.0.0
```

#### 6. Update Documentation

- Update `SOCIAL_MEDIA_PUBLISHING_GUIDE.md` with user-facing instructions
- Update this implementation guide with technical details

---

## Integration with Tool System

### Tool Registration

The `social_media_publisher` tool must be registered with the Tool Manager in `fastapi_server_complete.py`.

**Registration Code** (example):

```python
from user_tools.social_media_publisher import social_media_publisher, TOOL_METADATA

# In tool manager initialization
self.tools["social_media_publisher"] = {
    "function": social_media_publisher,
    "metadata": TOOL_METADATA
}
```

### Tool Calling LLM Detection

The Tool Calling LLM needs to be able to detect when to use the social media tool.

**Prompt Patterns**:
- "Post to Substack..."
- "Publish to Medium..."
- "Tweet about..."
- "Share on Twitter..."

**Tool Call Example**:

```json
{
  "name": "social_media_publisher",
  "arguments": {
    "platform": "substack",
    "title": "AI Revolution",
    "content": "<h1>Latest AI Developments</h1><p>...</p>",
    "account": "tech-blog",
    "visibility": "everyone",
    "send_email": true
  }
}
```

### POST-LLM vs PRE-LLM Execution

**Typical Flow**: POST-LLM (content generation first)

```
User: "Search for AI news and post to Substack"
  ↓
Tool Calling LLM detects: search_tool + social_media_publisher
  ↓
Search deferred to POST-LLM
Social media deferred to POST-LLM
  ↓
Primary LLM generates formatted article
  ↓
POST-LLM: search executes, social_media_publisher executes
  ↓
Article published
```

**Alternative Flow**: PRE-LLM (existing content)

```
User: "Post the above article to Substack"
  ↓
Tool Calling LLM detects: social_media_publisher + "above" keyword
  ↓
Content extracted from conversation history
  ↓
PRE-LLM: social_media_publisher executes immediately
  ↓
Article published
```

---

## Testing Strategy

### Unit Testing

**Test Coverage**:

1. **Base Publisher**:
   - `PublishResult` serialization
   - Helper methods (get_credential, save_draft, log_post)

2. **Configuration Loader**:
   - YAML parsing
   - Account retrieval (default, specific)
   - Validation logic
   - Feature flag checking

3. **Platform Publishers**:
   - Authentication success/failure
   - Publishing success/failure
   - Error handling
   - Draft saving
   - Post logging

**Example Test**:

```python
import pytest
from user_tools.social_media.config_loader import SocialMediaConfig

def test_get_default_account():
    config = SocialMediaConfig()
    account = config.get_account("substack")

    assert account is not None
    assert account["default"] == True
    assert account["enabled"] == True

def test_validate_account_missing_credentials():
    config = SocialMediaConfig()
    # Assuming credentials not in test environment
    result = config.validate_account("substack", "test-account")
    assert result == False
```

### Integration Testing

**Test Scenarios**:

1. **End-to-End Publishing**:
   - Authenticate with real account (test mode)
   - Publish test post
   - Verify post URL returned
   - Verify post appears on platform
   - Clean up (delete test post)

2. **Configuration Changes**:
   - Disable account, verify publishing fails
   - Enable account, verify publishing succeeds
   - Change default account, verify correct account used

3. **Error Handling**:
   - Invalid credentials → authentication fails
   - Platform unavailable → graceful error
   - Missing configuration → clear error message

**Example Integration Test**:

```python
import pytest
from user_tools.social_media_publisher import social_media_publisher
import json
import os

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("SUBSTACK_TEST_EMAIL"),
    reason="Substack test credentials not available"
)
def test_publish_to_substack():
    result_json = social_media_publisher(
        platform="substack",
        title="Test Post - Automated Testing",
        content="<p>This is a test post from automated testing.</p>",
        account="test-account"
    )

    result = json.loads(result_json)

    assert result["success"] == True
    assert "post_url" in result
    assert "substack.com" in result["post_url"]

    # Clean up: delete test post
    # (Implementation depends on platform API)
```

### Manual Testing Checklist

Before releasing new platform support:

- [ ] Authenticate with real account
- [ ] Publish test post with all features (title, subtitle, visibility, etc.)
- [ ] Verify post appears correctly on platform
- [ ] Test multiple accounts
- [ ] Test default account selection
- [ ] Test error scenarios (wrong credentials, disabled account)
- [ ] Verify draft saving
- [ ] Verify post logging
- [ ] Test with real user prompts
- [ ] Delete test posts

---

## Future Enhancements

### Planned Features

#### 1. Scheduled Publishing

**Concept**: Schedule posts for future publication

**Configuration**:
```yaml
features:
  enable_scheduling: true
```

**Usage**:
```
"Post to Substack tomorrow at 9 AM"
```

**Implementation**:
- Task queue (Celery, Redis)
- Scheduled task execution
- Post status tracking

#### 2. Cross-Posting

**Concept**: Publish to multiple platforms simultaneously

**Usage**:
```
"Post to Substack and Medium about AI developments"
```

**Implementation**:
- Parallel publishing to multiple platforms
- Format conversion (HTML for Substack, Markdown for Medium)
- Unified result reporting

#### 3. Post Analytics

**Concept**: Track post performance (views, likes, comments)

**Usage**:
```
"Show analytics for my last Substack post"
```

**Implementation**:
- Platform API integration for analytics
- Data aggregation and storage
- Visualization (charts, trends)

#### 4. Post Management

**Concept**: Update or delete published posts

**Usage**:
```
"Update my last Substack post with new information"
"Delete the post about quantum computing"
```

**Implementation**:
- Post ID tracking
- Update/delete API calls
- Confirmation before destructive operations

#### 5. Media Upload

**Concept**: Upload images, videos directly to posts

**Usage**:
```
"Post to Substack with the image generated earlier"
```

**Implementation**:
- Image/video upload to platform
- Embed in post content
- Alt text and captions

#### 6. Thread Support (Twitter)

**Concept**: Split long content into Twitter threads

**Usage**:
```
"Tweet this article as a thread"
```

**Implementation**:
- Content splitting (280 char chunks)
- Thread composition
- Maintain continuity with numbering

---

## Appendix

### Platform API Documentation

**Substack**:
- Unofficial library: https://github.com/iloveitaly/python-substack
- No official API documentation
- Risk: May break with Substack changes

**Medium**:
- Official API: https://github.com/Medium/medium-api-docs
- Integration tokens: https://medium.com/me/settings/security
- Note: Closed to new applications

**Twitter/X**:
- API v2: https://developer.twitter.com/en/docs/twitter-api
- OAuth 2.0: https://developer.twitter.com/en/docs/authentication/oauth-2-0
- Pricing: https://developer.twitter.com/en/portal/products

### Dependencies

```python
# Substack
python-substack>=1.0.0

# Medium (planned)
medium-api>=1.0.0  # or requests for manual API calls

# Twitter (planned)
tweepy>=4.14.0     # Twitter API v2 library
```

### Error Codes

**Common Error Patterns**:

```python
# Authentication Errors
{
    "success": False,
    "error": "Authentication failed",
    "hint": "Check credentials in .env file"
}

# Configuration Errors
{
    "success": False,
    "error": "Account validation failed",
    "hint": "Check that account is enabled and credentials are set"
}

# Platform Errors
{
    "success": False,
    "error": "Platform-specific error message",
    "error_type": "ApiException"
}
```

### Troubleshooting Guide for Developers

**Problem**: Import errors when adding new publisher

**Solution**: Ensure `__init__.py` files are updated:
```python
# user_tools/social_media/publishers/__init__.py
from user_tools.social_media.publishers.newplatform_publisher import NewPlatformPublisher
__all__ = ['SubstackPublisher', 'NewPlatformPublisher']
```

**Problem**: Configuration not loading

**Solution**: Check YAML syntax, ensure proper indentation

**Problem**: Credentials not found

**Solution**:
1. Verify `.env` file loaded
2. Check environment variable names match YAML references
3. Restart server to reload environment

---

**Version History**:
- v1.0.3.11 (Oct 18, 2025): Initial implementation guide
  - Base architecture documented
  - Substack implementation detailed
  - Plugin development guide
  - Testing strategy outlined

---

**For User Guide**: See `/docs/production/SOCIAL_MEDIA_PUBLISHING_GUIDE.md`
**For Research**: See `/docs/SOCIAL_MEDIA_PLUGINS_RESEARCH.md`
