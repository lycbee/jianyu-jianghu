"""Build and deploy the static site.

Uses build_site.py for HTML generation (zero dependencies).
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SITE_PUBLIC_DIR = PROJECT_ROOT / "site" / "public"


def build(trigger_deploy: bool = False) -> None:
    """Build the static site from chapters and optionally trigger deploy."""
    from build_site import build as build_site
    build_site()

    if trigger_deploy:
        _trigger_vercel_deploy()


def _trigger_vercel_deploy() -> None:
    import urllib.request
    hook_url = os.getenv("VERCEL_DEPLOY_HOOK", "")
    if not hook_url:
        print("  VERCEL_DEPLOY_HOOK not set, skipping")
        return
    try:
        req = urllib.request.Request(hook_url, method="POST")
        urllib.request.urlopen(req)
        print("  Vercel deploy triggered")
    except Exception as e:
        print(f"  Deploy error: {e}")
