import os
import itertools
import pandas as pd
import numpy as np

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

# Tập dữ liệu các máy đã dừng sản xuất (có nhãn)
df_labeled = df[df['Obsolete_Date_dt'].notna()].copy().reset_index(drop=True)
df_labeled['Lifecycle_Months'] = (df_labeled['Obsolete_Date_dt'] - df_labeled['Release_Date_dt']).dt.days / 30.4375

all_features = [
    'Release_Months', 'RAM_GB', 'Storage_GB', 'Geekbench_Single_Core',
    'Geekbench_Multi_Core', 'iOS_Version_Gap', 'USB_C', 'Bluetooth',
    'Camera (MP)', 'Cellular (G)', 'Wi-Fi (Gen)'
]

# ==========================================
# BƯỚC 1: LỌC BIẾN VÉT CẠN RANDOM FOREST (MAX_DEPTH=3 + LOOCV)
# ==========================================
print("=" * 60)
print(" BƯỚC 1: ĐANG CHẠY LỌC BIẾN RANDOM FOREST (MAX_DEPTH=3) CÓ LOOCV...")
print("=" * 60)

fixed_feature = 'Release_Months'
other_features = [f for f in all_features if f != fixed_feature]

all_combinations = []
for k in range(0, len(other_features) + 1):
    for combo in itertools.combinations(other_features, k):
        all_combinations.append([fixed_feature] + list(combo))

total_combos = len(all_combinations)
cv = LeaveOneOut()
results_fs = []

for idx, combo in enumerate(all_combinations, 1):
    X_sub = df_labeled[combo]
    y_sub = df_labeled['Lifecycle_Months']
    
    y_preds, y_trues = [], []
    for train_idx, test_idx in cv.split(X_sub):
        X_tr, X_te = X_sub.iloc[train_idx], X_sub.iloc[test_idx]
        y_tr, y_te = y_sub.iloc[train_idx], y_sub.iloc[test_idx]
        
        model = RandomForestRegressor(
            n_estimators=100, 
            max_depth=3, 
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_tr, y_tr)
        
        y_preds.append(model.predict(X_te)[0])
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
    
    if idx % 200 == 0 or idx == total_combos:
        print(f"-> Tiến độ: {idx}/{total_combos} tổ hợp ({(idx/total_combos)*100:.1f}%)")

df_results_fs = pd.DataFrame(results_fs).sort_values(by='MAE_LOOCV', ascending=True).reset_index(drop=True)

best_row = df_results_fs.iloc[0]
best_features = [f.strip() for f in best_row['Danh_sach_bien'].split(',')]

print(f"\n-> Tổ hợp biến RF tối ưu nhất: {best_features}")
print(f"-> MAE thấp nhất (LOOCV): {best_row['MAE_LOOCV']} tháng | R2: {best_row['R2_LOOCV']}")

# ==========================================
# BƯỚC 2: CHẠY DỰ ĐOÁN CHÍNH THỨC DỰA TRÊN TỔ HỢP TỐI ƯU
# ==========================================
print("\n" + "=" * 60)
print(" BƯỚC 2: HUẤN LUYỆN 100% DATA VÀ DỰ ĐOÁN CHO CÁC MẪU MÁY...")
print("=" * 60)

X_train_final = df_labeled[best_features]
y_train_final = df_labeled['Lifecycle_Months']

final_rf = RandomForestRegressor(
    n_estimators=100, 
    max_depth=3, 
    random_state=42,
    n_jobs=-1
)
final_rf.fit(X_train_final, y_train_final)

X_all = df[best_features]
df['Predicted_Lifecycle_Months'] = final_rf.predict(X_all).round(1)
df['Predicted_Obsolete_Date'] = df['Release_Date_dt'] + pd.to_timedelta(df['Predicted_Lifecycle_Months'] * 30.4375, unit='D')
df['Predicted_Obsolete_Date'] = df['Predicted_Obsolete_Date'].dt.strftime('%Y-%m-%d')

# ==========================================
# BƯỚC 3: PHÂN TÍCH ĐỘ NHẠY (ĐÃ SỬA LỖI TE_IDX TRÙNG BIẾN)
# ==========================================
print("\n" + "=" * 60)
print(" BƯỚC 3: ĐANG CHẠY PHÂN TÍCH ĐỘ NHẠY CHO RANDOM FOREST...")
print("=" * 60)

ratios = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
n_iterations = 20
sensitivity_results = []

np.random.seed(42)

for ratio in ratios:
    mae_list = []
    r2_list = []
    sample_size = int(len(df_labeled) * ratio)
    
    if sample_size < 5:
        continue
        
    for _ in range(n_iterations):
        # Reset index dữ liệu rút mẫu để tránh lệch index
        sampled_df = df_labeled.sample(n=sample_size, replace=False).reset_index(drop=True)
        
        X_samp = sampled_df[best_features]
        y_samp = sampled_df['Lifecycle_Months']
        
        y_p, y_t = [], []
        cv_sens = LeaveOneOut()
        for tr_idx, te_idx in cv_sens.split(X_samp):
            # SỬA LỖI TẠI ĐÂY: Dùng đúng te_idx thay vì test_idx
            X_tr, X_te = X_samp.iloc[tr_idx], X_samp.iloc[te_idx]
            y_tr, y_te = y_samp.iloc[tr_idx], y_samp.iloc[te_idx]
            
            md = RandomForestRegressor(
                n_estimators=100, 
                max_depth=3, 
                random_state=42,
                n_jobs=-1
            )
            md.fit(X_tr, y_tr)
            
            y_p.append(md.predict(X_te)[0])
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
output_file = '/Users/macbook/Library/CloudStorage/OneDrive-ut.edu.vn/Data cho NCKH/Iphone_RF_Full_Workflow_Results.xlsx'

export_cols = [col for col in df.columns if not col.endswith('_dt') and col != 'Release_Months']
export_df = df[export_cols].copy()

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet 1: Dự đoán tất cả dòng máy
    export_df.to_excel(writer, sheet_name='Du_Doan_Tat_Ca_Model', index=False)
    
    # Sheet 2: Dự đoán máy chưa dừng sản xuất
    unlabeled_df = export_df[export_df['Obsolete_Date'].isna()]
    unlabeled_df.to_excel(writer, sheet_name='Du_Doan_May_Chua_Obsolete', index=False)
    
    # Sheet 3: Bảng lọc biến
    df_results_fs.to_excel(writer, sheet_name='Ket_Qua_Loc_Bien_LOOCV', index=False)
    
    # Sheet 4: Bảng độ nhạy
    df_sensitivity.to_excel(writer, sheet_name='Phan_Tich_Do_Nhay', index=False)

print("\n" + "=" * 60)
print(f" XONG RỒI! File Excel đã lưu tại: {output_file}")
print("=" * 60)
