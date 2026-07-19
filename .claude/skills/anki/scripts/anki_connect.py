#!/usr/bin/env python3
"""Call Windows AnkiConnect from WSL without exposing it beyond loopback."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


URL = "http://127.0.0.1:8765"


def request_direct(body: bytes) -> str:
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3) as response:
        return response.read().decode("utf-8")


def request_powershell(body: bytes) -> str:
    powershell = shutil.which("powershell.exe")
    if not powershell:
        raise RuntimeError("powershell.exe not found and direct AnkiConnect access failed")
    script = (
        "[Console]::InputEncoding=[Text.UTF8Encoding]::new($false);"
        "$body=[Console]::In.ReadToEnd();"
        "$response=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8765' "
        "-Method Post -ContentType 'application/json; charset=utf-8' -Body $body;"
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
        "[Console]::Out.Write($response.Content)"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-Command", script],
        input=body,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(message or f"PowerShell exited with {result.returncode}")
    return result.stdout.decode("utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="AnkiConnect action, e.g. version or deckNames")
    parser.add_argument("params", nargs="?", default="{}", help="JSON object for params")
    args = parser.parse_args()
    try:
        params = json.loads(args.params)
        if not isinstance(params, dict):
            raise ValueError("params must be a JSON object")
        body = json.dumps(
            {"action": args.action, "version": 6, "params": params},
            ensure_ascii=False,
        ).encode("utf-8")
        try:
            raw = request_direct(body)
        except (OSError, urllib.error.URLError):
            raw = request_powershell(body)
        response = json.loads(raw)
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return 1 if response.get("error") else 0
    except (ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"anki_connect.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
