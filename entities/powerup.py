import pygame
import random
import settings

class PowerUp:
    """Vật phẩm tăng sức mạnh (Power-up)."""
    
    # Các loại power-up
    TYPES = ['shield', 'double_score', 'slow_down']
    
    def __init__(self, game_speed, x=None):
        """
        Khởi tạo power-up.
        
        Args:
            game_speed: Tốc độ game hiện tại để di chuyển
            x: Vị trí X khởi tạo, nếu None sẽ tự động sinh ở ngoài màng hình bên phải
        """
        self.type = random.choice(self.TYPES)
        self.width = settings.POWERUP_SIZE
        self.height = settings.POWERUP_SIZE
        
        if x is None:
            self.x = settings.SCREEN_WIDTH + random.randint(100, 300)
        else:
            self.x = x
            
        # Vị trí Y: Ngẫu nhiên từ giữa không trung đến gần mặt đất
        self.y = random.randint(settings.GROUND_Y - 150, settings.GROUND_Y - self.height - 20)
        
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Base color based on type
        if self.type == 'shield':
            self.color = settings.COLOR_POWERUP_SHIELD
        elif self.type == 'double_score':
            self.color = settings.COLOR_POWERUP_SCORE
        elif self.type == 'slow_down':
            self.color = settings.COLOR_POWERUP_SLOW
        
        # Sinh ra hiệu ứng nhấp nháy/dao động lên xuống
        self.base_y = self.y
        self.time = 0
            
    def update(self, game_speed):
        """Cập nhật vị trí power-up theo tốc độ game."""
        self.x -= game_speed
        self.rect.x = self.x
        
        # Hiệu ứng nổi bồng bềnh
        self.time += 0.1
        import math
        self.y = self.base_y + math.sin(self.time) * 5
        self.rect.y = self.y
        
    def draw(self, surface):
        """Vẽ power-up."""
        # Vẽ hình thoi hoặc hình tròn thay vì hình vuông
        center = (self.rect.centerx, self.rect.centery)
        radius = self.width // 2
        pygame.draw.circle(surface, self.color, center, radius)
        # Highlight
        pygame.draw.circle(surface, (255, 255, 255), (center[0] - radius // 3, center[1] - radius // 3), radius // 3)
        
    def get_rect(self):
        """Trả về hitbox của power-up."""
        return self.rect
        
    def is_off_screen(self):
        """Kiểm tra xem power-up đã ra khỏi màn hình bên trái chưa."""
        return self.x < -self.width
