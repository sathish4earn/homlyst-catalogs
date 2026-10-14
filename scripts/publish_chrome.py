#!/usr/bin/env python3
"""Publish UI-string (chrome) changes so every app gets the right files.

Why: the app reads chrome_manifest.json from jsDelivr's @main, which can serve
old copies for hours. Apps from 1.15.x on fetch the language files from the
exact commit named in the manifest ("ref") and ignore a file older than the
manifest expects ("files"), so a publish has two commits:

  1. the language files (each changed file's own "version" +1)
  2. the manifest: changed languages +1, "files" = every file's version,
     "ref" = commit 1

Usage (on a branch, after editing chrome/<lang>.json "strings"):

    python3 scripts/publish_chrome.py "Recipe screen strings"
    git push -u origin HEAD   # then open a PR and merge it as a MERGE commit
                              # (not squash: commit 1 must stay in main's history)
    python3 scripts/publish_chrome.py --purge   # once, after the merge

    python3 scripts/publish_chrome.py --all "message"   # re-publish every language

Only purge once: repeated purges get throttled and then nothing refreshes.
"""
import json
import subprocess
import sys
import urllib.request
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "chrome_manifest.json"
CDN = "https://purge.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def load(path: Path) -> OrderedDict:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)


def save(path: Path, data: OrderedDict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def purge() -> None:
    for path in ["chrome_manifest.json"]:
        with urllib.request.urlopen(CDN + path, timeout=20) as r:
            body = json.load(r)
        throttled = any(v.get("throttled") for v in body.get("paths", {}).values())
        print(f"purge {path}: {'THROTTLED, try again in a few minutes' if throttled else 'ok'}")


def publish(message: str, all_langs: bool = False) -> None:
    if git("rev-parse", "--abbrev-ref", "HEAD") == "main":
        sys.exit("Make a branch first (git checkout -b chrome/<topic>).")
    changed = sorted(
        Path(p).stem for p in git("diff", "--name-only", "origin/main", "--", "chrome/").splitlines()
        if p.endswith(".json")
    ) + sorted(
        Path(p).stem for p in git("diff", "--name-only", "--", "chrome/").splitlines() if p.endswith(".json")
    )
    changed = sorted(set(changed))
    if all_langs:
        changed = sorted(load(MANIFEST)["chrome"].keys())
    if not changed:
        sys.exit("No chrome/<lang>.json changes to publish.")

    # 1. Language files, each changed file's own version +1.
    for lang in changed:
        path = ROOT / "chrome" / f"{lang}.json"
        data = load(path)
        data["version"] = int(data.get("version", 1)) + 1
        save(path, data)
    git("add", "chrome")
    git("commit", "-q", "-m", f"Chrome strings: {message}")
    ref = git("rev-parse", "HEAD")

    # 2. Manifest pointing at that commit.
    manifest = load(MANIFEST)
    for lang in changed:
        manifest["chrome"][lang] = int(manifest["chrome"].get(lang, 0)) + 1
    manifest["files"] = OrderedDict(
        (lang, int(load(ROOT / "chrome" / f"{lang}.json").get("version", 1))) for lang in manifest["chrome"]
    )
    manifest["ref"] = ref
    save(MANIFEST, manifest)
    git("add", str(MANIFEST.relative_to(ROOT)))
    git("commit", "-q", "-m", f"Chrome manifest: {', '.join(changed)} -> {ref[:12]}")
    print(f"Published {len(changed)} language(s) at {ref[:12]}: {' '.join(changed)}")
    print("Next: push, open a PR, merge it as a merge commit, then run with --purge once.")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--purge":
        purge()
    elif len(sys.argv) == 3 and sys.argv[1] == "--all":
        publish(sys.argv[2], all_langs=True)
    elif len(sys.argv) == 2:
        publish(sys.argv[1])
    else:
        sys.exit(__doc__)
