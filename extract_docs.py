#!/usr/bin/env python3
import os
import re
import requests
from bs4 import BeautifulSoup
import html2text
import time

# Base URL
base_url = "https://strandsagents.com/latest/"
output_file = "/home/ec2-user/projects/finopsAgent/strands_documentation.md"
visited_urls = set()
temp_dir = "/home/ec2-user/projects/finopsAgent/temp_docs"

# Create HTML to text converter
h2t = html2text.HTML2Text()
h2t.ignore_links = False
h2t.ignore_images = False
h2t.ignore_tables = False
h2t.body_width = 0  # No wrapping

def clean_url(url):
    """Normalize URL for deduplication"""
    url = url.split('#')[0]  # Remove fragment
    if url.endswith('/'):
        url = url[:-1]
    return url

def get_content(url):
    """Fetch and extract content from a URL"""
    normalized_url = clean_url(url)
    if normalized_url in visited_urls:
        return None
    
    visited_urls.add(normalized_url)
    
    try:
        print(f"Fetching: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        # Save the HTML for debugging
        page_name = url.replace(base_url, '').replace('/', '_')
        if not page_name:
            page_name = "index"
        with open(f"{temp_dir}/{page_name}.html", "w") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main content
        main_content = soup.find('main')
        if not main_content:
            main_content = soup.find('div', class_='content')
        if not main_content:
            main_content = soup.find('article')
        if not main_content:
            main_content = soup.body
        
        # Extract title
        title = soup.find('title')
        title_text = title.text if title else url.split('/')[-1]
        
        # Convert to markdown
        content = h2t.handle(str(main_content))
        
        # Add title as heading
        result = f"# {title_text}\n\n{content}\n\n"
        result += f"Source: {url}\n\n---\n\n"
        
        return result, soup
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_links(soup, current_url):
    """Extract relevant links from the page"""
    links = []
    if not soup:
        return links
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # Skip external links, anchors, etc.
        if href.startswith('#') or href.startswith('mailto:'):
            continue
        
        # Convert relative URLs to absolute
        if not href.startswith('http'):
            if href.startswith('/'):
                href = base_url.rstrip('/') + href
            else:
                href = os.path.dirname(current_url) + '/' + href
        
        # Only include links from the same domain
        if href.startswith(base_url):
            links.append(href)
    
    return links

def crawl_site():
    """Crawl the site and extract documentation"""
    to_visit = [base_url]
    all_content = []
    
    while to_visit and len(visited_urls) < 50:  # Limit to 50 pages for safety
        url = to_visit.pop(0)
        result = get_content(url)
        
        if result:
            content, soup = result
            all_content.append(content)
            
            # Extract links and add to queue
            links = extract_links(soup, url)
            for link in links:
                if clean_url(link) not in visited_urls:
                    to_visit.append(link)
        
        # Be nice to the server
        time.sleep(0.5)
    
    # Write all content to file
    with open(output_file, 'w') as f:
        f.write("# Strands Agents SDK Documentation\n\n")
        f.write("*Automatically compiled from https://strandsagents.com/latest/*\n\n")
        f.write("---\n\n")
        f.write("".join(all_content))

if __name__ == "__main__":
    crawl_site()
    print(f"Documentation saved to {output_file}")
