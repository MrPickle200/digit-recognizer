# Digit Recognizer MVP

Hệ thống nhận diện chữ số viết tay (0-9) trên nền tảng Web, sử dụng FastAPI cho Backend và PyTorch cho Machine Learning. Dự án được thiết kế theo mô hình Client-Server tĩnh, tập trung vào tốc độ phản hồi và tối ưu hóa tài nguyên phần cứng (CPU-only inference).

## Tech Stack
- **Frontend:** HTML5 Canvas, Vanilla JavaScript, CSS3.
- **Backend:** Python 3.x, FastAPI, Uvicorn.
- **Machine Learning:** PyTorch (CPU version), Pillow, Numpy.
- **Mô hình AI:** Convolutional Neural Network (CNN) huấn luyện trên tập dataset MNIST.

## Cấu trúc thư mục
```text
digit-recognizer/
├── backend/
│   ├── main.py              # Entry point của API (FastAPI)
│   ├── model_handler.py     # Logic tiền xử lý ảnh và load model PyTorch
│   └── weights/             # Chứa file trọng số mô hình
├── frontend/
│   ├── index.html           # Giao diện người dùng
│   ├── style.css            # Stylesheet
│   └── app.js               # Logic bắt sự kiện Canvas và gọi API
├── requirements.txt         # Danh sách thư viện môi trường
└── README.md


