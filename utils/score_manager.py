"""
Score Manager - Quản lý đọc/ghi điểm cao nhất
Lưu trữ highscore vào file JSON trong thư mục data/.
"""

import os
import json
import settings


def load_highscore():
    """
    Đọc điểm cao nhất từ file JSON.
    
    Returns:
        int: Điểm cao nhất, trả về 0 nếu file chưa tồn tại
    """
    try:
        with open(settings.HIGHSCORE_FILE, "r") as f:
            data = json.load(f)
            return data.get("highscore", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def save_highscore(score):
    """
    Lưu điểm cao nhất vào file JSON.
    Chỉ lưu nếu score cao hơn highscore hiện tại.
    
    Args:
        score: Điểm số mới
    
    Returns:
        bool: True nếu đã lưu kỷ lục mới, False nếu không
    """
    current_high = load_highscore()
    
    if score > current_high:
        # Đảm bảo thư mục data/ tồn tại
        os.makedirs(os.path.dirname(settings.HIGHSCORE_FILE), exist_ok=True)
        
        with open(settings.HIGHSCORE_FILE, "w") as f:
            json.dump({"highscore": int(score)}, f, indent=2)
        
        return True
    
    return False
