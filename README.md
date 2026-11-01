# FortPS4-Archive

An archive of old Fortnite **PS4** builds, kept for preservation. Each build is listed below with
its version, changelist and where it came from, and is downloadable from this repo's
[Releases](https://github.com/Ducki67/FortPS4-Archive/releases).

## Builds

| Version | CL | Build string | Title ID | Engine | Season | Size | Download | Credit |
|---|---|---|---|---|---|---|---|---|
| 1.6.4 | 3668626 | `++Fortnite+Release-Cert-CL-3668626` | CUSA07022 | UE 4.16 | Chapter 1 Season 1 | 7.12 GiB (4 parts) | [Release](https://github.com/Ducki67/FortPS4-Archive/releases/tag/1.6.4) | 90sNath |

Want a build that isn't here? See [Submitting a build](#submitting-a-build).

## Downloading

GitHub limits release files to 2 GiB, so each build is split into parts. The helper script
downloads them in parallel, resumes if your connection drops, checks every SHA-256, joins the
parts and extracts the build. It only needs [Python 3.8+](https://www.python.org/downloads/).

```
python fortps4.py list
python fortps4.py get 1.6.4
```

Options for `get`:

| Option | What it does |
|---|---|
| `--out DIR` | extract somewhere else (default: a folder named after the build, in the current folder) |
| `--threads N` | how many parts to download at once (default 4) |
| `--keep-zip` | keep the joined `.zip` next to the extracted folder |

You need about twice the build's size in free space while it joins and extracts.

### By hand

Download every `.zip.001`, `.zip.002`, … from the release into one folder, then join them:

- **Windows:** `copy /b Fortnite-1.6.4-CL-3668626-PS4-CUSA07022.zip.0* Fortnite-1.6.4-CL-3668626-PS4-CUSA07022.zip`
- **Linux/macOS:** `cat Fortnite-1.6.4-CL-3668626-PS4-CUSA07022.zip.0* > Fortnite-1.6.4-CL-3668626-PS4-CUSA07022.zip`

7-Zip can also open the `.001` file directly. Checksums for every part and the full zip are in
[`builds.json`](builds.json).

## Submitting a build

Have a PS4 build that isn't archived yet, or a link to one? Open an issue with the
**Build submission** template, or message me on Discord (`Ducki67`). Please include:

- version and CL (from `engine/build/build.version` or the game's title screen)
- title ID (e.g. `CUSA07022`) and region
- size and where it came from
- how you'd like to be credited

**Before you share a dump, remove** `title.json`, `sce_sys/license.dat` and `sce_sys/keystone`. They hold
console license data tied to the dump and are never archived here.

## Credits

- **90sNath** – 1.6.4 PS4 build

## Notes

Fortnite and all its files belong to Epic Games. This repo is a non-commercial preservation
archive with no affiliation to Epic Games or Sony. If you're a rights holder and want something
removed, open an issue.
