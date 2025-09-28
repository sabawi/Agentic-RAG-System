- Operation Plan for updating and committing the project code: 1) Read and understand all project directive and rules in CLAUDE.md file, project configurations, /doc documentations to make sure you understand the baseline of the project 2) Review the development work status: What was accomplished in fixes, features, modifications for this the current update 3) Take count of all tracked files changes, added files, and configuration changes 4) Decisions: a) Does the documentaions need update as a result of the modifications?  b) does the install/upgrade process or scripts need update? Make a list of action plans to make the needed update to a, b, or both 5) Was thorough testing (Unit/Functional Verifications/ System) done? If it was not, build and run the needed testing scenaios. Once passed you are readu to the last 2 steps 6) Does the version number needs updating? if yes, increment the product version number 7) Stage the files correctly 8) Commit and push to github
- YOU DO NOT NEED MY PERMISSION to view the logs or view any files in the project, YOU WILL NEED PERMISSION TO MAKE CODE OR CONFIGURATION CHANGES IN THE PROJECT FILES. ALWAYS EXPLAIN WHAT YOU ARE DOING AND WHY.
- ALL DOCUMENTATIONS AND HELP INFORMATION SHOULD GO UNER THE ./docs DIRECTORY UNDER APPROPRIATE LOCATION AND POSSIBLY MERGED WIHIN THE MAIN DOCUMENTATION FILES
- ALL TEST SCRIPTS AND TESTING CODE SHOULD GO UNDER THE ./tests DIRECTORY UNDER APPROPRIATE SUBDIRECTORY STRUCTURE

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