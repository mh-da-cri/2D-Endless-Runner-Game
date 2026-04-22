import pygame
import settings

class BossBullet:
    """Đạn của Boss bắn ra."""
    
    def __init__(self, x, y, vel_x, vel_y, requires_dash=False):
        """
        Khởi tạo đạn boss.
        
        Args:
            x, y: Vị trí xuất phát
            vel_x, vel_y: Vận tốc theo 2 trục
            requires_dash: True nếu bắt buộc phải dash qua
        """
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.radius = settings.BOSS_BULLET_SIZE
        self.requires_dash = requires_dash
        self.is_countered = False
        
        # Hitbox (vẽ to hơn một chút so với bán kính vật lí nhưng hitbox chuẩn là hình vuông bao quanh)
        self.rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), 
                               self.radius * 2, self.radius * 2)
    
    def update(self):
        """Cập nhật vị trí đạn."""
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Cập nhật hitbox
        self.rect.x = int(self.x - self.radius)
        self.rect.y = int(self.y - self.radius)
        
    def counter(self):
        """Bị player phản lại boss."""
        self.is_countered = True
        self.vel_x = max(10, abs(self.vel_x) * 2)  # Bay ngược lại thật nhanh, đảm bảo bay ngang kể cả khi đang rơi dọc
        self.vel_y = 0                    # Bay thẳng ngang
        self.requires_dash = False        # Hết nguy hiểm
        
    def draw(self, screen):
        """Vẽ đạn."""
        if self.is_countered:
            color = settings.COLOR_COUNTERED_BULLET
        elif self.requires_dash:
            color = settings.COLOR_BOSS_BULLET_DASH
        else:
            color = settings.COLOR_BOSS_BULLET
            
        cx, cy = int(self.x), int(self.y)
        
        # Vẽ glow
        glow_radius = self.radius + 6
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, 80), (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surf, (cx - glow_radius, cy - glow_radius))
        
        # Lõi sáng
        pygame.draw.circle(screen, color, (cx, cy), self.radius)
        pygame.draw.circle(screen, settings.COLOR_WHITE, (cx, cy), max(2, self.radius - 4))
        
    def get_rect(self):
        """Hitbox cho logic va chạm."""
        # Bóp hitbox nhỏ lại 1 chút để "dễ thở" hơn cho người chơi
        shrink = 4
        return self.rect.inflate(-shrink * 2, -shrink * 2)
        
    def is_off_screen(self):
        """Kiểm tra đạn ra khỏi màn hình."""
        if self.is_countered:
            return self.x > settings.SCREEN_WIDTH + 100
        else:
            return self.x < -50 or self.y < -50 or self.y > settings.SCREEN_HEIGHT + 50
