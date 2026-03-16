import asyncio
import sys
from src.crawl import get_urls_from_html, get_html, crawl_page, crawl_site_async
from src.json_report import write_json_report


async def main():
    if len(sys.argv) < 2:
        print("no website provided")
        sys.exit(1)
    elif len(sys.argv) > 4:
        print("too many arguments provided")
        sys.exit(1)
    base_url = sys.argv[1]
    try:
        max_concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    except ValueError:
        print("Invalid number provided for arguments")
        sys.exit(1)
    print(f"starting crawl of: {base_url}")
    crawled = await crawl_site_async(base_url, max_concurrency, max_pages)
    write_json_report(crawled)


if __name__ == "__main__":
    asyncio.run(main())
