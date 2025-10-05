# News Sources Configuration Guide

## Overview

The Agentic-RAG Server allows you to customize news sources without editing code by modifying the `config/news_sources.yaml` file. This provides:

- **User-friendly customization**: Add/remove news sources easily
- **No code changes required**: Edit YAML configuration file only
- **No server restart needed**: Changes take effect on next news query
- **Category-based detection**: Intelligent query-to-category mapping
- **Fallback protection**: System uses hardcoded defaults if config fails

---

## Configuration File Location

```
config/news_sources.yaml
```

---

## Configuration Structure

The configuration file has three main sections:

### 1. News Sources (`news_sources`)

Maps categories to RSS/feed URLs:

```yaml
news_sources:
  crypto:
    - https://www.coindesk.com/arc/outboundfeeds/rss/
    - https://decrypt.co/feed
    - https://www.theblock.co/rss.xml

  finance:
    - https://www.cnbc.com/id/100003114/device/rss/rss.html
    - https://finance.yahoo.com/news/rssindex
```

**Supported Categories:**
- `world` - International news
- `national` - US/domestic news
- `business` - Business news
- `finance` - Financial markets
- `economy` - Economic policy
- `technology` - Tech news
- `crypto` - Cryptocurrency
- `science` - Scientific news
- `politics` - Political news
- `local` - Regional/local news
- `default` - Fallback sources

### 2. Category Mapping (`category_mapping`)

Defines how user queries are mapped to categories:

```yaml
category_mapping:
  crypto:
    primary_terms:          # Core keywords (highest weight)
      - crypto
      - bitcoin
      - ethereum
    secondary_terms:        # Related keywords (medium weight)
      - defi
      - nft
      - altcoin
    compound_phrases:       # Multi-word phrases (highest priority)
      - crypto news
      - bitcoin price
    weight: 1.0            # Category priority (0.0 to 1.0)
    fallback_categories:   # Alternatives if primary fails
      - finance
      - technology
```

**Term Types:**
- **primary_terms**: Core keywords with high weight
- **secondary_terms**: Related keywords with medium weight
- **compound_phrases**: Multi-word phrases with highest priority
- **weight**: Category priority (0.0 = low, 1.0 = high)
- **fallback_categories**: Alternative categories if primary fails

### 3. Keyword Mappings (`keyword_mappings`)

Direct keyword-to-category mappings for precise targeting:

```yaml
keyword_mappings:
  stock market:
    - finance
    - economy
  cryptocurrency:
    - crypto
  california:
    - local
```

---

## How to Customize

### Adding a News Source

1. Open `config/news_sources.yaml`
2. Find the appropriate category
3. Add the RSS/feed URL to the list:

```yaml
news_sources:
  crypto:
    - https://www.coindesk.com/arc/outboundfeeds/rss/
    - https://decrypt.co/feed
    - https://YOUR_NEW_FEED_URL_HERE.rss  # <-- Add here
```

4. Save the file
5. Next news query will use the new source

### Adding a New Category

1. Add category to `news_sources`:

```yaml
news_sources:
  your_category:
    - https://your-news-source-1.com/rss
    - https://your-news-source-2.com/feed
```

2. Add category mapping to `category_mapping`:

```yaml
category_mapping:
  your_category:
    primary_terms:
      - keyword1
      - keyword2
    secondary_terms:
      - related1
      - related2
    compound_phrases:
      - "keyword1 news"
      - "keyword2 update"
    weight: 0.8
    fallback_categories:
      - default
```

3. (Optional) Add keyword mappings:

```yaml
keyword_mappings:
  specific keyword:
    - your_category
```

### Removing a News Source

Simply delete or comment out the URL:

```yaml
news_sources:
  crypto:
    - https://www.coindesk.com/arc/outboundfeeds/rss/
    # - https://decrypt.co/feed  # <-- Commented out
```

### Modifying Category Detection

To make a category more/less likely to be selected:

1. **Increase priority**: Add more terms or increase weight

```yaml
category_mapping:
  crypto:
    weight: 1.0  # Change from 0.8 to 1.0
```

2. **Add compound phrases** (highest priority matching):

```yaml
compound_phrases:
  - crypto news
  - bitcoin price
  - ethereum news  # <-- Add specific phrases
```

3. **Adjust fallbacks**:

```yaml
fallback_categories:
  - finance
  - technology
  - business  # <-- Add more fallbacks
```

---

## Examples

### Example 1: Add Bloomberg as Finance Source

```yaml
news_sources:
  finance:
    - https://www.cnbc.com/id/100003114/device/rss/rss.html
    - https://feeds.bloomberg.com/markets/news.rss  # <-- Added
```

### Example 2: Create AI/ML News Category

```yaml
# 1. Add news sources
news_sources:
  ai_ml:
    - https://www.artificialintelligence-news.com/feed/
    - https://machinelearningmastery.com/blog/feed/

# 2. Add category mapping
category_mapping:
  ai_ml:
    primary_terms:
      - ai
      - artificial intelligence
      - machine learning
      - ml
    secondary_terms:
      - deep learning
      - neural network
      - llm
      - gpt
    compound_phrases:
      - ai news
      - machine learning update
      - llm development
    weight: 0.9
    fallback_categories:
      - technology

# 3. Add keyword mappings
keyword_mappings:
  chatgpt:
    - ai_ml
  neural network:
    - ai_ml
```

### Example 3: Regional News for Texas

```yaml
# Add Texas-specific sources
news_sources:
  local:
    - https://www.dallasnews.com/feed/
    - https://www.houstonchronicle.com/rss/feed/  # <-- Add

# Ensure "texas" triggers local category
keyword_mappings:
  texas:
    - local
```

---

## Fallback System

The news system has triple fallback protection:

### Level 1: User Configuration (Preferred)
```
config/news_sources.yaml → Loads user customization
```

### Level 2: Main Config Fallback
```
config/llm_config.yaml → Checks for 'news' section
```

### Level 3: Hardcoded Defaults
```
fastapi_server_complete.py → Uses hardcoded dictionaries
```

**This ensures the system NEVER fails** - if configuration is missing or corrupt, hardcoded defaults are used automatically.

---

## Troubleshooting

### Problem: News sources not loading from config

**Check:**
1. File exists: `config/news_sources.yaml`
2. YAML syntax is valid:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('config/news_sources.yaml'))"
   ```
3. Check server logs:
   ```bash
   tail -f logs/server_complete.log | grep -i news
   ```

**Expected Log Messages:**
- ✅ Success: `📰 Using news sources from configuration file`
- ⚠️ Fallback: `📋 News config empty, using hardcoded defaults`
- ❌ Error: `⚠️ Failed to load news config: [error], using hardcoded defaults`

### Problem: New category not being detected

**Solutions:**
1. **Add more specific terms:**
   ```yaml
   primary_terms:
     - very_specific_keyword
     - another_keyword
   ```

2. **Add compound phrases** (higher priority):
   ```yaml
   compound_phrases:
     - "exact phrase match"
   ```

3. **Increase weight:**
   ```yaml
   weight: 1.0  # Maximum priority
   ```

4. **Add keyword mapping** (direct match):
   ```yaml
   keyword_mappings:
     exact keyword:
       - your_category
   ```

### Problem: Getting wrong news sources

**Diagnosis:**
1. Check which category is being detected:
   - Look for log line: `🎯 Selected Category: 'category_name' with score X.XX`

2. Adjust category terms to better match your query

3. Use more specific query terms

### Problem: RSS feed not working

**Check:**
1. URL is accessible:
   ```bash
   curl -I https://your-feed-url.com/rss
   ```

2. Returns XML/RSS content:
   ```bash
   curl https://your-feed-url.com/rss | head -20
   ```

3. Feed is valid RSS/Atom format

**Common Issues:**
- 404 Not Found → URL changed, find new URL
- 403 Forbidden → Site blocks automated access
- Invalid XML → Feed is malformed

### Problem: YAML syntax error

**Common Mistakes:**
```yaml
# ❌ WRONG: Missing quotes for special characters
url: https://example.com/feed?param=value&other=value

# ✅ CORRECT: Quote URLs with special characters
url: "https://example.com/feed?param=value&other=value"

# ❌ WRONG: Inconsistent indentation
news_sources:
  crypto:
    - url1
     - url2  # Wrong indentation

# ✅ CORRECT: Consistent indentation (2 spaces)
news_sources:
  crypto:
    - url1
    - url2

# ❌ WRONG: Missing hyphen for list items
primary_terms:
  crypto
  bitcoin

# ✅ CORRECT: Use hyphens for lists
primary_terms:
  - crypto
  - bitcoin
```

**Validate YAML:**
```bash
python3 -c "import yaml; yaml.safe_load(open('config/news_sources.yaml'))"
```

---

## Best Practices

### 1. **Start Small**
- Add one source at a time
- Test each addition
- Build up gradually

### 2. **Use Reliable Sources**
- Prefer established news outlets
- Check RSS feeds are actively maintained
- Avoid feeds that frequently break

### 3. **Balance Categories**
- Don't overload one category with too many sources
- 3-10 sources per category is optimal
- Too many sources slow down queries

### 4. **Test Your Changes**
- After editing, test with a news query
- Check logs for errors
- Verify correct sources are used

### 5. **Backup Configuration**
- Keep a backup of `news_sources.yaml`
- Document your customizations
- Version control your config

### 6. **Use Descriptive Terms**
- Add specific keywords users might search
- Include variations and synonyms
- Think about how users phrase queries

---

## Advanced Configuration

### Custom Scoring Weights

Adjust how categories are prioritized:

```yaml
category_mapping:
  high_priority_category:
    weight: 1.0  # Highest priority

  medium_priority:
    weight: 0.7  # Medium priority

  low_priority:
    weight: 0.3  # Lower priority
```

### Crossover Terms

Handle queries that span multiple categories:

```yaml
category_mapping:
  crypto:
    financial_crossover:  # Crypto + Finance terms
      - crypto stocks
      - bitcoin etf
    tech_crossover:  # Crypto + Tech terms
      - blockchain development
      - smart contracts
```

### Geographic Indicators

Target local/regional queries:

```yaml
category_mapping:
  local:
    geo_indicators:
      - california
      - texas
      - new york
      - chicago
```

---

## FAQ

**Q: Do I need to restart the server after changing the config?**
A: No! Changes take effect on the next news query.

**Q: What happens if I delete news_sources.yaml?**
A: The system automatically falls back to hardcoded defaults. No errors, no downtime.

**Q: Can I use the same RSS feed in multiple categories?**
A: Yes! The same feed can appear in multiple categories.

**Q: How do I disable a category temporarily?**
A: Comment out the category or set its sources to an empty list: `category: []`

**Q: Can I use Atom feeds in addition to RSS?**
A: Yes! The system supports both RSS and Atom feed formats.

**Q: How many sources should I have per category?**
A: 3-10 sources is optimal. Too few = limited coverage, too many = slower queries.

**Q: Can I add non-RSS sources?**
A: Only RSS/Atom feeds are supported. Regular web pages won't work.

**Q: How do I know which category was selected for my query?**
A: Check the server logs for: `🎯 Selected Category: 'name' with score X.XX`

---

## Getting Help

If you encounter issues:

1. **Check logs**: `tail -f logs/server_complete.log | grep -i news`
2. **Validate YAML**: `python3 -c "import yaml; yaml.safe_load(open('config/news_sources.yaml'))"`
3. **Test config loading**: See "Troubleshooting" section
4. **Reset to defaults**: Rename/delete `news_sources.yaml` to use hardcoded defaults

---

## Related Documentation

- [User Guide](production/USER_GUIDE.md) - General usage guide
- [Configuration Guide](LLM_CONFIGURATION_GUIDE.md) - LLM configuration
- [Project Configuration Directive](PROJECT_CONFIGURATION_DIRECTIVE.md) - Configuration standards

---

**Last Updated**: October 5, 2025
**Version**: 1.0.2.99
