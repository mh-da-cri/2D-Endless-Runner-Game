"""
Companion Pickup - Item đặc biệt trao đồng hành cho người chơi.
Xuất hiện tại các mốc điểm cụ thể (200, 500).
"""

import pygame
import math
import settings


class CompanionPickup:
    """Item đặc biệt - nhặt để nhận đồng hành."""
    
    def __init__(self, game_speed):
        """
        Khởi tạo item đồng hành.
        
        Args:
            game_speed: Tốc độ game hiện tại để di chuyển
        """
        self.width = settings.COMPANION_PICKUP_SIZE
        self.height = settings.COMPANION_PICKUP_SIZE
        self.x = settings.SCREEN_WIDTH + 50
        self.y = settings.GROUND_Y - 100  # Lơ lửng trên mặt đất
        self.base_y = self.y
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.time = 0
    
    def update(self, game_speed):
        """Cập nhật vị trí item mỗi frame."""
        self.x -= game_speed
        self.rect.x = self.x
        # Hiệu ứng lơ lửng
        self.time += 0.08
        self.y = self.base_y + math.sin(self.time) * 8
        self.rect.y = self.y
    
    def draw(self, screen):
        """Vẽ item đồng hành với hiệu ứng hào quang vàng."""
        cx = int(self.x + self.width // 2)
        cy = int(self.y + self.height // 2)
        
        # Hào quang ngoài (nhấp nháy)
        gr = self.width // 2 + 8 + int(math.sin(self.time * 2) * 4)
        gs = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
        ga = int(60 + 30 * math.sin(self.time * 3))
        pygame.draw.circle(gs, (*settings.COLOR_COMPANION_PICKUP_GLOW, ga), (gr, gr), gr)
        screen.blit(gs, (cx - gr, cy - gr))
        
        # Quả cầu chính
        pygame.draw.circle(screen, settings.COLOR_COMPANION_PICKUP, (cx, cy), self.width // 2)
        
        # Điểm sáng bên trong
        pygame.draw.circle(screen, settings.COLOR_COMPANION_PICKUP_GLOW,
                          (cx - 3, cy - 3), self.width // 4)
        
        # Ngôi sao trang trí
        size = 6
        points = []
        for i in range(5):
            a = math.radians(i * 72 - 90)
            points.append((cx + math.cos(a)*size, cy + math.sin(a)*size))
            a2 = math.radians(i * 72 + 36 - 90)
            points.append((cx + math.cos(a2)*size*0.4, cy + math.sin(a2)*size*0.4))
        pygame.draw.polygon(screen, settings.COLOR_WHITE, points)
        
        # Nhãn "ALLY" phía trên
        font = pygame.font.Font(None, 18)
        label = font.render("ALLY", True, settings.COLOR_COMPANION_PICKUP)
        screen.blit(label, label.get_rect(center=(cx, cy - self.height//2 - 12)))
    
    def get_rect(self):
        """Trả về hitbox cho phát hiện va chạm."""
        return self.rect
    
    def is_off_screen(self):
        """Kiểm tra item đã ra khỏi màn hình chưa."""
        return self.x < -self.width
