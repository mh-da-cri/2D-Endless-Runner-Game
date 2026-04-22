import pygame
import math
import settings

class CounterShieldPickup:
    """Item đặc biệt - nhặt để nhận khiên phản đạn thần thánh."""
    
    def __init__(self, game_speed):
        """
        Khởi tạo item counter shield.
        
        Args:
            game_speed: Tốc độ game hiện tại để di chuyển
        """
        self.width = settings.COUNTER_SHIELD_SIZE
        self.height = settings.COUNTER_SHIELD_SIZE
        self.x = settings.SCREEN_WIDTH + 50
        
        # Lơ lửng trên không trung, độ cứng thấp để dễ nhặt
        import random
        self.y = random.randint(settings.GROUND_Y - 250, settings.GROUND_Y - 100)
        self.base_y = self.y
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.time = 0
    
    def update(self, game_speed):
        """Cập nhật vị trí item mỗi frame."""
        self.x -= game_speed * 1.5 # Trôi bay vèo vào cho người ta nhặt
        self.rect.x = int(self.x)
        # Hiệu ứng lơ lửng
        self.time += 0.1
        self.y = self.base_y + math.sin(self.time) * 15
        self.rect.y = int(self.y)
    
    def draw(self, screen):
        """Vẽ item với hiệu ứng hào quang."""
        cx = int(self.x + self.width // 2)
        cy = int(self.y + self.height // 2)
        
        # Hào quang ngoài (nhấp nháy mạnh)
        gr = self.width // 2 + 10 + int(math.sin(self.time * 3) * 6)
        gs = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
        ga = int(80 + 40 * math.sin(self.time * 5))
        pygame.draw.circle(gs, (*settings.COLOR_COUNTER_SHIELD_GLOW, ga), (gr, gr), gr)
        screen.blit(gs, (cx - gr, cy - gr))
        
        # Quả cầu chính (hình khiên lục giác sẽ đẹp hơn, nhưng ta vẽ hình thoi để đơn giản)
        points = [
            (cx, cy - self.height//2),
            (cx + self.width//2, cy),
            (cx, cy + self.height//2),
            (cx - self.width//2, cy)
        ]
        pygame.draw.polygon(screen, settings.COLOR_COUNTER_SHIELD, points)
        pygame.draw.polygon(screen, settings.COLOR_WHITE, points, 2)
        
        # Ký hiệu bên trong
        pygame.draw.circle(screen, settings.COLOR_WHITE, (cx, cy), self.width // 4)
        
        # Nhãn "COUNTER" phía trên
        font = pygame.font.Font(None, 16)
        label = font.render("COUNTER", True, settings.COLOR_COUNTER_SHIELD_GLOW)
        screen.blit(label, label.get_rect(center=(cx, cy - self.height//2 - 12)))
    
    def get_rect(self):
        """Trả về hitbox."""
        return self.rect
    
    def is_off_screen(self):
        """Kiểm tra item đã ra khỏi màn hình chưa."""
        return self.x < -self.width
