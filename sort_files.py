import argparse
import asyncio
import logging
import os
from pathlib import Path

import aiofiles
import aiofiles.os


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def copy_file(file_path: Path, output_folder: Path) -> None:
    suffix = file_path.suffix.lower()
    subfolder_name = suffix.lstrip(".") if suffix else "no_extension"
    dest_dir = output_folder / subfolder_name

    try:
        await aiofiles.os.makedirs(dest_dir, exist_ok=True)
        dest_file = dest_dir / file_path.name

        async with aiofiles.open(file_path, "rb") as src:
            content = await src.read()

        async with aiofiles.open(dest_file, "wb") as dst:
            await dst.write(content)

    except Exception as e:
        logger.error("Failed to copy %s: %s", file_path, e)


async def read_folder(source_folder: Path, output_folder: Path) -> None:
    tasks = []

    try:
        entries = await asyncio.to_thread(lambda: list(os.scandir(source_folder)))
    except OSError as e:
        logger.error("Cannot read folder %s: %s", source_folder, e)
        return

    for entry in entries:
        entry_path = Path(entry.path)
        if entry.is_dir(follow_symlinks=False):
            tasks.append(read_folder(entry_path, output_folder))
        elif entry.is_file(follow_symlinks=False):
            tasks.append(copy_file(entry_path, output_folder))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sorts files from source to output folder by extension, asynchronously.",
    )
    parser.add_argument("source", type=str, help="Path to the source folder")
    parser.add_argument("output", type=str, help="Path to the output folder")
    args = parser.parse_args()

    source_folder = Path(args.source)
    output_folder = Path(args.output)

    if not source_folder.exists():
        parser.error(f"Source folder does not exist: {source_folder}")
    if not source_folder.is_dir():
        parser.error(f"Source path is not a directory: {source_folder}")

    output_folder.mkdir(parents=True, exist_ok=True)

    asyncio.run(read_folder(source_folder, output_folder))
    print(f"Done. Files sorted into: {output_folder}")


if __name__ == "__main__":
    main()
