import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def upload_feedback_image(image_bytes: bytes, filename: str):
    """Đẩy ảnh lên Supabase Storage"""
    res = supabase.storage.from_('digit-images').upload(
        path=filename,
        file=image_bytes,
        file_options={"content-type": "image/png"}
    )
    # Lấy URL công khai để lưu vào Table
    return supabase.storage.from_('digit-images').get_public_url(filename)

def save_feedback_record(img_url: str, predicted: int, actual: int, confidence: float):
    """Lưu thông tin nhãn đúng vào Postgres Table"""
    data = {
        "image_url": img_url,
        "predicted_label": predicted,
        "actual_label": actual,
        "confidence": confidence
    }
    supabase.table("digit_feedbacks").insert(data).execute()

def get_untrained_feedback(limit : int = 10):
    res = supabase.table("digit_feedbacks").select("*").eq("status", "approved").limit(limit).execute()
    return res.data

def mark_feedback_trained(feedback_ids : list):
    if not feedback_ids:
        return
    supabase.table("digit_feedbacks").update({"status" : "trained"}).in_("id", feedback_ids).execute()

def get_pending_feedbacks_for_admin(limit : int = 50):
    res = supabase.table("digit_feedbacks").select("*").eq("status", "pending").order("created_at", desc = True).limit(limit).execute()
    return res.data if res.data is not None else [] 

def download_latest_weights(local_path: str):
    """Tải file trọng số mới nhất từ Supabase về máy"""
    try:
        with open(local_path, 'wb') as f:
            res = supabase.storage.from_('digit-weights').download('simple_cnn.pth')
            f.write(res)
        print(f"[THÔNG BÁO] Đã tải trọng số mới nhất từ Supabase về {local_path}")
    except Exception as e:
        print(f"[LỖI] Không tìm thấy trọng số trên Supabase hoặc lỗi: {e}. Sử dụng trọng số mặc định.")

def upload_weights(local_path: str):
    """Đẩy file trọng số sau khi train lên Supabase (Ghi đè bản cũ)"""
    try:
        with open(local_path, 'rb') as f:
            # Dùng file_options={"upsert": "true"} để ghi đè file cũ cùng tên
            supabase.storage.from_('digit-weights').upload(
                path='simple_cnn.pth',
                file=f,
                file_options={"x-upsert": "true", "content-type": "application/octet-stream"}
            )
        print("[THÔNG BÁO] Đã sao lưu trọng số mới lên Supabase Storage thành công.")
    except Exception as e:
        print(f"[LỖI] Lỗi khi backup trọng số: {e}")