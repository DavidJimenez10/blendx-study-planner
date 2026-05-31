from app.models.plan_document import DocumentChunk, PlanDocument


def _mock_search_similar_empty(self, plan_id, embedding, top_k, threshold):
    return []


def _mock_search_similar_with_results(self, plan_id, embedding, top_k, threshold):
    chunk = DocumentChunk(
        id=1,
        document_id=1,
        plan_id=plan_id,
        content="Python is a programming language created by Guido van Rossum.",
        chunk_index=0,
    )
    return [(chunk, 0.95)]


def _mock_get_document_by_chunk_id(self, chunk_id):
    return PlanDocument(id=1, plan_id=1, filename="notes.txt", file_type="txt")


def test_chat_returns_answer(client, plan, mock_llm, monkeypatch):
    # Arrange
    mock_llm.chat_response = "Python was created by Guido van Rossum in 1991."
    monkeypatch.setattr(
        "app.services.chat_service.DocumentRepository.search_similar",
        _mock_search_similar_with_results,
    )
    monkeypatch.setattr(
        "app.services.chat_service.DocumentRepository.get_document_by_chunk_id",
        _mock_get_document_by_chunk_id,
    )

    # Act
    response = client.post(
        f"/plans/{plan['id']}/chat",
        json={"question": "Who created Python?"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Python was created by Guido van Rossum in 1991."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["filename"] == "notes.txt"
    assert "Python" in data["sources"][0]["content"]


def test_chat_no_relevant_chunks(client, plan, monkeypatch):
    # Arrange
    monkeypatch.setattr(
        "app.services.chat_service.DocumentRepository.search_similar",
        _mock_search_similar_empty,
    )

    # Act
    response = client.post(
        f"/plans/{plan['id']}/chat",
        json={"question": "Who created Python?"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "No encontré" in data["answer"]
    assert data["sources"] == []


def test_chat_plan_not_found(client):
    # Act
    response = client.post(
        "/plans/999/chat",
        json={"question": "Who created Python?"},
    )

    # Assert
    assert response.status_code == 404


def test_chat_includes_multiple_sources(client, plan, mock_llm, mocker):
    # Arrange
    mock_llm.chat_response = "Multi-source answer."

    chunk_a = DocumentChunk(
        id=1,
        document_id=1,
        plan_id=plan["id"],
        content="Chunk A content.",
        chunk_index=0,
    )
    chunk_b = DocumentChunk(
        id=2,
        document_id=2,
        plan_id=plan["id"],
        content="Chunk B content.",
        chunk_index=0,
    )
    doc_a = PlanDocument(id=1, plan_id=plan["id"], filename="a.txt", file_type="txt")
    doc_b = PlanDocument(id=2, plan_id=plan["id"], filename="b.txt", file_type="txt")

    mock_repo = mocker.Mock()
    mock_repo.search_similar.return_value = [(chunk_a, 0.9), (chunk_b, 0.85)]
    mock_repo.get_document_by_chunk_id.side_effect = lambda chunk_id: doc_a if chunk_id == 1 else doc_b

    mocker.patch(
        "app.services.chat_service.DocumentRepository",
        return_value=mock_repo,
    )

    # Act
    response = client.post(
        f"/plans/{plan['id']}/chat",
        json={"question": "Test multiple sources"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Multi-source answer."
    assert len(data["sources"]) == 2
    filenames = {s["filename"] for s in data["sources"]}
    assert filenames == {"a.txt", "b.txt"}
