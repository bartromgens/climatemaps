import zipfile
from pathlib import Path
from urllib.request import urlretrieve

from climatemaps.geotiff import verify_geotiff_file
from climatemaps.logger import logger


def download_file(url: str, destination: Path, verify: bool = True) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading from {url}")
    logger.info(f"Saving to {destination}")

    try:
        urlretrieve(url, destination)
        logger.info(f"Successfully downloaded {destination}")

        if verify and destination.suffix.lower() in [".tif", ".tiff"]:
            if not verify_geotiff_file(destination):
                logger.warning(
                    f"Downloaded file {destination} failed verification, deleting and will retry"
                )
                destination.unlink()
                raise ValueError(f"Downloaded file {destination} failed verification")
    except Exception as e:
        if isinstance(e, ValueError) and "failed verification" in str(e):
            raise
        logger.error(f"Failed to download {url}: {e}")
        raise


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    logger.info(f"Extracting {zip_path} to {extract_to}")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

    logger.info(f"Successfully extracted to {extract_to}")

    zip_path.unlink()
    logger.info(f"Removed temporary file {zip_path}")

