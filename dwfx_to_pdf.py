#!/usr/bin/env python3

import argparse
import logging
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Configure logging
logger = logging.getLogger(__name__)


def _which_or_none(cmd: str) -> str | None:
    found = shutil.which(cmd)
    if found:
        return found

    # Homebrew's libgxps is often keg-only (not on PATH) due to conflicts.
    candidates = [
        "/opt/homebrew/opt/libgxps/bin/" + cmd,
        "/usr/local/opt/libgxps/bin/" + cmd,
    ]
    for c in candidates:
        if Path(c).exists():
            return c

    return None


def _run_xpstopdf(in_path: Path, out_path: Path) -> None:
    # libgxps installs `xpstopdf`
    xpstopdf = _which_or_none("xpstopdf")
    if not xpstopdf:
        raise RuntimeError(
            "Missing `xpstopdf`. Install it with: brew install libgxps"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # `xpstopdf INPUT OUTPUT`
    # Some tools are picky about extension; DWFX is a zip-based container very similar to XPS.
    # We try direct first, then retry with a temp `.xps` name.
    try:
        subprocess.run(
            [xpstopdf, str(in_path), str(out_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return
    except subprocess.CalledProcessError as e1:
        tmp_xps = in_path.with_suffix(in_path.suffix + ".xps")
        try:
            shutil.copy2(in_path, tmp_xps)
            subprocess.run(
                [xpstopdf, str(tmp_xps), str(out_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return
        except subprocess.CalledProcessError as e2:
            raise RuntimeError(
                "xpstopdf failed.\n"
                f"Tried: {in_path.name} -> {out_path.name}\n\n"
                f"First error:\n{e1.stderr.strip()}\n\n"
                f"Second error (with .xps rename):\n{e2.stderr.strip()}"
            )
        finally:
            try:
                if tmp_xps.exists():
                    tmp_xps.unlink()
            except Exception:
                pass


def convert_all(dwfx_dir: Path, pdf_dir: Path, *, overwrite: bool, max_workers: int = 4) -> int:
    dwfx_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # Gather DWFX files
    dwfx_files = sorted([p for p in dwfx_dir.iterdir() if p.is_file() and p.suffix.lower() == ".dwfx"])
    if not dwfx_files:
        logger.info(f"No .dwfx files found in '{dwfx_dir}'")
        return 0

    # Build queue of tasks
    tasks = []
    for in_path in dwfx_files:
        # pathlib with_suffix trick
        out_path = pdf_dir / in_path.with_suffix(".pdf").name
        if out_path.exists() and not overwrite:
            logger.info(f"Skip (exists): {out_path.name}")
            continue
        tasks.append((in_path, out_path))

    if not tasks:
        logger.info("No new files to convert.")
        return 0

    logger.info(f"Starting conversion of {len(tasks)} files using {max_workers} worker(s)...")
    failures = 0

    def process_file(in_path: Path, out_path: Path):
        t0 = time.time()
        try:
            _run_xpstopdf(in_path, out_path)
            dt = time.time() - t0
            return (True, in_path, out_path, dt, None)
        except Exception as e:
            return (False, in_path, out_path, 0, e)

    # Setup progress bar if tqdm is installed
    pbar = None
    if tqdm:
        pbar = tqdm(total=len(tasks), desc="Converting", unit="file", dynamic_ncols=True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, inp, outp): (inp, outp) for inp, outp in tasks}
        
        for future in as_completed(futures):
            success, in_path, out_path, dt, error = future.result()
            
            if success:
                # If using progress bar, suppress OK messages to avoid console spam
                if not tqdm:
                    logger.info(f"OK: {in_path.name} -> {out_path.name} ({dt:.2f}s)")
            else:
                failures += 1
                # Use tqdm.write if progress bar is active so it doesn't break UI
                if tqdm:
                    tqdm.write(f"FAIL: {in_path.name}: {error}")
                else:
                    logger.error(f"FAIL: {in_path.name}: {error}")
            
            if pbar:
                pbar.update(1)
    
    if pbar:
        pbar.close()

    logger.info(f"Done. Processed {len(tasks)} file(s) with {failures} failure(s).")
    return failures


def watch(dwfx_dir: Path, pdf_dir: Path, *, overwrite: bool) -> None:
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        logger.error("Watch mode requires 'watchdog'. Install it with: pip install -r requirements.txt")
        sys.exit(1)

    class Handler(FileSystemEventHandler):
        def on_created(self, event):
            if event.is_directory:
                return
            p = Path(event.src_path)
            if p.suffix.lower() != ".dwfx":
                return

            # Debounce and size-check: wait for file copy to finish AND file size > 0
            for _ in range(40):  # max wait 10 seconds (40 * 0.25)
                try:
                    size1 = p.stat().st_size
                    time.sleep(0.25)
                    size2 = p.stat().st_size
                    if size1 == size2 and size1 > 0:
                        break
                except FileNotFoundError:
                    return
            
            # Double check if size is still 0 (e.g. touch or empty file)
            try:
                if p.stat().st_size == 0:
                    logger.warning(f"File {p.name} remains empty (0 bytes). Skipping.")
                    return
            except FileNotFoundError:
                return

            out_path = pdf_dir / p.with_suffix(".pdf").name
            if out_path.exists() and not overwrite:
                logger.info(f"Skip (exists): {out_path.name}")
                return

            try:
                logger.info(f"Converting new file: {p.name}...")
                t0 = time.time()
                _run_xpstopdf(p, out_path)
                dt = time.time() - t0
                logger.info(f"OK: {p.name} -> {out_path.name} ({dt:.2f}s)")
            except Exception as e:
                logger.error(f"FAIL: {p.name}: {e}")

    dwfx_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    observer = Observer()
    observer.schedule(Handler(), str(dwfx_dir), recursive=False)
    observer.start()

    logger.info(f"Watching directory '{dwfx_dir}' (drop .dwfx files here)")
    logger.info(f"Output PDFs will appear in '{pdf_dir}'")
    logger.info("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nStopping watch mode...")
    finally:
        observer.stop()
        observer.join()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    parser = argparse.ArgumentParser(description="Convert DWFX files to PDFs using libgxps")
    
    # Parent parser to share common arguments between "convert" and "watch"
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--dwfx-dir", default="dwfx", type=Path, help="Input folder containing .dwfx files")
    parent_parser.add_argument("--pdf-dir", default="pdf", type=Path, help="Output folder for PDFs")
    parent_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing PDFs")

    sub = parser.add_subparsers(dest="cmd", required=True)
    
    # Convert command
    convert_parser = sub.add_parser("convert", parents=[parent_parser], help="Convert all .dwfx files currently in the input folder")
    convert_parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers for conversion (default: 4)")

    # Watch command
    sub.add_parser("watch", parents=[parent_parser], help="Watch the input folder and auto-convert new .dwfx files")

    # Web command
    web_parser = sub.add_parser("web", help="Start a web interface for drag-and-drop conversion")
    web_parser.add_argument("--port", type=int, default=8080, help="Port to run the web server on (default: 8080)")
    web_parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")

    args = parser.parse_args()

    if args.cmd == "web":
        from web_app import run_web
        run_web(host=args.host, port=args.port)
        return 0

    dwfx_dir = args.dwfx_dir
    pdf_dir = args.pdf_dir

    if args.cmd == "convert":
        failures = convert_all(dwfx_dir, pdf_dir, overwrite=args.overwrite, max_workers=args.workers)
        return 1 if failures else 0

    if args.cmd == "watch":
        watch(dwfx_dir, pdf_dir, overwrite=args.overwrite)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
