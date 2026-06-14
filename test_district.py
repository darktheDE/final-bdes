import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.ingest.init_db import _extract_district

tests = [
    "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1, Ho Chi Minh City 70000 Vietnam",
    "Phường Bến Nghé, Quận 1",
    "District 1, HCMC",
    "Q. Bình Thạnh",
    "Quận Tân Bình, Vietnam",
    "Binh Thanh District, Ho Chi Minh City",
    "22 - 22 Bis Le Thanh Ton street, Ben Nghe Ward, District 1 Lancaster Building, Ho Chi Minh City 700000 Vietnam",
    "Level 3 - 68 Nguyễn Huệ, Quận 1, Ho Chi Minh City 700000 Vietnam"
]

print("=== District Parsing Test Results ===\n")
for t in tests:
    result = _extract_district(t)
    print(f"Raw     : {t}\nExtracted: {result}\n")
