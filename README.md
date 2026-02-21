# DWFX to PDF Converter

A blazingly fast, multi-threaded command-line tool to convert `.dwfx` files to `.pdf` format using `libgxps`. 

Includes a robust **Watch Mode** to auto-convert files as they are dropped into a directory.

## Features
- 🚀 **Multi-threaded**: Processes hundreds of files concurrently (configurable via `--workers`).
- 📊 **Progress Bar**: Beautiful progress tracking during batch conversions using `tqdm`.
- 👀 **Watch Mode**: Real-time folder monitoring with debounce protection (ignores incomplete network transfers).
- 🐍 **Installable**: Easily installable as a global `dwfx2pdf` command.

---

## Installation

### 1. Install System Dependencies (macOS)
The tool requires `xpstopdf` under the hood, provided by `libgxps`.
```bash
brew install libgxps
```
*(Note: If Homebrew keeps it keg-only, the tool will auto-detect its path `/opt/homebrew/opt/libgxps/bin/xpstopdf`.)*

### 2. Install the CLI Tool
You can install this repository directly or locally using `pip`:
```bash
# Clone the repository
git clone https://github.com/danyanovich/dwfx-to-pdf.git
cd dwfx-to-pdf

# Install globally (or in your venv)
pip install .
```

---

## Usage
Once installed, you can use the `dwfx2pdf` command anywhere.

### Batch Conversion (`convert`)
Convert all currently existing `.dwfx` files in a folder:
```bash
dwfx2pdf convert --dwfx-dir ./dwfx --pdf-dir ./pdf --workers 8
```
- `--dwfx-dir`: Folder to read `.dwfx` files from (default: `dwfx`).
- `--pdf-dir`: Folder to output PDFs to (default: `pdf`).
- `--workers`: Number of parallel conversion threads (default: `4`).
- `--overwrite`: Pass this flag to force overwrite existing PDFs.

### Watch Mode (`watch`)
Monitor a folder and automatically convert any new `.dwfx` files dropped there:
```bash
dwfx2pdf watch --dwfx-dir ./drop_here --pdf-dir ./output
```
The watch mode includes a debounce mechanism that safely waits for large files to finish copying before attempting conversion.

### Web Interface (`web`)
Launch a beautiful drag-and-drop web UI in your browser:
```bash
dwfx2pdf web --port 8080
```
Then open `http://localhost:8080` in your browser. You can drag `.dwfx` files onto the page and download the converted PDFs instantly.

- `--port`: Port to run the server on (default: `8080`).
- `--host`: Host to bind (default: `0.0.0.0`).

**Quick start with the run script:**
```bash
./run.sh --web
```

---

## Development
If you prefer running the script directly without installing:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python dwfx_to_pdf.py convert --help
```

## License
MIT
