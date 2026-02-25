#!/usr/bin/env python3

import os
import sys
from datetime import datetime
from scholarly import scholarly

def load_scholar_user_id() -> str:
    """Load the Google Scholar user ID from the configuration file."""
    config_file = "_data/socials.yml"
    if not os.path.exists(config_file):
        print(f"Configuration file {config_file} not found.")
        sys.exit(1)
    try:
        import yaml
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        scholar_user_id = config.get("scholar_userid")
        if not scholar_user_id:
            print("No 'scholar_userid' found in _data/socials.yml.")
            sys.exit(1)
        return scholar_user_id
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

SCHOLAR_USER_ID = load_scholar_user_id()
BIB_FILE = "_bibliography/papers.bib"

def get_existing_titles():
    """Get set of existing paper titles from bib file."""
    titles = set()
    if os.path.exists(BIB_FILE):
        with open(BIB_FILE, "r") as f:
            content = f.read()
            # Simple check for title= in bib
            for line in content.split('\n'):
                if 'title' in line and '=' in line:
                    # Extract title roughly
                    parts = line.split('=', 1)
                    if len(parts) > 1:
                        title = parts[1].strip().strip('{},')
                        titles.add(title.lower())
    return titles

def generate_bibtex(pub):
    """Generate BibTeX entry from pub data."""
    bib = pub.get('bib', {})
    title = bib.get('title', 'Unknown Title')
    authors = bib.get('author', 'Unknown Author')
    year = bib.get('pub_year', 'Unknown Year')
    journal = bib.get('journal', '')
    volume = bib.get('volume', '')
    pages = bib.get('pages', '')
    doi = pub.get('pub_url', '')  # Scholarly may have doi

    # Create a simple bib key
    first_author = authors.split()[0].lower() if authors else 'unknown'
    bib_key = f"{first_author}{year}"

    entry = f"@article{{{bib_key},\n"
    entry += f"  title={{{title}}},\n"
    entry += f"  author={{{authors}}},\n"
    entry += f"  year={{{year}}},\n"
    if journal:
        entry += f"  journal={{{journal}}},\n"
    if volume:
        entry += f"  volume={{{volume}}},\n"
    if pages:
        entry += f"  pages={{{pages}}},\n"
    if doi:
        entry += f"  doi={{{doi}}},\n"
    entry += "}\n\n"

    return entry

def sync_papers():
    """Sync papers from Google Scholar to bib file."""
    print(f"Fetching publications for Google Scholar ID: {SCHOLAR_USER_ID}")

    existing_titles = get_existing_titles()
    print(f"Found {len(existing_titles)} existing papers in {BIB_FILE}")

    try:
        author = scholarly.search_author_id(SCHOLAR_USER_ID)
        author_data = scholarly.fill(author)
    except Exception as e:
        print(f"Error fetching author data: {e}")
        sys.exit(1)

    if "publications" not in author_data:
        print("No publications found.")
        return

    new_entries = []
    for pub in author_data["publications"]:
        try:
            # Fill pub for more details
            pub_filled = scholarly.fill(pub)
            title = pub_filled.get('bib', {}).get('title', '').lower()
            if title and title not in existing_titles:
                bib_entry = generate_bibtex(pub_filled)
                new_entries.append(bib_entry)
                print(f"Adding new paper: {title}")
            else:
                print(f"Skipping existing paper: {title}")
        except Exception as e:
            print(f"Error processing publication: {e}")

    if new_entries:
        with open(BIB_FILE, "a") as f:
            f.writelines(new_entries)
        print(f"Added {len(new_entries)} new papers to {BIB_FILE}")
    else:
        print("No new papers to add.")

if __name__ == "__main__":
    sync_papers()