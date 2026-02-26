import pytest
from pathlib import Path
from web_app import app, UPLOAD_DIR, PDF_DIR
import io

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Test that the index page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"dwfx" in response.data.lower()

def test_upload_invalid_filetype(client):
    """Test that non-DWFX files are rejected."""
    data = {
        'files': (io.BytesIO(b"fake data"), "test.txt")
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    res_json = response.get_json()
    assert res_json['results'][0]['success'] is False
    assert "not a .dwfx file" in res_json['results'][0]['error'].lower()

def test_upload_dwfx_success(client, tmp_path, monkeypatch):
    """Test successful upload and conversion attempt."""
    # Mock the conversion function to avoid needing libgxps in CI/tests
    import web_app
    def mock_run_xpstopdf(in_path, out_path):
        out_path.touch()
    
    monkeypatch.setattr(web_app, "_run_xpstopdf", mock_run_xpstopdf)
    
    # Ensure dirs exist (relative to BASE_DIR usually, but we use absolute paths now)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        'files': (io.BytesIO(b"fake dwfx content"), "test.dwfx")
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    res_json = response.get_json()
    assert res_json['results'][0]['success'] is True
    assert res_json['results'][0]['pdf_name'] == "test.pdf"
    
    # Cleanup
    pdf_path = PDF_DIR / "test.pdf"
    if pdf_path.exists():
        pdf_path.unlink()

def test_download_all_empty(client):
    """Test download-all returns error if no files requested."""
    response = client.post('/download-all', json={'files': []})
    assert response.status_code == 400

def test_max_content_length(client):
    """Test that very large files are rejected by Flask/Werkzeug (MAX_CONTENT_LENGTH)."""
    # Create a 101MB stream
    large_data = b"0" * (101 * 1024 * 1024)
    data = {
        'files': (io.BytesIO(large_data), "too_big.dwfx")
    }
    # Flask typically returns 413 for Request Entity Too Large
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 413
