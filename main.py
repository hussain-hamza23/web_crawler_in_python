from src.crawl import get_urls_from_html

def main():
    html = "<html><body><a>No href here</a></body></html>"
    base_url = "https://www.example.com"

    actual = get_urls_from_html(html, base_url)
    print("Actual URLs:", actual)


if __name__ == "__main__":
    main()
