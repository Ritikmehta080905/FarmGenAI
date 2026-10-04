"""
scripts/create_chatgpt_bundle.py

Packages crucial FarmGenAI source files into a lightweight ZIP (<512 MB)
for uploading to ChatGPT / LLM testing environments.

Excludes:
- .git/
- .venv/ and virtualenvs
- node_modules/
- dist/ and build/
- __pycache__/ and *.pyc
- .pytest_cache/
- .env (preserves .env.example)
- local SQLite databases
"""

import os
import zipfile


def create_bundle(output_zip: str = "farmgenai_crucial_source.zip") -> str:
    exclude_dirs = {
        ".git", ".github", ".venv", "venv", "node_modules", "dist", "build",
        "__pycache__", ".pytest_cache", ".next", ".cache", "scratch"
    }
    exclude_files = {
        ".env", "agrinegotiator.db", output_zip
    }
    exclude_exts = {".pyc", ".pyo", ".pyd"}

    file_count = 0
    total_raw_bytes = 0

    print(f"Creating {output_zip}...")

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk("."):
            # Filter directories in-place to prevent walking excluded trees
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.endswith(".egg-info")]

            for file in files:
                if file in exclude_files or any(file.endswith(ext) for ext in exclude_exts):
                    continue

                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, ".")

                if arcname == output_zip:
                    continue

                zipf.write(full_path, arcname)
                file_count += 1
                total_raw_bytes += os.path.getsize(full_path)

    zip_size_bytes = os.path.getsize(output_zip)
    zip_size_mb = zip_size_bytes / (1024 * 1024)
    raw_size_mb = total_raw_bytes / (1024 * 1024)

    print(f"Archived {file_count} files.")
    print(f"Uncompressed: {raw_size_mb:.2f} MB")
    print(f"Compressed ZIP Size: {zip_size_mb:.2f} MB")
    print(f"ChatGPT Upload Check: {zip_size_mb:.2f} MB / 512.00 MB ({(zip_size_mb / 512.0) * 100:.2f}%)")

    return output_zip


if __name__ == "__main__":
    create_bundle()
