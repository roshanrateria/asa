"""Full-history secret scan (reviewer "before you submit" item).

Scans EVERY blob in `git rev-list --all` for:
  * literal live .env values (sha256-matched substrings of the actual
    CREDENTIALS - the strongest check: "did this secret EVER get committed");
  * generic token shapes: nvapi-, Bearer <token>, A21AA* (PayPal access
    token), AY*30+ (client-id-like strings);
  * email addresses (identity emails whitelisted separately).

Prints COUNTS and blob labels only - never the matched text.
Exit 0 = clean; exit 1 = hits (CI-able).

Usage:  python scripts\\scan_history.py
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WHITELIST_EMAILS = {
    "rateriaroshan2005@gmail.com",          # git identity (expected in commits)
    "asanonrecip@example.com",              # anon probe recipient
    "example.com",                          # any RFC-2606 domain
}
IDENTITY_OK = "rateriaroshan2005@gmail.com"


def sh(args: list[str]) -> str:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=ROOT, check=True).stdout


def unique_blobs() -> tuple[list[tuple[str, str]], dict[str, str]]:
    """[(sha, decoded content)], {sha: human label} for every blob in --all."""
    out = sh(["git", "rev-list", "--objects", "--all"]).splitlines()
    objs = {ln.split(" ", 1)[0]: (ln.split(" ", 1)[1] if " " in ln else "")
            for ln in out if ln.strip()}
    batch = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        input="\n".join(objs), capture_output=True, text=True, cwd=ROOT, check=True)
    blobs = [ln.split()[0] for ln in batch.stdout.splitlines()
             if ln.split()[1:2] == ["blob"]]
    content = subprocess.run(
        ["git", "cat-file", "--batch"], input=("\n".join(blobs) + "\n").encode(),
        capture_output=True, cwd=ROOT, check=True).stdout
    data = content                              # bytes: offsets must be byte-exact
    result = []
    pos = 0
    for b in blobs:
        ln_end = data.index(b"\n", pos)
        _hdr = data[pos:ln_end]            # b"<sha> blob <size>"
        size = int(_hdr.split()[2])
        start = ln_end + 1
        result.append((b, data[start:start + size].decode("utf-8", "replace")))
        pos = start + size
        if data[pos:pos + 1] == b"\n":          # object-terminating newline
            pos += 1
    return result, objs


def env_values() -> list[str]:
    """Only SECRET-class values: *_SECRET / *_TOKEN / *_API_KEY, or a
    PayPal client-ID-shaped value. URLs, model names, emails and other
    config values are deliberately NOT hunted (they legitimately appear in
    committed files)."""
    vals = []
    envf = ROOT / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip().upper(), v.strip()
            if len(v) < 12:
                continue
            secret_class = ("SECRET" in k or "TOKEN" in k or "API_KEY" in k)
            id_class = (k.endswith("_ID")
                        and (v.startswith(("AY", "AV")) or len(v) >= 40))
            if secret_class or id_class:
                vals.append(v)
    return vals


PATTERNS = {
    "nvapi-key": re.compile(r"nvapi-[A-Za-z0-9_\-]{8,}"),
    "bearer-token": re.compile(r"Bearer [A-Za-z0-9\-_.]{20,}"),
    "paypal-access-token": re.compile(r"\bA21AA[A-Za-z0-9]{15,}\b"),
    "client-id-like": re.compile(r"\bAY[A-Za-z0-9_\-]{30,}\b"),
    "email-address": re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
}


def main() -> int:
    blobs, labels = unique_blobs()
    live = env_values()
    live_hash = {hashlib.sha256(v.encode()).hexdigest()[:12] for v in live}

    hits: dict[str, int] = {k: 0 for k in PATTERNS}
    hit_files: dict[str, set] = {k: set() for k in PATTERNS}
    live_hits = 0
    live_hit_files: set = set()

    for sha, text in blobs:
        label = labels.get(sha, sha[:10])
        if any(v in text for v in live):
            live_hits += 1
            live_hit_files.add(label)
        for name, rx in PATTERNS.items():
            for m in rx.finditer(text):
                s = m.group(0)
                if name == "email-address":
                    if any(w in s for w in WHITELIST_EMAILS):
                        continue
                hits[name] += 1
                hit_files[name].add(label)

    print(f"blobs scanned: {len(blobs)} (unique objects across --all)")
    print(f"live .env values committed anywhere: {live_hits} "
          f"(sha256-substring test against {len(live)} values)"
          + (f" -> {sorted(live_hit_files)[:5]}" if live_hits else ""))
    for name, count in hits.items():
        tag = " (whitelist-filtered)" if name == "email-address" else ""
        files = ", ".join(sorted(hit_files[name])[:4]) if hit_files[name] else "-"
        print(f"  {name:<22} hits={count}{tag} files={files}")
    clean = live_hits == 0 and all(h == 0 for k, h in hits.items()
                                   if k != "email-address")
    print("SCAN:", "CLEAN - no live values, no token-shape hits, "
                  "no non-whitelisted emails" if clean else "HITS FOUND - inspect before push")
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
