#!/usr/bin/env python3
"""
Strands Documentation Scraper
Recursively crawls https://strandsagents.com/ to extract documentation
and creates an LLM-friendly README file.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import os
from typing import Set, Dict, List
import re
from datetime import datetime

class StrandsDocScraper:
    def __init__(self, base_url: str = "https://strandsagents.com/"):
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.documentation_data: Dict[str, Dict] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; StrandsDocScraper/1.0; +https://github.com/finops-agent)'
        })
        
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is within the documentation domain and not already visited."""
        parsed = urlparse(url)
        return (
            parsed.netloc == urlparse(self.base_url).netloc and
            url not in self.visited_urls and
            not any(ext in url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.css', '.js']) and
            '#' not in url  # Skip anchor links
        )
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract meaningful content from a page."""
        content = {
            'url': url,
            'title': '',
            'headings': [],
            'content': '',
            'code_blocks': [],
            'links': []
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            content['title'] = title_tag.get_text().strip()
        
        # Extract main content area (try common selectors)
        main_content = None
        for selector in ['main', '.content', '.documentation', '.docs', 'article', '.main-content']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            # Extract headings
            for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                content['headings'].append({
                    'level': int(heading.name[1]),
                    'text': heading.get_text().strip()
                })
            
            # Extract code blocks
            for code_block in main_content.find_all(['code', 'pre']):
                code_text = code_block.get_text().strip()
                if len(code_text) > 10:  # Only meaningful code blocks
                    content['code_blocks'].append(code_text)
            
            # Extract text content (remove scripts, styles, etc.)
            for script in main_content(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            content['content'] = main_content.get_text().strip()
            content['content'] = re.sub(r'\n\s*\n', '\n\n', content['content'])  # Clean up whitespace
            
            # Extract internal links
            for link in main_content.find_all('a', href=True):
                href = urljoin(url, link['href'])
                if self.is_valid_url(href):
                    content['links'].append(href)
        
        return content
    
    def scrape_page(self, url: str) -> Dict:
        """Scrape a single page and return its content."""
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self.extract_content(soup, url)
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def crawl_recursively(self, start_url: str, max_pages: int = 100):
        """Recursively crawl the documentation starting from start_url."""
        urls_to_visit = [start_url]
        pages_scraped = 0
        
        while urls_to_visit and pages_scraped < max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.visited_urls.add(current_url)
            content = self.scrape_page(current_url)
            
            if content:
                self.documentation_data[current_url] = content
                pages_scraped += 1
                
                # Add new links to visit
                for link in content['links']:
                    if link not in self.visited_urls and link not in urls_to_visit:
                        urls_to_visit.append(link)
                
                # Be respectful - add delay between requests
                time.sleep(1)
        
        print(f"Scraped {pages_scraped} pages total")
    
    def generate_readme(self, output_file: str = "STRANDS_SDK_README.md"):
        """Generate an LLM-friendly README from scraped documentation."""
        readme_content = []
        
        # Header
        readme_content.append("# Strands SDK Documentation")
        readme_content.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        readme_content.append("")
        readme_content.append("This documentation was automatically extracted from https://strandsagents.com/")
        readme_content.append("")
        
        # Table of Contents
        readme_content.append("## Table of Contents")
        readme_content.append("")
        
        # Sort pages by URL for consistent ordering
        sorted_pages = sorted(self.documentation_data.items(), key=lambda x: x[0])
        
        for i, (url, content) in enumerate(sorted_pages, 1):
            title = content['title'] or f"Page {i}"
            readme_content.append(f"{i}. [{title}](#{self.create_anchor(title)})")
        
        readme_content.append("")
        
        # Content sections
        for i, (url, content) in enumerate(sorted_pages, 1):
            title = content['title'] or f"Page {i}"
            readme_content.append(f"## {i}. {title}")
            readme_content.append(f"**Source:** {url}")
            readme_content.append("")
            
            # Add headings structure
            if content['headings']:
                readme_content.append("### Page Structure")
                for heading in content['headings']:
                    indent = "  " * (heading['level'] - 1)
                    readme_content.append(f"{indent}- {heading['text']}")
                readme_content.append("")
            
            # Add main content (truncated if too long)
            if content['content']:
                content_text = content['content'][:2000]  # Limit content length
                if len(content['content']) > 2000:
                    content_text += "\n\n*[Content truncated for brevity]*"
                
                readme_content.append("### Content")
                readme_content.append(content_text)
                readme_content.append("")
            
            # Add code examples
            if content['code_blocks']:
                readme_content.append("### Code Examples")
                for j, code in enumerate(content['code_blocks'][:3], 1):  # Limit to 3 examples
                    readme_content.append(f"#### Example {j}")
                    readme_content.append("```")
                    readme_content.append(code[:500])  # Limit code block length
                    if len(code) > 500:
                        readme_content.append("# [Code truncated for brevity]")
                    readme_content.append("```")
                    readme_content.append("")
            
            readme_content.append("---")
            readme_content.append("")
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(readme_content))
        
        print(f"README generated: {output_file}")
    
    def create_anchor(self, text: str) -> str:
        """Create a markdown anchor from text."""
        return re.sub(r'[^\w\s-]', '', text).strip().lower().replace(' ', '-')
    
    def save_raw_data(self, output_file: str = "strands_documentation_raw.json"):
        """Save raw scraped data as JSON for further processing."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.documentation_data, f, indent=2, ensure_ascii=False)
        print(f"Raw data saved: {output_file}")

def main():
    """Main function to run the scraper."""
    scraper = StrandsDocScraper()
    
    print("Starting Strands documentation scraping...")
    print("This may take several minutes depending on the site structure.")
    
    # Start crawling from the main documentation page
    scraper.crawl_recursively("https://strandsagents.com/", max_pages=50)
    
    # Generate outputs
    scraper.generate_readme("STRANDS_SDK_README.md")
    scraper.save_raw_data("strands_documentation_raw.json")
    
    print("Documentation scraping completed!")
    print(f"Found {len(scraper.documentation_data)} pages")
    print("Files generated:")
    print("- STRANDS_SDK_README.md (LLM-friendly documentation)")
    print("- strands_documentation_raw.json (raw scraped data)")

if __name__ == "__main__":
    main()
