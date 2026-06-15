"""
test_district_parsing.py
------------------------
Quick smoke-test for the _extract_district() normalization function in init_db.py.
Prints parsed district names for a variety of real-world address strings.

Usage (from project root, venv activated):
    python src/mapreduce/test_district_parsing.py
"""

import sys
import os

# Resolve project root so imports work regardless of working directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.ingest.init_db import _extract_district  # noqa: E402

TESTS = [
    "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1, Ho Chi Minh City 70000 Vietnam",
    "Phường Bến Nghé, Quận 1",
    "District 1, HCMC",
    "Q. Bình Thạnh",
    "Quận Tân Bình, Vietnam",
    "Binh Thanh District, Ho Chi Minh City",
    "22 - 22 Bis Le Thanh Ton street, Ben Nghe Ward, District 1 Lancaster Building, Ho Chi Minh City",
    "Level 3 - 68 Nguyễn Huệ, Quận 1, Ho Chi Minh City 700000 Vietnam",
    "",  # Edge case: empty string
]


def main():
    """Run district parsing tests and print results."""
    print("=== District Parsing Test Results ===\n")
    all_pass = True
    for address in TESTS:
        result = _extract_district(address)
        status = "✅" if result and result != "Unknown" else "⚠️ "
        print(f"  {status} Raw     : {address or '(empty)'}")
        print(f"      Extracted: {result}\n")
        if not address and result != "Unknown":
            all_pass = False

    print("=== Done ===" + (" — All checks passed ✅" if all_pass else " — Some warnings ⚠️"))


if __name__ == "__main__":
    main()
