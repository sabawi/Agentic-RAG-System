# 🎯 URL CITATION HALLUCINATION FIX - IMPLEMENTATION PLAN v1.0.2.0

**CRITICAL PROJECT**: Fix LLM URL citation hallucinations across all tools
**TARGET VERSION**: v1.0.2.0 (Major architectural enhancement)
**PROJECT START**: 2025-09-14
**PRIORITY**: HIGH - Context quality is the PRIMARY LLM's most important asset

---

## 🚨 **SESSION RECOVERY INSTRUCTIONS**

**IF SESSION DISCONNECTS - LOAD THIS DOCUMENT IMMEDIATELY:**

1. **Read this entire document** to understand current progress
2. **Check the Gantt Chart Status** section below for current phase
3. **Run the Current Status Check** commands in Testing section
4. **Continue from the last completed checkpoint**
5. **Update this document** as you proceed with each step

**DOCUMENT LOCATION**: `/home/sabawi/Development/flaskserver/docs/URL_CITATION_FIX_IMPLEMENTATION_PLAN.md`

**LOAD COMMAND**: `cat /home/sabawi/Development/flaskserver/docs/URL_CITATION_FIX_IMPLEMENTATION_PLAN.md`

---

## 📋 **PROJECT OVERVIEW**

### **Problem Statement**
The Primary LLM is hallucinating URLs in citations, converting specific URLs like `https://www.aljazeera.com/middle-east/` to generic domain citations like `[Al Jazeera](https://www.aljazeera.com)`. This degrades response quality and user trust.

### **Root Cause Analysis**
1. **Poor Source-Information Association**: Current context format mixes URLs with content without clear attribution
2. **Cognitive Load**: Dense context makes it hard for LLM to maintain URL-content relationships  
3. **Format Sensitivity**: Research shows LLMs are highly sensitive to context formatting

### **Solution Framework**
- **Phase 1**: Enhanced Block Formatting with Source Attribution
- **Phase 2**: CO-STAR Framework + Citation Enforcement Prompts
- **Success Metric**: 95%+ URL citation accuracy (currently ~30%)

---

## 🔍 **COMPLETE TOOL INVENTORY**

### **Core Server Tools** (fastapi_server_complete.py)
| Tool | Function | Line | URL Pattern | Status |
|------|----------|------|-------------|--------|
| News Sources | `get_news_summaries()` | 1007 | `f"From Source: {newsURL}"` | ✅ COMPLETED |
| Web Search | `search_web()` | 1099 | `f"URL: {href}"` | ✅ COMPLETED |
| Website Lookup | `lookup_website()` | 1243 | `f"URL: {result['url']}"` | ✅ COMPLETED |
| Wikipedia Query | `wikipedia_query()` | 647 | `page.fullurl` | ✅ COMPLETED |

### **User Tools** (user_tools/)
| Tool | File | URL Pattern | Complexity | Status |
|------|------|-------------|------------|--------|
| Academic Papers | `published_papers_search_tool.py` | arXiv, PubMed, DOI URLs | HIGH | ⏳ PENDING |
| Flight Search | `flight_search.py` | Verification links JSON | HIGH | ⏳ PENDING |
| Stock Analysis | `comprehensive_stock_analyzer.py` | News source URLs | MEDIUM | ⏳ PENDING |
| Document Search | `document_search.py` | Document references | LOW | ⏳ PENDING |
| PDF Generators | Multiple files | Embedded URLs | LOW | ⏳ PENDING |

### **Context Processing Pipeline**
| Function | Line | Purpose | Status |
|----------|------|---------|--------|
| `_build_structured_context_block()` | 1893 | Primary context formatter | ⏳ PENDING |
| `_build_enhanced_primary_system_prompt()` | 1917 | System prompt builder | ⏳ PENDING |
| Context assembly | 7364 | Final prompt construction | ⏳ PENDING |

---

## 📊 **GANTT CHART & PROGRESS TRACKING**

### **PHASE 1A: Core Server Tools (Week 1)**
```
Task                           Day 1  Day 2  Day 3  Day 4  Day 5  Status
────────────────────────────────────────────────────────────────────────
1.1 Create Source Block Fmt    ████   ....   ....   ....   ....   ✅ COMPLETED
1.2 Test Block Formatter       ████   ....   ....   ....   ....   ✅ COMPLETED  
1.3 Modify get_news_summaries  ████   ....   ....   ....   ....   ✅ COMPLETED
1.4 Test News Tool             ████   ....   ....   ....   ....   ✅ COMPLETED
1.5 Modify search_web          ....   ████   ....   ....   ....   ✅ COMPLETED
1.6 Test Web Search            ....   ████   ....   ....   ....   ✅ COMPLETED
1.7 Modify lookup_website      ....   ....   ████   ....   ....   ✅ COMPLETED
1.8 Test lookup_website        ....   ....   ████   ....   ....   ✅ COMPLETED
1.9 Modify wikipedia_query     ....   ....   ....   ████   ....   ✅ COMPLETED
1.10 Test wikipedia_query      ....   ....   ....   ████   ....   ✅ COMPLETED
1.11 Integration Testing       ....   ....   ....   ....   ████   ⏳ PENDING
```

### **PHASE 1B: User Tools (Week 2)**
```
Task                           Day 6  Day 7  Day 8  Day 9  Day10  Status
────────────────────────────────────────────────────────────────────────
1.8 Papers Tool Modification   ████   ....   ....   ....   ....   ⏳ PENDING
1.9 Flight Tool Modification   ....   ████   ....   ....   ....   ⏳ PENDING
1.10 Stock Tool Modification   ....   ....   ████   ....   ....   ⏳ PENDING
1.11 User Tools Testing        ....   ....   ....   ████   ....   ⏳ PENDING
1.12 Full Integration Test     ....   ....   ....   ....   ████   ⏳ PENDING
```

### **PHASE 2: System Prompts (Week 3)**
```
Task                           Day11  Day12  Day13  Day14  Day15  Status
────────────────────────────────────────────────────────────────────────
2.1 CO-STAR Prompt Design      ████   ....   ....   ....   ....   ⏳ PENDING
2.2 Citation Rules Addition    ....   ████   ....   ....   ....   ⏳ PENDING
2.3 System Prompt Testing      ....   ....   ████   ....   ....   ⏳ PENDING
2.4 End-to-End Validation      ....   ....   ....   ████   ....   ⏳ PENDING
2.5 Production Deploy          ....   ....   ....   ....   ████   ⏳ PENDING
```

---

## 🛠️ **DETAILED IMPLEMENTATION STEPS**

### **📋 PHASE 1A: CORE SERVER TOOLS**

#### **Step 1.1: Create Source Block Formatter** ✅ COMPLETED

**Objective**: Create reusable source block formatter for consistent URL attribution

**Implementation**:
```python
def _format_source_block(source_url: str, title: str, content: str, source_num: int, timestamp: str = None) -> str:
    """Format individual source with enhanced block structure for accurate LLM citation"""
    if not timestamp:
        timestamp = datetime.now().strftime('%A, %B %d, %Y %I:%M:%S %p')
    
    return f"""
═══════════════════════════════════════════════════════
📄 SOURCE BLOCK #{source_num} [REQUIRED CITATION: {source_url}]
═══════════════════════════════════════════════════════
Title: {title}
🔗 MANDATORY CITATION URL: {source_url}
📅 Retrieved: {timestamp}
───────────────────────────────────────────────────────
CONTENT: {content}
═══════════════════════════════════════════════════════
"""
```

**Location**: Add to `fastapi_server_complete.py` after line 1892
**Testing**: Unit test with sample URL/content
**Success Criteria**: Function returns properly formatted block
**Status**: ✅ COMPLETED - 2025-09-14 16:18
**Assigned Tester**: Claude Code  
**Test Results**: PASSED - Function created successfully, all unit tests passed

---

#### **Step 1.2: Test Source Block Formatter** ✅ COMPLETED

**Objective**: Validate source block formatter produces correct output

**Test Commands**:
```bash
# Create test script
python3 -c "
from fastapi_server_complete import _format_source_block
result = _format_source_block(
    'https://www.coindesk.com/markets/2024/09/14/bitcoin-rises',
    'Bitcoin Rises Above 60K',
    'Bitcoin reached new highs today...',
    1
)
print(result)
print('Length:', len(result))
"
```

**Success Criteria**: 
- Block contains exact URL
- Visual separators present
- MANDATORY CITATION URL field visible
- Content properly formatted

**Status**: ✅ COMPLETED - 2025-09-14 16:18
**Test Results**: PASSED - All 6 success criteria met, 611 char output, proper formatting

---

#### **Step 1.3: Modify get_news_summaries()** ✅ COMPLETED

**Objective**: Replace current news source formatting with enhanced source blocks

**Current Code** (Line 1007):
```python
res += f"\n\nFrom Source: {newsURL}\n{url_content}\n\n"
```

**New Code**:
```python
formatted_source = _format_source_block(
    source_url=newsURL,
    title=f"News from {self._extract_domain(newsURL)}",
    content=url_content,
    source_num=successful_sources + 1
)
res += formatted_source
```

**Additional Changes Required**:
- Add `_extract_domain()` helper function
- Update source numbering logic
- Modify fallback source formatting

**Status**: ✅ COMPLETED - 2025-09-14 16:19
**Test Results**: PASSED - Both primary and fallback sources now use enhanced source blocks

---

#### **Step 1.4: Test News Tool** ✅ COMPLETED

**Objective**: Verify news tool produces properly formatted source blocks

**Test Commands**:
```bash
# Test crypto news with enhanced formatting
curl -X POST "http://localhost:5000/v1/chat/completions" \
-H "Content-Type: application/json" \
-d '{
  "model": "test",
  "messages": [{"role": "user", "content": "Get latest cryptocurrency news"}],
  "tools": [{"type": "function", "function": {"name": "get_news_summaries", "description": "Get news", "parameters": {"type": "object", "properties": {"filter": {"type": "string"}}}}}]
}'
```

**Success Criteria**:
- Source blocks properly formatted
- URLs visible in MANDATORY CITATION URL fields
- Content properly separated
- No regression in news fetching functionality

**Status**: ✅ COMPLETED - 2025-09-14 16:20  
**Test Results**: PASSED - Source blocks visible in context, 3 sources with proper formatting, no regression

---

#### **Step 1.5: Modify search_web()** ✅ COMPLETED

**Objective**: Update web search to use enhanced source block formatting

**Current Code** (Line 1487):
```python
res += f"\nResult {i}:\nTitle: {title}\nURL: {href}\nDescription: {body}\n"
```

**New Code**:
```python
formatted_result = _format_source_block(
    source_url=href,
    title=title,
    content=f"Description: {body}\n\nExtracted Content: {extracted_content}",
    source_num=i
)
res += formatted_result
```

**Status**: ✅ COMPLETED - 2025-09-15 17:04
**Test Results**: PASSED - Enhanced source blocks now properly formatted with visual separators, mandatory citation URL fields, and clear content structure

---

#### **Step 1.6: Test Web Search** ✅ COMPLETED

**Test Commands**:
```bash
# Test web search formatting
python3 test_web_search_formatting.py
```

**Success Criteria**:
- Enhanced source blocks with visual separators (═══════════)
- SOURCE BLOCK identification present
- MANDATORY CITATION URL fields visible
- Visual icons (📄, 🔗, 📅) included
- Content properly separated

**Status**: ✅ COMPLETED - 2025-09-15 17:04
**Test Results**: PASSED - All 5 formatting checks passed successfully. Enhanced source blocks now include visual separators, mandatory citation URLs, and proper content structure. Web search successfully extracts content from target URLs and formats results consistently.

---

#### **Step 1.7: Modify lookup_website()** ✅ COMPLETED

**Objective**: Update website content lookup to use enhanced source block formatting

**Current Code** (Line 1964-1978):
```python
response_parts = [
    f"\nAs of [Current Date and Time: {todayStr}] here are the website lookup results:",
    f"Title: {result['title']}",
    f"URL: {url}",
    f"Type: {content_type}",
    f"Content:\n{content}"
]
```

**New Code**:
```python
# Use enhanced source block formatting
formatted_result = _format_source_block(
    source_url=url,
    title=result['title'],
    content=full_content,
    source_num=1,
    timestamp=todayStr
)
```

**Status**: ✅ COMPLETED - 2025-09-15 17:07
**Test Results**: PASSED - Enhanced source blocks working correctly with website metadata (author, publication date, content type) properly integrated into the source block structure.

---

#### **Step 1.8: Test lookup_website()** ✅ COMPLETED

**Test Commands**:
```bash
# Test lookup_website formatting
python3 test_lookup_website_formatting.py
```

**Success Criteria**:
- Enhanced source blocks with visual separators (═══════════)
- SOURCE BLOCK identification present
- MANDATORY CITATION URL fields visible
- Visual icons (📄, 🔗, 📅) included
- Content properly separated with metadata

**Status**: ✅ COMPLETED - 2025-09-15 17:07
**Test Results**: PASSED - All 5 formatting checks passed successfully. Website lookup now properly extracts content and formats with enhanced source blocks including metadata (Type: Web Page, etc.) and full content structure.

---

#### **Step 1.9: Modify wikipedia_query()** ✅ COMPLETED

**Objective**: Update Wikipedia content query to use enhanced source block formatting

**Current Code** (Line 665-667):
```python
if page.exists():
    return page.summary[:1000] + "..." if len(page.summary) > 1000 else page.summary
return f"No Wikipedia page found for: {query}"
```

**New Code**:
```python
if page.exists():
    # Use enhanced source block formatting
    formatted_result = _format_source_block(
        source_url=page.fullurl,
        title=page.title,
        content=f"Wikipedia Summary:\n\n{summary}",
        source_num=1,
        timestamp=timestamp
    )
    return f"\nAs of [Current Date and Time: {timestamp}] here are the Wikipedia query results:\n{formatted_result}"
```

**Status**: ✅ COMPLETED - 2025-09-15 20:59
**Test Results**: PASSED - Enhanced source blocks working correctly with proper Wikipedia URLs and comprehensive summaries properly formatted.

---

#### **Step 1.10: Test wikipedia_query()** ✅ COMPLETED

**Test Commands**:
```bash
# Test wikipedia_query formatting
python3 test_wikipedia_query_formatting.py
```

**Success Criteria**:
- Enhanced source blocks with visual separators (═══════════)
- SOURCE BLOCK identification present
- MANDATORY CITATION URL fields visible
- Visual icons (📄, 🔗, 📅) included
- Proper Wikipedia URLs (wikipedia.org)
- Content properly formatted with summary

**Status**: ✅ COMPLETED - 2025-09-15 20:59
**Test Results**: PASSED - All 6 formatting checks passed successfully. Wikipedia query now properly extracts summaries and formats with enhanced source blocks including proper Wikipedia URLs (e.g., https://en.wikipedia.org/wiki/Artificial_intelligence).

---

### **📋 PHASE 1B: USER TOOLS**

#### **Step 1.12: Academic Papers Tool** ✅/❌ INCOMPLETE

**File**: `/home/sabawi/Development/flaskserver/user_tools/published_papers_search_tool.py`

**Challenge**: Multiple URL types (arXiv, DOI, PDF links)

**Implementation Strategy**: 
- Modify result formatting to use source blocks
- Handle multiple URL types per paper
- Maintain JSON structure compatibility

**Status**: ⏳ PENDING
**Test Results**: [TO BE FILLED]

---

#### **Step 1.9: Flight Search Tool** ✅/❌ INCOMPLETE

**File**: `/home/sabawi/Development/flaskserver/user_tools/flight_search.py`

**Challenge**: Verification links in JSON structure

**Implementation Strategy**:
- Format verification links as source blocks
- Maintain booking functionality
- Preserve JSON API compatibility

**Status**: ⏳ PENDING  
**Test Results**: [TO BE FILLED]

---

### **📋 PHASE 2: SYSTEM PROMPTS**

#### **Step 2.1: CO-STAR Prompt Design** ✅/❌ INCOMPLETE

**File**: `primary_model_system_prompt.txt`

**CO-STAR Framework**:
- **Context**: You have access to verified sources with specific URLs in SOURCE BLOCKs
- **Objective**: Cite EXACT URLs from MANDATORY CITATION URL fields
- **Style**: Use precise format: [Title](exact_url_from_source_block)
- **Tone**: Authoritative with strict source attribution
- **Audience**: Users requiring precise citations  
- **Response**: Always include exact URLs from context

**Status**: ⏳ PENDING
**Test Results**: [TO BE FILLED]

---

## 🧪 **TESTING FRAMEWORK**

### **Unit Tests**
```bash
# Test individual formatter functions
python3 -m pytest tests/test_url_formatting.py -v
```

### **Integration Tests**  
```bash
# Test complete tool chain
python3 -m pytest tests/test_citation_accuracy.py -v
```

### **Citation Accuracy Tests**
```bash
# Manual verification script
python3 scripts/test_citation_accuracy.py --tools news,web,papers --samples 10
```

### **Current Status Check Commands**
```bash
# Check logging status
curl -X GET http://localhost:5000/admin/logging/status

# Check optimization status
curl -X GET http://localhost:5000/optimization/status

# Check version
grep "__version__" /home/sabawi/Development/flaskserver/fastapi_server_complete.py

# Check logs for errors
tail -50 /home/sabawi/Development/flaskserver/logs/server_complete.log | grep -i error
```

---

## 📊 **SUCCESS METRICS**

### **Before Implementation**
- Citation Accuracy: ~30% (URLs frequently hallucinated)
- Context Quality: Medium (mixed URL/content format)
- User Trust: Impacted by inaccurate citations

### **Target After Implementation** 
- Citation Accuracy: 95%+ (exact URLs from context)
- Context Quality: High (structured source blocks)  
- User Trust: Restored with verifiable citations

### **Performance Metrics**
- Context Size Impact: <20% increase acceptable
- Response Time: <10% degradation acceptable
- Tool Success Rate: Maintain current 75%+ rates

---

## 🛡️ **ROLLBACK PLAN**

### **Git-Based Rollback**
```bash
# Create implementation branch
git checkout -b feature/url-citation-fix-v1.0.2.0

# If rollback needed
git checkout master
git branch -D feature/url-citation-fix-v1.0.2.0
```

### **Feature Flag Rollback**
```python
# Add to config
URL_CITATION_ENHANCED = False  # Toggle old/new format
```

### **Function-Level Rollback**
- Original functions preserved as `_legacy_*` versions
- Quick toggle between implementations possible

---

## 📝 **CHANGELOG TRACKING**

### **Version History**
- v1.0.1.14 (Current): Enhanced news sources, 60+ diverse outlets
- v1.0.2.0-alpha (Planned): Core tools with source block formatting
- v1.0.2.0-beta (Planned): All tools with enhanced formatting  
- v1.0.2.0 (Target): Complete URL citation fix with CO-STAR prompts

### **Change Log Template**
```
## v1.0.2.0 - URL Citation Hallucination Fix

### 🎯 Major Changes
- Enhanced source block formatting across all tools
- CO-STAR framework system prompts
- Citation enforcement mechanisms

### 🛠️ Technical Details
- Modified 8 core functions
- Updated 5 user tools
- Enhanced context processing pipeline

### 📊 Performance Impact
- Citation accuracy: 30% → 95%
- Context size: +15%
- Response time: +5%
```

---

## ⚠️ **CRITICAL REMINDERS**

### **🔴 NEVER FORGET**
1. **VERSION INCREMENT MANDATORY** - Every commit requires version bump
2. **TEST EACH STEP** - No changes without testing
3. **UPDATE THIS DOCUMENT** - Mark progress after each step  
4. **BACKUP BEFORE MAJOR CHANGES** - Create checkpoints
5. **CONTEXT IS EVERYTHING** - Quality context = Superior LLM responses

### **🟡 SESSION RECOVERY CHECKLIST**
- [ ] Load this document immediately
- [ ] Check Gantt chart status  
- [ ] Run status check commands
- [ ] Verify last completed step
- [ ] Continue from current checkpoint

### **🟢 SUCCESS INDICATORS** 
- LLM uses exact URLs from context
- Citations match source blocks exactly
- No URL simplification or hallucination
- Maintained or improved response quality

---

**DOCUMENT VERSION**: 1.0  
**LAST UPDATED**: 2025-09-14  
**NEXT UPDATE**: After each completed step

**🎯 REMEMBER: THE PRIMARY LLM'S RESPONSE QUALITY DEPENDS ON CONTEXT QUALITY!**

---

*END OF IMPLEMENTATION PLAN*