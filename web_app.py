#!/usr/bin/env python3
"""Flask web application for DWFX to PDF conversion."""

import io
import logging
import uuid
import zipfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from dwfx_to_pdf import _run_xpstopdf

logger = logging.getLogger(__name__)

# Suppress Werkzeug HTTPS probe errors
class WerkzeugFilter(logging.Filter):
    def filter(self, record):
        if "Bad request version" in record.getMessage():
            return False
        return True

logging.getLogger("werkzeug").addFilter(WerkzeugFilter())

app = Flask(__name__)

UPLOAD_DIR = Path("uploads")
PDF_DIR = Path("pdf")


def _ensure_dirs():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    _ensure_dirs()

    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files selected"}), 400

    results = []
    for f in files:
        if not f.filename:
            continue
        original_name = f.filename
        if not original_name.lower().endswith(".dwfx"):
            results.append({
                "name": original_name,
                "success": False,
                "error": "Not a .dwfx file",
            })
            continue

        # Save uploaded file with unique prefix to avoid collisions
        unique_id = uuid.uuid4().hex[:8]
        safe_name = f"{unique_id}_{original_name}"
        upload_path = UPLOAD_DIR / safe_name
        f.save(upload_path)

        # Derive output PDF name (keep original base name)
        pdf_name = Path(original_name).with_suffix(".pdf").name
        pdf_path = PDF_DIR / pdf_name

        try:
            _run_xpstopdf(upload_path, pdf_path)
            results.append({
                "name": original_name,
                "pdf_name": pdf_name,
                "success": True,
            })
        except Exception as e:
            results.append({
                "name": original_name,
                "success": False,
                "error": str(e),
            })
        finally:
            # Clean up uploaded file
            try:
                upload_path.unlink()
            except Exception:
                pass

    return jsonify({"results": results})


@app.route("/download/<path:filename>")
def download(filename):
    pdf_path = PDF_DIR / filename
    if not pdf_path.exists():
        return jsonify({"error": "File not found"}), 404
    return send_file(pdf_path, as_attachment=True, download_name=filename)


@app.route("/download-all", methods=["POST"])
def download_all():
    data = request.get_json(silent=True) or {}
    filenames = data.get("files", [])

    if not filenames:
        return jsonify({"error": "No files specified"}), 400

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in filenames:
            pdf_path = PDF_DIR / name
            if pdf_path.exists():
                zf.write(pdf_path, arcname=name)

    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="converted.zip", mimetype="application/zip")


@app.route("/api/files")
def list_files():
    _ensure_dirs()
    files = sorted([
        p.name for p in PDF_DIR.iterdir()
        if p.is_file() and p.suffix.lower() == ".pdf"
    ])
    return jsonify({"files": files})


def run_web(host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
    """Entry point called from the CLI."""
    _ensure_dirs()
    logger.info(f"Starting web server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_web(debug=True)
