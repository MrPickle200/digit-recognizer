# Digit Recognizer MVP - Active Learning System

Hệ thống nhận diện chữ số viết tay (0-9) đa nền tảng (PC & Mobile). Dự án không chỉ dừng lại ở việc dự đoán mà còn tích hợp vòng lặp phản hồi (Feedback Loop) và khả năng tự động huấn luyện lại (Background Retraining) để liên tục cải thiện độ chính xác thông qua dữ liệu người dùng.

## Kiến trúc Hệ thống
- **Frontend:** Vanilla JS, HTML5 Canvas (Tối ưu hóa Touch Event cho Mobile).
- **Backend:** FastAPI, PyTorch (CPU-only Inference & Fine-tuning).
- **Database & Storage:** Supabase (PostgreSQL & Object Storage).
- **Cơ chế đặc biệt:** - *Hot-swap Weights:* Trọng số Model được lưu trữ bền vững trên Supabase và tự động đồng bộ xuống RAM khi khởi động (Lifespan events).
  - *Mutex Lock:* Khóa luồng an toàn chống tràn bộ nhớ (OOM) khi kích hoạt tiến trình Retrain dưới nền (Background Tasks).

## Cấu trúc thư mục
```text
digit-recognizer/
├── .env                     # BẮT BUỘC: Biến môi trường Supabase (KHÔNG PUSH LÊN GIT)
├── requirements.txt         # Danh sách thư viện (FastAPI, PyTorch, Supabase...)
├── backend/
│   ├── main.py              # API Endpoints & Lifespan/Background Tasks
│   ├── database.py          # Logic tương tác Supabase (Upload, Insert, Download)
│   ├── model_handler.py     # Định nghĩa CNN, Preprocessing và Fine-tuning
│   └── weights/             # Nơi lưu trữ cache file simple_cnn.pth ở Local
└── frontend/
    ├── index.html           # Giao diện người dùng
    ├── style.css            # Stylesheet (Chống cuộn trang trên mobile)
    └── app.js               # Logic vẽ Canvas và gọi API
```

## Yêu cầu thiết lập Supabase (Bắt buộc trước khi chạy)
Hệ thống yêu cầu một project Supabase đã được cấu hình sẵn:
1. **Database Table:** Tạo bảng `digit_feedback` gồm các cột: `id` (int8), `image_url` (text), `predicted_label` (int4), `actual_label` (int4), `confidence` (float8), `is_trained` (boolean, default: false).
2. **Storage Buckets:** - `digit-images`: Public bucket (Lưu ảnh feedback).
   - `digit-weights`: Private bucket (Lưu file `simple_cnn.pth` dùng để backup model).

## Hướng dẫn cài đặt (Local Development)

### Bước 1: Thiết lập Môi trường & Backend
1. Clone repository về máy và mở terminal tại thư mục gốc.
2. Tạo môi trường ảo và cài đặt thư viện:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Trên Windows dùng: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Tạo file `.env` tại thư mục gốc và điền thông tin (Sử dụng Service Role Key để bypass RLS):
   ```text
   SUPABASE_URL=https://<your-project-id>.supabase.co
   SUPABASE_KEY=<your-service-role-key>
   ```
4. Đảm bảo file trọng số khởi tạo `simple_cnn.pth` đã được upload lên bucket `digit-weights` trên Supabase.
5. Khởi chạy server:
   ```bash
   uvicorn backend.main:app --reload
   ```
   *Khi khởi động, server sẽ tự động tải file `.pth` mới nhất từ mây về máy.*

### Bước 2: Khởi chạy Frontend
Sử dụng Live Server extension trên VS Code để mở file `frontend/index.html` hoặc mở trực tiếp trên trình duyệt.

## API Endpoints
- `POST /predict`: Nhận ảnh từ Canvas, trả về số dự đoán và % tự tin.
- `POST /feedback`: Ghi nhận dữ liệu sai từ người dùng, đẩy ảnh lên mây. Nếu số lượng bản ghi `is_trained = false` đạt ngưỡng, sẽ tự động kích hoạt tiến trình Fine-tune ngầm, cập nhật model và sao lưu trọng số mới lên Supabase.
```
