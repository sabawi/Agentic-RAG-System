# 🚨 MANDATORY DEVELOPMENT DIRECTIVES & RULES 🚨

> **CRITICAL**: This document MUST be reviewed before EVERY development task - debugging OR feature additions.
> 
> **NO EXCEPTIONS**: These rules prevent costly mistakes and ensure consistent quality.

---

## **📋 PRE-TASK CHECKLIST** 
**✅ READ THIS BEFORE STARTING ANY WORK**

### **🎯 TASK DEFINITION**
- [ ] **Clearly define the problem/requirement** - What exactly needs to be fixed/built?
- [ ] **Identify scope boundaries** - What is included/excluded from this task?
- [ ] **Set success criteria** - How will you know when it's complete?

### **🔍 DEBUGGING TASKS ONLY**
- [ ] **Get full stack trace FIRST** - Never debug without exact error location
- [ ] **Reproduce the error** - Can you make it happen consistently?
- [ ] **Evidence over hypothesis** - What does the error actually say?
- [ ] **Isolate before expanding** - Fix the immediate issue before improving architecture

### **🏗️ FEATURE ADDITION TASKS ONLY**  
- [ ] **Check existing architecture** - How does current code handle similar features?
- [ ] **Identify integration points** - What existing code will this affect?
- [ ] **Plan modular implementation** - Can this be centralized in one location?
- [ ] **Consider error scenarios** - What happens when this feature fails?

---

## **🚫 ABSOLUTE PROHIBITIONS**

### **❌ NEVER DO THESE - NO EXCEPTIONS**

1. **NEVER hardcode values after initialization**
   ```python
   # ❌ FORBIDDEN - After variable has been used
   model = get_configured_model()
   # Later...
   model = "gpt-4"  # NEVER DO THIS
   
   # ✅ ACCEPTABLE - At start only
   DEFAULT_MODEL = "gpt-4"
   model = DEFAULT_MODEL
   ```

2. **NEVER debug without stack traces**
   ```python
   # ❌ USELESS
   except Exception as e:
       logger.error("Error occurred")
   
   # ✅ REQUIRED
   except Exception as e:
       import traceback
       logger.error(f"ERROR: {e}")
       logger.error(f"TRACEBACK: {traceback.format_exc()}")
   ```

3. **NEVER scatter critical logic across multiple locations**
   ```python
   # ❌ SCATTERED - Hard to debug
   # File 1: if provider == 'openai': model = config_model
   # File 2: if provider == 'openai': model = provider_model  
   # File 3: if provider == 'openai': model = default_model
   
   # ✅ CENTRALIZED
   class ModelSelector:
       @staticmethod
       def get_model(provider, config, override=None):
           # ALL logic here
   ```

4. **NEVER assume external API response structure**
   ```python
   # ❌ DANGEROUS
   content = response['data']['content'][:100]
   
   # ✅ DEFENSIVE
   content = response.get('data', {}).get('content')
   if content:
       content = content[:100]
   ```

5. **NEVER make architectural changes during debugging**
   - Fix the immediate error FIRST
   - Verify the fix works
   - THEN improve architecture in separate task

---

## **✅ MANDATORY REQUIREMENTS**

### **🔧 FOR ALL DEVELOPMENT TASKS**

1. **EVIDENCE-DRIVEN DECISIONS**
   - Collect data before making changes
   - Log assumptions and verify them
   - Document what you found vs. what you expected

2. **SINGLE RESPONSIBILITY PRINCIPLE**
   - One function/class does one thing
   - Critical decisions made in one location only
   - Easy to find and modify logic

3. **DEFENSIVE PROGRAMMING**
   - Validate all external inputs
   - Handle null/missing values explicitly
   - Comprehensive error logging with context

4. **MODULAR ARCHITECTURE**
   - Centralize related functionality
   - Minimize code duplication
   - Clear separation of concerns

### **🐛 FOR DEBUGGING TASKS SPECIFICALLY**

1. **EXCEPTION-FIRST METHODOLOGY**
   ```
   Step 1: Get full stack trace with line numbers
   Step 2: Reproduce error consistently  
   Step 3: Identify exact failure point
   Step 4: Implement minimal fix
   Step 5: Verify fix resolves error
   Step 6: (Optional) Improve architecture
   ```

2. **SCOPE ISOLATION**
   - Fix immediate problem before expanding scope
   - Resist urge to "fix everything at once"
   - Separate bug fixes from feature improvements

3. **COMPLETE SIMULATION**
   - Test entire data flow, not just happy path
   - Include edge cases and error conditions
   - Validate assumptions about external systems

### **🏗️ FOR FEATURE ADDITIONS SPECIFICALLY**

1. **INTEGRATION ANALYSIS**
   - Map all affected components
   - Identify potential breaking changes  
   - Plan rollback strategy

2. **ERROR SCENARIO PLANNING**
   - What happens when feature fails?
   - How will errors be detected and reported?
   - What's the recovery mechanism?

3. **CONSISTENCY VERIFICATION**
   - Does this follow existing patterns?
   - Are naming conventions consistent?
   - Does this fit the overall architecture?

---

## **📊 QUALITY GATES**

### **🚦 BEFORE STARTING WORK**
- [ ] Reviewed this document completely
- [ ] Understood the exact problem/requirement
- [ ] Identified all affected components
- [ ] Planned approach following directives

### **🚦 BEFORE IMPLEMENTING SOLUTION**
- [ ] Collected sufficient evidence (for debugging)
- [ ] Verified integration points (for features)
- [ ] Confirmed modular approach
- [ ] No hardcoded values planned

### **🚦 BEFORE SUBMITTING WORK**
- [ ] Solution follows single responsibility principle
- [ ] Error handling is comprehensive
- [ ] No scattered logic across multiple files
- [ ] Code is defensive against external failures
- [ ] Testing covers edge cases and error scenarios

---

## **⚡ EMERGENCY PROTOCOLS**

### **🚨 IF YOU FIND YOURSELF...**

**"Debugging for more than 30 minutes without progress"**
→ STOP. Get stack trace. Follow exception-first methodology.

**"Making changes in multiple files for same logic"**  
→ STOP. Centralize the logic first. Then implement.

**"Tempted to hardcode a value for testing"**
→ STOP. Use constants at start of function/class only.

**"Assuming external API response format"**
→ STOP. Add defensive validation. Handle null cases.

**"Expanding scope during debugging"**
→ STOP. Fix immediate error first. Improve later.

### **🔄 RECOVERY ACTIONS**

1. **Return to evidence collection**
2. **Re-read the relevant directive section**  
3. **Apply the prescribed methodology**
4. **Document what went wrong for future learning**

---

## **📚 REFERENCE QUICK CARDS**

### **🐛 DEBUGGING DECISION TREE**

```
Problem Reported
    ↓
Get Stack Trace? 
    ↓ NO → GET STACK TRACE FIRST
    ↓ YES
Can Reproduce?
    ↓ NO → REPRODUCE ERROR FIRST  
    ↓ YES
Exact Failure Location Known?
    ↓ NO → TRACE THROUGH CODE
    ↓ YES
Minimal Fix Available?
    ↓ NO → IDENTIFY ROOT CAUSE
    ↓ YES
Fix Applied & Tested?
    ↓ NO → IMPLEMENT & VERIFY
    ↓ YES
    ✅ DONE - Improve Architecture Later
```

### **🏗️ FEATURE ADDITION DECISION TREE**

```
Feature Requested
    ↓
Requirements Clear?
    ↓ NO → CLARIFY REQUIREMENTS
    ↓ YES  
Existing Patterns Identified?
    ↓ NO → RESEARCH CODEBASE
    ↓ YES
Integration Points Mapped?
    ↓ NO → MAP ALL AFFECTED COMPONENTS
    ↓ YES
Modular Design Planned?
    ↓ NO → CENTRALIZE LOGIC DESIGN
    ↓ YES
Error Scenarios Considered?
    ↓ NO → PLAN ERROR HANDLING
    ↓ YES
    ✅ READY TO IMPLEMENT
```

### **⚠️ RED FLAGS - STOP IMMEDIATELY**

- **Multiple files being edited for same logical change**
- **Hardcoding values anywhere except start of function**
- **Making assumptions about external API responses**
- **Debugging without stack traces**
- **Architecture changes during bug fixes**
- **Copy-pasting similar logic instead of centralizing**

---

## **🎯 SUCCESS METRICS**

### **📈 DEBUGGING EFFICIENCY TARGETS**
- **Time to root cause identification: < 15 minutes**
- **Number of files modified for single fix: ≤ 2**
- **Hardcoded values in production: 0**
- **Debugging sessions without stack trace: 0**

### **📈 FEATURE QUALITY TARGETS**  
- **Central logic locations per feature: 1**
- **Code duplication for similar functionality: 0**
- **Features breaking existing functionality: 0**
- **Error scenarios without handling: 0**

### **📈 OVERALL DEVELOPMENT TARGETS**
- **Tasks requiring major rework: < 5%**
- **Critical logic scattered across files: 0**  
- **External API calls without validation: 0**
- **Exception handling without context: 0**

---

## **🔄 DIRECTIVE UPDATES**

### **📝 HOW TO UPDATE THIS DOCUMENT**
1. **After every major debugging session**: Add lessons learned
2. **After architectural mistakes**: Update prevention rules
3. **When patterns emerge**: Codify into directives
4. **Monthly review**: Assess effectiveness and adjust

### **📋 UPDATE TRIGGERS**
- **Debugging took > 2 hours for simple issue**
- **Same mistake made twice in different tasks**  
- **Architecture required major refactoring**
- **Production issue due to code quality**

---

## **💡 FINAL REMINDERS**

### **🎯 CORE PRINCIPLES**
1. **Evidence over assumptions**
2. **Centralization over scattered logic**  
3. **Defense over optimism**
4. **Isolation over expansion**
5. **Documentation over memory**

### **⚡ EMERGENCY MANTRA**
> **"When in doubt, STOP. Read the directives. Follow the process."**

### **🏆 SUCCESS MANTRA**  
> **"Quality code comes from quality process, not heroic effort."**

---

**📌 COMMITMENT**: By reading this document, you commit to following these directives for every development task. These rules prevent expensive mistakes and ensure consistent, maintainable code quality.

**🚨 ACCOUNTABILITY**: Violations of these directives must be documented as learning opportunities and process improvements.**