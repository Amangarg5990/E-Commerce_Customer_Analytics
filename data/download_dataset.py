import os
import sys
import zipfile
import ssl
import urllib.request
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DatasetDownloader")

DATA_DIR = Path(__file__).resolve().parent / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Primary URL: UCI Online Retail Dataset
UCI_ONLINE_RETAIL_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"


def download_file(url: str, dest_path: Path):
    logger.info(f"Downloading from {url} to {dest_path}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    
    # Bypass self-signed SSL verification issues
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, timeout=120, context=ctx) as response, open(dest_path, "wb") as out_file:
        total_size = response.getheader("Content-Length")
        if total_size:
            total_size = int(total_size)
            logger.info(f"Total file size: {total_size / (1024*1024):.2f} MB")
        chunk_size = 1024 * 1024  # 1 MB
        downloaded = 0
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total_size:
                percent = (downloaded / total_size) * 100
                sys.stdout.write(f"\rProgress: {downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB ({percent:.1f}%)")
                sys.stdout.flush()
    print()
    logger.info("Download completed successfully.")


def get_dataset() -> Path:
    """Downloads and extracts the Online Retail dataset."""
    zip_target = DATA_DIR / "online_retail.zip"
    excel_target = DATA_DIR / "Online Retail.xlsx"

    if excel_target.exists():
        logger.info(f"Found existing Excel dataset at {excel_target}")
        return excel_target

    download_file(UCI_ONLINE_RETAIL_URL, zip_target)
    logger.info(f"Extracting {zip_target}...")
    with zipfile.ZipFile(zip_target, "r") as zip_ref:
        zip_ref.extractall(DATA_DIR)
    logger.info("Extraction complete.")

    if excel_target.exists():
        logger.info(f"Extracted dataset verified at {excel_target}")
        return excel_target
    raise FileNotFoundError("Could not find Online Retail.xlsx after extraction.")


if __name__ == "__main__":
    path = get_dataset()
    print("Dataset ready at:", path)
