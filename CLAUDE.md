- Operation Plan for updating and committing the project code: 1) Read and understand all project directive and rules in CLAUDE.md file, project configurations, /doc documentations to make sure you understand the baseline of the project 2) Review the development work status: What was accomplished in fixes, features, modifications for this the current update 3) Take count of all tracked files changes, added files, and configuration changes 4) Decisions: a) Does the documentaions need update as a result of the modifications?  b) does the install/upgrade process or scripts need update? Make a list of action plans to make the needed update to a, b, or both 5) Was thorough testing (Unit/Functional Verifications/ System) done? If it was not, build and run the needed testing scenaios. Once passed you are readu to the last 2 steps 6) Does the version number needs updating? if yes, increment the product version number 7) Stage the files correctly 8) Commit and push to github
- YOU DO NOT NEED MY PERMISSION to view the logs or view any files in the project, YOU WILL NEED PERMISSION TO MAKE CODE OR CONFIGURATION CHANGES IN THE PROJECT FILES. ALWAYS EXPLAIN WHAT YOU ARE DOING AND WHY.
- ALL DOCUMENTATIONS AND HELP INFORMATION SHOULD GO UNER THE ./docs DIRECTORY UNDER APPROPRIATE LOCATION AND POSSIBLY MERGED WIHIN THE MAIN DOCUMENTATION FILES
- ALL TEST SCRIPTS AND TESTING CODE SHOULD GO UNDER THE ./tests DIRECTORY UNDER APPROPRIATE SUBDIRECTORY STRUCTURE

# 📁 MANDATORY PROJECT DIRECTORY ORGANIZATION

## ROOT DIRECTORY - Keep Clean and Essential Only
- **README.md** - Main project documentation (REQUIRED)
- **CLAUDE.md** - Project directives and rules (REQUIRED)
- **Core Python modules with active dependencies** - http_helpers.py, http_pool_manager.py, text_chunker.py, document_interrogator.py, signature_image_detection.py (KEEP IN ROOT - critical imports)
- **fastapi_server_complete.py** - Main server file (REQUIRED)
- **version.py** - Centralized version management (REQUIRED)

## DIRECTORY STRUCTURE RULES - STRICTLY ENFORCE

### /docs/ - Development Documentation
```
docs/
├── production/          # REQUIRED - User/Admin/Developer/Installation guides
├── housekeeping/        # NEW - Project management, internal docs
│   ├── procedures/      # Emergency procedures, test checklists
│   ├── status-tracking/ # Project status, phase reviews, changelogs
│   └── workflow-automation/ # Internal workflow tools, optimization
├── archive/             # Historical docs, validation reports
└── *.md                 # Technical documentation (HTML_EMAIL_CONVERSION_SYSTEM.md, etc.)
```

### /tests/ - All Testing Code
```
tests/
├── utilities/           # Test utilities, API testing scripts
├── vision_regression/   # Image/vision testing
├── integration/         # Integration testing
└── data/               # Test data files
```

### /archive/experimental/ - Development/Debug Files
- analyze_*.py, debug_*.py, improved_*.py files
- Experimental implementations not in production

## FILE PLACEMENT RULES

### HOUSEKEEPING DOCUMENTATION (→ docs/housekeeping/)
**Project management docs NOT relevant to code development:**
- Status tracking: PHASE_STATUS_*.md, PROJECT_CHANGELOG.md, *_STATUS.md, **CHANGELOG_v*.md** (version-specific changelogs)
- Procedures: ROLLBACK_PROCEDURE*.md, *_TEST_CHECKLIST.md, UNTESTED_CHANGES.md
- Workflow: AUTOMATION_*PLAN.md, CLI_*QUICKSTART.md
- **MANDATORY: Every version release MUST have CHANGELOG_vX.X.X.XX.md in docs/housekeeping/status-tracking/**

### DEVELOPMENT DOCUMENTATION (→ docs/)
**Technical docs relevant to developers:**
- Configuration guides: LLM_CONFIGURATION_GUIDE.md, PROJECT_CONFIGURATION_DIRECTIVE.md
- Technical specs: HTML_EMAIL_CONVERSION_SYSTEM.md, VERSION_MANAGEMENT.md
- Implementation plans: *_IMPLEMENTATION_PLAN.md

### TEST FILES (→ tests/appropriate_subdir/)
- test_*.py files go to tests/utilities/ or tests/vision_regression/ or tests/integration/
- Never leave test files in root directory

### DEBUG/ANALYSIS FILES (→ archive/experimental/)
- debug_*.py, analyze_*.py, improved_*.py files
- Experimental implementations
- Development analysis scripts

## ENFORCEMENT RULES
1. **NEVER leave housekeeping docs in root or docs/ main directory**
2. **NEVER leave test files in root directory**
3. **ALWAYS check dependencies before moving Python files** (use comprehensive grep analysis)
4. **ALWAYS document moves as "UNTESTED" until validation complete**
5. **PRESERVE all core development documentation in proper locations**

# 🚨 MANDATORY PROJECT CONFIGURATION DIRECTIVE 🚨
## ZERO TOLERANCE FOR HARDCODED CONFIGURATION VALUES

**CRITICAL:** Read and enforce /docs/PROJECT_CONFIGURATION_DIRECTIVE.md

### CONFIGURATION RULES (NO EXCEPTIONS):
1. **NO HARDCODED CONFIGURATION VALUES IN CODE EVER!** - All config must be in llm_config.yaml
2. **NO HARDCODED FALLBACKS** - System must fail fast if config is missing
3. **NO CONSTANTS FILES** - config/llm_constants.py is ELIMINATED from project
4. **.env ONLY FOR SECRETS** - Email addresses, passwords, API keys, user IDs ONLY
5. **SINGLE CONFIG FILE** - config/llm_config.yaml is the ONLY source of truth

### ENFORCEMENT:
- REJECT any code with hardcoded config values
- REQUIRE configuration values be moved to llm_config.yaml
- VERIFY .env contains ONLY user secrets (no URLs, models, timeouts)
- ENFORCE fail-fast behavior when configuration is missing

**Before making ANY configuration changes, read /docs/PROJECT_CONFIGURATION_DIRECTIVE.md**
- WHEN PROMPTED TO INVESTIGATE A BUG/PROBLEM ALWAYS START BY REVIEWING THE LOGS AND COMPARING IT TO THE EXPECTED SERVER BEHAVIOUR ACCORDING THE ARCHITECURE AND DESIGN
- NEVER ASSUMES THE FIX WORKS UNLESS THE HUMAN USER TELLS YOU IT DOES
- ALWAYS FOLLOW THE DOCUMENTED PROJECT DIRECTORY ORGANIZATION WHEN CREATING AND MOVING FILES
- ALWAYS TEST YOUR FIX THROUGH PROMPTS TO THE SERVER FROM END-TO-END
- ALWAYS FOLLOW THE RULE OF ALL RULES AND NEVER FORGET IT: Read and understand CLAUDE.md FULLY. Second, I want you to read ALL the architecture, design, and development documentations in /docs very carefully and learn about ALL ASPECTS OF ARCHITECTURE AND DESIGN OF THE SERVER BEFORE ATTAMPTING TO ANSWER ANY QUESTION. IT IS PROHIBITED TO MAKE ANY CODE CHANGES IF YOU HAVE NOT 'RECENTLY' READ AND UNDERSTOOD THE ARCHITECTURE AND DESIGN
- DO NOT MAKE ASSUMPTIONS AND BASE ANYTHING ON THEM WITHOUT INVESTIGATING AND TESTING THEM FIRST
- WHEN INDOUBT, ALWAYS EXPLAIN THE ISSUE AND ASK GUIDANCE FROM HUMAN USER
- BEFORE WRITING A NEW UTILITY FUNCTION, SEARCH THE CODEBASE IF THERE IS A WORKING FUNCTION ALREADY WRITTEN TO DO THE SAME WORK. ALWAYS, REUSED EXITING CODE AND IMPROVE IT
- KEEP INVESTIGATING THE ROOT CAUSE OF A BUG/ISSUE UNTIL YOU HAVE NEAR ~100% OF THE CORRECT AND FULL ROOT CAUSE THEN REPORT IT TO USER
- NEVER ATTEMPT A CODE FIX UNTIL (1) YOU HAVE SATISFIED THE REQUIREMENTS OF INVESTIGATING THE ROOT CAUSE (2) YOU HAVE PLANNED/ANALYZED/RESEARCH/EXPERIMENTED WITH AND VERIFIED THAT THE FIX WILL WORK WITH HIGH CONFIDENCE (NEAR ~100%)
- CHECKPOINT PROTOCOL: FOLLOW A STRICT PLAN TO STAGE AND COMMIT FILES TO REPO: review all the code change in this current project diectory and list all changed files tracked and untracked. Examine all current documentations for requiring updates/correction and update them as result of changes (README.md, ./docs/production, other files in ./docs etc). Ensure the directory organization is strictly followed. Ensure security issues are resolved 100% (no passwords/keys/credintials etc). Update the version numbers to be consistant across ALL files and gitbuh README.md, as well as the 'About' box version number on github site. **MANDATORY: Create version-specific changelog at docs/housekeeping/status-tracking/CHANGELOG_vX.X.X.XX.md documenting all changes, new features, fixes, dependencies, breaking changes, and migration guide.** Add core/required files (tracked and new if required only) and stage them for check-in. Ensure the dependencies (./requirements.txt) is uptodate for any new imports. Commit and Push changes.
- NO FULL CONTENT OF BINARY FILE SHOULD BE DUMPED IN THE LOGS. ONLY FIRST 100 BYTES e.g."/HmfPngUAfPjhh1i6dGmx/Rw+fBiTJk1Cu3bt0KBBA9So ..."