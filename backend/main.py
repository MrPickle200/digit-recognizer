from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from backend.model_handler import preprocess_image, predict_digit_from_array # Import hàm vừa viết
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict")
async def predict_digit(file: UploadFile = File(...)):
    try:
        # Đọc dữ liệu ảnh thành dạng byte
        image_bytes = await file.read()
        
        # Tiền xử lý
        img_array, _ = preprocess_image(image_bytes)
        if img_array.sum() == 0:
            return {
                "message" : "Hãy vẽ gì đó"
            }
        
        digit, confidence = predict_digit_from_array(img_array)
        if float(confidence) < 0.6:
            return {
                "message" : "Hình vẽ quấ xấu họăc không hợp lệ"
                }

        return {
            "prediction" : int(digit),
            "confidence" : float(confidence),
            "message" : f"{digit} - Tự tin: {float(confidence) * 100:.2f}%"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)