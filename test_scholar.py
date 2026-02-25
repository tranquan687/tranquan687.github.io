#!/usr/bin/env python3

import os
from datetime import datetime

# Mock scholarly for testing
class MockScholarly:
    def search_author_id(self, id):
        return {"name": "Mock Author"}

    def fill(self, author):
        return {
            "publications": [
                {
                    "pub_id": "test_id_1",
                    "bib": {"title": "Test Paper 1", "pub_year": "2023"},
                    "num_citations": 5
                },
                {
                    "pub_id": "test_id_2",
                    "bib": {"title": "Test Paper 2", "pub_year": "2024"},
                    "num_citations": 10
                }
            ]
        }

scholarly = MockScholarly()

def load_scholar_user_id():
    return "NfwzqKoAAAAJ"  # From socials.yml

SCHOLAR_USER_ID = load_scholar_user_id()

def get_scholar_citations():
    today = datetime.now().strftime("%Y-%m-%d")
    citation_data = {"metadata": {"last_updated": today}, "papers": {}}

    try:
        author = scholarly.search_author_id(SCHOLAR_USER_ID)
        author_data = scholarly.fill(author)
    except Exception as e:
        print(f"Error: {e}")
        return

    for pub in author_data["publications"]:
        pub_id = pub.get("pub_id")
        title = pub.get("bib", {}).get("title", "Unknown")
        year = pub.get("bib", {}).get("pub_year", "Unknown")
        citations = pub.get("num_citations", 0)

        print(f"Found: {title} ({year}) - Citations: {citations}")

        citation_data["papers"][pub_id] = {
            "title": title,
            "year": year,
            "citations": citations,
        }

    print("Mock citation data:")
    import json
    print(json.dumps(citation_data, indent=2))

if __name__ == "__main__":
    get_scholar_citations()