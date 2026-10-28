from src.retrieval import Retriever


def test_retriever_loads_corpus():
    retriever = Retriever()
    assert len(retriever._docs) >= 8  # 4 runbooks + 4 incidents minimum


def test_retriever_finds_relevant_runbook():
    retriever = Retriever()
    results = retriever.search("ECS task restarting latency spike", top_k=3)
    assert any(d["doc_id"] == "RB-014" for d in results)


def test_retriever_finds_relevant_incident():
    retriever = Retriever()
    results = retriever.search("certificate expiring TLS ALB", top_k=3)
    assert any(d["doc_id"] in {"RB-031", "INC-0029"} for d in results)


def test_retriever_returns_empty_for_nonsense_query():
    retriever = Retriever()
    results = retriever.search("zzqxv unrelated nonsense token", top_k=3)
    assert results == [] or all(d["score"] < 0.1 for d in results)
