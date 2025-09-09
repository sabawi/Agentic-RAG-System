# PDF Header and Footer Date/Title Display Fix

## Overview
Fixed the issue where PDF headers and footers showed blank values instead of displaying the document date and title properly.

## Problem
WeasyPrint was unable to resolve `attr(data-date)` and `attr(data-title)` functions in CSS `@page` context, resulting in:
- Header showing "Generated on " (blank date)
- Footer showing blank title
- CSS warnings: `Unable to compute PageType value for content: "attr(), ('data-title', 'string', '')"`

## Root Cause Analysis
Research revealed that WeasyPrint's `attr()` function in `@page` context has limitations. The proper approach is to use WeasyPrint's **named strings** pattern with `string-set`.

## Solution Implementation

### 1. CSS Update - Named Strings Pattern
**Location**: `config/pdf_styles.css` lines 285-287

```css
/* Named strings for WeasyPrint attribute access */
html {
    string-set: date-content attr(data-date), title-content attr(data-title);
}
```

### 2. Updated @page Rules
**Location**: `config/pdf_styles.css` lines 298-314

```css
@page {
    /* Header for pages 2+ */
    @top-left {
        content: "Generated on " string(date-content);  /* Instead of attr(data-date) */
        font-family: "DejaVu Sans", Arial, sans-serif;
        font-size: 9pt;
        color: #718096;
        margin-bottom: 0.3in;
        padding-top: 0.2in;
    }
    
    /* Footer with page number and title */
    @bottom-left {
        content: string(title-content);  /* Instead of attr(data-title) */
        font-family: "DejaVu Sans", Arial, sans-serif;
        font-size: 9pt;
        color: #718096;
        font-weight: normal;
    }
}
```

### 3. HTML Data Attributes (Already Working)
**Location**: `services/pdf_service.py` lines 368-369

```html
<html lang="en" data-title="{formatted_title}" data-date="{current_date}">
```

### 4. Date Formatting
**Location**: `services/pdf_service.py` lines 361-363

```python
now = datetime.now()
day_suffix = "th" if 4 <= now.day <= 20 or 24 <= now.day <= 30 else ["st", "nd", "rd"][now.day % 10 - 1]
current_date = now.strftime(f'%b. {now.day}{day_suffix}, %Y - %-I:%M %p')
```

### 5. Title Formatting
**Location**: `services/pdf_service.py` lines 400-404

```python
def _format_title(self, title: str) -> str:
    """Format title by replacing underscores with spaces and capitalizing words"""
    formatted = title.replace('_', ' ')
    formatted = formatted.title()
    return formatted
```

## Results

### Before Fix
- Header: `"Generated on "`
- Footer: `(blank title)`
- CSS Warnings: Multiple `Unable to compute PageType` errors

### After Fix  
- Header: `"Generated on Sep. 9th, 2025 - 12:28 PM"`
- Footer: `"Formatted Document Title"`
- No CSS warnings

## Key Learning
**Research-First Approach**: Instead of experimenting with various solutions, online research revealed WeasyPrint's official documentation pattern using named strings with `string-set`. This saved time, tokens, and electricity while delivering the correct solution immediately.

## WeasyPrint Named Strings Pattern
This is the official WeasyPrint approach for accessing HTML attributes in PDF headers/footers:

1. Define named strings in CSS: `html { string-set: name attr(attribute); }`
2. Use in @page rules: `@page { @top-left { content: string(name); } }`

## Technical Notes
- All `@page` rules updated: default, `:first`, `:left`, `:right`
- Maintains backward compatibility
- Works with WeasyPrint's CSS Paged Media Module Level 3
- Supports dynamic date generation and title formatting

## Updated: 2025-09-09