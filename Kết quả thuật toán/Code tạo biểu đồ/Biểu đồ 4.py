import matplotlib.pyplot as plt

# 1. Tạo khung ảnh trắng sắc nét
fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=300)
ax.axis('off')

# 2. Tiêu đề bảng tiếng Việt
plt.text(0.5, 0.92, 'BẢNG VIII', fontsize=11, fontweight='bold', ha='center', fontfamily='sans-serif')
plt.text(0.5, 0.83, 'TÓM TẮT XẾP HẠNG LỰA CHỌN MÔ HÌNH', fontsize=10, fontweight='bold', ha='center', fontfamily='sans-serif')

# 3. Các đường kẻ ngang kiểu Booktabs
ax.axhline(y=0.76, xmin=0.05, xmax=0.95, color='black', linewidth=1.2) # Đường kẻ trên
ax.axhline(y=0.67, xmin=0.05, xmax=0.95, color='black', linewidth=0.6) # Đường kẻ dưới tiêu đề

# Tiêu đề các cột
plt.text(0.72, 0.70, 'RF', fontsize=10, fontweight='bold', ha='center', fontfamily='sans-serif')
plt.text(0.87, 0.70, 'SVR', fontsize=10, fontweight='bold', ha='center', fontfamily='sans-serif')

# 4. Nội dung các dòng trong bảng tiếng Việt
rows = [
    ("Các đặc tính dựa trên kết quả vận hành", "", "", True),
    ("Mức độ chính xác (Accuracy)", "Hạng 2", "Hạng 1", False),
    ("Tốc độ tính toán (Evaluation Speed)", "Hạng 2", "Hạng 1", False),
    ("Các đặc tính ngoài kết quả vận hành", "", "", True),
    ("Độ dễ hiểu / Giải thích (Interpretability)", "Hạng 1", "Hạng 2", False),
    ("Độ linh hoạt / Dễ bảo trì (Maintainability)", "Hạng 1", "Hạng 2", False)
]

y_pos = 0.58
for label, rf, svr, is_group_header in rows:
    if is_group_header:
        # Tên nhóm (in nghiêng)
        plt.text(0.06, y_pos, label, fontsize=9.5, style='italic', fontfamily='sans-serif')
    else:
        # Nội dung từng tiêu chí
        plt.text(0.09, y_pos, label, fontsize=9.5, fontfamily='sans-serif')
        plt.text(0.72, y_pos, rf, fontsize=9.5, ha='center', fontfamily='sans-serif')
        plt.text(0.87, y_pos, svr, fontsize=9.5, ha='center', fontfamily='sans-serif')
    y_pos -= 0.085

# Đường kẻ ngang đáy bảng
ax.axhline(y=y_pos + 0.04, xmin=0.05, xmax=0.95, color='black', linewidth=1.2)

# 5. Lưu file ảnh
output_path = '/Users/macbook/Library/CloudStorage/OneDrive-ut.edu.vn/Data cho NCKH/Model_Preference_Ranking_Table_VN.png'
plt.tight_layout()
plt.savefig(output_path, bbox_inches='tight', dpi=300)
print(f"Đã xuất xong bảng tiếng Việt tại: {output_path}")
plt.show()