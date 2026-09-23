"""NAMED_CONTROLS: a submit input's value is its accessible name."""

from page_ready._dom_legacy import score_html

# Comment-form shape from tygartmedia.com: visible label is the value,
# with no aria-label and no aria-labelledby. Text values and empty
# icon buttons must stay unnamed.
PAGE = """<!doctype html>
<html><body>
<main>
  <h1>Article</h1>
  <form>
    <input type="submit" id="submit" value="Post Comment">
    <input type="button" id="btn" value="Preview">
    <input type="reset" id="rst" value="Reset">
    <input type="submit" id="blank-submit" value="">
    <input type="text" id="search" value="typed text">
    <button type="button" class="icon-only" style="width:24px;height:24px"></button>
  </form>
</main>
</body></html>
"""


def _unnamed():
    result = score_html(PAGE, source="named-controls.html")
    gate = next(g for g in result["gates"] if g["gate"] == "NAMED_CONTROLS")
    return gate, gate["evidence"]["unnamed_sample"]


def test_submit_value_counts_as_accessible_name():
    gate, unnamed = _unnamed()
    ids = {item["id"] for item in unnamed}
    assert "submit" not in ids
    assert "btn" not in ids
    assert "rst" not in ids
    assert "blank-submit" in ids
    assert "search" in ids
    assert any(item["tag"] == "button" and item["class"] == "icon-only" for item in unnamed)
    assert gate["status"] == "FAIL"
