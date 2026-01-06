from obrbr.reporting import render_summary_table_md


def test_render_summary_table_md():
    rows = [
        {"index": "i1", "model": "A", "queries": 10, "recall@1": 0.5},
        {"index": "i1", "model": "B", "queries": 10, "recall@1": 0.25},
    ]
    md = render_summary_table_md(rows)
    assert "| index | model | queries | recall@1 |" in md
    assert "| --- | --- | --- | --- |" in md
