# Social Media Publishing Plugins - Research & Design

**Created**: October 18, 2025
**Status**: Research Phase
**Target Version**: v1.0.4.0

---

## Executive Summary

Research findings for implementing social media publishing plugins for Substack, Medium, and Twitter/X. This document outlines authentication methods, API capabilities, limitations, and recommended implementation approach.

---

## Platform Research

### 1. Substack

**API Status**: ❌ No official API
**Posting Capability**: ⚠️ Unofficial Python library available
**Complexity**: MEDIUM

#### Authentication Methods
1. **Email + Password**
   - Traditional username/password auth
   - ⚠️ WARNING: New accounts may not have passwords (magic link only)
   - Security: Store in `.env` file

#### Available Library
```bash
pip install python-substack
```

**GitHub**: https://github.com/ma2za/python-substack
**PyPI**: https://pypi.org/project/python-substack/

#### Code Example
```python
import os
from substack import Api
from substack.post import Post

api = Api(
    email=os.getenv("SUBSTACK_EMAIL"),
    password=os.getenv("SUBSTACK_PASSWORD"),
)

user_id = api.get_user_id()

post = Post(
    title="Article Title",
    subtitle="Article Subtitle",
    user_id=user_id
)

post.add({'type': 'paragraph', 'content': 'Content here'})

# Create draft, then publish
draft = api.post_draft(post.get_draft())
api.prepublish_draft(draft.get("id"))
api.publish_draft(draft.get("id"))
```

#### Supported Features
- ✅ Title, subtitle, content
- ✅ Multiple paragraphs
- ✅ Formatting (bold, links)
- ✅ Images
- ✅ Paywall boundaries
- ✅ Draft → Prepublish → Publish workflow

#### Limitations
- ❌ No official API (library may break if Substack changes internals)
- ⚠️ Magic link accounts can't authenticate programmatically
- ⚠️ No OAuth support
- ⚠️ Rate limits unknown

---

### 2. Medium

**API Status**: 🟡 Official API (Closed to new apps as of Jan 2025)
**Posting Capability**: ✅ Full support with existing tokens
**Complexity**: LOW

#### Authentication Methods
1. **Integration Token** (Self-issued)
   - Permanent access token
   - Generated in Medium settings
   - ✅ **Best option for automation**
   - Security: Store in `.env` file

2. **OAuth 2.0**
   - ⚠️ Closed to new integrations (Jan 2025)
   - Existing tokens still work
   - Not recommended for new implementations

#### Getting Integration Token
1. Go to: https://medium.com/me/settings
2. Under "Integration tokens", select "Create an integration token"
3. Copy token (starts with `2` usually)

#### API Endpoint
```
POST https://api.medium.com/v1/users/<authorId>/posts
```

#### Code Example
```python
import requests

# Get user ID
user_response = requests.get(
    'https://api.medium.com/v1/me',
    headers={'Authorization': f'Bearer {MEDIUM_TOKEN}'}
)
author_id = user_response.json()['data']['id']

# Create post
post_data = {
    'title': 'Article Title',
    'contentFormat': 'html',  # or 'markdown'
    'content': '<h1>Content</h1><p>Article content here</p>',
    'publishStatus': 'public'  # 'public', 'draft', or 'unlisted'
}

response = requests.post(
    f'https://api.medium.com/v1/users/{author_id}/posts',
    json=post_data,
    headers={'Authorization': f'Bearer {MEDIUM_TOKEN}'}
)
```

#### Supported Features
- ✅ Title, content
- ✅ HTML or Markdown format
- ✅ Tags (up to 5)
- ✅ Canonical URL
- ✅ License selection
- ✅ Publish status (public, draft, unlisted)
- ✅ Notify followers option

#### Limitations
- ❌ New integrations closed as of Jan 2025 (existing tokens work)
- ⚠️ API "not officially supported" but functional
- ⚠️ Rate limits: Unknown, but conservative approach recommended

#### Documentation
- **Official**: https://github.com/Medium/medium-api-docs
- **Status**: Archived but functional

---

### 3. Twitter/X

**API Status**: ✅ Official API v2
**Posting Capability**: ✅ Full support
**Complexity**: MEDIUM-HIGH

#### Authentication Methods
1. **OAuth 2.0 Authorization Code Flow with PKCE** (Recommended)
   - User logs in once
   - Access token valid 2 hours
   - Refresh token valid 6 months
   - ✅ **Most secure for user context**

2. **OAuth 1.0a**
   - API Key + API Secret + Access Token + Access Token Secret
   - No expiration
   - Simpler but less secure

3. **Bearer Token** (App-Only)
   - Read-only access
   - ❌ Cannot post tweets

#### API Pricing (2025)
- **Free Tier**: 50 tweets/day (very limited)
- **Basic Tier**: $100/month
- **Pro Tier**: Higher limits

⚠️ **Cost consideration**: Free tier may be too limited for production use

#### Available Libraries
1. **Tweepy** (Most popular)
   ```bash
   pip install tweepy
   ```
   - Full OAuth 2.0 support
   - Active development
   - Comprehensive documentation

2. **python-twitter-v2**
   ```bash
   pip install python-twitter-v2
   ```
   - Lighter weight alternative

#### Code Example (Tweepy with OAuth 2.0)
```python
import tweepy

# OAuth 2.0 with PKCE
oauth2_user_handler = tweepy.OAuth2UserHandler(
    client_id=TWITTER_CLIENT_ID,
    redirect_uri="http://localhost:8000/callback",
    scope=["tweet.read", "tweet.write", "users.read"],
    client_secret=TWITTER_CLIENT_SECRET
)

# Get authorization URL
auth_url = oauth2_user_handler.get_authorization_url()
# User visits URL, gets code
access_token = oauth2_user_handler.fetch_token(code)

# Create client
client = tweepy.Client(
    bearer_token=access_token['access_token']
)

# Post tweet
response = client.create_tweet(text="Hello from Python!")
```

#### Supported Features
- ✅ Text tweets (280 characters)
- ✅ Media attachments (images, videos)
- ✅ Polls
- ✅ Quote tweets
- ✅ Reply to tweets
- ✅ Thread support

#### Limitations
- ⚠️ 280 character limit (extended with Twitter Blue)
- ⚠️ Rate limits: 50 tweets/day (Free), higher on paid tiers
- ⚠️ OAuth 2.0 requires web callback (complex for CLI tools)
- ⚠️ Cost: Free tier very limited

#### Documentation
- **Official**: https://developer.x.com/en/docs/twitter-api
- **Tweepy**: https://docs.tweepy.org/

---

## Unified Design Proposal

### Configuration File Structure

**File**: `config/social_media_accounts.yaml`

```yaml
version: "1.0"
accounts:
  # Substack Accounts
  substack:
    agentic-developer:
      enabled: true
      platform: substack
      auth_method: email_password
      email_env: SUBSTACK_AGENTIC_EMAIL
      password_env: SUBSTACK_AGENTIC_PASSWORD
      publication_url: "https://agentic-developer.substack.com"
      default_settings:
        paywall: false
        send_notifications: true

    personal-blog:
      enabled: false
      platform: substack
      auth_method: email_password
      email_env: SUBSTACK_PERSONAL_EMAIL
      password_env: SUBSTACK_PERSONAL_PASSWORD
      publication_url: "https://personal-blog.substack.com"

  # Medium Accounts
  medium:
    tech-writer:
      enabled: true
      platform: medium
      auth_method: integration_token
      token_env: MEDIUM_TECH_TOKEN
      username: "@techwriter"
      default_settings:
        content_format: html  # html or markdown
        publish_status: public  # public, draft, unlisted
        notify_followers: true
        license: all-rights-reserved

  # Twitter/X Accounts
  twitter:
    main-account:
      enabled: true
      platform: twitter
      auth_method: oauth2_pkce
      client_id_env: TWITTER_CLIENT_ID
      client_secret_env: TWITTER_CLIENT_SECRET
      access_token_env: TWITTER_ACCESS_TOKEN
      refresh_token_env: TWITTER_REFRESH_TOKEN
      username: "@yourusername"
      default_settings:
        max_length: 280
        enable_threading: true  # Auto-split long posts

    bot-account:
      enabled: false
      platform: twitter
      auth_method: oauth1a
      api_key_env: TWITTER_BOT_API_KEY
      api_secret_env: TWITTER_BOT_API_SECRET
      access_token_env: TWITTER_BOT_ACCESS_TOKEN
      access_secret_env: TWITTER_BOT_ACCESS_SECRET
      username: "@botaccount"
```

### Environment Variables (`.env`)

```bash
# Substack Credentials
SUBSTACK_AGENTIC_EMAIL=user@example.com
SUBSTACK_AGENTIC_PASSWORD=secure_password_here

# Medium Integration Tokens
MEDIUM_TECH_TOKEN=2xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Twitter/X OAuth 2.0 Credentials
TWITTER_CLIENT_ID=your_client_id
TWITTER_CLIENT_SECRET=your_client_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_REFRESH_TOKEN=your_refresh_token
```

---

## Plugin Architecture Design

### Directory Structure
```
user_tools/
├── social_media/
│   ├── __init__.py
│   ├── base.py                    # Base class for all social media plugins
│   ├── substack_publisher.py     # Substack implementation
│   ├── medium_publisher.py        # Medium implementation
│   ├── twitter_publisher.py       # Twitter implementation
│   └── config_loader.py           # Load social_media_accounts.yaml
└── social_media_publisher.py      # Main tool (Tool Calling LLM interface)
```

### Base Class Design

```python
# user_tools/social_media/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class SocialMediaPublisher(ABC):
    """Base class for all social media publishing plugins"""

    def __init__(self, account_name: str, config: Dict[str, Any]):
        self.account_name = account_name
        self.config = config
        self.platform = config.get('platform')
        self.enabled = config.get('enabled', False)

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the platform"""
        pass

    @abstractmethod
    def publish(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        Publish content to the platform

        Args:
            title: Post/article title
            content: Post/article content (HTML or markdown)
            **kwargs: Platform-specific options

        Returns:
            {
                'success': bool,
                'post_url': str,
                'post_id': str,
                'message': str
            }
        """
        pass

    @abstractmethod
    def create_draft(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        """Create draft without publishing"""
        pass

    def validate_config(self) -> bool:
        """Validate configuration and credentials"""
        if not self.enabled:
            return False
        return True
```

### Tool Interface Design

```python
# user_tools/social_media_publisher.py

def social_media_publisher(
    platform: str,
    account_name: str,
    title: str,
    content: str,
    publish_status: str = "publish",
    **kwargs
) -> str:
    """
    Publish content to social media platforms

    Args:
        platform: Platform name (substack, medium, twitter)
        account_name: Account identifier from config
        title: Post/article title
        content: Content to publish (HTML, markdown, or plain text)
        publish_status: "publish" (immediate) or "draft" (save only)
        **kwargs: Platform-specific options

    Returns:
        JSON string with publication result

    Examples:
        # Substack
        social_media_publisher(
            platform="substack",
            account_name="agentic-developer",
            title="AI News Summary",
            content="<h1>Latest AI Developments</h1>...",
            publish_status="publish"
        )

        # Medium
        social_media_publisher(
            platform="medium",
            account_name="tech-writer",
            title="Understanding LLMs",
            content="<p>Article content...</p>",
            content_format="html",
            tags=["AI", "Machine Learning"]
        )

        # Twitter
        social_media_publisher(
            platform="twitter",
            account_name="main-account",
            title="",  # Not used for tweets
            content="Check out this amazing AI development!",
            enable_threading=True
        )
    """
    pass
```

### Prompt Trigger Examples

```
User: "Post to substack 'agentic-developer' a summary of today's AI news"
→ Tool Call: social_media_publisher(
    platform="substack",
    account_name="agentic-developer",
    title="AI News Summary - [DATE]",
    content="[Generated content]"
)

User: "Share this on medium 'tech-writer' as a draft"
→ Tool Call: social_media_publisher(
    platform="medium",
    account_name="tech-writer",
    title="[Title from context]",
    content="[Content from context]",
    publish_status="draft"
)

User: "Tweet this summary to my main twitter account"
→ Tool Call: social_media_publisher(
    platform="twitter",
    account_name="main-account",
    title="",
    content="[Generated summary under 280 chars]"
)
```

---

## Implementation Phases

### Phase 1: Infrastructure (Week 1)
- [ ] Create `config/social_media_accounts.yaml` structure
- [ ] Create `user_tools/social_media/` directory
- [ ] Implement base class (`base.py`)
- [ ] Implement config loader (`config_loader.py`)
- [ ] Update `.env.example` with social media variables
- [ ] Add dependencies to `requirements.txt`

### Phase 2: Substack Plugin (Week 2)
- [ ] Install `python-substack` library
- [ ] Implement `SubstackPublisher` class
- [ ] Add authentication handling
- [ ] Add publish/draft functionality
- [ ] Add error handling and logging
- [ ] Test with real Substack account
- [ ] Document usage and limitations

### Phase 3: Main Tool Interface (Week 2-3)
- [ ] Create `social_media_publisher.py` tool
- [ ] Add to Tool Calling LLM system prompt
- [ ] Implement routing logic (platform → plugin)
- [ ] Add validation and error messages
- [ ] Test with various prompts
- [ ] Update user documentation

### Phase 4: Medium Plugin (Week 3)
- [ ] Implement `MediumPublisher` class
- [ ] Add integration token authentication
- [ ] Add publish/draft functionality
- [ ] Support HTML and Markdown formats
- [ ] Test with real Medium account
- [ ] Document usage

### Phase 5: Twitter/X Plugin (Week 4)
- [ ] Install `tweepy` library
- [ ] Implement `TwitterPublisher` class
- [ ] Add OAuth 2.0 PKCE authentication flow
- [ ] Add tweet posting with auto-threading
- [ ] Handle 280 character limit
- [ ] Test with real Twitter account
- [ ] Document API costs and limitations

### Phase 6: Documentation & Testing (Week 5)
- [ ] Comprehensive user guide
- [ ] Admin guide for setup
- [ ] Testing checklist
- [ ] Example prompts
- [ ] Troubleshooting guide

---

## Risk Assessment

### High Risk
1. **Substack - No Official API**
   - **Risk**: Library may break with Substack internal changes
   - **Mitigation**: Regular testing, version pinning, fallback to manual posting
   - **Impact**: HIGH - Plugin could stop working without notice

2. **Twitter - API Costs**
   - **Risk**: Free tier (50 tweets/day) too limited for production
   - **Mitigation**: Warn users, implement rate limiting, consider paid tier requirement
   - **Impact**: MEDIUM - Users must pay $100/month for reasonable usage

### Medium Risk
3. **Medium - API Deprecation**
   - **Risk**: API closed to new apps, may be fully deprecated
   - **Mitigation**: Document clearly, have migration plan
   - **Impact**: MEDIUM - Existing tokens work but future uncertain

4. **Authentication Security**
   - **Risk**: Credentials in `.env` file
   - **Mitigation**: Secure file permissions, git ignore, encryption option
   - **Impact**: MEDIUM - Standard security practices mitigate

### Low Risk
5. **Rate Limiting**
   - **Risk**: Hitting undocumented rate limits
   - **Mitigation**: Conservative posting, exponential backoff, user warnings
   - **Impact**: LOW - Can be managed with retry logic

---

## Dependencies Required

### Python Packages
```txt
# Social Media Publishing
python-substack>=1.0.0    # Substack (unofficial)
requests>=2.31.0          # Medium API calls
tweepy>=4.14.0            # Twitter/X API v2

# Existing (already in requirements.txt)
python-dotenv>=1.0.0      # Environment variables
pyyaml>=6.0              # YAML config parsing
```

### Platform Requirements
1. **Substack**: Email + password enabled account
2. **Medium**: Integration token from settings
3. **Twitter**: Developer account + OAuth 2.0 app setup

---

## Success Criteria

### Phase 1 (Substack)
- ✅ User can configure Substack account in YAML
- ✅ Tool authenticates with Substack
- ✅ User can post article with prompt: "Post to substack 'account-name' ..."
- ✅ Draft mode works
- ✅ Error messages are clear and actionable

### Phase 2 (Medium)
- ✅ User can configure Medium account with integration token
- ✅ Tool posts to Medium via official API
- ✅ HTML and Markdown formats supported
- ✅ Tags and settings work

### Phase 3 (Twitter)
- ✅ User can configure Twitter account with OAuth 2.0
- ✅ Tool posts tweets under 280 characters
- ✅ Auto-threading works for long content
- ✅ Rate limiting handled gracefully

---

## Next Steps

**DECISION POINT**: Which platform to implement first?

**Recommendation: Start with Substack**
- Simpler authentication (email/password)
- No API costs
- User's primary requested platform
- Proof of concept for architecture

**After User Approval**:
1. Create configuration file structure
2. Implement base class and infrastructure
3. Implement Substack plugin
4. Test end-to-end
5. Move to Medium, then Twitter

---

**Status**: ✅ Research Complete - Awaiting User Decision
