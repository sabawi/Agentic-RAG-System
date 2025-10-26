# Contact Management System - Design Document

**Version**: 1.0
**Date**: 2025-10-19
**Status**: Planning Phase

---

## 📋 Overview

A comprehensive contact management system that allows natural language interaction with contacts, contact groups, and seamless integration with the email system.

### Key Features

1. **Individual Contact Management**
   - Store names, emails, phone numbers, addresses
   - Query contact information via natural language
   - CRUD operations for contacts

2. **Contact Groups**
   - Create named groups of contacts
   - Add/remove contacts from groups
   - Email entire groups with single command

3. **Smart Email Resolution**
   - Resolve names to email addresses automatically
   - Support for "email John Doe..." instead of requiring explicit email
   - Group-based email sending

4. **Natural Language Interface**
   - "What's John Doe's contact info?"
   - "Show me Jenny Walker's phone number"
   - "Draft an email to my Marketing_TeamA contact group"
   - "Add Jimmy Johns to MySalesTeam101"
   - "Email David Sabawi the sales_sheet202404.xcl"

---

## 🗄️ Database Schema

### contacts Table
```sql
CREATE TABLE IF NOT EXISTS contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    full_name TEXT NOT NULL,  -- Indexed for search
    email TEXT,               -- Primary email
    phone TEXT,
    address TEXT,
    company TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(full_name, email)  -- Prevent duplicates
);

-- Index for fast lookup
CREATE INDEX idx_contacts_full_name ON contacts(full_name);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_last_name ON contacts(last_name);
```

### contact_emails Table (Support for multiple emails per contact)
```sql
CREATE TABLE IF NOT EXISTS contact_emails (
    email_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    email_type TEXT DEFAULT 'personal',  -- personal, work, other
    is_primary BOOLEAN DEFAULT 0,
    FOREIGN KEY(contact_id) REFERENCES contacts(contact_id) ON DELETE CASCADE,
    UNIQUE(contact_id, email)
);

CREATE INDEX idx_contact_emails_contact_id ON contact_emails(contact_id);
CREATE INDEX idx_contact_emails_email ON contact_emails(email);
```

### contact_phones Table (Support for multiple phone numbers)
```sql
CREATE TABLE IF NOT EXISTS contact_phones (
    phone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    phone_type TEXT DEFAULT 'mobile',  -- mobile, work, home, other
    is_primary BOOLEAN DEFAULT 0,
    FOREIGN KEY(contact_id) REFERENCES contacts(contact_id) ON DELETE CASCADE,
    UNIQUE(contact_id, phone, phone_type)
);

CREATE INDEX idx_contact_phones_contact_id ON contact_phones(contact_id);
```

### contact_groups Table
```sql
CREATE TABLE IF NOT EXISTS contact_groups (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contact_groups_name ON contact_groups(group_name);
```

### group_members Table (Many-to-many relationship)
```sql
CREATE TABLE IF NOT EXISTS group_members (
    membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    contact_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(group_id) REFERENCES contact_groups(group_id) ON DELETE CASCADE,
    FOREIGN KEY(contact_id) REFERENCES contacts(contact_id) ON DELETE CASCADE,
    UNIQUE(group_id, contact_id)  -- Prevent duplicate memberships
);

CREATE INDEX idx_group_members_group_id ON group_members(group_id);
CREATE INDEX idx_group_members_contact_id ON group_members(contact_id);
```

---

## 🛠️ Tool Interfaces

### Tool 1: contact_manager
Primary tool for all contact operations (CRUD + search)

```python
{
    "name": "contact_manager",
    "description": "Manage contacts: create, read, update, delete, search contacts by name, email, phone, or company",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "read", "update", "delete", "search", "list_all"],
                "description": "Operation to perform"
            },
            "first_name": {
                "type": "string",
                "description": "Contact's first name"
            },
            "last_name": {
                "type": "string",
                "description": "Contact's last name"
            },
            "email": {
                "type": "string",
                "description": "Contact's primary email address"
            },
            "phone": {
                "type": "string",
                "description": "Contact's phone number"
            },
            "address": {
                "type": "string",
                "description": "Contact's physical address"
            },
            "company": {
                "type": "string",
                "description": "Contact's company/organization"
            },
            "notes": {
                "type": "string",
                "description": "Additional notes about the contact"
            },
            "search_query": {
                "type": "string",
                "description": "Search query to find contacts (searches name, email, company)"
            },
            "contact_id": {
                "type": "integer",
                "description": "Contact ID for update/delete operations"
            }
        },
        "required": ["action"]
    }
}
```

### Tool 2: contact_group_manager
Manage contact groups and memberships

```python
{
    "name": "contact_group_manager",
    "description": "Manage contact groups: create groups, add/remove members, list groups and members",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create_group", "delete_group", "add_member", "remove_member", "list_groups", "list_members", "get_group_emails"],
                "description": "Group operation to perform"
            },
            "group_name": {
                "type": "string",
                "description": "Name of the contact group"
            },
            "description": {
                "type": "string",
                "description": "Description of the group"
            },
            "contact_name": {
                "type": "string",
                "description": "Full name of contact to add/remove"
            },
            "contact_id": {
                "type": "integer",
                "description": "Contact ID to add/remove"
            },
            "group_id": {
                "type": "integer",
                "description": "Group ID for operations"
            }
        },
        "required": ["action"]
    }
}
```

---

## 🔗 Integration Points

### 1. Enhanced secure_email_sender Tool

**Current Parameter:**
```python
"to_email": {
    "type": "string",
    "description": "Primary recipient email address"
}
```

**Enhanced to Support:**
```python
"to_email": {
    "type": "string",
    "description": "Recipient: email address, contact name, or group name (e.g., 'john.doe@email.com', 'John Doe', '@Marketing_TeamA')"
}
```

**Resolution Logic:**
1. If contains `@` at start → Group name (e.g., `@Marketing_TeamA`)
2. If contains `@` inside → Email address (e.g., `john.doe@email.com`)
3. Otherwise → Contact name search (e.g., `John Doe`)

**Implementation:**
- Add `_resolve_recipient(to_email_param)` method to SecureEmailSenderTool
- Query contacts database for name matches
- Query groups database for group names
- Return resolved email address(es)
- Support comma-separated mix: `"John Doe, jane@example.com, @SalesTeam"`

### 2. Pre-tool Model System Prompt Updates

Add new section for contact management:

```
N. Contact Management and Smart Email Resolution
📇 CONTACT OPERATIONS:
For managing contacts and sending emails to contacts by name:

contact_manager(action="search", search_query="John Doe")
contact_manager(action="create", first_name="John", last_name="Doe", email="john.doe@example.com")
contact_group_manager(action="create_group", group_name="Marketing_TeamA")
contact_group_manager(action="add_member", group_name="Marketing_TeamA", contact_name="John Doe")

🚨 SMART EMAIL RESOLUTION:
When user provides a contact name or group instead of email address:
- Use contact_manager to search for the contact first
- Then use secure_email_sender with the resolved email

✅ EXAMPLES:
User: "What's John Doe's email?"
→ contact_manager(action="search", search_query="John Doe")

User: "Email David Sabawi the sales report"
→ contact_manager(action="search", search_query="David Sabawi")
→ secure_email_sender(to_email="[resolved email]", subject="Sales Report", attachments="sales_report.pdf")

User: "Send the quarterly report to the Marketing_TeamA group"
→ contact_group_manager(action="get_group_emails", group_name="Marketing_TeamA")
→ secure_email_sender(to_email="[comma-separated group emails]", subject="Quarterly Report", ...)

User: "Add Jimmy Johns to MySalesTeam101"
→ contact_manager(action="search", search_query="Jimmy Johns")
→ contact_group_manager(action="add_member", group_name="MySalesTeam101", contact_id=[found_id])
```

---

## 📁 File Structure

```
/home/sabawi/Development/flaskserver/
├── user_tools/
│   ├── contact_manager.py              # NEW - Contact CRUD operations
│   ├── contact_group_manager.py        # NEW - Group management
│   ├── secure_email_sender.py          # MODIFIED - Add recipient resolution
│   └── base_user_tool.py               # Existing base class
├── config/
│   └── llm_config.yaml                 # Existing config
├── contacts.db                          # NEW - Contact database
├── pre_tool_model_system_prompt.txt    # MODIFIED - Add contact section
└── docs/
    └── CONTACT_MANAGEMENT_SYSTEM_DESIGN.md  # This document
```

---

## 🎯 Use Case Examples

### Use Case 1: Query Contact Information
**User:** "What's John Doe's contact info?"

**Tool Calls:**
```json
[
    {
        "function": "contact_manager",
        "arguments": {
            "action": "search",
            "search_query": "John Doe"
        }
    }
]
```

**Response:**
```
Contact Information for John Doe:
- Email: john.doe@example.com
- Phone: (555) 123-4567
- Company: Acme Corp
- Address: 123 Main St, City, State 12345
```

### Use Case 2: Email by Contact Name
**User:** "Email David Sabawi the sales_sheet202404.xcl"

**Tool Calls:**
```json
[
    {
        "function": "contact_manager",
        "arguments": {
            "action": "search",
            "search_query": "David Sabawi"
        }
    },
    {
        "function": "secure_email_sender",
        "arguments": {
            "to_email": "david.sabawi@example.com",  // Resolved from contact
            "subject": "Sales Sheet - April 2024",
            "body": "Please find attached the sales sheet for April 2024.",
            "attachments": "sales_sheet202404.xcl"
        }
    }
]
```

### Use Case 3: Email to Contact Group
**User:** "Draft an email to my Marketing_TeamA contact group about the Q3 results"

**Tool Calls:**
```json
[
    {
        "function": "contact_group_manager",
        "arguments": {
            "action": "get_group_emails",
            "group_name": "Marketing_TeamA"
        }
    },
    {
        "function": "secure_email_sender",
        "arguments": {
            "to_email": "john@example.com,jane@example.com,bob@example.com",  // Group members
            "subject": "Q3 Results Summary",
            "body": "Dear Marketing Team,\n\nPlease find attached our Q3 results...",
            "attachments": "q3_results.pdf"
        }
    }
]
```

### Use Case 4: Add Contact to Group
**User:** "Add Jimmy Johns to MySalesTeam101"

**Tool Calls:**
```json
[
    {
        "function": "contact_manager",
        "arguments": {
            "action": "search",
            "search_query": "Jimmy Johns"
        }
    },
    {
        "function": "contact_group_manager",
        "arguments": {
            "action": "add_member",
            "group_name": "MySalesTeam101",
            "contact_id": 42  // Found from search
        }
    }
]
```

### Use Case 5: Create New Contact
**User:** "Add a new contact: Jane Smith, email sarah.j@example.com, phone 555-0123, works at TechCorp"

**Tool Calls:**
```json
[
    {
        "function": "contact_manager",
        "arguments": {
            "action": "create",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.j@example.com",
            "phone": "555-0123",
            "company": "TechCorp"
        }
    }
]
```

---

## 🔄 Implementation Phases

### Phase 1: Database and Core Infrastructure (2-3 hours)
**Deliverables:**
- [ ] Create `contacts.db` SQLite database
- [ ] Implement schema with all tables
- [ ] Create database migration/initialization script
- [ ] Write unit tests for database operations

**Files:**
- `contact_database.py` - Database initialization and management
- `tests/test_contact_database.py` - Database tests

### Phase 2: Contact Manager Tool (3-4 hours)
**Deliverables:**
- [ ] Implement `contact_manager.py` tool
- [ ] All CRUD operations (create, read, update, delete)
- [ ] Smart search functionality (fuzzy matching)
- [ ] Handle duplicate detection
- [ ] Write comprehensive tests

**Files:**
- `user_tools/contact_manager.py`
- `tests/test_contact_manager.py`

### Phase 3: Contact Group Manager Tool (2-3 hours)
**Deliverables:**
- [ ] Implement `contact_group_manager.py` tool
- [ ] Group CRUD operations
- [ ] Member management (add/remove)
- [ ] Bulk email resolution for groups
- [ ] Write tests

**Files:**
- `user_tools/contact_group_manager.py`
- `tests/test_contact_group_manager.py`

### Phase 4: Email Integration (2-3 hours)
**Deliverables:**
- [ ] Enhance `secure_email_sender.py` with recipient resolution
- [ ] Support contact names in `to_email` parameter
- [ ] Support group names with `@GroupName` syntax
- [ ] Support mixed recipients (names, emails, groups)
- [ ] Write integration tests

**Files:**
- `user_tools/secure_email_sender.py` (MODIFIED)
- `tests/test_email_contact_integration.py`

### Phase 5: System Prompt Updates (1 hour)
**Deliverables:**
- [ ] Add Contact Management section to `pre_tool_model_system_prompt.txt`
- [ ] Add examples for all contact operations
- [ ] Add smart email resolution examples
- [ ] Test with various prompts

**Files:**
- `pre_tool_model_system_prompt.txt` (MODIFIED)

### Phase 6: Documentation and User Guide (1-2 hours)
**Deliverables:**
- [ ] Complete this design document
- [ ] Create user guide for contact management
- [ ] Add to DEVELOPER_GUIDE.md
- [ ] Add to USER_GUIDE.md
- [ ] Create CLI tool for contact management (optional)

**Files:**
- `docs/CONTACT_MANAGEMENT_USER_GUIDE.md`
- `docs/production/USER_GUIDE.md` (UPDATED)
- `docs/production/DEVELOPER_GUIDE.md` (UPDATED)

### Phase 7: Testing and Refinement (2-3 hours)
**Deliverables:**
- [ ] End-to-end testing with real prompts
- [ ] Performance testing with large contact databases
- [ ] Security audit (SQL injection prevention)
- [ ] Edge case testing (duplicate names, missing fields)
- [ ] Bug fixes and refinements

**Total Estimated Time:** 13-19 hours

---

## 🔒 Security Considerations

### 1. SQL Injection Prevention
- Use parameterized queries for all database operations
- Never use string formatting for SQL queries
- Validate all input data types

### 2. Data Privacy
- Contact data is stored locally in SQLite
- No external API calls with contact information
- Consider encryption for sensitive fields (future enhancement)

### 3. Access Control
- All contact operations via tool interface only
- No direct database access from user prompts
- Audit logging for contact modifications (future enhancement)

### 4. Input Validation
- Email format validation
- Phone number sanitization
- Name length limits
- SQL reserved word escaping

---

## 📊 Database Performance Optimizations

### Indexes (Already included in schema)
- `full_name` - Fast contact search
- `email` - Fast email lookup
- `last_name` - Fast surname search
- Group and membership indexes for fast group operations

### Query Optimizations
- Use LIMIT for large result sets
- Implement pagination for contact lists
- Cache frequently accessed groups

### Expected Performance
- **Contact Search:** < 10ms for 10,000 contacts
- **Group Email Resolution:** < 20ms for 100-member groups
- **Contact Creation:** < 5ms
- **Database Size:** ~1KB per contact (est. 10MB for 10,000 contacts)

---

## 🧪 Testing Strategy

### Unit Tests
- Database CRUD operations
- Search and fuzzy matching
- Group operations
- Email resolution logic

### Integration Tests
- Contact manager + email sender
- Group manager + email sender
- Multi-step workflows

### End-to-End Tests
- Full user prompts through tool calling LLM
- Real email sending to test contacts
- Group email distribution

### Test Data
- Sample contacts database with 100+ entries
- Multiple groups with overlapping memberships
- Edge cases (duplicate names, missing emails, special characters)

---

## 🚀 Future Enhancements

### Phase 8: Advanced Features (Future)
- [ ] Contact import/export (CSV, vCard)
- [ ] Contact photos/avatars
- [ ] Contact history (email tracking)
- [ ] Smart suggestions (auto-complete)
- [ ] Contact merge/de-duplication wizard
- [ ] Integration with email_retriever (match sender to contact)
- [ ] Birthday/anniversary reminders
- [ ] Contact tags/categories
- [ ] Advanced search (boolean queries)
- [ ] REST API for contact management

---

## 📝 Notes and Decisions

### Design Decisions

1. **Separate email/phone tables:** Supports multiple emails/phones per contact
2. **Full_name field:** Denormalized for fast search, updated via trigger
3. **Group prefix `@`:** Unambiguous identification of groups vs contacts
4. **SQLite choice:** Consistent with existing project patterns, no external dependencies
5. **Tool split:** Separate tools for contacts vs groups for clarity and focused operations

### Open Questions
- [ ] Should we support nested groups (groups containing other groups)?
- [ ] Should we track email history per contact?
- [ ] Should we integrate with external contact services (Google Contacts, etc.)?
- [ ] Should we implement contact synchronization across devices?

---

## 📚 References

- Project directive: `CLAUDE.md`
- Database pattern: `document_interrogator.py`
- Email tool: `user_tools/secure_email_sender.py`
- Tool prompt: `pre_tool_model_system_prompt.txt`

---

**Document Status:** ✅ Complete - Ready for Implementation

**Next Steps:**
1. Review and approval of design
2. Begin Phase 1 implementation (Database setup)
3. Iterative development following phases 1-7
