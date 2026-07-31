import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import mean_absolute_error, r2_score

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

# Tập dữ liệu có nhãn
df_labeled = df[df['Obsolete_Date_dt'].notna()].copy().reset_index(drop=True)
df_labeled['Lifecycle_Months'] = (df_labeled['Obsolete_Date_dt'] - df_labeled['Release_Date_dt']).dt.days / 30.4375

# Tính mốc năm thực tế (dạng số thập phân)
actual_years = df_labeled['Obsolete_Date_dt'].dt.year + (df_labeled['Obsolete_Date_dt'].dt.dayofyear / 365.25)

# ==========================================
# 2. KHAI BÁO TỔ HỢP BIẾN TỐI ƯU TỪ EXCEL CỦA BẠN
# ==========================================
# Tổ hợp biến SVR tối ưu (từ Hình 3: MAE = 4.5051)
svr_best_features = [
    'Release_Months', 'Storage_GB', 'iOS_Version_Gap', 
    'Bluetooth', 'Cellular (G)', 'Wi-Fi (Gen)'
]

# Tổ hợp biến RF tối ưu (từ Hình 2: MAE = 6.6572)
rf_best_features = [
    'Release_Months', 'Storage_GB', 'iOS_Version_Gap', 
    'USB_C', 'Bluetooth', 'Camera (MP)', 'Cellular (G)'
]

cv = LeaveOneOut()

# --- A. LOOCV CHO SVR ---
svr_preds_months = []
for train_idx, test_idx in cv.split(df_labeled):
    X_tr = df_labeled[svr_best_features].iloc[train_idx]
    X_te = df_labeled[svr_best_features].iloc[test_idx]
    y_tr = df_labeled['Lifecycle_Months'].iloc[train_idx]
    
    scaler = StandardScaler()
    X_tr_sc = scaler.fit_transform(X_tr)
    X_te_sc = scaler.transform(X_te)
    
    model_svr = SVR(kernel='rbf', C=100.0, epsilon=1.0)
    model_svr.fit(X_tr_sc, y_tr)
    svr_preds_months.append(model_svr.predict(X_te_sc)[0])

svr_preds_months = np.array(svr_preds_months)
svr_mae = mean_absolute_error(df_labeled['Lifecycle_Months'], svr_preds_months)
svr_r2 = r2_score(df_labeled['Lifecycle_Months'], svr_preds_months)

# Quy đổi số tháng ra mốc năm để vẽ đồ thị
svr_pred_dates = df_labeled['Release_Date_dt'] + pd.to_timedelta(svr_preds_months * 30.4375, unit='D')
svr_pred_years = svr_pred_dates.dt.year + (svr_pred_dates.dt.dayofyear / 365.25)

# --- B. LOOCV CHO RANDOM FOREST ---
rf_preds_months = []
for train_idx, test_idx in cv.split(df_labeled):
    X_tr = df_labeled[rf_best_features].iloc[train_idx]
    X_te = df_labeled[rf_best_features].iloc[test_idx]
    y_tr = df_labeled['Lifecycle_Months'].iloc[train_idx]
    
    model_rf = RandomForestRegressor(n_estimators=100, max_depth=3, random_state=42, n_jobs=-1)
    model_rf.fit(X_tr, y_tr)
    rf_preds_months.append(model_rf.predict(X_te)[0])

rf_preds_months = np.array(rf_preds_months)
rf_mae = mean_absolute_error(df_labeled['Lifecycle_Months'], rf_preds_months)
rf_r2 = r2_score(df_labeled['Lifecycle_Months'], rf_preds_months)

rf_pred_dates = df_labeled['Release_Date_dt'] + pd.to_timedelta(rf_preds_months * 30.4375, unit='D')
rf_pred_years = rf_pred_dates.dt.year + (rf_pred_dates.dt.dayofyear / 365.25)

# ==========================================
# 3. VẼ BIỂU ĐỒ SO SÁNH
# ==========================================
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(13, 6), dpi=300)

min_year = min(actual_years.min(), svr_pred_years.min(), rf_pred_years.min()) - 1
max_year = max(actual_years.max(), svr_pred_years.max(), rf_pred_years.max()) + 1

models_info = [
    {
        "ax": axes[0], "pred": svr_pred_years, "title": "SVR Model", 
        "color": "blue", "mae": svr_mae, "r2": svr_r2
    },
    {
        "ax": axes[1], "pred": rf_pred_years, "title": "Random Forest Model", 
        "color": "royalblue", "mae": rf_mae, "r2": rf_r2
    }
]

for item in models_info:
    ax = item["ax"]
    
    # 1. Đường nét đứt màu đỏ y = x
    ax.plot([min_year, max_year], [min_year, max_year], 'r--', linewidth=1.5, label='Ideal Fit (y = x)')
    
    # 2. Đường xu hướng và điểm dữ liệu
    sns.regplot(
        x=actual_years, 
        y=item["pred"], 
        ax=ax, 
        color=item["color"],
        scatter_kws={'color': 'black', 's': 30, 'alpha': 0.85},
        line_kws={'linewidth': 2}
    )
    
    # Hộp thông tin MAE và R2 chuẩn từ Excel
    ax.text(
        0.05, 0.88, 
        f"MAE = {item['mae']:.2f} tháng\n$R^2$ = {item['r2']:.3f}", 
        transform=ax.transAxes, 
        fontsize=11, 
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9, edgecolor="gray")
    )
    
    ax.set_xlim(min_year, max_year)
    ax.set_ylim(min_year, max_year)
    ax.set_xlabel('Actual Obsolete Year', fontsize=11, fontweight='bold')
    ax.set_ylabel('Prediction Obsolete Year', fontsize=11, fontweight='bold')
    ax.set_title(item["title"], fontsize=13, fontweight='bold', pad=10)
    ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()

output_plot = '/Users/macbook/Library/CloudStorage/OneDrive-ut.edu.vn/Data cho NCKH/Actual_vs_Predicted_Corrected.png'
plt.savefig(output_plot, dpi=300, bbox_inches='tight')
print(f"Đã lưu biểu đồ chính xác tại: {output_plot}")
plt.show()