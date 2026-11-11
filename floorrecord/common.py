"""Shared helpers: config, paths, polite HTTP fetching."""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("FLOORRECORD_DATA", ROOT / "data"))
SITE = Path(os.environ.get("FLOORRECORD_SITE", ROOT / "site"))
USER_AGENT = "FloorRecord/1.0 (public-interest vote tracker; +https://github.com/)"


def config():
    return json.loads((ROOT / "config.json").read_text())


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text())


def write_json(path, obj, compact=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    else:
        text = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True)
    path.write_text(text + "\n")


class NotFound(Exception):
    pass


def fetch(url, headers=None, data=None, tries=4, timeout=40):
    """GET (or POST when data is given) with retries. Raises NotFound on 404."""
    hdrs = {"User-Agent": USER_AGENT}
    hdrs.update(headers or {})
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=hdrs, data=data)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as err:
            if err.code == 404:
                raise NotFound(url) from None
            last = err
            if err.code in (400, 401, 403):
                break
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            last = err
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Could not fetch {url}: {last}")
