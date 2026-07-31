import os
import pandas as pd

# Đường dẫn file Excel cũ của bạn (nằm trong thư mục Data cho NCKH)
EXCEL_FILE = "Data cho NCKH/iphone_geekbench.xlsx"

# Kiểm tra xem file gốc đã tồn tại chưa
if not os.path.exists(EXCEL_FILE):
    print(
        f"Không tìm thấy file {EXCEL_FILE}. Hãy chắc chắn bạn đã chạy file cào dữ liệu trước đó!"
    )
else:
    print(
        f"Đang đọc dữ liệu từ file {EXCEL_FILE} để bổ sung biến số kỹ thuật..."
    )
    df = pd.read_excel(EXCEL_FILE)

    # Định nghĩa hàm phân loại dựa trên tên thiết bị
    def add_features(device_name):
        # Chuyển về chữ thường để so sánh chính xác không phân biệt hoa thường
        device_lower = str(device_name).lower()

        # 1. Phân loại cổng sạc (USB-C = 1, Lightning = 0)
        # Từ iPhone 15 series trở đi Apple bắt đầu dùng USB-C
        if (
            "iphone 15" in device_lower
            or "iphone 16" in device_lower
            or "iphone 17" in device_lower
        ):
            usb_c = 1
        else:
            usb_c = 0

        # 2. Phân loại mạng (5G = 1, 4G = 0)
        # Từ iPhone 12 series trở đi hỗ trợ mạng 5G
        if (
            "iphone 12" in device_lower
            or "iphone 13" in device_lower
            or "iphone 14" in device_lower
            or "iphone 15" in device_lower
            or "iphone 16" in device_lower
            or "iphone 17" in device_lower
        ):
            is_5g = 1
        else:
            is_5g = 0

        # Trường hợp ngoại lệ đặc biệt của dòng iPhone SE
        if "iphone se" in device_lower:
            # Chỉ có SE 3 (bản năm 2022) mới hỗ trợ 5G, còn SE 1 và SE 2 chỉ có 4G
            if "3rd gen" in device_lower or "2022" in device_lower:
                is_5g = 1
            else:
                is_5g = 0

        return pd.Series([usb_c, is_5g])

    # Áp dụng hàm trực tiếp vào cột Device_Model để sinh ra 2 cột mới
    df[["USB_C", "Network_5G"]] = df["Device_Model"].apply(add_features)

    # Lưu đè lại vào chính file Excel đó với đầy đủ dữ liệu mới
    df.to_excel(EXCEL_FILE, index=False)

    print("\n--- KẾT QUẢ SAU KHI CẬP NHẬT BIẾN SỐ MẠNG & CỔNG SẠC ---")
    print(df.head())
    print(f"\nĐã xử lý xong toàn bộ {len(df)} mẫu iPhone.")
    print(f"Dữ liệu mới đã được lưu thành công vào file: {EXCEL_FILE}")