import asyncio
from urllib.parse import urlparse, urljoin
import aiohttp
from bs4 import BeautifulSoup, Tag
import requests


class AsyncCrawler:
    def __init__(self, base_url: str, max_concurrency: int, max_pages: int):
        self.base_url: str = base_url
        self.base_domain: str = urlparse(base_url).netloc
        self.page_data: dict[str, any] = {}
        self.lock = asyncio.Lock()
        self.max_concurrency: int = max_concurrency
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.session = None
        self.max_pages: int = max_pages
        self.should_stop: bool = False
        self.all_tasks: set[asyncio.Task] = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers={"User-Agent": "BootCrawler/1.0"})
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:
        async with self.lock:
            if self.should_stop or normalized_url in self.page_data:
                print(f"Skipping {normalized_url} - already crawled or stopping")
                return False
            if len(self.page_data) >= self.max_pages:
                self.should_stop = True
                print("Reached max page limit, stopping crawl")
                self.all_tasks.clear()
                return False
            return True

    async def get_html(self, url: str) -> str:
        try:
            async with self.session.get(url) as response:
                if response.status > 400:
                    raise Exception(
                        f"Failed to fetch {url}: Status code {response.status}"
                    )
                if "text/html" not in response.headers.get("Content-Type", ""):
                    raise Exception(f"URL {url} does not contain HTML content")
                return await response.text()
        except Exception as e:
            print(f"Network error fetching {url}: {e}")
            return ""

    async def crawl_page(self, current_url: str):
        if self.should_stop:
            return

        base_domain, current_domain = (
            urlparse(self.base_url).netloc,
            urlparse(current_url).netloc,
        )
        normalized_current = normalize_url(current_url)
        if current_domain != base_domain:
            print(f"Skipping {current_url} - outside of base domain")
            return
        if not await self.add_page_visit(normalized_current):
            print(f"Skipping {current_url} - already crawled")
            return
        print(f"Crawling {current_url}")
        async with self.semaphore:
            html = await self.get_html(current_url)
            page_info = extract_page_data(html, current_url)
            async with self.lock:
                self.page_data[normalized_current] = page_info
            urls_to_crawl = get_urls_from_html(
                html, current_url, BeautifulSoup(html, "html.parser")
            )

        tasks = []
        for url_link in set(urls_to_crawl):
            try:
                print(f"Crawling inner link: {url_link}")
                task = asyncio.create_task(self.crawl_page(url_link))
                self.all_tasks.add(task)
                tasks.append(task)
            finally:
                self.all_tasks.discard(task)

        await asyncio.gather(*tasks)

    async def crawl(self) -> dict[str, any]:
        await self.crawl_page(self.base_url)
        return self.page_data


async def crawl_site_async(
    base_url: str, max_concurrency: int = 10, max_pages: int = 1000
) -> dict[str, any]:
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()


def normalize_url(url: str) -> str:
    parsed_url = urlparse(url)
    if not parsed_url:
        print(f"Error parsing URL: {url}")
        return ""
    netloc = parsed_url.netloc
    path = parsed_url.path

    return (netloc + path.rstrip("/")).lower()


def get_heading_from_html(html: str, soup: BeautifulSoup) -> str:
    h_tag = soup.find("h1") or soup.find("h2")
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""


def get_first_paragraph_from_html(html: str, soup: BeautifulSoup) -> str:
    main_block = soup.find("main")
    if isinstance(main_block, Tag):
        p_tag = main_block.find("p")
    else:
        p_tag = soup.find("p")

    return p_tag.get_text(strip=True) if isinstance(p_tag, Tag) else ""


def get_urls_from_html(html: str, base_url: str, soup: BeautifulSoup) -> list[str]:
    urls = [urljoin(base_url, a_tag["href"]) for a_tag in soup.find_all("a", href=True)]
    return urls


def get_images_from_html(html: str, base_url: str, soup: BeautifulSoup) -> list[str]:
    image_urls = [
        urljoin(base_url, img_tag["src"]) for img_tag in soup.find_all("img", src=True)
    ]
    return image_urls


def extract_page_data(html: str, page_url: str) -> dict[str, any]:
    soup = BeautifulSoup(html, "html.parser")
    heading = get_heading_from_html(html, soup)
    first_paragraph = get_first_paragraph_from_html(html, soup)
    image_urls = get_images_from_html(html, page_url, soup)
    outgoing_links = get_urls_from_html(html, page_url, soup)

    return {
        "url": page_url,
        "heading": heading,
        "first_paragraph": first_paragraph,
        "outgoing_links": outgoing_links,
        "image_urls": image_urls,
    }


def get_html(url: str) -> str:
    try:
        response = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
        if response.status_code > 400:
            raise Exception(
                f"Failed to fetch {url}: Status code {response.status_code}"
            )
        if "text/html" not in response.headers.get("Content-Type", ""):
            raise Exception(f"URL {url} does not contain HTML content")
    except Exception as e:
        print(f"Network error fetching {url}: {e}")
        return ""
    return response.text


def crawl_page(
    base_url: str,
    current_url: str | None = None,
    page_data: dict[str, any] | None = None,
) -> dict[str, any]:
    current_url = current_url if current_url else base_url
    page_data = page_data if page_data else {}
    base_domain, current_domain = (
        urlparse(base_url).netloc,
        urlparse(current_url).netloc,
    )

    normalized_current = normalize_url(current_url)

    if current_domain != base_domain:
        print(f"Skipping {current_url} - outside of base domain")
        return page_data
    if normalized_current in page_data:
        print(f"Skipping {current_url} - already crawled")
        return page_data
    print(f"Crawling {current_url}")
    html = get_html(current_url)
    page_data[normalized_current] = extract_page_data(html, current_url)
    for url_link in page_data[normalized_current]["outgoing_links"]:
        print(f"Crawling inner link: {url_link}")
        crawl_page(base_url, url_link, page_data)
    return page_data
