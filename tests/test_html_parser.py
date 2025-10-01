from codegraphcontext.tools.graph_builder import GraphBuilder
from pathlib import Path

def test_parse_html_file(tmp_path):
    html_content = "<div class='box'>Hello</div>"
    html_file = tmp_path / "sample.html"
    html_file.write_text(html_content)

    gb = GraphBuilder()
    result = gb.parse_html_file(tmp_path, html_file)

    assert "elements" in result
    assert result["elements"][0]["tag"] == "div"
    assert result["elements"][0]["attributes"]["class"] == "box"
    assert result["elements"][0]["text"] == "Hello"
