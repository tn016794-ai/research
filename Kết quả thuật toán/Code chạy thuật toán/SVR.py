import os
import itertools
import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import mean_absolute_error, r2_score

# ==========================================
# 1. ĐỌC VÀ CHUẨN BỊ DỮ LIỆU
# ==========================================
file_path = '/Users/macbook/Library/CloudStorage/OneDrive-ut.edu.vn/Data cho NCKH/Iphone_dataset.xlsx'

if not os.path.exists(file_path):
    raise FileNotFoundError(f"Không tìm thấy file tại đường dẫn: '{file_path}'")

df = pd.read_excel(file_path)

# Đổi định dạng mốc thời gian
df['Release_Date_dt'] = pd.to_datetime(df['Release_Date'])
df['Obsolete_Date_dt'] = pd.to_datetime(df['Obsolete_Date'])

base_date = pd.Timestamp('2007-06-29')
df['Release_Months'] = (df['Release_Date_dt'] - base_date).dt.days / 30.4375

# Tập dữ liệu các máy đã dừng sản xuất
df_labeled = df[df['Obsolete_Date_dt'].notna()].copy().reset_index(drop=True)
df_labeled['Lifecycle_Months'] = (df_labeled['Obsolete_Date_dt'] - df_labeled['Release_Date_dt']).dt.days / 30.4375

# Danh sách 11 biến
all_features = [
    'Release_Months', 'RAM_GB', 'Storage_GB', 'Geekbench_Single_Core',
    'Geekbench_Multi_Core', 'iOS_Version_Gap', 'USB_C', 'Bluetooth',
    'Camera (MP)', 'Cellular (G)', 'Wi-Fi (Gen)'
]

# ==========================================
# BƯỚC 1: LỌC BIẾN VÉT CẠN (CỐ ĐỊNH RELEASE_MONTHS + LOOCV)
# ==========================================
print("=" * 60)
print(" BƯỚC 1: ĐANG CHẠY LỌC BIẾN VÉT CẠN CÓ LOOCV...")
print("=" * 60)

fixed_feature = 'Release_Months'
other_features = [f for f in all_features if f != fixed_feature]

all_combinations = []
for k in range(0, len(other_features) + 1):
    for combo in itertools.combinations(other_features, k):
        all_combinations.append([fixed_feature] + list(combo))

cv = LeaveOneOut()
results_fs = []

for idx, combo in enumerate(all_combinations, 1):
    X_sub = df_labeled[combo]
    y_sub = df_labeled['Lifecycle_Months']
    
    y_preds, y_trues = [], []
    for train_idx, test_idx in cv.split(X_sub):
        X_tr, X_te = X_sub.iloc[train_idx], X_sub.iloc[test_idx]
        y_tr, y_te = y_sub.iloc[train_idx], y_sub.iloc[test_idx]
        
        scaler = StandardScaler()
        X_tr_scaled = scaler.fit_transform(X_tr)
        X_te_scaled = scaler.transform(X_te)
        
        model = SVR(kernel='rbf', C=100.0, epsilon=1.0)
        model.fit(X_tr_scaled, y_tr)
        
        y_preds.append(model.predict(X_te_scaled)[0])
        y_trues.append(y_te.iloc[0])
        
    mae = mean_absolute_error(y_trues, y_preds)
    r2 = r2_score(y_trues, y_preds)
    
    results_fs.append({
        'STT': idx,
        'So_luong_bien': len(combo),
        'Danh_sach_bien': ", ".join(combo),
        'MAE_LOOCV': round(mae, 4),
        'R2_LOOCV': round(r2, 4)
    })

df_results_fs = pd.DataFrame(results_fs).sort_values(by='MAE_LOOCV', ascending=True).reset_index(drop=True)

# Lấy tổ hợp biến tối ưu nhất
best_row = df_results_fs.iloc[0]
best_features = [f.strip() for f in best_row['Danh_sach_bien'].split(',')]

print(f"-> Tổ hợp biến tối ưu nhất: {best_features}")
print(f"-> MAE thấp nhất (LOOCV): {best_row['MAE_LOOCV']} tháng | R2: {best_row['R2_LOOCV']}")

# ==========================================
# BƯỚC 2: CHẠY DỰ ĐOÁN CHÍNH THỨC DỰA TRÊN TỔ HỢP TỐI ƯU
# ==========================================
print("\n" + "=" * 60)
print(" BƯỚC 2: HUẤN LUYỆN 100% DATA VÀ DỰ ĐOÁN CHO CÁC MẪU MÁY...")
print("=" * 60)

X_train_final = df_labeled[best_features]
y_train_final = df_labeled['Lifecycle_Months']

scaler_final = StandardScaler()
X_train_scaled = scaler_final.fit_transform(X_train_final)

final_svr = SVR(kernel='rbf', C=100.0, epsilon=1.0)
final_svr.fit(X_train_scaled, y_train_final)

# Dự đoán cho toàn bộ máy
X_all = df[best_features]
X_all_scaled = scaler_final.transform(X_all)

df['SVR_Predicted_Lifecycle_Months'] = final_svr.predict(X_all_scaled).round(1)
df['SVR_Predicted_Obsolete_Date'] = df['Release_Date_dt'] + pd.to_timedelta(df['SVR_Predicted_Lifecycle_Months'] * 30.4375, unit='D')
df['SVR_Predicted_Obsolete_Date'] = df['SVR_Predicted_Obsolete_Date'].dt.strftime('%Y-%m-%d')

# ==========================================
# BƯỚC 3: PHÂN TÍCH ĐỘ NHẠY (SENSITIVITY ANALYSIS)
# ==========================================
print("\n" + "=" * 60)
print(" BƯỚC 3: ĐANG CHẠY PHÂN TÍCH ĐỘ NHẠY (SENSITIVITY ANALYSIS)...")
print("=" * 60)

ratios = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
n_iterations = 20  # Lặp lại 20 lần cho mỗi tỷ lệ rút mẫu
sensitivity_results = []

np.random.seed(42)  # Cố định ngẫu nhiên để kết quả ổn định

for ratio in ratios:
    mae_list = []
    r2_list = []
    sample_size = int(len(df_labeled) * ratio)
    
    # Đảm bảo mẫu ít nhất phải >= 5 máy để chạy LOOCV
    if sample_size < 5:
        continue
        
    for _ in range(n_iterations):
        # Rút ngẫu nhiên một tỷ lệ phần trăm mẫu
        sampled_df = df_labeled.sample(n=sample_size, replace=False)
        
        X_samp = sampled_df[best_features]
        y_samp = sampled_df['Lifecycle_Months']
        
        y_p, y_t = [], []
        cv_sens = LeaveOneOut()
        for tr_idx, te_idx in cv_sens.split(X_samp):
            X_tr, X_te = X_samp.iloc[tr_idx], X_samp.iloc[te_idx]
            y_tr, y_te = y_samp.iloc[tr_idx], y_samp.iloc[te_idx]
            
            sc = StandardScaler()
            X_tr_sc = sc.fit_transform(X_tr)
            X_te_sc = sc.transform(X_te)
            
            md = SVR(kernel='rbf', C=100.0, epsilon=1.0)
            md.fit(X_tr_sc, y_tr)
            
            y_p.append(md.predict(X_te_sc)[0])
            y_t.append(y_te.iloc[0])
            
        mae_list.append(mean_absolute_error(y_t, y_p))
        r2_list.append(r2_score(y_t, y_p))
        
    sensitivity_results.append({
        'Ty_Le_Du_Lieu': f"{int(ratio * 100)}%",
        'So_Luong_Mau': sample_size,
        'MAE_Trung_Binh': round(np.mean(mae_list), 4),
        'MAE_Do_Lech_Chuan': round(np.std(mae_list), 4),
        'R2_Trung_Binh': round(np.mean(r2_list), 4)
    })

df_sensitivity = pd.DataFrame(sensitivity_results)
print(df_sensitivity.to_string(index=False))

# ==========================================
# 4. XUẤT TOÀN BỘ KẾT QUẢ RA FILE EXCEL
# ==========================================
output_file = '/Users/macbook/Library/CloudStorage/OneDrive-ut.edu.vn/Data cho NCKH/Iphone_SVR_Full_Workflow_Results.xlsx'

export_cols = [col for col in df.columns if not col.endswith('_dt') and col != 'Release_Months']
export_df = df[export_cols].copy()

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet 1: Tất cả máy
    export_df.to_excel(writer, sheet_name='Du_Doan_Tat_Ca_Model', index=False)
    
    # Sheet 2: Máy chưa dừng sản xuất
    unlabeled_df = export_df[export_df['Obsolete_Date'].isna()]
    unlabeled_df.to_excel(writer, sheet_name='Du_Doan_May_Chua_Obsolete', index=False)
    
    # Sheet 3: Kết quả lọc biến
    df_results_fs.to_excel(writer, sheet_name='Ket_Qua_Loc_Bien_LOOCV', index=False)
    
    # Sheet 4: Phân tích độ nhạy
    df_sensitivity.to_excel(writer, sheet_name='Phan_Tich_Do_Nhay', index=False)

print("\n" + "=" * 60)
print(f" HOÀN TẤT TOÀN BỘ CÔNG VIỆC!")
print(f" File Excel kết quả đã lưu tại: {output_file}")
print("=" * 60)
