import json

def test_catalog_urls():
    """Verify all catalog URLs are valid SHL URLs."""
    print("\n--- Testing Catalog URLs ---")
    
    with open("shl_catalog_data.json", "r") as f:
        catalog = json.load(f)
    
    invalid_urls = []
    non_shl_urls = []
    
    for item in catalog:
        url = item.get("link", "")
        if not url:
            invalid_urls.append(f"{item['name']}: Missing URL")
        elif not url.startswith("https://www.shl.com"):
            non_shl_urls.append(f"{item['name']}: {url}")
    
    if invalid_urls:
        print(f"✗ Found {len(invalid_urls)} missing URLs:")
        for url in invalid_urls[:5]:
            print(f"  - {url}")
    else:
        print("✓ All assessments have URLs")
    
    if non_shl_urls:
        print(f"✗ Found {len(non_shl_urls)} non-SHL URLs:")
        for url in non_shl_urls[:5]:
            print(f"  - {url}")
    else:
        print("✓ All URLs are from SHL domain")
    
    if not invalid_urls and not non_shl_urls:
        print(f"✓ All {len(catalog)} catalog entries have valid SHL URLs")
        return True
    else:
        return False

if __name__ == "__main__":
    test_catalog_urls()
