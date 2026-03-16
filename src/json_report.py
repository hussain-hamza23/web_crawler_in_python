import json


def write_json_report(page_data: dict[str, any], filename: str = "report.json") -> None:
    if not page_data:
        print("No data to write to report")
        return

    pages = sorted(page_data.values(), key=lambda x: x["url"])
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(pages, file, indent=2)
