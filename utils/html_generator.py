"""
Shared HTML Generation Utility
Provides unified HTML report generation for all tools
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup  # Requires: pip install beautifulsoup4


class HTMLReportGenerator:
    """Unified HTML report generator using shared templates"""

    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.template_path = self.template_dir / "html_report_template.html"
        self._template_cache = None

    def _load_template(self) -> str:
        """Load HTML template from file with caching"""
        if self._template_cache is None:
            try:
                if not self.template_path.exists():
                    raise FileNotFoundError(f"Template not found: {self.template_path}")
                with open(self.template_path, 'r', encoding='utf-8') as f:
                    self._template_cache = f.read()
            except Exception:
                # Fallback to embedded template
                self._template_cache = self._get_fallback_template()
        return self._template_cache

    def _get_fallback_template(self) -> str:
        """Clean, simple template matching user-preferred style"""
        return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<style>
/* Clean, Minimal Styling for Professional Reports */
body {
  font-family: Arial, sans-serif;
  background-color: #f4f4f4;
  color: #333;
  line-height: 1.6;
  margin: 20px;
  padding: 20px;
}

h1, h2, h3 {
  color: #2c3e50;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

th, td {
  padding: 10px;
  border: 1px solid #ddd;
  text-align: left;
}

th {
  background-color: #3498db;
  color: white;
}

/* Custom CSS Placeholder */
{{CUSTOM_CSS}}
</style>
</head>
<body>
{{CONTENT}}
</body>
</html>"""

    def _clean_html_content(self, html: str) -> str:
        """Remove <pre><code> wrappers and invalid nesting while preserving HTML entities"""
        import html as html_module
        
        soup = BeautifulSoup(html, 'html.parser')

        # Unwrap <pre> and <code>, preserve text or inner HTML
        for pre in soup.find_all("pre"):
            pre.unwrap()
        for code in soup.find_all("code"):
            code.unwrap()

        # Remove <p> wrapping block elements like <h1>-<h3>
        for tag in soup.find_all(['h1', 'h2', 'h3', 'ul', 'ol', 'table']):
            parent = tag.parent
            if parent.name == 'p':
                parent.unwrap()

        # Note: Removed aggressive HTML escaping that was breaking formatted content
        # BeautifulSoup handles entities correctly, no need to re-escape everything

        return str(soup)

    def _convert_citations_to_html(self, content: str) -> str:
        """
        Convert plain text citations to clickable HTML.

        Converts patterns like:
          [Source: Yahoo Finance, as of 2025-11-01]
          [Source: Rivian Newsroom, "Georgia Plant Kickoff Ceremony", October 30, 2025]

        To:
          <span class="citation">[Source: Yahoo Finance, as of 2025-11-01]</span>
        """
        import re

        # Pattern to match citations in square brackets starting with "Source:"
        # Matches: [Source: anything here]
        pattern = r'\[Source:\s*([^\]]+)\]'

        def citation_replacement(match):
            citation_text = match.group(1).strip()
            return f'<span class="citation">[Source: {citation_text}]</span>'

        return re.sub(pattern, citation_replacement, content)

    def _custom_markdown_converter(self, markdown_text: str) -> str:
        """
        Fallback: Basic markdown converter using regex.
        Used only if the markdown library is not available.
        """
        import re

        html = markdown_text

        # Convert headers (must be done before other conversions)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Convert links [text](url) to <a href="url">text</a>
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

        # Convert bold **text** to <strong>text</strong>
        html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)

        # Convert italic *text* to <em>text</em>
        html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)

        # Convert bullet lists - → <li>
        lines = html.split('\n')
        in_list = False
        result = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                result.append(f'<li>{stripped[2:]}</li>')
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append(line)

        if in_list:
            result.append('</ul>')

        html = '\n'.join(result)

        # Convert paragraphs (double newlines) to <p> tags
        # But don't wrap block elements
        paragraphs = html.split('\n\n')
        formatted_paras = []
        for para in paragraphs:
            para = para.strip()
            if para:
                # Check if it's already a block element
                if para.startswith(('<h1>', '<h2>', '<h3>', '<ul>', '<ol>', '<div>', '<table>')):
                    formatted_paras.append(para)
                else:
                    # Regular paragraph - wrap in <p> but let single newlines flow naturally
                    # DO NOT convert single newlines to <br> - let HTML handle whitespace naturally
                    para = para.replace('\n', ' ')  # Single newlines become spaces (normal HTML behavior)
                    formatted_paras.append(f'<p>{para}</p>')

        return '\n'.join(formatted_paras)

    def _convert_markdown_to_html(self, markdown_text: str) -> str:
        """
        Convert markdown to HTML using professional markdown library.
        Supports tables, code blocks, syntax highlighting, and more.
        Falls back to custom converter if library unavailable.
        """
        try:
            import markdown
            import re

            # 🐛 FIX: Pre-process malformed markdown tables to ensure correct parsing.

            # 0. Remove extra separator rows from table bodies
            # LLMs sometimes generate separator rows BETWEEN data rows, which markdown
            # library renders as data cells containing "---". Remove all but the first separator.
            # Pattern: After a separator row, remove any subsequent separator rows until non-separator
            lines = markdown_text.split('\n')
            cleaned_lines = []
            separator_seen = False
            for line in lines:
                # Check if this is a separator row (contains only |, -, :, and whitespace)
                is_separator = bool(re.match(r'^\s*\|[\s\-:|]+\|\s*$', line))

                if is_separator:
                    if not separator_seen:
                        # First separator - keep it
                        cleaned_lines.append(line)
                        separator_seen = True
                    # else: skip additional separators
                else:
                    # Not a separator - reset flag if we've moved to a new section
                    if line.strip() == '' or not line.strip().startswith('|'):
                        separator_seen = False
                    cleaned_lines.append(line)

            markdown_text = '\n'.join(cleaned_lines)

            # 0.5. FIX CRITICAL BUG: Re-insert blank lines after tables
            # _clean_llm_response_content() removes blank lines, but tables REQUIRE blank lines
            # after them to properly close before: headings, horizontal rules, code blocks, etc.
            # Insert blank line after any table row that's followed by non-table content
            markdown_text = re.sub(
                r'(\|\s*[^\n]+\|\s*)\n(?!\s*\|)',  # table row + newline + NOT another table row
                r'\1\n\n',  # add double blank line
                markdown_text
            )

            # 1. Split rows that have been concatenated onto a single line.
            # e.g., | A | B | | C | D | -> | A | B |\n| C | D |
            # ONLY split when there are consecutive pipes (empty cell or concatenated rows)
            markdown_text = re.sub(r'\|\s*\|', '|\n|', markdown_text)

            # 2. Ensure tables are preceded by a blank line - FIXED VERSION
            # 🐛 CRITICAL FIX v1.0.3.97: Original regex matched EVERY table row, injecting
            # blank lines MID-TABLE, breaking table structure. New version only matches
            # table HEADERS by looking ahead for separator row pattern.
            # Match: non-blank-line + header-row + separator-row
            markdown_text = re.sub(
                r'(?<!\n)\n(\s*\|[^\n]+\|\s*\n)(\s*\|[\s\-:|]+\|\s*\n)',
                r'\n\n\1\2',
                markdown_text
            )

            # 3. REMOVED: Separator injection - was causing more harm than good
            # 🐛 CRITICAL FIX v1.0.3.97: The hardcoded 10-column separator was being injected
            # into tables with different column counts, causing markdown library to treat ALL
            # content after the table as malformed table rows. LLMs generate proper separators,
            # so this preprocessing is unnecessary and destructive.


            # 🔧 DEBUG: Log first 500 chars of input markdown
            print(f"\n{'='*80}")
            print(f"📥 MARKDOWN INPUT (first 500 chars):")
            print(f"{markdown_text[:500]}")
            print(f"{'='*80}\n")

            # Professional markdown extensions
            # 🐛 FIX: Removed 'nl2br' extension - it breaks table parsing by inserting <br> tags
            # Tables need consecutive lines without <br> to be recognized properly
            extensions = [
                'extra',          # Tables, fenced_code, footnotes, attr_list, def_list, abbr
                'codehilite',     # Syntax highlighting with Pygments
                'sane_lists',     # Better list handling
            ]

            # Configure extensions
            extension_configs = {
                'codehilite': {
                    'guess_lang': True,         # Auto-detect code language
                    'css_class': 'highlight',   # CSS class for code blocks
                    'pygments_style': 'github', # Use GitHub-style syntax highlighting
                    'noclasses': False,         # Use CSS classes (not inline styles)
                }
            }

            # Create markdown converter
            md = markdown.Markdown(
                extensions=extensions,
                extension_configs=extension_configs
            )

            # Convert markdown to HTML
            html_content = md.convert(markdown_text)

            # 🔧 DEBUG: Log first 500 chars of output HTML
            print(f"\n{'='*80}")
            print(f"📤 HTML OUTPUT (first 500 chars):")
            print(f"{html_content[:500]}")
            print(f"{'='*80}\n")

            print(f"✅ Markdown converted using professional library (markdown v{markdown.__version__})")
            return html_content

        except ImportError:
            # Fallback to custom converter
            print("⚠️ markdown library not available, using fallback custom converter")
            return self._custom_markdown_converter(markdown_text)
        except Exception as e:
            # On any error, fallback to custom converter
            print(f"⚠️ Error in markdown library: {e}, using fallback custom converter")
            return self._custom_markdown_converter(markdown_text)

    def generate_html_report(
        self,
        content: str,
        title: str = "Report",
        header_title: str = "Analysis Report",
        header_subtitle: str = "",
        include_disclaimer: bool = True,
        custom_timestamp: Optional[str] = None,
        custom_css: Optional[str] = None
    ) -> str:
        """
        Generate clean HTML report using shared template.

        Args:
            content: Report content (Markdown, HTML, or plain text)
            title: Page title (appears in browser tab)
            header_title: Main heading in report header
            header_subtitle: Subtitle/description in header
            include_disclaimer: Whether to include financial disclaimer
            custom_timestamp: Custom timestamp string (default: current time)
            custom_css: Optional custom CSS to inject into template
                       WARNING: Must be trusted input only - no user input sanitization

        Returns:
            Complete HTML document as string
        """
        try:
            # 🔧 FIX: If content is already complete HTML, return it as-is
            if self.is_already_html(content):
                print(f"✅ HTML GENERATOR: Content is already complete HTML - returning as-is (no wrapping)")
                return content

            template = self._load_template()

            # 🔧 FIX: Normalize special Unicode characters that cause encoding issues in email clients
            # Replace en-dash (U+2013) and em-dash (U+2014) with regular hyphen
            content = content.replace('\u2013', '-')  # en-dash → hyphen
            content = content.replace('\u2014', '-')  # em-dash → hyphen
            content = content.replace('\u2026', '...')  # ellipsis → three dots

            # 🔧 FIX: Detect and convert markdown to HTML
            # Check if content looks like markdown (has ## headers, [](links), tables, etc.)
            has_markdown_headers = '##' in content or '###' in content
            has_markdown_links = '](' in content
            has_markdown_formatting = '**' in content or content.count('*') > 2
            has_markdown_lists = '\n- ' in content or '\n* ' in content
            has_markdown_tables = '|' in content and ('---' in content or '|-' in content)  # Table syntax: | col | and |---|

            is_markdown = has_markdown_headers or has_markdown_links or has_markdown_formatting or has_markdown_lists or has_markdown_tables

            if is_markdown:
                print(f"📝 Markdown detected - headers:{has_markdown_headers}, links:{has_markdown_links}, formatting:{has_markdown_formatting}, lists:{has_markdown_lists}, tables:{has_markdown_tables}")

            if is_markdown:
                # Convert markdown to HTML
                content = self._convert_markdown_to_html(content)

            elif not ('<' in content and '>' in content):
                # Plain text - convert newlines to paragraphs
                import html as html_module
                paragraphs = content.strip().split('\n\n')
                formatted_content = ""
                for para in paragraphs:
                    if para.strip():
                        # Escape HTML entities and convert single newlines to <br>
                        escaped_para = html_module.escape(para.strip())
                        escaped_para = escaped_para.replace('\n', '<br>')
                        formatted_content += f"<p>{escaped_para}</p>\n"
                content = formatted_content

            # Convert plain text citations to styled HTML citations
            content = self._convert_citations_to_html(content)

            # Clean content (only for HTML content)
            content = self._clean_html_content(content)

            # Prepare disclaimer
            disclaimer = ""
            if include_disclaimer:
                disclaimer = """
                <div class="warning">
                    <strong>⚠️ Important Disclaimer:</strong>
                    This analysis is for informational purposes only and should not be considered financial advice.
                    Always consult qualified financial professionals before making investment decisions.
                </div>
                """

            # Prepare timestamp
            timestamp = custom_timestamp or f"{datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}"

            # Prepare custom CSS
            custom_css_content = ""
            if custom_css:
                custom_css_content = f"\n{custom_css}\n"

            # Replace placeholders with properly escaped content
            import html as html_module
            html_document = template.replace("{{TITLE}}", html_module.escape(title, quote=True))
            html_document = html_document.replace("{{CONTENT}}", content)
            html_document = html_document.replace("{{CUSTOM_CSS}}", custom_css_content)

            return html_document

        except Exception as e:
            return f"""<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
    <h1>{header_title}</h1>
    <div>{content}</div>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><em>Error in template processing: {str(e)}</em></p>
</body>
</html>"""

    def is_already_html(self, content: str) -> bool:
        """
        Check if content is already complete HTML document.

        Returns True if content appears to be a full HTML document with structure.
        """
        import re
        content_lower = content.strip().lower()

        # Check for DOCTYPE declaration
        if content_lower.startswith('<!doctype html'):
            return True

        # Check for <html> tag at the start
        if content_lower.startswith('<html'):
            return True

        # Check for presence of both <html> and <body> tags (complete HTML structure)
        has_html_tag = bool(re.search(r'<html[>\s]', content_lower))
        has_body_tag = bool(re.search(r'<body[>\s]', content_lower))
        has_head_tag = bool(re.search(r'<head[>\s]', content_lower))

        # If it has both html and body tags, it's a complete HTML document
        if has_html_tag and has_body_tag:
            return True

        # If it has html and head tags, it's a complete HTML document
        if has_html_tag and has_head_tag:
            return True

        return False


# Singleton instance for global use
html_generator = HTMLReportGenerator()


def create_html_report(
    content: str,
    title: str = "Report",
    header_title: str = "Analysis Report",
    header_subtitle: str = "",
    include_disclaimer: bool = True,
    custom_timestamp: Optional[str] = None,
    custom_css: Optional[str] = None
) -> str:
    """
    Convenience wrapper for generating HTML reports.

    Args:
        content: Report content (Markdown, HTML, or plain text)
        title: Page title (appears in browser tab)
        header_title: Main heading in report header
        header_subtitle: Subtitle/description in header
        include_disclaimer: Whether to include financial disclaimer
        custom_timestamp: Custom timestamp string (default: current time)
        custom_css: Optional custom CSS to inject into template

    Returns:
        Complete HTML document as string
    """
    return html_generator.generate_html_report(
        content=content,
        title=title,
        header_title=header_title,
        header_subtitle=header_subtitle,
        include_disclaimer=include_disclaimer,
        custom_timestamp=custom_timestamp,
        custom_css=custom_css
    )
