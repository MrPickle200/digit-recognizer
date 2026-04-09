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
    supabase.table("digit_feedback").insert(data).execute()