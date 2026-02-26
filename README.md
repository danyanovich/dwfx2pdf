<div align="center">
  <br />
  <h1>
    <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Flask-Dark.svg" width="32" height="32" style="vertical-align: middle; margin-bottom: 6px;" />
    dwfx2pdf
  </h1>
  <p><strong>A blazingly fast, multi-threaded command-line & web tool to convert DWFX files to PDFs</strong></p>

  <p>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge&color=6366f1" alt="License: MIT"></a>
    <img src="https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&color=4ade80&logo=python&logoColor=white" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/Contributions-Welcome-blue.svg?style=for-the-badge&color=f472b6" alt="Contributions Welcome">
  </p>
  <br />
</div>

## ✨ Features

- 🚀 **Multi-threaded CLI**: Processes hundreds of files concurrently (configurable via `--workers`).
- 🌐 **Beautiful Web UI**: Start a local web server with a stunning, drag-and-drop dark mode interface.
- 👀 **Watch Mode**: Real-time folder monitoring with debounce protection (ignores incomplete network transfers).
- 📊 **Progress Bar**: Beautiful progress tracking during batch conversions using `tqdm`.
- 🔒 **Secure**: Hardened against common file upload vulnerabilities (Path Traversal).

---

## 🛠️ Installation

### 1. System Dependencies (macOS)
The tool requires `xpstopdf` under the hood, provided by `libgxps`.

```bash
brew install libgxps
```
> **Note:** If Homebrew keeps it keg-only, the tool will automatically detect its path at `/opt/homebrew/opt/libgxps/bin/xpstopdf`.

### 2. Install the Project
You can install this repository directly from GitHub or locally:

```bash
# Clone the repository
git clone https://github.com/danyanovich/dwfx2pdf.git
cd dwfx2pdf

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

*(Alternatively, you can install the CLI globally via `pip install .`)*

---

## 💻 Usage

### 🎨 Web Interface (Recommended)
Launch a beautiful drag-and-drop web UI in your browser:

```bash
./run.sh --web
```
> Or manually: `python dwfx_to_pdf.py web --port 8080`

Open **`http://localhost:8080`** in your browser. You can drag `.dwfx` files onto the page and download the converted PDFs instantly.

### 🔄 Batch Conversion (`convert`)
Convert all currently existing `.dwfx` files in a folder using the CLI:

```bash
python dwfx_to_pdf.py convert --dwfx-dir ./dwfx --pdf-dir ./pdf --workers 8
```
| Argument | Description | Default |
|----------|-------------|---------|
| `--dwfx-dir` | Folder to read `.dwfx` files from | `./dwfx` |
| `--pdf-dir` | Folder to output PDFs to | `./pdf` |
| `--workers` | Number of parallel conversion threads | `4` |
| `--overwrite` | Force overwrite existing PDFs | `False` |

### 🔍 Watch Mode (`watch`)
Monitor a folder and automatically convert any new `.dwfx` files dropped there:

```bash
./run.sh
```
> Or manually: `python dwfx_to_pdf.py watch --dwfx-dir ./dwfx --pdf-dir ./output`

The watch mode includes a debounce mechanism that safely waits for large files to finish copying before attempting conversion.

---

## 🏗️ Architecture & Security

- Concurrency is managed via `concurrent.futures.ThreadPoolExecutor`.
- The Web UI uses **Flask** and includes strict checks using `werkzeug.utils.secure_filename` to prevent Directory Traversal attacks.
- Outputs are zipped in-memory for bulk downloads, minimizing I/O overhead.

---

## 🚀 Deployment

For production usage, do not use the built-in Flask development server. Instead, use a robust WSGI server like **Gunicorn** (Linux/macOS) or **Waitress** (Windows).

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 "web_app:app"
```

### Using Waitress
```bash
pip install waitress
waitress-serve --port=8080 web_app:app
```

> **Tip:** In a real-world scenario, you should also run a reverse proxy like **Nginx** in front of the WSGI server to handle SSL and static file serving more efficiently.

## 📄 License

This software is released under the **[MIT License](LICENSE)**.
