import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

def get_text_from_url(url : str):
    
    def convert_html_table_to_text(table):

        rows = []
        for row in table.find_all('tr'):
            # Get all cells (th and td) from the row
            cells = row.find_all(['th', 'td'])
            row_text = ' | '.join(cell.get_text().strip() for cell in cells)
            rows.append(row_text)
        
        return '\n'.join(rows)
    
    
    try:
        # Make the POST request to the proxy server
        response = requests.get(url) 
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        # Parse the HTML content
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted tags (equivalent to removeUnwantedTags)
        for tag_name in ['footer', 'nav', 'script', 'style']:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Replace links with their text content
        for link in soup.find_all('a'):
            link.replace_with(link.get_text())
        
        # Extract paragraphs
        paragraphs = [p.get_text().strip() for p in soup.find_all('p')]
        paragraphs = [p for p in paragraphs if p]  # Filter out empty paragraphs
        
        if not paragraphs:
            print("Warning: No paragraphs were found!")
        
        # Process tables
        for table in soup.find_all('table'):
            table_text = convert_html_table_to_text(table)
            paragraphs.append(table_text)
        
        # Join all text with double newlines
        text = '\n\n'.join(paragraphs)
        
        return url, text
        
    except requests.exceptions.RequestException as error:
        print(f'Error fetching text from URL: {error}',flush=True)
        return f'Error fetching text from URL: {error}', None


if __name__ == "__main__":
    # Example usage:
    url = input("Enter URL:")

    text = get_text_from_url(url)
    if text:
        print(f"Extracted text from {url}:\n{text}")

