from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from backend.model_handler import preprocess_image, predict_digit_from_array
from backend.database import upload_feedback_image, save_feedback_record
import uuid
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
        if float(confidence) < 0.4:
            return {
                "message" : f"Hình vẽ quấ xấu họăc không hợp lệ. Độ tự tin: {float(confidence)}"
                }

        return {
            "prediction" : int(digit),
            "confidence" : float(confidence),
            "message" : f"{digit} - Tự tin: {float(confidence) * 100:.2f}%"
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/feedback")
async def receive_feedback(
    file: UploadFile = File(...),
    predicted: int = Form(...),
    actual: int = Form(...),
    confidence: float = Form(...)
):
    try:
        image_bytes = await file.read()
        filename = f"rev_{uuid.uuid4()}.png"
        
        # 1. Lưu ảnh lên Storage
        img_url = upload_feedback_image(image_bytes, filename)
        
        # 2. Lưu record vào Database
        save_feedback_record(img_url, predicted, actual, confidence)
        
        return {"status": "success", "message": "Cảm ơn bạn đã giúp model tốt hơn!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)