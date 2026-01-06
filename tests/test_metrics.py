from obrbr.metrics import QueryEval, recall_at_k, recall_table


def test_recall_at_k_single_hit():
    evals = [
        QueryEval(query_id="q1", truth={"a"}, ranked_labels=["a", "b", "c"]),
        QueryEval(query_id="q2", truth={"x"}, ranked_labels=["a", "b", "x"]),
    ]
    assert recall_at_k(evals, 1) == 0.5
    assert recall_at_k(evals, 3) == 1.0


def test_recall_table():
    evals = [QueryEval(query_id="q", truth={"z"}, ranked_labels=["a", "z"])]
    table = recall_table(evals, [1, 2, 10])
    assert table[1] == 0.0
    assert table[2] == 1.0
    assert table[10] == 1.0
