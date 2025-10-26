# Twitter API Setup Guide

**Status**: 🔧 Setup Required
**Date**: 2025-10-19
**Estimated Time**: 15-30 minutes

---

## Overview

To use the Twitter social media plugin, you need to:
1. Create a Twitter Developer account
2. Create an App in the Twitter Developer Portal
3. Generate API keys and access tokens
4. Add credentials to `.env` file
5. Test the connection

⚠️ **IMPORTANT**: Twitter API has **different pricing tiers**:
- **Free Tier**: Very limited (write-only, 1,500 tweets/month)
- **Basic Tier**: $100/month (3,000 tweets/month, read + write)
- **Pro Tier**: $5,000/month (300,000 tweets/month, full features)

For testing purposes, the **Free Tier** should be sufficient.

---

## Step 1: Create Twitter Developer Account

### 1.1 Apply for Developer Access

1. Go to: https://developer.twitter.com/
2. Click "Sign up" or "Apply" (if you already have a Twitter account, use it)
3. Choose your use case:
   - **Hobby**: For personal projects
   - **Professional**: For testing/development
   - **Academic**: If this is for research
4. Fill out the application:
   - **Name**: Your name
   - **Email**: Your email
   - **Country**: Your country
   - **Use case description**:
     ```
     I'm building an automated social media publishing system that allows
     posting content to multiple platforms (Twitter, Substack, Medium).
     This is for personal/business use to manage social media presence.
     ```
5. Agree to terms and submit
6. **Wait for approval** (usually instant to 24 hours)

### 1.2 Verify Your Email

- Check your email for verification link
- Click link to verify
- Return to developer portal

---

## Step 2: Create a Twitter App

### 2.1 Create New App

1. Once approved, go to: https://developer.twitter.com/en/portal/dashboard
2. Click "Create Project" or "Create App"
3. Fill in app details:
   - **App Name**: `SubstackRagTestApp` (or any unique name)
   - **Description**:
     ```
     Test application for automated social media publishing system.
     Allows posting tweets programmatically via API.
     ```
   - **Website URL**: Your website (or use `https://github.com/sabawi/Agentic-RAG-System`)
   - **Callback URL**: Leave blank (not needed for OAuth 1.0a user context)
   - **Organization**: Individual or your organization name

4. Click "Create"

### 2.2 Set App Permissions

1. In your app settings, go to "Settings" tab
2. Scroll to "User authentication settings"
3. Click "Edit"
4. Enable **OAuth 1.0a**
5. Set permissions:
   - ✅ **Read and Write** (required for posting)
   - ❌ Direct Messages (optional - we don't need this)
6. Set App Type:
   - Choose **"Web App, Automated App or Bot"**
7. Callback URL: `https://localhost` (required but won't be used)
8. Website URL: Your website
9. Click "Save"

---

## Step 3: Generate API Keys

### 3.1 Get Consumer Keys (API Keys)

1. In your app, go to "Keys and tokens" tab
2. Under **"Consumer Keys"**:
   - You'll see **API Key** (also called Consumer Key)
   - You'll see **API Secret** (also called Consumer Secret)
3. **Copy these immediately** - the secret won't be shown again!
4. Store temporarily in a secure note

### 3.2 Generate Access Tokens

1. Scroll down to **"Authentication Tokens"**
2. Click "Generate" under **"Access Token and Secret"**
3. You'll see:
   - **Access Token**
   - **Access Token Secret**
4. **Copy these immediately** - the secret won't be shown again!
5. Store temporarily in a secure note

### 3.3 Verify Permissions

Make sure the access token shows:
- **Access Level**: Read and Write
- **Owner**: Your Twitter username

If it shows "Read Only", regenerate the tokens after fixing app permissions.

---

## Step 4: Add Credentials to .env

### 4.1 Open .env File

```bash
cd /home/sabawi/Development/flaskserver
nano .env  # or use your preferred editor
```

### 4.2 Add Twitter Credentials

Add these lines to your `.env` file (at the end or in a Twitter section):

```bash
# =============================================================================
# TWITTER API CREDENTIALS (OAuth 1.0a)
# =============================================================================
# Get from: https://developer.twitter.com/en/portal/dashboard
# App: [Your App Name]
# Permissions: Read and Write
# =============================================================================

TWITTER_TEST_API_KEY=your_api_key_here
TWITTER_TEST_API_SECRET=your_api_secret_here
TWITTER_TEST_ACCESS_TOKEN=your_access_token_here
TWITTER_TEST_ACCESS_SECRET=your_access_token_secret_here
```

**Replace the placeholder values** with your actual credentials:
- `your_api_key_here` → Your API Key from step 3.1
- `your_api_secret_here` → Your API Secret from step 3.1
- `your_access_token_here` → Your Access Token from step 3.2
- `your_access_token_secret_here` → Your Access Token Secret from step 3.2

### 4.3 Save and Verify

1. Save the file
2. **Never commit .env to git!** (already in .gitignore)
3. Verify format:
   ```bash
   grep TWITTER .env
   ```
   You should see 4 lines with your credentials (values will be masked)

---

## Step 5: Test Twitter Connection

### 5.1 Quick Test Script

I'll create a test script for you that:
- Loads credentials from .env
- Tests authentication
- Verifies API access
- Posts a test tweet (with confirmation)

### 5.2 Run Test

```bash
cd /home/sabawi/Development/flaskserver
python3 tests/utilities/test_twitter_manual.py
```

---

## Twitter API Limitations

### Free Tier (Read and Write)
- **Tweets per month**: 1,500
- **Tweets per day**: ~50
- **Rate limits**: Very restrictive
- **Cost**: $0/month

### Basic Tier
- **Tweets per month**: 3,000
- **Cost**: $100/month
- **Additional features**: Read tweets, user lookup

### Important Notes
- **Duplicate tweets**: Twitter blocks exact duplicate text within ~24 hours
- **Rate limits**: 429 errors are common - plugin handles with retry
- **Character limit**: 280 chars (or 4,000 with Twitter Blue)
- **Media**: Requires separate upload API calls (not implemented yet)

---

## Available Twitter Functions

Based on our implementation and Twitter API v2:

### Supported ✅
- ✅ **Post tweet** (basic text up to 280 chars)
- ✅ **Reply to tweet** (create reply thread)
- ✅ **Quote tweet** (quote another tweet)
- ✅ **Create poll** (up to 4 options)
- ✅ **Set reply settings** (who can reply)

### Not Yet Implemented ⏸️
- ⏸️ **Attach media** (images, videos) - requires media upload API
- ⏸️ **Read tweets** - would require additional API calls
- ⏸️ **Delete tweets** - not in current handler
- ⏸️ **Like tweets** - would require additional API calls
- ⏸️ **Retweet** - would require additional API calls
- ⏸️ **Read replies** - would require additional API calls

### Could Add Later
These features are available in Twitter API v2 but not implemented:
- Thread creation (multiple tweets at once)
- Media upload and attachment
- Tweet deletion
- Like/Unlike
- Retweet/Unretweet
- Read user timeline
- Search tweets
- Get tweet details

---

## Troubleshooting

### Error: "401 Unauthorized"
**Causes**:
- Wrong API keys
- Wrong access tokens
- App permissions not set to "Read and Write"
- Tokens generated before permission change

**Fix**:
1. Verify credentials in `.env`
2. Check app permissions in developer portal
3. Regenerate access tokens if permissions were changed

### Error: "403 Forbidden"
**Causes**:
- Account suspended
- App suspended
- API access revoked
- Rate limited

**Fix**:
1. Check Twitter account status
2. Check app status in developer portal
3. Wait if rate limited

### Error: "429 Rate Limit Exceeded"
**Causes**:
- Too many requests in time window
- Free tier limits hit

**Fix**:
1. Wait for rate limit reset (shown in error message)
2. Plugin will automatically retry after delay
3. Consider upgrading to Basic tier ($100/month)

### Error: "Duplicate content"
**Cause**: Twitter blocks identical tweets within ~24 hours

**Fix**:
1. Change tweet text slightly
2. Add timestamp or unique identifier
3. Wait 24 hours

---

## Security Best Practices

### Credential Storage
- ✅ Store in `.env` (already in .gitignore)
- ❌ Never commit to git
- ❌ Never share in chat/email
- ❌ Never log in application

### Credential Rotation
- **Frequency**: Every 90 days recommended
- **When compromised**: Immediately regenerate
- **How**: Regenerate in Twitter Developer Portal → Update .env → Restart server

### Access Control
- Use app-specific tokens (don't share main account password)
- Monitor usage in Twitter Developer Portal
- Revoke access if needed

---

## Cost Considerations

### Free Tier is Sufficient For:
- ✅ Development and testing
- ✅ Personal use (few tweets per day)
- ✅ Proof of concept

### Need Paid Tier ($100/month) For:
- ❌ High-volume posting (>50 tweets/day)
- ❌ Reading tweets programmatically
- ❌ User lookups and follower management
- ❌ Production use at scale

**Recommendation for Testing**: Start with Free Tier, upgrade only if needed.

---

## Next Steps After Setup

Once credentials are in `.env`:

1. **Run test script** (will create for you)
2. **Post test tweet** via script
3. **Test via LLM prompt**:
   ```
   "Tweet from test account: 'Testing automated Twitter posting - timestamp [current time]'"
   ```
4. **Verify on Twitter** that tweet appears
5. **Delete test tweet** (manually or via API later)

---

## Additional Resources

- **Twitter API Documentation**: https://developer.twitter.com/en/docs/twitter-api
- **Rate Limits**: https://developer.twitter.com/en/docs/twitter-api/rate-limits
- **OAuth 1.0a Guide**: https://developer.twitter.com/en/docs/authentication/oauth-1-0a
- **Pricing**: https://developer.twitter.com/en/products/twitter-api/pricing

---

**Status**: Ready for credential setup
**Next**: Create Twitter Developer account and generate credentials
**Time Required**: 15-30 minutes
**Cost**: Free (Free Tier) or $100/month (Basic Tier)
