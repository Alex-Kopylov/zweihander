#!/usr/bin/env python3
"""Search arXiv and display results in a clean format.

Usage:
    python search_arxiv.py "GRPO reinforcement learning"
    python search_arxiv.py "GRPO reinforcement learning" --max 10
    python search_arxiv.py "GRPO reinforcement learning" --sort date
    python search_arxiv.py --author "Yann LeCun" --max 5
    python search_arxiv.py --category cs.AI --sort date --max 10
    python search_arxiv.py --id 2402.03300
    python search_arxiv.py --id 2402.03300,2401.12345
"""

import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET  # ruff: ignore[suspicious-xml-etree-import] - stdlib only; parses arXiv's own Atom
from dataclasses import dataclass

API_URL = "https://export.arxiv.org/api/query?"
USER_AGENT = "zweihander-arxiv/1.0 (+https://github.com/Alex-Kopylov/zweihander)"
NS = {"a": "http://www.w3.org/2005/Atom"}
TOTAL_RESULTS = "{http://a9.com/-/spec/opensearch/1.1/}totalResults"
SORT_BY = {"relevance": "relevance", "date": "submittedDate", "updated": "lastUpdatedDate"}
VALUE_FLAGS = {"--max", "--sort", "--author", "--category", "--id"}
ABSTRACT_CHARS = 300
VERSION_SUFFIX = re.compile(r"v\d+$")


@dataclass
class Search:
    """What to ask the arXiv API for; ``ids`` takes precedence over the other filters."""

    query: str | None = None
    author: str | None = None
    category: str | None = None
    ids: str | None = None
    max_results: int = 5
    sort: str = "relevance"


def parse_args(args: list[str]) -> Search:
    """Parse command-line arguments into a search.

    A value flag without a following value, and any unknown argument, joins the
    free-text query.

    Args:
        args: Command-line arguments without the program name.

    Returns:
        The requested search.
    """
    search = Search()
    positional: list[str] = []
    i = 0
    while i < len(args):
        flag = args[i]
        if flag not in VALUE_FLAGS or i + 1 == len(args):
            positional.append(flag)
            i += 1
            continue
        value = args[i + 1]
        i += 2
        match flag:
            case "--max":
                search.max_results = int(value)
            case "--sort":
                search.sort = value
            case "--author":
                search.author = value
            case "--category":
                search.category = value
            case _:
                search.ids = value
    if positional:
        search.query = " ".join(positional)
    return search


def build_url(search: Search) -> str:
    """Build the arXiv API query URL for a search.

    Args:
        search: The search to run.

    Returns:
        The full API URL.
    """
    params: dict[str, str] = {}
    if search.ids:
        params["id_list"] = search.ids
    else:
        parts = []
        if search.query:
            parts.append(f"all:{urllib.parse.quote(search.query)}")
        if search.author:
            parts.append(f"au:{urllib.parse.quote(search.author)}")
        if search.category:
            parts.append(f"cat:{search.category}")
        if not parts:
            print("Error: provide a query, --author, --category, or --id")
            sys.exit(1)
        params["search_query"] = "+AND+".join(parts)
    params["max_results"] = str(search.max_results)
    params["sortBy"] = SORT_BY.get(search.sort, search.sort)
    params["sortOrder"] = "descending"
    return API_URL + "&".join(f"{key}={value}" for key, value in params.items())


def fetch(url: str) -> bytes:
    """Fetch a URL from the arXiv API.

    Args:
        url: The API URL to fetch.

    Returns:
        The raw response body.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # ruff: ignore[suspicious-url-open-usage] - always the https arXiv API URL
    with urllib.request.urlopen(request, timeout=15) as response:  # ruff: ignore[suspicious-url-open-usage] - always the https arXiv API URL
        return response.read()


def print_entry(number: int, entry: ET.Element) -> None:
    """Print one Atom feed entry; missing elements print as empty text.

    Args:
        number: The entry's 1-based position in the results.
        entry: The ``<entry>`` element.
    """
    title = entry.findtext("a:title", "", NS).strip().replace("\n", " ")
    full_id = entry.findtext("a:id", "", NS).strip().split("/abs/")[-1]
    arxiv_id = VERSION_SUFFIX.sub("", full_id)  # base ID for links
    published = entry.findtext("a:published", "", NS)[:10]
    updated = entry.findtext("a:updated", "", NS)[:10]
    authors = ", ".join(author.findtext("a:name", "", NS) for author in entry.findall("a:author", NS))
    summary = entry.findtext("a:summary", "", NS).strip().replace("\n", " ")
    categories = ", ".join(category.get("term", "") for category in entry.findall("a:category", NS))

    print(f"{number}. {title}")
    print(f"   ID: {full_id} | Published: {published} | Updated: {updated}")
    print(f"   Authors: {authors}")
    print(f"   Categories: {categories}")
    print(f"   Abstract: {summary[:ABSTRACT_CHARS]}{'...' if len(summary) > ABSTRACT_CHARS else ''}")
    print(f"   Links: https://arxiv.org/abs/{arxiv_id} | https://arxiv.org/pdf/{arxiv_id}")
    print()


def run(search: Search) -> None:
    """Query arXiv and print the matching papers.

    Args:
        search: The search to run.
    """
    root = ET.fromstring(fetch(build_url(search)))  # ruff: ignore[suspicious-xml-element-tree-usage] - stdlib only; arXiv's own Atom
    entries = root.findall("a:entry", NS)
    if not entries:
        print("No results found.")
        return

    total = root.findtext(TOTAL_RESULTS)
    if total is not None:
        print(f"Found {total} results (showing {len(entries)})\n")
    for number, entry in enumerate(entries, start=1):
        print_entry(number, entry)


def main() -> None:
    """Run the command-line interface."""
    args = sys.argv[1:]
    if not args or args[0] in {"-h", "--help"}:
        print(__doc__)
        sys.exit(0)
    run(parse_args(args))


if __name__ == "__main__":
    main()
