import sys
from pathlib import Path

import cloudinary
import cloudinary.uploader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.core.config.settings import config

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

cloudinary.config(
    cloud_name=config.CLOUDINARY_CLOUD_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
)


def upload_folder(local_path: Path, cloud_folder: str):
    for file in local_path.iterdir():
        if file.is_dir():
            upload_folder(file, f"{cloud_folder}/{file.name}")
        elif file.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"):
            public_id = f"{cloud_folder}/{file.stem}"
            print(f"Uploading {file.name} -> {public_id} ...", end=" ")
            result = cloudinary.uploader.upload(str(file), public_id=public_id, overwrite=True)
            print(f"OK ({result['secure_url']})")


def main():
    if not config.CLOUDINARY_CLOUD_NAME:
        print("Error: CLOUDINARY_CLOUD_NAME is not set in .env.local")
        sys.exit(1)
    print(f"Uploading {ASSETS_DIR} to Cloudinary folder '{config.CLOUDINARY_FOLDER}' ...")
    upload_folder(ASSETS_DIR, config.CLOUDINARY_FOLDER)
    print("Done!")


if __name__ == "__main__":
    main()
