from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, Tag


def normalize_url(url:str) -> str:
    parsed_url = urlparse(url)
    if not parsed_url:
        print(f"Error parsing URL: {url}")
        return ""
    netloc = parsed_url.netloc
    path = parsed_url.path
    if path.endswith('/'):
        path = path.rstrip('/')
    return (netloc + path).lower()

def get_heading_from_html(html:str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    h_tag = soup.find('h1') or soup.find('h2')
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""

def get_first_paragraph_from_html(html:str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    main_block = soup.find("main")
    if isinstance(main_block, Tag):
        p_tag = main_block.find("p")
    else:
        p_tag = soup.find('p')

    return p_tag.get_text(strip=True) if isinstance(p_tag, Tag) else ""

def get_urls_from_html(html:str, base_url:str) -> list[str]:
    soup = BeautifulSoup(html, 'html.parser')
    urls = []
    for a_tag in soup.find_all('a', href=True):
        url: str = a_tag.get('href')
        absolute_url: str = urljoin(base_url, url)
        urls.append(absolute_url)
    return urls

def get_images_from_html(html:str, base_url:str) -> list[str]:
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = []
    for img_tag in soup.find_all('img', src=True):
        img: str = img_tag.get('src')
        absolute_url = urljoin(base_url, img)
        image_urls.append(absolute_url)
    return image_urls
