import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import mean_absolute_error

# ==========================================
# 1. ĐỌC VÀ CHUẨN BỊ DỮ LIỆU
# ==========================================
file_path = '/Users/macbook/Library/CloudStorage/OneDrive-ut.edu.vn/Data cho NCKH/Iphone_dataset.xlsx'

if not os.path.exists(file_path):
    raise FileNotFoundError(f"Không tìm thấy file tại đường dẫn: '{file_path}'")

df = pd.read_excel(file_path)

df['Release_Date_dt'] = pd.to_datetime(df['Release_Date'])
df['Obsolete_Date_dt'] = pd.to_datetime(df['Obsolete_Date'])

base_date = pd.Timestamp('2007-06-29')
df['Release_Months'] = (df['Release_Date_dt'] - base_date).dt.days / 30.4375

df_labeled = df[df['Obsolete_Date_dt'].notna()].copy().reset_index(drop=True)
df_labeled['Lifecycle_Months'] = (df_labeled['Obsolete_Date_dt'] - df_labeled['Release_Date_dt']).dt.days / 30.4375

# Tổ hợp biến tối ưu đã xác định từ bước lọc biến (mục 3.4)
svr_best_features = ['Release_Months', 'Storage_GB', 'iOS_Version_Gap', 'Bluetooth', 'Cellular (G)', 'Wi-Fi (Gen)']
rf_best_features = ['Release_Months', 'Storage_GB', 'iOS_Version_Gap', 'USB_C', 'Bluetooth', 'Camera (MP)', 'Cellular (G)']

# ==========================================
# 2. PHÂN TÍCH ĐỘ NHẠY: THỜI GIAN CHẠY (RÚT MẪU NGẪU NHIÊN, LẶP 20 LẦN)
# ==========================================
ratios = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
n_iterations = 20

np.random.seed(42)

svr_time_avg, rf_time_avg = [], []
svr_time_std, rf_time_std = [], []

print("Đang chạy phân tích thời gian thực thi theo tỷ lệ dữ liệu...")

for ratio in ratios:
    sample_size = int(len(df_labeled) * ratio)
    if sample_size < 5:
        continue

    svr_times_this_ratio = []
    rf_times_this_ratio = []

    for _ in range(n_iterations):
        sampled_df = df_labeled.sample(n=sample_size, replace=False).reset_index(drop=True)
        cv = LeaveOneOut()

        # --- Đo thời gian chạy toàn bộ vòng LOOCV cho SVR ---
        X_svr = sampled_df[svr_best_features]
        y = sampled_df['Lifecycle_Months']

        t0 = time.perf_counter()
        for train_idx, test_idx in cv.split(X_svr):
            X_tr, X_te = X_svr.iloc[train_idx], X_svr.iloc[test_idx]
            y_tr = y.iloc[train_idx]

            scaler = StandardScaler()
            X_tr_sc = scaler.fit_transform(X_tr)
            X_te_sc = scaler.transform(X_te)

            model = SVR(kernel='rbf', C=100.0, epsilon=1.0)
            model.fit(X_tr_sc, y_tr)
            model.predict(X_te_sc)
        t1 = time.perf_counter()
        svr_times_this_ratio.append(t1 - t0)

        # --- Đo thời gian chạy toàn bộ vòng LOOCV cho Random Forest ---
        X_rf = sampled_df[rf_best_features]

        t0 = time.perf_counter()
        for train_idx, test_idx in cv.split(X_rf):
            X_tr, X_te = X_rf.iloc[train_idx], X_rf.iloc[test_idx]
            y_tr = y.iloc[train_idx]

            model = RandomForestRegressor(n_estimators=100, max_depth=3, random_state=42, n_jobs=-1)
            model.fit(X_tr, y_tr)
            model.predict(X_te)
        t1 = time.perf_counter()
        rf_times_this_ratio.append(t1 - t0)

    svr_time_avg.append(np.mean(svr_times_this_ratio))
    svr_time_std.append(np.std(svr_times_this_ratio))
    rf_time_avg.append(np.mean(rf_times_this_ratio))
    rf_time_std.append(np.std(rf_times_this_ratio))

    print(f"-> Tỷ lệ {int(ratio*100)}% hoàn tất.")

# ==========================================
# 3. VẼ BIỂU ĐỒ THỜI GIAN CHẠY
# ==========================================
fractions_pct = [int(r * 100) for r in ratios]

fig, ax = plt.subplots(figsize=(8, 5), dpi=300)

ax.plot(fractions_pct, rf_time_avg, color='#E74C3C', marker='o', linewidth=2.2,
        markersize=6, label='Random Forest')
ax.plot(fractions_pct, svr_time_avg, color='#27AE60', marker='s', linewidth=2.2,
        markersize=6, label='SVR')

ax.set_xlabel('Tỷ lệ dữ liệu rút mẫu (%)', fontsize=12, fontweight='bold')
ax.set_ylabel('Thời gian chạy (giây)', fontsize=12, fontweight='bold')
ax.set_title('Thời gian thực thi theo cỡ mẫu dữ liệu', fontsize=13, fontweight='bold', pad=12)
ax.grid(True, linestyle='--', alpha=0.4)

# Legend đặt bên phải, ngoài khung vẽ, giống hình tham chiếu
ax.legend(title='Thuật toán', frameon=True, facecolor='white',
          edgecolor='gray', loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=10,
          title_fontsize=11)

plt.tight_layout()

output_plot = '/Users/macbook/Library/CloudStorage/OneDrive-ut.edu.vn/Data cho NCKH/Execution_Time_vs_Dataset_Size.png'
plt.savefig(output_plot, dpi=300, bbox_inches='tight')
print(f"\nĐã lưu biểu đồ tại: {output_plot}")
