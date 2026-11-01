"""FortPS4-Archive helper: list, download and extract the archived builds.

    python fortps4.py list
    python fortps4.py get 1.6.4 [--out DIR] [--threads 4] [--keep-zip]

Maintainers:
    python fortps4.py split <build.zip> <out dir> [--size-mb 1900]

Only needs Python 3.8+, no extra packages. Downloads resume if interrupted.
"""
import argparse
import hashlib
import json
import os
import sys
import threading
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor

REPO = "Ducki67/FortPS4-Archive"
INDEX_URL = f"https://raw.githubusercontent.com/{REPO}/main/builds.json"
ASSET_URL = f"https://github.com/{REPO}/releases/download/{{tag}}/{{name}}"
CHUNK = 1 << 20

progress_lock = threading.Lock()
progress = {}


def load_index():
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "builds.json")
    if os.path.exists(local):
        with open(local, encoding="utf-8") as f:
            return json.load(f)
    with urllib.request.urlopen(INDEX_URL) as r:
        return json.load(r)


def find_build(index, version):
    for build in index["builds"]:
        if version in (build["version"], build["tag"], str(build.get("cl"))):
            return build
    sys.exit(f"no build '{version}'. Run: python fortps4.py list")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def show_progress(total):
    with progress_lock:
        done = sum(progress.values())
    sys.stdout.write(f"\r  {done / 2**30:6.2f} / {total / 2**30:.2f} GiB ({done * 100 // max(total, 1)}%)")
    sys.stdout.flush()


def download_part(build, part, folder, total):
    path = os.path.join(folder, part["name"])
    have = os.path.getsize(path) if os.path.exists(path) else 0
    if have == part["size"] and sha256_file(path) == part["sha256"]:
        progress[part["name"]] = have
        return
    if have > part["size"]:
        os.remove(path)
        have = 0
    request = urllib.request.Request(ASSET_URL.format(tag=build["tag"], name=part["name"]))
    if have:
        request.add_header("Range", f"bytes={have}-")
    with urllib.request.urlopen(request) as r, open(path, "ab" if have and r.status == 206 else "wb") as f:
        if r.status != 206:
            have = 0
        progress[part["name"]] = have
        for block in iter(lambda: r.read(CHUNK), b""):
            f.write(block)
            with progress_lock:
                progress[part["name"]] += len(block)
            show_progress(total)
    if sha256_file(path) != part["sha256"]:
        os.remove(path)
        raise RuntimeError(f"{part['name']}: checksum mismatch, deleted it, run again")


def cmd_list(args):
    for b in load_index()["builds"]:
        print(f"{b['version']:8} CL {b['cl']:<9} {b['title_id']}  {b['size'] / 2**30:5.2f} GiB  {len(b['parts'])} parts  by {b['credit']}")


def cmd_get(args):
    build = find_build(load_index(), args.version)
    out = os.path.abspath(args.out or build["zip"][:-4])
    parts_dir = out + ".parts"
    os.makedirs(parts_dir, exist_ok=True)
    total = sum(p["size"] for p in build["parts"])

    print(f"downloading {build['zip']} ({len(build['parts'])} parts, {args.threads} at a time)")
    with ThreadPoolExecutor(args.threads) as pool:
        for future in [pool.submit(download_part, build, p, parts_dir, total) for p in build["parts"]]:
            future.result()
    print()

    zip_path = os.path.join(parts_dir, build["zip"])
    print("joining parts")
    h = hashlib.sha256()
    with open(zip_path, "wb") as dst:
        for part in build["parts"]:
            with open(os.path.join(parts_dir, part["name"]), "rb") as src:
                for block in iter(lambda: src.read(CHUNK), b""):
                    dst.write(block)
                    h.update(block)
    if h.hexdigest() != build["sha256"]:
        sys.exit("joined zip checksum mismatch, delete the .parts folder and run again")
    for part in build["parts"]:
        os.remove(os.path.join(parts_dir, part["name"]))

    print(f"extracting to {out}")
    with zipfile.ZipFile(zip_path) as z:
        names = z.infolist()
        for i, info in enumerate(names, 1):
            z.extract(info, out)
            if i % 200 == 0 or i == len(names):
                sys.stdout.write(f"\r  {i}/{len(names)} files")
                sys.stdout.flush()
    print()
    if args.keep_zip:
        os.replace(zip_path, out + ".zip")
    else:
        os.remove(zip_path)
    os.rmdir(parts_dir)
    print("done")


def cmd_split(args):
    size = args.size_mb * 2**20
    os.makedirs(args.out, exist_ok=True)
    name = os.path.basename(args.zip)
    whole = hashlib.sha256()
    parts = []
    with open(args.zip, "rb") as src:
        index = 1
        while True:
            part_name = f"{name}.{index:03d}"
            h = hashlib.sha256()
            written = 0
            with open(os.path.join(args.out, part_name), "wb") as dst:
                while written < size:
                    block = src.read(min(CHUNK, size - written))
                    if not block:
                        break
                    dst.write(block)
                    h.update(block)
                    whole.update(block)
                    written += len(block)
            if written == 0:
                os.remove(os.path.join(args.out, part_name))
                break
            parts.append({"name": part_name, "size": written, "sha256": h.hexdigest()})
            print(f"{part_name}  {written / 2**30:.2f} GiB")
            index += 1
    entry = {"zip": name, "size": os.path.getsize(args.zip), "sha256": whole.hexdigest(), "parts": parts}
    print(json.dumps(entry, indent=2))


def main():
    parser = argparse.ArgumentParser(description="FortPS4-Archive downloader")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="show archived builds").set_defaults(func=cmd_list)
    get = sub.add_parser("get", help="download, verify and extract a build")
    get.add_argument("version", help="version, tag or CL, e.g. 1.6.4")
    get.add_argument("--out", help="folder to extract into (default: a folder named after the build, in the current folder)")
    get.add_argument("--threads", type=int, default=4)
    get.add_argument("--keep-zip", action="store_true")
    get.set_defaults(func=cmd_get)
    split = sub.add_parser("split", help="maintainers: cut a zip into release-sized parts")
    split.add_argument("zip")
    split.add_argument("out")
    split.add_argument("--size-mb", type=int, default=1900)
    split.set_defaults(func=cmd_split)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
