import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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

# Tổ hợp biến tối ưu từ kết quả trước
svr_best_features = ['Release_Months', 'Storage_GB', 'iOS_Version_Gap', 'Bluetooth', 'Cellular (G)', 'Wi-Fi (Gen)']
rf_best_features = ['Release_Months', 'Storage_GB', 'iOS_Version_Gap', 'USB_C', 'Bluetooth', 'Camera (MP)', 'Cellular (G)']

# Các mốc phần trăm dữ liệu để phân tích
fractions = [20, 40, 60, 80, 100]

svr_times, rf_times = [], []
svr_maes, rf_maes = [], []

# ==========================================
# 2. CHẠY THỬ NGHIỆM ĐỂ LẤY THỜI GIAN VÀ MAE
# ==========================================
print("Đang tiến hành chạy thử nghiệm theo các mốc tỉ lệ dữ liệu...")

for frac in fractions:
    sample_size = int(len(df_labeled) * (frac / 100.0))
    if sample_size < 3:
        sample_size = 3
    
    df_sub = df_labeled.iloc[:sample_size].reset_index(drop=True)
    cv = LeaveOneOut()

    # --- SVR ---
    t0 = time.perf_counter()
    svr_preds, svr_trues = [], []
    for train_idx, test_idx in cv.split(df_sub):
        X_tr, X_te = df_sub[svr_best_features].iloc[train_idx], df_sub[svr_best_features].iloc[test_idx]
        y_tr, y_te = df_sub['Lifecycle_Months'].iloc[train_idx], df_sub['Lifecycle_Months'].iloc[test_idx]

        scaler = StandardScaler()
        X_tr_sc = scaler.fit_transform(X_tr)
        X_te_sc = scaler.transform(X_te)

        model = SVR(kernel='rbf', C=100.0, epsilon=1.0)
        model.fit(X_tr_sc, y_tr)
        svr_preds.append(model.predict(X_te_sc)[0])
        svr_trues.append(y_te.values[0])
    t1 = time.perf_counter()

    svr_times.append(t1 - t0)
    svr_maes.append(mean_absolute_error(svr_trues, svr_preds))

    # --- Random Forest ---
    t0 = time.perf_counter()
    rf_preds, rf_trues = [], []
    for train_idx, test_idx in cv.split(df_sub):
        X_tr, X_te = df_sub[rf_best_features].iloc[train_idx], df_sub[rf_best_features].iloc[test_idx]
        y_tr, y_te = df_sub['Lifecycle_Months'].iloc[train_idx], df_sub['Lifecycle_Months'].iloc[test_idx]

        model = RandomForestRegressor(n_estimators=100, max_depth=3, random_state=42, n_jobs=-1)
        model.fit(X_tr, y_tr)
        rf_preds.append(model.predict(X_te)[0])
        rf_trues.append(y_te.values[0])
    t1 = time.perf_counter()

    rf_times.append(t1 - t0)
    rf_maes.append(mean_absolute_error(rf_trues, rf_preds))

# ==========================================
# 3. VẼ BIỂU ĐỒ KÉP CHUẨN BÀI BÁO KHÓA HỌC
# ==========================================
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

# ------------------------------------------
# Biểu đồ 1: Thời gian chạy (Execution Time)
# ------------------------------------------
axes[0].plot(fractions, rf_times, color='red', marker='o', linewidth=2, markersize=6, label='Random Forest')
axes[0].plot(fractions, svr_times, color='green', marker='s', linewidth=2, markersize=6, label='Support Vector Machines (SVR)')

axes[0].set_xlabel('Training Dataset Fraction (%)', fontsize=11, fontweight='bold')
axes[0].set_ylabel('Execution Time (Seconds)', fontsize=11, fontweight='bold')
axes[0].set_title('(a) Execution Time vs Dataset Size', fontsize=12, fontweight='bold', pad=12)
axes[0].grid(True, linestyle='--', alpha=0.5)
axes[0].legend(title='Machine Learning\nAlgorithm', frameon=True, facecolor='white', edgecolor='gray')

# ------------------------------------------
# Biểu đồ 2: Độ sai lệch MAE (Prediction Error)
# ------------------------------------------
axes[1].plot(fractions, rf_maes, color='red', marker='o', linewidth=2, markersize=6, label='Random Forest')
axes[1].plot(fractions, svr_maes, color='green', marker='s', linewidth=2, markersize=6, label='Support Vector Machines (SVR)')

axes[1].set_xlabel('Training Dataset Fraction (%)', fontsize=11, fontweight='bold')
axes[1].set_ylabel('MAE Error (Months)', fontsize=11, fontweight='bold')
axes[1].set_title('(b) MAE Prediction Error vs Dataset Size', fontsize=12, fontweight='bold', pad=12)
axes[1].grid(True, linestyle='--', alpha=0.5)
axes[1].legend(title='Machine Learning\nAlgorithm', frameon=True, facecolor='white', edgecolor='gray')

plt.tight_layout()

# Lưu ảnh chất lượng cao
output_plot = '/Users/macbook/Library/CloudStorage/OneDrive-ut.edu.vn/Data cho NCKH/Sensitivity_Analysis_Plots.png'
plt.savefig(output_plot, dpi=300, bbox_inches='tight')
print(f"\nĐã xuất file hình ảnh thành công tại: {output_plot}")
plt.show()