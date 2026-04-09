import io
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import requests
from torchvision import transforms
from PIL import Image, ImageOps
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WEIGHTS_PATH = BASE_DIR / "weights" / "simple_cnn.pth"

class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.layers = nn.Sequential(
            nn.Linear(28 * 28, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 10)
        )

    def forward(self, x):
        x = self.flatten(x)
        pred = self.layers(x)
        return pred
    

# Khởi tạo model và load trọng số
model = SimpleCNN()

try:
    model.load_state_dict(torch.load(str(WEIGHTS_PATH), map_location= torch.device("cpu")))
    model.eval()
    print("[THÔNG BÁO] Load trọng số mặc định thành công")
except:
    print("[THÔNG BÁO] Chưa tìm thấy file weights, khởi tạo trọng số ngẫu nhiên")


def preprocess_image(image_bytes: bytes):
    """
    Biến đổi ảnh raw từ Canvas thành chuẩn MNIST (28x28, nét trắng nền đen, căn giữa)
    """
    # 1. Đọc ảnh từ binary và chuyển sang Grayscale (ảnh xám 1 kênh màu)
    img = Image.open(io.BytesIO(image_bytes)).convert('L')
    
    # 2. Đảo màu (Invert): Nét đen nền trắng -> Nét trắng nền đen
    img = ImageOps.invert(img)
    
    # 3. Tìm Bounding Box: Cắt bỏ sạch sẽ phần viền đen tĩnh lặng xung quanh
    # Chỉ lấy khung chữ nhật chứa đúng nét vẽ
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
        
    # 4. Thu nhỏ (Resize) phần nét vẽ vừa cắt.
    # MNIST chuẩn chứa chữ số trong một khung tối đa 20x20 pixel.
    # Dùng thumbnail để giữ nguyên tỷ lệ (aspect ratio) không bị méo hình.
    img.thumbnail((20, 20), Image.Resampling.LANCZOS)
    
    # 5. Căn giữa (Padding): Tạo một phông nền đen chuẩn 28x28
    new_img = Image.new('L', (28, 28), color=0) # color=0 là màu đen
    
    # Tính toán tọa độ (x, y) để dán phần nét vẽ vào chính giữa phông nền đen
    paste_x = (28 - img.width) // 2
    paste_y = (28 - img.height) // 2
    new_img.paste(img, (paste_x, paste_y))
    
    # Chuyển ảnh thành mảng Numpy để chuẩn bị feed vào Model
    img_array = np.array(new_img)
    
    # Trả về cả mảng data và ảnh PIL để test
    return img_array, new_img


def predict_digit_from_array(img_array):
    # 1. Chuyển mảng numpy về dạng Tensor và Normalize về khoảng [0, 1]
    # MNIST yêu cầu đầu vào là (BatchSize, Channel, Height, Width) -> (1, 1, 28, 28)
    img_tensor = torch.from_numpy(img_array).float() / 255.0
    img_tensor = img_tensor.unsqueeze(0).unsqueeze(0) 

    # 2. Thực hiện dự đoán, không tính toán gradient để tiết kiệm RAM/CPU
    with torch.no_grad():
        output = model(img_tensor)
        
        # Lấy chỉ số (index) của giá trị lớn nhất trong 10 đầu ra
        prediction = torch.argmax(output, dim=1).item()
        
        # Tính toán độ tự tin (confidence) bằng Softmax
        probabilities = F.softmax(output, dim=1)
        confidence = probabilities[0][prediction].item()

    return prediction, confidence


def fine_tune_model(feedback_data):
    """Hàm chạy ngầm để huấn luyện lại model"""
    global model # Sử dụng model đang load trên RAM
    
    # 1. Chuẩn bị dữ liệu
    images = []
    labels = []
    ids = []
    
    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((28, 28)),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])

    for item in feedback_data:
        try:
            # Tải ảnh từ Supabase URL
            response = requests.get(item['image_url'])
            img = Image.open(io.BytesIO(response.content))
            img_tensor = transform(img)
            
            images.append(img_tensor)
            labels.append(item['actual_label'])
            ids.append(item['id'])
        except Exception as e:
            print(f"Lỗi tải ảnh {item['id']}: {e}")
            continue

    if not images: return []

    # Chuyển thành Batch Tensor
    X = torch.stack(images)
    y = torch.tensor(labels, dtype=torch.long)

    # 2. Cài đặt Training
    model.train() # Bật chế độ train
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    # Chỉ chạy 2 Epochs để tiết kiệm tài nguyên
    for _ in range(2):
        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()

    # 3. Lưu model mới & Trả lại chế độ dự đoán
    torch.save(model.state_dict(), WEIGHTS_PATH)
    model.eval()
    
    print(f"[THÔNG BÁO] Đã fine-tune thành công với {len(ids)} ảnh mới.")
    return ids