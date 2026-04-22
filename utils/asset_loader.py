"""
Asset Loader - Hàm tiện ích để load tài nguyên game
Load ảnh và âm thanh từ thư mục assets/, xử lý lỗi nếu file không tồn tại.
"""

import os
import pygame
import settings


def load_image(filename, scale=None, convert_alpha=True):
    """
    Load một ảnh từ thư mục assets/images/.
    
    Args:
        filename: Tên file ảnh (VD: 'knight.png')
        scale: Tuple (width, height) để resize, None = giữ nguyên
        convert_alpha: True nếu ảnh có nền trong suốt
    
    Returns:
        pygame.Surface: Ảnh đã load (hoặc placeholder nếu lỗi)
    """
    filepaths = [
        os.path.join("assets", "images", filename),
        os.path.join("assets", filename),
    ]
    
    try:
        image = None
        filepath = filepaths[0]
        for candidate in filepaths:
            filepath = candidate
            if os.path.exists(candidate):
                if convert_alpha:
                    image = pygame.image.load(candidate).convert_alpha()
                else:
                    image = pygame.image.load(candidate).convert()
                break
        
        if image is None:
            raise FileNotFoundError(filepath)
        
        if scale:
            image = pygame.transform.scale(image, scale)
        
        return image
    
    except (pygame.error, FileNotFoundError):
        # Tạo placeholder surface nếu không tìm thấy file
        print(f"[WARNING] Không tìm thấy ảnh: {filepath} - Dùng placeholder")
        width = scale[0] if scale else 50
        height = scale[1] if scale else 50
        placeholder = pygame.Surface((width, height), pygame.SRCALPHA)
        placeholder.fill((255, 0, 255, 180))  # Màu hồng neon = dễ nhận biết placeholder
        return placeholder


def load_sound(filename):
    """
    Load một file âm thanh từ thư mục assets/audio/.
    
    Args:
        filename: Tên file âm thanh (VD: 'jump.wav')
    
    Returns:
        pygame.mixer.Sound hoặc None nếu lỗi
    """
    filepath = os.path.join("assets", "audio", filename)
    
    try:
        sound = pygame.mixer.Sound(filepath)
        return sound
    except (pygame.error, FileNotFoundError):
        print(f"[WARNING] Không tìm thấy âm thanh: {filepath} - Bỏ qua")
        return None


def play_sound(sound, volume=0.5):
    """
    Phát một âm thanh nếu nó tồn tại.
    
    Args:
        sound: pygame.mixer.Sound hoặc None
        volume: Âm lượng từ 0.0 đến 1.0
    """
    if sound:
        sound.set_volume(volume)
        sound.play()


def load_font(size, font_name=None):
    """
    Load font chữ.
    
    Args:
        size: Kích thước font
        font_name: Tên font (None = font mặc định của Pygame)
    
    Returns:
        pygame.font.Font
    """
    try:
        if font_name:
            return pygame.font.SysFont(font_name, size)
        else:
            return pygame.font.Font(None, size)
    except Exception:
        return pygame.font.Font(None, size)
