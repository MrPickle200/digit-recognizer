from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.model_handler import preprocess_image, predict_digit_from_array, fine_tune_model, WEIGHTS_PATH, model, torch
from backend.database import supabase, get_pending_feedbacks_for_admin, upload_feedback_image, save_feedback_record, get_untrained_feedback, mark_feedback_trained, upload_weights, download_latest_weights
from backend.auth import create_access_token, verify_token, verify_password
from contextlib import asynccontextmanager
import uuid
import uvicorn
import threading

training_lock = threading.Lock()
RETRAIN_THRESHOLD = 5
    
def background_retrain_task():
    if not training_lock.acquire(blocking= False):
        print("[THÔNG BÁO] Model đang được train, bỏ qua yêu cầu này.")
        return 
    try:
        data = get_untrained_feedback(limit = RETRAIN_THRESHOLD)
        if len(data) >= RETRAIN_THRESHOLD:
            print(f"[THÔNG BÁO] Bắt đàu retrain với {len(data)} mẫu dữ liệu...")
            train_ids = fine_tune_model(data)
            upload_weights(str(WEIGHTS_PATH))
            mark_feedback_trained(train_ids)
    finally:
        training_lock.release()

@asynccontextmanager 
async def life_span(app : FastAPI):
    print("[THÔNG BÁO] Khởi động hệ thống")
    download_latest_weights(str(WEIGHTS_PATH))
    try:
        model.load_state_dict(torch.load(str(WEIGHTS_PATH), map_location= torch.device("cpu")))
        model.eval()
        print("[THÔNG BÁO] Model đã được nạp trọng số mới nhất")
    except Exception as e:
        print("[LỖI] Lỗi khi nạp trọng số mới nhất")
    yield
    print("[THÔNG BÁO] Tắt hệ thống")

app = FastAPI(lifespan= life_span)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/admin/login")
def admin_login(username : str = Form(...), password : str = Form(...)):
    response = supabase.table("admin_users").select("*").eq("user_name", username).execute()
    users = response.data
    if not users or len(users) == 0:
        return {"error" : "Sai tài khoản hoặc mật khẩu"}
    user = users[0]
    if not verify_password(password, user["hashed_password"]):
        return {"error" : "Sai mật khẩu"}    
    token = create_access_token(data = {"sub" : username, "role" : user["role"]})
    return {"access_token" : token, "token_type" : "Bearer"}

@app.get("/admin/feedbacks")
def get_pending_feedbacks(admin_data : dict = Depends(verify_token)):
    print(f"[THÔNG BÁO] Admin {admin_data['sub']} đang truy cập")
    data = get_pending_feedbacks_for_admin()
    return {"status" : "success", "data" : data}

@app.put("/admin/feedbacks/{feedback_id}/approve")
def approve_feedback(
    feedback_id : int,
    background_tasks : BackgroundTasks,
    admin_data : dict = Depends(verify_token)
):
    try:
        supabase.table("digit_feedbacks").update({"status": "approved"}).eq("id", feedback_id).execute()
        background_tasks.add_task(background_retrain_task)
        return {"status" : "success", "message" : "Đã duyệt và đưa vào hàng chờ huấn luyện"}
    except Exception as e:
        return {"status" : "error", "message" : f"{e}"}
    
@app.put("/admin/feedbacks/{feedback_id}/reject")
def reject_feedback(
    feedback_id : int,
    admin_data : dict = Depends(verify_token)
):
    try:
        supabase.table("digit_feedbacks").update({"status": "rejected"}).eq("id", feedback_id).execute()
        return {"status" : "success", "message" : "Đã loại ảnh rác"}
    except Exception as e:
        return {"status" : "error", "message" : f"{e}"}

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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    predicted: int = Form(...),
    actual: int = Form(...),
    confidence: float = Form(...)
):
    try:
        if predicted == actual:
            return {"status" : "success", "message" : "Cảm ơn bạn đã giúp model tốt hơn!"} 
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