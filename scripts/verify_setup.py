"""Self-check setup for course 69-1.

Run: python scripts/verify_setup.py
Exit 0 if all OK, 1 if any FAIL.
"""

import os
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def check_python_version():
    """Check Python is 3.11 or higher."""
    if sys.version_info >= (3, 11):
        return True, f"Python {sys.version_info.major}.{sys.version_info.minor}"
    return False, f"Python {sys.version_info.major}.{sys.version_info.minor} (need 3.11+)"


def check_env_var(name: str, hint: str) -> tuple[bool, str]:
    """Check env var is set and non-empty."""
    value = os.environ.get(name, "")
    if value and not value.startswith("AIzaSy...your"):
        return True, f"{name} is set"
    return False, f"{name} missing or placeholder : {hint}"


def check_gemini_reachable() -> tuple[bool, str]:
    """Try to import google-genai and ping Gemini API."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key or api_key.startswith("AIzaSy...your"):
        return False, "Skipped (GOOGLE_API_KEY not set)"
    try:
        from google import genai
    except ImportError:
        return False, "google-genai not installed : run pip install -r requirements.txt"
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="ping",
        )
        if response.text:
            return True, "Gemini API reachable"
        return False, "Gemini API returned empty response"
    except Exception as exc:
        return False, f"Gemini API call failed: {type(exc).__name__}: {exc}"


def main() -> int:
    """Run all checks, print summary, return exit code."""
    checks = [
        ("Python version", check_python_version()),
        ("GOOGLE_API_KEY", check_env_var("GOOGLE_API_KEY", "ดู Quickstart ขั้นที่ 4")),
        ("Gemini API connectivity", check_gemini_reachable()),
    ]

    all_pass = True
    for label, (ok, msg) in checks:
        marker = "[OK]  " if ok else "[FAIL]"
        print(f"{marker} {label}: {msg}")
        if not ok:
            all_pass = False

    print()
    if all_pass:
        print("All checks passed. Ready for Session 1.")
        return 0
    print("Some checks failed. แก้แล้วรันใหม่ ถ้าติดถามใน cohort/อาจารย์")
    return 1


if __name__ == "__main__":
    sys.exit(main())
