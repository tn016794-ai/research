"""
CAO DU LIEU CAU HINH IPHONE TU FILE HTML DA LUU SAN (THEAPPLEWIKI.COM)
========================================================================
Phuc vu nghien cuu rui ro loi thoi (obsolescence risk) cua tung dong iPhone.

TAI SAO DOI CHIEN LUOC (so voi ban goc goi API):
  API MediaWiki tra ve WIKITEXT THO (chua render). Cac may doi moi tren
  TheAppleWiki dung template/Lua de sinh nhan field, nen chuoi "CPU:",
  "RAM:", "Latest public firmware:" KHONG ton tai duoi dang van ban trong
  ma nguon tho -> regex tren wikitext bi "mu" voi hau het may moi, khien
  so lieu iOS moi nhat tinh sai.
  File HTML da render (ban tai ve bang trinh duyet, khong bi Cloudflare
  chan) thi KHONG co van de nay - moi nhan field la van ban that.
  => Script nay doc THANG file HTML, khong goi mang, on dinh 100%.

NGUON DU LIEU:
  1) List of iPhones - The Apple Wiki.html
     -> Device_Model, Chip_Name, RAM, Storage, Initial_iOS, Max_Supported_iOS
  2) Models_iPhone_-_The_Apple_Wiki.html
     -> Chi dung de DOI CHIEU (QA): kiem tra ten doi may co khop giua 2 file
        khong. File nay KHONG co Chip/RAM/ngay phat hanh nen khong dung de
        lay du lieu chinh.
  3) Release_Date: KHONG co trong ca 2 file HTML tren. Duoc dien tu bang
     tra cuu thu cong RELEASE_DATE_MAP ben duoi, tong hop tu Apple Newsroom
     / thong bao chinh thuc. NEN TRICH NGUON NAY TRONG BAO CAO.

CACH DUNG:
  1. Dat 2 file HTML cung thu muc voi script nay (hoac sua duong dan trong
     LIST_HTML_FILE / MODELS_HTML_FILE ben duoi).
  2. Chay: python cao_du_lieu_iphone.py
  3. Ket qua: thong_tin_cau_hinh_iphone.xlsx
"""

import os
import re
import pandas as pd
from bs4 import BeautifulSoup

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_HTML_FILE = os.path.join(CURRENT_DIR, "List of iPhones - The Apple Wiki.html")
MODELS_HTML_FILE = os.path.join(CURRENT_DIR, "Models of iPhones - The Apple Wiki.html")
OUTPUT_FILE = os.path.join(CURRENT_DIR, "thong_tin_cau_hinh_iphone.xlsx")

# ============================================================
# BANG NGAY PHAT HANH (khong co trong wiki -> tra cuu thu cong)
# Nguon: Apple Newsroom / thong bao chinh thuc. Kiem tra lai truoc khi
# dua vao bao cao chinh thuc neu can do chinh xac tuyet doi.
# ============================================================
RELEASE_DATE_MAP = {
    "iPhone": "2007-06-29",
    "iPhone 3G": "2008-07-11",
    "iPhone 3GS": "2009-06-19",
    "iPhone 4": "2010-06-24",
    "iPhone 4S": "2011-10-14",
    "iPhone 5": "2012-09-21",
    "iPhone 5c": "2013-09-20",
    "iPhone 5s": "2013-09-20",
    "iPhone 6": "2014-09-19",
    "iPhone 6 Plus": "2014-09-19",
    "iPhone 6s": "2015-09-25",
    "iPhone 6s Plus": "2015-09-25",
    "iPhone SE (1st generation)": "2016-03-31",
    "iPhone 7": "2016-09-16",
    "iPhone 7 Plus": "2016-09-16",
    "iPhone 8": "2017-09-22",
    "iPhone 8 Plus": "2017-09-22",
    "iPhone X": "2017-11-03",
    "iPhone XS": "2018-09-21",
    "iPhone XS Max": "2018-09-21",
    "iPhone XR": "2018-10-26",
    "iPhone 11": "2019-09-20",
    "iPhone 11 Pro": "2019-09-20",
    "iPhone 11 Pro Max": "2019-09-20",
    "iPhone SE (2nd generation)": "2020-04-24",
    "iPhone 12": "2020-10-23",
    "iPhone 12 Pro": "2020-10-23",
    "iPhone 12 mini": "2020-11-13",
    "iPhone 12 Pro Max": "2020-11-13",
    "iPhone 13": "2021-09-24",
    "iPhone 13 mini": "2021-09-24",
    "iPhone 13 Pro": "2021-09-24",
    "iPhone 13 Pro Max": "2021-09-24",
    "iPhone SE (3rd generation)": "2022-03-18",
    "iPhone 14": "2022-09-16",
    "iPhone 14 Pro": "2022-09-16",
    "iPhone 14 Pro Max": "2022-09-16",
    "iPhone 14 Plus": "2022-10-07",
    "iPhone 15": "2023-09-22",
    "iPhone 15 Plus": "2023-09-22",
    "iPhone 15 Pro": "2023-09-22",
    "iPhone 15 Pro Max": "2023-09-22",
    "iPhone 16": "2024-09-20",
    "iPhone 16 Plus": "2024-09-20",
    "iPhone 16 Pro": "2024-09-20",
    "iPhone 16 Pro Max": "2024-09-20",
    "iPhone 16e": "2025-02-28",
    "iPhone 17": "2025-09-19",
    "iPhone 17 Pro": "2025-09-19",
    "iPhone 17 Pro Max": "2025-09-19",
    "iPhone Air": "2025-09-19",
    "iPhone 17e": "2026-03-11",
}


def parse_ios_major(text):
    """Lay so phien ban iOS lon dau tien tu 1 chuoi, vd '17.5.1 (21F90)' -> 17"""
    if not text:
        return None
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else None


def normalize_core_count(raw):
    """Chuan hoa 'Core Design' thanh dang 'N-core', cong tat ca cum 'x N'
    vd 'Apple Everest x 2 and Apple Sawtooth x 4' -> '6-core'
       'ARM1176 x 1' -> '1-core'
    """
    if not raw:
        return "Khong ro"
    nums = re.findall(r"x\s*(\d+)", raw, re.IGNORECASE)
    if nums:
        return f"{sum(int(n) for n in nums)}-core"
    m = re.search(r"(\d+)\s*[- ]core", raw, re.IGNORECASE)
    if m:
        return f"{m.group(1)}-core"
    return raw.strip()


def clean_chip_name(raw):
    """'A14 "A14 Bionic"' -> 'A14 Bionic' ; 'A17 Pro' -> 'A17 Pro'"""
    if not raw:
        return "Khong ro"
    quoted = re.search(r'"([^"]+)"', raw)
    if quoted:
        return quoted.group(1).strip()
    return raw.strip()


def parse_device_section(nodes):
    """
    Duyet cac the sibling (p, ul, ...) thuoc ve 1 thiet bi va tra ve:
      - flat: dict {ten_field: gia_tri} lay tu cac <li> dang 'Key: Value'
              (hoat dong cho CA 2 kieu cau truc cu/moi cua wiki)
      - storage_list / color_list: danh sach gia tri KHONG co dau ':'
        (chi xuat hien o kieu cau truc moi, vd 'Storage Options' -> '128GB')
    """
    flat = {}
    storage_list, color_list = [], []
    current_label = None

    for node in nodes:
        if node.name == "p":
            current_label = node.get_text(strip=True)
        elif node.name == "ul":
            # Chi lay <li> LA (khong co <li> con) de tranh trung lap noi dung
            # giua li cha (kieu cu, gom chu ca cac li con) va li con.
            leaves = [li for li in node.find_all("li") if li.find("li") is None]
            for li in leaves:
                text = li.get_text(" ", strip=True)
                if ":" in text:
                    key, _, val = text.partition(":")
                    key = key.strip()
                    # Khong ghi de neu field da co gia tri (uu tien gia tri dau tien)
                    if key not in flat:
                        flat[key] = val.strip()
                else:
                    if current_label and "storage" in current_label.lower():
                        storage_list.append(text)
                    elif current_label and "color" in current_label.lower():
                        color_list.append(text)
    return flat, storage_list, color_list


def get_iphone_data_from_html(html_path):
    print(f"Dang doc file: {html_path}")
    if not os.path.exists(html_path):
        print(f"  !! KHONG TIM THAY FILE: {html_path}")
        return []

    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    content = soup.find("div", class_="mw-parser-output")
    if content is None:
        print("  !! Khong tim thay noi dung chinh (div.mw-parser-output).")
        return []

    results = []
    for h2 in content.find_all("h2"):
        model_name = h2.get_text(strip=True)
        if "iphone" not in model_name.lower():
            continue  # bo qua 'Notes', 'References', v.v.

        wrapper = h2.parent  # <div class="mw-heading mw-heading2">
        nodes = []
        node = wrapper.find_next_sibling()
        while node and not (node.name == "div" and "mw-heading2" in (node.get("class") or [])):
            nodes.append(node)
            node = node.find_next_sibling()

        flat, storage_list, _ = parse_device_section(nodes)

        # 3 bien the ten field tung xuat hien qua cac thoi ky cua wiki:
        max_fw = (flat.get("Latest public firmware")
                  or flat.get("Latest firmware")
                  or flat.get("Last firmware"))
        init_fw = flat.get("Initial firmware")
        max_ios = parse_ios_major(max_fw)
        initial_ios = parse_ios_major(init_fw)

        if max_ios is None:
            print(f"  [Bo qua] '{model_name}': khong tim thay firmware/iOS.")
            continue

        storage = flat.get("Storage") or (
            "/".join(storage_list) if storage_list else "Khong ro"
        )

        results.append({
            "Device_Model": model_name,
            "Chip_Name": clean_chip_name(flat.get("CPU")),
            "CPU_Cores": normalize_core_count(flat.get("Core Design")),
            "RAM": flat.get("RAM", "Khong ro"),
            "Storage": storage,
            "Initial_iOS": initial_ios if initial_ios is not None else "Khong ro",
            "Max_Supported_iOS": max_ios,
        })

    print(f"  -> Da parse duoc {len(results)} dong may.\n")
    return results


def cross_check_with_models_file(devices, models_html_path):
    """
    QA doi chieu (khong bat buoc): kiem tra xem ten 'Generation' trong file
    Models/iPhone co xuat hien du trong danh sach device da parse hay khong.
    Giup phat hien thieu sot / sai ten khi viet phuong phap luan bao cao.
    """
    if not os.path.exists(models_html_path):
        print("(Bo qua doi chieu QA - khong tim thay file Models/iPhone)")
        return

    with open(models_html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    content = soup.find("div", class_="mw-parser-output")
    table = content.find("table") if content else None
    if table is None:
        return

    generations_in_models_file = set()
    for row in table.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if cells and "iphone" in cells[0].get_text(strip=True).lower():
            generations_in_models_file.add(cells[0].get_text(strip=True))

    device_names = {d["Device_Model"] for d in devices}
    missing = generations_in_models_file - device_names
    if missing:
        print("[QA] Cac ten may xuat hien trong Models/iPhone nhung KHONG khop "
              "voi Device_Model da parse (kiem tra lai chinh ta neu can):")
        for m in sorted(missing):
            print("   -", m)
    else:
        print("[QA] Ten thiet bi khop 100% giua 2 file nguon.")
    print()


def main():
    print("=" * 70)
    print("CAO DU LIEU CAU HINH IPHONE TU FILE HTML (THEAPPLEWIKI)")
    print("=" * 70)

    devices = get_iphone_data_from_html(LIST_HTML_FILE)
    if not devices:
        print("Khong co du lieu de xuat file. Dung chuong trinh.")
        return

    cross_check_with_models_file(devices, MODELS_HTML_FILE)

    for d in devices:
        d["Release_Date"] = RELEASE_DATE_MAP.get(d["Device_Model"], "Can xac nhan")

    # KHONG HARD-CODE: iOS moi nhat toan cau = max cua chinh bo du lieu vua cao
    latest_ios_global = max(d["Max_Supported_iOS"] for d in devices)
    for d in devices:
        d["Latest_Apple_iOS"] = latest_ios_global
        d["So_Doi_Bi_Bo_Roi"] = latest_ios_global - d["Max_Supported_iOS"]

    df = pd.DataFrame(devices)
    col_order = [
        "Device_Model", "Release_Date", "Chip_Name", "CPU_Cores", "RAM", "Storage",
        "Initial_iOS", "Max_Supported_iOS", "Latest_Apple_iOS", "So_Doi_Bi_Bo_Roi",
    ]
    df = df[col_order]
    df.to_excel(OUTPUT_FILE, index=False)

    print("=" * 40)
    print("XONG!")
    print(f"iOS moi nhat phat hien duoc (tinh dong, khong hard-code): {latest_ios_global}")
    print(f"Da xu ly {len(df)} dong may.")
    print(f"File luu tai: {OUTPUT_FILE}")
    print("=" * 40)


if __name__ == "__main__":
    main()
