import pytest


def test_upload_text_document(client, plan):
    # Arrange
    content = b"Hello world. This is a test document for chunking."

    # Act
    response = client.post(
        f"/plans/{plan['id']}/documents",
        files={"file": ("test.txt", content)},
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["file_type"] == "txt"
    assert data["file_size"] > 0
    assert data["chunk_count"] > 0
    assert isinstance(data["id"], int)


def test_upload_markdown_document(client, plan):
    # Arrange
    content = b"# Title\n\nSome content here. More content for testing chunk extraction."

    # Act
    response = client.post(
        f"/plans/{plan['id']}/documents",
        files={"file": ("notes.md", content, "text/markdown")},
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "notes.md"
    assert data["file_type"] == "md"


def test_list_documents(client, plan):
    # Arrange
    client.post(
        f"/plans/{plan['id']}/documents",
        files={"file": ("a.txt", b"Document A content.")},
    )
    client.post(
        f"/plans/{plan['id']}/documents",
        files={"file": ("b.txt", b"Document B content.")},
    )

    # Act
    response = client.get(f"/plans/{plan['id']}/documents")

    # Assert
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 2
    filenames = {d["filename"] for d in docs}
    assert filenames == {"a.txt", "b.txt"}


def test_list_documents_empty(client, plan):
    # Act
    response = client.get(f"/plans/{plan['id']}/documents")

    # Assert
    assert response.status_code == 200
    assert response.json() == []


def test_delete_document(client, plan):
    # Arrange
    doc = client.post(
        f"/plans/{plan['id']}/documents",
        files={"file": ("to_delete.txt", b"Delete me.")},
    ).json()

    # Act
    response = client.delete(f"/plans/{plan['id']}/documents/{doc['id']}")

    # Assert
    assert response.status_code == 204

    # Assert — document list is empty after deletion
    remaining = client.get(f"/plans/{plan['id']}/documents").json()
    assert len(remaining) == 0


@pytest.mark.parametrize(
    "method,url,expected_status",
    [
        pytest.param("POST", "/plans/999/documents", 404, id="upload_plan_not_found"),
        pytest.param("GET", "/plans/999/documents", 404, id="list_documents_plan_not_found"),
    ],
)
def test_document_operations_plan_not_found(client, method, url, expected_status):
    # Arrange
    if method == "POST":
        body = {"files": {"file": ("test.txt", b"content")}}
    else:
        body = {}

    # Act
    response = client.request(method, url, **body)

    # Assert
    assert response.status_code == expected_status


def test_delete_document_not_found(client, plan):
    # Act
    response = client.delete(f"/plans/{plan['id']}/documents/999")

    # Assert
    assert response.status_code == 404


def test_upload_empty_file(client, plan):
    # Act
    response = client.post(
        f"/plans/{plan['id']}/documents",
        files={"file": ("empty.txt", b"")},
    )

    # Assert
    assert response.status_code == 422


def test_upload_unsupported_type(client, plan):
    # Act
    response = client.post(
        f"/plans/{plan['id']}/documents",
        files={"file": ("image.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )

    # Assert
    assert response.status_code == 400


def test_upload_file_too_large(client, plan, monkeypatch):
    # Arrange
    monkeypatch.setattr(
        "app.services.document_service.MAX_FILE_SIZE",
        10,
    )

    # Act
    response = client.post(
        f"/plans/{plan['id']}/documents",
        files={"file": ("big.txt", b"x" * 100)},
    )

    # Assert
    assert response.status_code == 413


def test_upload_invalid_pdf_returns_422(client, plan):
    # Act
    response = client.post(
        f"/plans/{plan['id']}/documents",
        files={"file": ("broken.pdf", b"not a real pdf", "application/pdf")},
    )

    # Assert
    assert response.status_code == 422
