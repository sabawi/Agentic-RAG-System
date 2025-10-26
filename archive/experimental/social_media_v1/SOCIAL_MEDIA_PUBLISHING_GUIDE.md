# Social Media Publishing Guide

**Version**: 1.0.3.11
**Last Updated**: October 18, 2025

---

## Overview

The Agentic-RAG system now supports publishing content directly to social media platforms including Substack, Medium, and Twitter/X. This guide explains how to configure accounts, use the publishing features, and understand the workflow.

**Currently Supported Platforms**:
- ✅ **Substack** - Full implementation (v1.0.3.11)
- 🔜 **Medium** - Coming soon
- 🔜 **Twitter/X** - Coming soon

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Publishing to Substack](#publishing-to-substack)
4. [Usage Patterns](#usage-patterns)
5. [Account Management](#account-management)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

---

## Quick Start

### Prerequisites

1. **Substack Account**: You need an active Substack publication
2. **Credentials**: Email and password for your Substack account
3. **Configuration**: Set up in `config/social_media_accounts.yaml` and `.env`

### Basic Publishing Example

```
User: "Search for latest AI news and post it to Substack 'agentic-developer'"
```

The system will:
1. Search for AI news
2. Format the content as HTML
3. Publish to your Substack publication
4. Return the published post URL

---

## Configuration

### Step 1: Configure Account (YAML)

Edit `config/social_media_accounts.yaml`:

```yaml
accounts:
  substack:
    - name: "agentic-developer"
      description: "Technical blog for AI and development topics"
      publication_url: "https://agentic-developer.substack.com"
      email_env: "SUBSTACK_AGENTIC_EMAIL"
      password_env: "SUBSTACK_AGENTIC_PASSWORD"
      enabled: true
      default: true
```

**Important Fields**:
- `name`: Unique identifier for this account
- `publication_url`: Your Substack publication URL
- `email_env`: Environment variable name for login email
- `password_env`: Environment variable name for password
- `enabled`: Set to `true` to activate
- `default`: Set to `true` to use when no account specified

### Step 2: Add Credentials (.env)

Add to your `.env` file (NOT in version control):

```bash
# Substack Credentials
SUBSTACK_AGENTIC_EMAIL=your_email@example.com
SUBSTACK_AGENTIC_PASSWORD=your_secure_password
```

**Security Note**: Never commit `.env` file to git. Use `.env.example` for templates.

### Step 3: Enable Platform

In `config/social_media_accounts.yaml`, ensure feature is enabled:

```yaml
features:
  enable_substack: true
```

---

## Publishing to Substack

### Basic Publishing

**Pattern**: `Post to Substack [account] [content description]`

**Examples**:

```
✅ "Post to Substack 'agentic-developer' a summary of recent AI developments"

✅ "Search for machine learning news and publish to Substack"

✅ "Create a blog post about quantum computing and post it to Substack 'agentic-developer'"
```

### With Specific Options

You can control:
- **Title**: Automatically generated or specified
- **Subtitle**: Optional subtitle
- **Visibility**: `everyone` (default), `paid_subscribers`, `founding_members`
- **Email Notification**: Send to subscribers (default: true)

**Examples**:

```
✅ "Post to Substack with title 'AI Revolution' and subtitle 'A Technical Analysis'"

✅ "Post to Substack for paid subscribers only"

✅ "Post to Substack without sending email notification"
```

### Multi-Step Workflow

**Step 1**: Generate content
```
User: "Write a detailed article about the benefits of AI in healthcare"
```

**Step 2**: Publish the generated content
```
User: "Post the above article to Substack 'agentic-developer' with title 'AI in Healthcare'"
```

---

## Usage Patterns

### Pattern 1: Research + Publish

**Use Case**: Search for information and publish the findings

```
"Search for latest developments in renewable energy and post to Substack"
```

**How It Works**:
1. Tool Calling LLM detects search + social media tools
2. Search executes and gathers data
3. Primary LLM formats content as HTML article
4. Substack publisher publishes the article
5. Returns post URL

### Pattern 2: Generate + Publish

**Use Case**: Generate original content and publish

```
"Write an analysis of current tech trends. Post it to Substack 'tech-writer'"
```

**How It Works**:
1. Primary LLM generates article content
2. Content formatted as HTML
3. Published to specified Substack account
4. Returns confirmation and URL

### Pattern 3: Publish Previous Response

**Use Case**: Generate content first, then publish it

```
Step 1: "Explain the concept of neural networks in simple terms"
Step 2: "Post the above explanation to Substack with title 'Neural Networks 101'"
```

**How It Works**:
1. First prompt generates content
2. Second prompt references previous content
3. System extracts previous response
4. Publishes to Substack
5. Returns post URL

---

## Account Management

### Multiple Accounts

You can configure multiple Substack accounts:

```yaml
accounts:
  substack:
    - name: "tech-blog"
      publication_url: "https://tech-blog.substack.com"
      email_env: "SUBSTACK_TECH_EMAIL"
      password_env: "SUBSTACK_TECH_PASSWORD"
      enabled: true
      default: true

    - name: "personal-blog"
      publication_url: "https://personal.substack.com"
      email_env: "SUBSTACK_PERSONAL_EMAIL"
      password_env: "SUBSTACK_PERSONAL_PASSWORD"
      enabled: true
      default: false
```

**Specify Account in Prompt**:
```
"Post to Substack 'personal-blog' about my weekend adventure"
```

### Default Account

If you don't specify an account name, the system uses the `default: true` account:

```
"Post to Substack about AI ethics"  # Uses default account
```

### Enabling/Disabling Accounts

Set `enabled: false` to temporarily disable an account:

```yaml
- name: "old-blog"
  enabled: false  # Won't be used
```

---

## Platform Settings

### Substack-Specific Settings

Configure defaults in `config/social_media_accounts.yaml`:

```yaml
settings:
  substack:
    default_visibility: "everyone"  # or "paid_subscribers", "founding_members"
    default_send_email: true        # Send notification to subscribers
```

### Global Publishing Settings

```yaml
defaults:
  save_drafts: true                     # Save local copies before publishing
  drafts_directory: "./drafts/social_media"
  require_confirmation: false           # If true, ask before publishing
  log_posts: true                       # Log all published posts
  posts_log_file: "./logs/social_media_posts.json"
```

**Draft Saves**: When `save_drafts: true`, the system saves a JSON copy of each post before publishing to `./drafts/social_media/`. Useful for backup and review.

**Post Logging**: When `log_posts: true`, all published posts are logged to `./logs/social_media_posts.json` with timestamps, URLs, and metadata.

---

## Visibility Options

### Substack Visibility Levels

1. **`everyone`** (default)
   - Public post visible to all
   - Free subscribers receive it
   - Most common for public blogs

2. **`paid_subscribers`**
   - Only paying subscribers can read
   - Good for premium content
   - Requires Substack paid subscriptions enabled

3. **`founding_members`**
   - Highest tier subscribers only
   - Exclusive content
   - Requires founding member tier setup

**Usage**:
```
"Post to Substack for paid subscribers only"
```

---

## Troubleshooting

### Problem: "Authentication failed"

**Possible Causes**:
1. Incorrect credentials in `.env`
2. Environment variables not loaded
3. Substack password changed

**Solutions**:
1. Verify credentials in `.env`:
   ```bash
   echo $SUBSTACK_AGENTIC_EMAIL
   echo $SUBSTACK_AGENTIC_PASSWORD
   ```
2. Restart server to reload environment
3. Check Substack account is active

### Problem: "Account is disabled"

**Cause**: Account has `enabled: false` in configuration

**Solution**: Edit `config/social_media_accounts.yaml`:
```yaml
- name: "your-account"
  enabled: true  # Change from false to true
```

### Problem: "python-substack library not installed"

**Cause**: Missing dependency

**Solution**:
```bash
source venv/bin/activate  # Activate virtual environment
pip install python-substack
```

### Problem: "Platform substack is not enabled"

**Cause**: Feature flag disabled in configuration

**Solution**: Edit `config/social_media_accounts.yaml`:
```yaml
features:
  enable_substack: true  # Ensure this is true
```

### Problem: "Title is required for Substack posts"

**Cause**: Substack requires all posts to have a title

**Solution**: Include title in your prompt:
```
"Post to Substack with title 'My Article Title'"
```

Or let the AI generate a title from content:
```
"Post to Substack about AI developments"  # AI will create appropriate title
```

---

## Security Best Practices

### 1. Credential Storage

✅ **DO**:
- Store credentials in `.env` file
- Use environment variable references in YAML
- Keep `.env` out of version control
- Use `.env.example` for templates

❌ **DON'T**:
- Hardcode passwords in YAML files
- Commit `.env` to git
- Share credentials in plain text
- Use same password across accounts

### 2. Access Control

- Use separate Substack accounts for different purposes
- Limit who has access to production `.env` file
- Rotate passwords periodically
- Monitor published posts log for unauthorized access

### 3. Draft Review

Enable draft saving for review before publishing:

```yaml
defaults:
  save_drafts: true
  drafts_directory: "./drafts/social_media"
```

Review drafts in `./drafts/social_media/` before they're published.

### 4. Confirmation Mode

For high-stakes publishing, enable confirmation:

```yaml
defaults:
  require_confirmation: true
```

System will ask for confirmation before publishing.

---

## Coming Soon

### Medium Publishing (Planned)

```yaml
accounts:
  medium:
    - name: "tech-writer"
      integration_token_env: "MEDIUM_TECH_TOKEN"
      enabled: true
```

**Usage** (future):
```
"Post to Medium about machine learning"
```

### Twitter/X Publishing (Planned)

```yaml
accounts:
  twitter:
    - name: "tech-updates"
      api_key_env: "TWITTER_TECH_API_KEY"
      api_secret_env: "TWITTER_TECH_API_SECRET"
      enabled: true
```

**Usage** (future):
```
"Tweet about this AI breakthrough"
```

### Advanced Features (Planned)

- 📅 **Scheduled Publishing**: Schedule posts for future dates
- 🔄 **Cross-Posting**: Publish to multiple platforms simultaneously
- 📊 **Analytics**: Track post performance
- ✏️ **Post Updates**: Edit published posts
- 🗑️ **Post Deletion**: Remove published posts

---

## Examples by Use Case

### Technical Blog

```
User: "Search for latest developments in quantum computing and create a technical analysis. Post it to Substack 'tech-blog' with subtitle 'A Deep Dive into Quantum Algorithms'"

System:
1. Searches for quantum computing news
2. Generates technical analysis
3. Formats as HTML
4. Publishes to Substack
5. Returns: "✅ Published to Substack (tech-blog): https://tech-blog.substack.com/p/quantum-computing-deep-dive"
```

### Newsletter Update

```
User: "Summarize this week's AI news and post to Substack 'ai-weekly' for everyone with email notification"

System:
1. Gathers AI news from current week
2. Creates formatted summary
3. Publishes publicly
4. Sends email to all subscribers
5. Returns post URL
```

### Premium Content

```
User: "Write an advanced tutorial on transformer architectures. Post to Substack for paid subscribers only"

System:
1. Generates advanced tutorial
2. Formats with code examples
3. Publishes with paid subscriber restriction
4. Returns post URL
```

---

## Support and Feedback

### Getting Help

1. Check this guide for common patterns
2. Review troubleshooting section
3. Check logs: `./logs/social_media_posts.json`
4. Review drafts: `./drafts/social_media/`

### Known Limitations

1. **Unofficial API**: Substack support uses unofficial `python-substack` library
   - May break if Substack changes their API
   - Monitor for errors and report issues

2. **Character Limits**: Platform-specific limits apply
   - Substack: No strict limit (reasonable article length)
   - Twitter: 280 characters per tweet (future)

3. **Media Uploads**: Image uploading not yet supported
   - HTML content with image URLs works
   - Direct image upload coming in future version

### Feature Requests

Have ideas for improvements? Check project documentation for contribution guidelines.

---

## Version History

- **v1.0.3.11** (Oct 18, 2025): Initial Substack publishing implementation
  - Configuration system with YAML + environment variables
  - Base plugin architecture for extensibility
  - Substack publisher with full authentication and posting
  - Draft saving and post logging
  - Multiple account support

---

**For Technical Details**: See `/docs/SOCIAL_MEDIA_PLUGINS_RESEARCH.md` for architecture and implementation details.
