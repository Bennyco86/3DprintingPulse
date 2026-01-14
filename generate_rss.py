import os
import glob
import re
import datetime
import markdown
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
from xml.dom import minidom

# Configuration
REPO_URL = "https://github.com/Bennyco86/3DprintingPulse"
SITE_URL = "https://Bennyco86.github.io/3DprintingPulse"
FEED_FILE = "feed.xml"
TITLE = "Quality3Ds Daily Pulse"
DESCRIPTION = "Curated daily news for 3D printing enthusiasts."

def parse_daily_readme(file_path, date_str):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract stories (looking for lines starting with emoji like ??)
    stories = []
    # Split by double newline to find blocks
    blocks = content.split('\n\n')
    
    current_story = {}
    
    for block in blocks:
        lines = block.strip().split('\n')
        if not lines:
            continue
            
        headline = lines[0].strip()
        # Check if it looks like a headline (starts with emoji or non-standard char)
        if re.match(r'^[^Ww# ]', headline) or headline.startswith('## '):
             if headline.startswith('## '): # Skip section headers
                 continue
             
             # Start new story
             if current_story:
                 stories.append(current_story)
             
             current_story = {
                 'title': headline,
                 'description': '\n'.join(lines[1:]),
                 'link': SITE_URL, # Default link
                 'date': date_str
             }
             
             # Try to extract a specific link
             link_match = re.search(r'https?://[^Ss ]+', block)
             if link_match:
                 current_story['link'] = link_match.group(0)

    if current_story:
        stories.append(current_story)
        
    return stories

def generate_rss():
    root = Element('rss')
    root.set('version', '2.0')
    channel = SubElement(root, 'channel')

    SubElement(channel, 'title').text = TITLE
    SubElement(channel, 'link').text = SITE_URL
    SubElement(channel, 'description').text = DESCRIPTION
    SubElement(channel, 'lastBuildDate').text = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Find all daily folders (YYYY-MM-DD)
    search_path = os.path.join('.', '20??-??-??', 'README.md')
    files = glob.glob(search_path)
    files.sort(reverse=True) # Newest first

    for file_path in files:
        # Extract date from path (.\2026-01-14\README.md)
        date_str = os.path.dirname(file_path).split(os.sep)[-1]
        
        stories = parse_daily_readme(file_path, date_str)
        
        for story in stories:
            item = SubElement(channel, 'item')
            SubElement(item, 'title').text = f"[{date_str}] {story['title']}"
            SubElement(item, 'link').text = story['link']
            
            # Create a description with HTML
            desc_html = markdown.markdown(story['description'])
            SubElement(item, 'description').text = desc_html
            
            SubElement(item, 'pubDate').text = f"{date_str} 12:00:00 GMT"
            SubElement(item, 'guid').text = f"{date_str}-{hash(story['title'])}"

    # Write to file
    xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
    with open(FEED_FILE, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"Generated {FEED_FILE} with {len(files)} days of content.")

if __name__ == "__main__":
    generate_rss()
