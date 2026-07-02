import asyncio
from catalog import SHLCatalog


async def main():
    """Scrape the SHL catalog and save to JSON."""
    catalog = SHLCatalog()
    await catalog.scrape_catalog()
    catalog.save_to_json("catalog.json")
    print(f"Saved {len(catalog.assessments)} assessments to catalog.json")


if __name__ == "__main__":
    asyncio.run(main())
