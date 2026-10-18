"""The arxiv skill's search script, run as a CLI from the tree a user installs.

Covers ``scripts/search_arxiv.py``: the arXiv API URL each documented flag
builds, and the text it prints for the Atom feed the API returns. The network
is never touched; ``urllib.request.urlopen`` serves canned Atom XML.
"""

import io
import runpy
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest import mock

import pytest

API = "https://export.arxiv.org/api/query?"
DEFAULTS = "&max_results=5&sortBy=relevance&sortOrder=descending"

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
{total}{entries}
</feed>"""

TOTAL = "<opensearch:totalResults>1342</opensearch:totalResults>"

LONG_ENTRY = f"""<entry>
  <id>http://arxiv.org/abs/2402.03300v3</id>
  <updated>2024-04-27T15:24:11Z</updated>
  <published>2024-02-05T18:45:54Z</published>
  <title>DeepSeekMath: Pushing the Limits of Mathematical
  Reasoning</title>
  <summary>  Mathematical reasoning
is hard. {"a" * 300}
</summary>
  <author><name>Zhihong Shao</name></author>
  <author><name>Peiyi Wang</name></author>
  <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
  <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
</entry>"""

SHORT_ENTRY = """<entry>
  <id>http://arxiv.org/abs/hep-th/9901001</id>
  <updated>1999-01-02T00:00:00Z</updated>
  <published>1999-01-01T00:00:00Z</published>
  <title>Short</title>
  <summary>Brief.</summary>
  <author><name>Ann Author</name></author>
  <category term="hep-th"/>
</entry>"""

SHORT_OUTPUT = """1. Short
   ID: hep-th/9901001 | Published: 1999-01-01 | Updated: 1999-01-02
   Authors: Ann Author
   Categories: hep-th
   Abstract: Brief.
   Links: https://arxiv.org/abs/hep-th/9901001 | https://arxiv.org/pdf/hep-th/9901001

"""


def feed(*entries: str, total: str = TOTAL) -> bytes:
    return FEED.format(total=total, entries="".join(entries)).encode()


@pytest.fixture
def script(rendered: Path) -> Path:
    return rendered / "research" / "skills" / "arxiv" / "scripts" / "search_arxiv.py"


@pytest.fixture
def urlopen() -> Iterator[mock.MagicMock]:
    """Patch ``urlopen`` to serve an empty feed; tests swap in their own response."""
    with mock.patch("urllib.request.urlopen", return_value=io.BytesIO(feed())) as patched:
        yield patched


def respond(urlopen: mock.MagicMock, *entries: str, total: str = TOTAL) -> None:
    urlopen.return_value = io.BytesIO(feed(*entries, total=total))


def run(script: Path, *argv: str) -> None:
    """Run the script as ``__main__``, as ``python3 search_arxiv.py *argv`` would."""
    with mock.patch.object(sys, "argv", [str(script), *argv]):
        runpy.run_path(str(script), run_name="__main__")


def requested_url(urlopen: mock.MagicMock) -> str:
    urlopen.assert_called_once()
    return urlopen.call_args.args[0].full_url


@pytest.mark.parametrize(
    ("argv", "query"),
    [
        (("GRPO reinforcement learning",), "search_query=all:GRPO%20reinforcement%20learning" + DEFAULTS),
        (("GRPO", "reinforcement"), "search_query=all:GRPO%20reinforcement" + DEFAULTS),
        (("C++ & you",), "search_query=all:C%2B%2B%20%26%20you" + DEFAULTS),
        (("--author", "Yann LeCun", "--max", "5"), "search_query=au:Yann%20LeCun" + DEFAULTS),
        (
            ("--category", "cs.AI", "--sort", "date", "--max", "10"),
            "search_query=cat:cs.AI&max_results=10&sortBy=submittedDate&sortOrder=descending",
        ),
        (
            ("attention", "--author", "Vaswani", "--category", "cs.CL"),
            "search_query=all:attention+AND+au:Vaswani+AND+cat:cs.CL" + DEFAULTS,
        ),
        (("--id", "2402.03300,2401.12345"), "id_list=2402.03300,2401.12345" + DEFAULTS),
        (("ignored", "--author", "X", "--id", "2402.03300"), "id_list=2402.03300" + DEFAULTS),
        (("attention", "--max"), "search_query=all:attention%20--max" + DEFAULTS),
        (("--foo", "bar"), "search_query=all:--foo%20bar" + DEFAULTS),
    ],
)
def test_cli_arguments_build_expected_api_query(
    script: Path, urlopen: mock.MagicMock, argv: tuple[str, ...], query: str
) -> None:
    run(script, *argv)

    assert requested_url(urlopen) == API + query


@pytest.mark.parametrize(
    ("sort", "sort_by"),
    [
        ("relevance", "relevance"),
        ("date", "submittedDate"),
        ("updated", "lastUpdatedDate"),
        ("lastUpdatedDate", "lastUpdatedDate"),
    ],
)
def test_sort_option_maps_to_api_sort_by(script: Path, urlopen: mock.MagicMock, sort: str, sort_by: str) -> None:
    run(script, "q", "--sort", sort)

    assert requested_url(urlopen).endswith(f"&sortBy={sort_by}&sortOrder=descending")


@pytest.mark.parametrize("argv", [("--max", "3"), ("--sort", "date"), ("--author", "")])
def test_no_query_author_category_or_id_exits_with_error(
    script: Path, urlopen: mock.MagicMock, argv: tuple[str, ...], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exited:
        run(script, *argv)

    assert exited.value.code == 1
    assert capsys.readouterr().out == "Error: provide a query, --author, --category, or --id\n"
    urlopen.assert_not_called()


@pytest.mark.parametrize("argv", [(), ("-h",), ("--help", "ignored")])
def test_help_or_no_arguments_prints_usage_and_exits_zero(
    script: Path, urlopen: mock.MagicMock, argv: tuple[str, ...], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exited:
        run(script, *argv)

    assert exited.value.code == 0
    out = capsys.readouterr().out
    assert out.startswith("Search arXiv and display results in a clean format.\n\nUsage:\n")
    assert "search_arxiv.py --id 2402.03300,2401.12345\n" in out
    urlopen.assert_not_called()


def test_non_integer_max_fails_before_any_request(script: Path, urlopen: mock.MagicMock) -> None:
    with pytest.raises(ValueError, match="ten"):
        run(script, "q", "--max", "ten")

    urlopen.assert_not_called()


def test_results_print_title_id_authors_date_categories_abstract_and_links(
    script: Path, urlopen: mock.MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    respond(urlopen, LONG_ENTRY, SHORT_ENTRY)
    run(script, "q")

    assert capsys.readouterr().out == (
        "Found 1342 results (showing 2)\n"
        "\n"
        "1. DeepSeekMath: Pushing the Limits of Mathematical   Reasoning\n"
        "   ID: 2402.03300v3 | Published: 2024-02-05 | Updated: 2024-04-27\n"
        "   Authors: Zhihong Shao, Peiyi Wang\n"
        "   Categories: cs.CL, cs.AI\n"
        f"   Abstract: Mathematical reasoning is hard. {'a' * 268}...\n"
        "   Links: https://arxiv.org/abs/2402.03300 | https://arxiv.org/pdf/2402.03300\n"
        "\n" + SHORT_OUTPUT.replace("1. Short", "2. Short")
    )


def test_feed_without_total_results_skips_found_line(
    script: Path, urlopen: mock.MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    respond(urlopen, SHORT_ENTRY, total="")
    run(script, "q")

    assert capsys.readouterr().out == SHORT_OUTPUT


def test_feed_without_entries_prints_no_results(
    script: Path, urlopen: mock.MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    run(script, "q")

    assert capsys.readouterr().out == "No results found.\n"


@pytest.mark.parametrize(
    ("full_id", "base_id"),
    [
        ("solv-int/9901001v1", "solv-int/9901001"),
        ("solv-int/9901001", "solv-int/9901001"),
        ("2402.03300v12", "2402.03300"),
    ],
)
def test_links_strip_only_trailing_version_suffix(
    script: Path, urlopen: mock.MagicMock, capsys: pytest.CaptureFixture[str], full_id: str, base_id: str
) -> None:
    respond(urlopen, SHORT_ENTRY.replace("hep-th/9901001", full_id))
    run(script, "q")

    out = capsys.readouterr().out
    assert f"   ID: {full_id} | Published:" in out
    assert f"   Links: https://arxiv.org/abs/{base_id} | https://arxiv.org/pdf/{base_id}\n" in out


def test_request_identifies_zweihander_with_timeout(script: Path, urlopen: mock.MagicMock) -> None:
    run(script, "q")

    request = urlopen.call_args.args[0]
    assert request.get_header("User-agent") == "zweihander-arxiv/1.0 (+https://github.com/Alex-Kopylov/zweihander)"
    assert urlopen.call_args.kwargs == {"timeout": 15}


def test_entry_missing_elements_prints_empty_fields(
    script: Path, urlopen: mock.MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    respond(urlopen, "<entry><author/><category/></entry>", total="")
    run(script, "q")

    assert capsys.readouterr().out == (
        "1. \n"
        "   ID:  | Published:  | Updated: \n"
        "   Authors: \n"
        "   Categories: \n"
        "   Abstract: \n"
        "   Links: https://arxiv.org/abs/ | https://arxiv.org/pdf/\n"
        "\n"
    )
