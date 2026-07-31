

from bs4 import BeautifulSoup
import pandas as pd

HTML_FILE = "Data cho NCKH/iOS Benchmarks 1 - Geekbench.html"
with open(HTML_FILE, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")


def parse_table(tab_id):
    data = {}

    tab = soup.find("div", id=tab_id)
    if tab is None:
        print(f"Không tìm thấy tab {tab_id}")
        return data

    table = tab.find("table")
    if table is None:
        print(f"Không tìm thấy bảng trong {tab_id}")
        return data

    for row in table.find_all("tr"):

        name_td = row.find("td", class_="name")
        score_td = row.find("td", class_="score")

        if not name_td or not score_td:
            continue

        a = name_td.find("a")
        if not a:
            continue

        device = a.get_text(" ", strip=True)

        # Chỉ lấy iPhone
        if not device.startswith("iPhone"):
            continue

        desc = name_td.find("div", class_="description")
        chip = desc.get_text(" ", strip=True) if desc else ""

        score = score_td.get_text(strip=True).replace(",", "")

        try:
            score = int(score)
        except:
            continue

        data[device] = {
            "Chip": chip,
            "Score": score
        }

    return data


print("Đang đọc Single-Core...")
single = parse_table("single-core")

print("Đang đọc Multi-Core...")
multi = parse_table("multi-core")

rows = []

devices = sorted(set(single.keys()) | set(multi.keys()))

for device in devices:

    chip = ""

    if device in single:
        chip = single[device]["Chip"]
    elif device in multi:
        chip = multi[device]["Chip"]

    rows.append({

        "Device_Model": device,

        "Chip": chip,

        "Single_Core": single.get(device, {}).get("Score"),

        "Multi_Core": multi.get(device, {}).get("Score")

    })

df = pd.DataFrame(rows)

df = df.sort_values("Single_Core", ascending=False)

df.to_excel("Data cho NCKH/iphone_geekbench.xlsx", index=False)

print(df.head())

print(f"\nĐã lấy {len(df)} mẫu iPhone")
print("Đã lưu file iphone_geekbench.xlsx")