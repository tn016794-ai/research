import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import os

# ===================================================
# TẠO FOLDER "Data cho NCKH" ĐỂ LƯU ẢNH
# ===================================================
folder_name = "Data cho NCKH"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

# ===================================================
# DATA
# ===================================================

ratios = ['50%', '60%', '70%', '80%', '90%', '100%']
sample_counts = [10, 12, 14, 16, 18, 21]

svr_data = [
    ("7.87 (2.15)", "-0.270"),
    ("6.56 (1.73)", "-0.006"),
    ("6.92 (1.42)", "-0.001"),
    ("5.92 (1.03)", "0.193"),
    ("5.12 (0.87)", "0.348"),
    ("4.51 (0.00)", "0.452")
]

rf_data = [
    ("7.78 (1.15)", "-0.233"),
    ("7.56 (1.59)", "-0.127"),
    ("7.03 (1.76)", "0.011"),
    ("7.63 (1.03)", "-0.112"),
    ("7.23 (0.65)", "-0.058"),
    ("6.94 (0.18)", "0.014")
]

# ===================================================
# TABLE DATA (TIẾNG VIỆT THEO CHUẨN NCKH)
# ===================================================

headers = [
    "Tỷ lệ\ndữ liệu",
    "Số mẫu",
    "SVR\nMAE TB (SD)",
    "SVR\nR² TB",
    "RF\nMAE TB (SD)",
    "RF\nR² TB"
]

rows = []

for i in range(len(ratios)):
    rows.append([
        ratios[i],
        sample_counts[i],
        svr_data[i][0],
        svr_data[i][1],
        rf_data[i][0],
        rf_data[i][1]
    ])

# ===================================================
# FIGURE
# ===================================================

fig, ax = plt.subplots(figsize=(11,4.5), dpi=600)

ax.axis("off")

plt.title(
    "BẢNG VII\nKẾT QUẢ ĐÁNH GIÁ VÀ PHÂN TÍCH ĐỘ NHẠY CỦA CÁC MÔ HÌNH",
    fontsize=13,
    fontweight="bold",
    family="serif",
    pad=20
)

# ===================================================
# CREATE TABLE
# ===================================================

table = ax.table(
    cellText=rows,
    colLabels=headers,
    cellLoc="center",
    colLoc="center",
    loc="center"
)

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1.15,2.0)

font = FontProperties(
    family="Times New Roman",
    size=9
)

# ===================================================
# STYLE
# ===================================================

nrows = len(rows)+1
ncols = len(headers)

for (r,c),cell in table.get_celld().items():

    cell.set_facecolor("white")
    cell.set_linewidth(0)

    cell.get_text().set_fontproperties(font)

    if r==0:
        cell.get_text().set_weight("bold")
        cell.visible_edges="TB"
        cell.set_linewidth(1.2)

    elif r==nrows-1:
        cell.visible_edges="B"
        cell.set_linewidth(1.2)

# ===================================================
# COLUMN WIDTH
# ===================================================

widths = {
    0:0.18,
    1:0.12,
    2:0.22,
    3:0.12,
    4:0.22,
    5:0.12
}

for c,w in widths.items():
    for r in range(nrows):
        table[(r,c)].set_width(w)

plt.tight_layout()

# ===================================================
# XUẤT FILE VÀO THƯ MỤC
# ===================================================
output = os.path.join(folder_name, "Bang_Ket_Qua_Chuan_Template.png")

plt.savefig(
    output,
    dpi=600,
    bbox_inches="tight"
)

print("Đã lưu ảnh tại:", output)

plt.show()