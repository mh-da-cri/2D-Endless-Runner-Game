"""
Fireball - Đạn cầu lửa cho skill của Sorcerer
Bắn từ vị trí nhân vật, di chuyển sang phải, phá hủy chướng ngại vật.
"""

import pygame
import math
import settings


class Fireball:
    """Quả cầu lửa - Skill của Sorcerer."""
    
    def __init__(self, x, y, offset_y=0):
        """
        Khởi tạo fireball tại vị trí chỉ định.
        
        Args:
            x: Tọa độ X ban đầu (vị trí player)
            y: Tọa độ Y ban đầu (vị trí player)
            offset_y: Offset dọc để tạo spread giữa các fireball
        """
        self.x = x
        self.y = y + offset_y
        self.radius = settings.FIREBALL_SIZE
        self.speed = settings.FIREBALL_SPEED
        
        # Hitbox
        self.rect = pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2, self.radius * 2
        )
        
        # Animation
        self.time = 0
        self.alive = True
        
        # Trail particles
        self.trail = []
    
    def update(self):
        """Cập nhật vị trí fireball mỗi frame."""
        if not self.alive:
            return
        
        self.time += 1
        
        # Di chuyển sang phải
        self.x += self.speed
        
        # Cập nhật hitbox
        self.rect.x = self.x - self.radius
        self.rect.y = self.y - self.radius
        
        # Thêm trail particle
        self.trail.append({
            'x': self.x,
            'y': self.y,
            'life': 15,  # Số frame tồn tại
            'radius': self.radius * 0.8
        })
        
        # Cập nhật trail
        for particle in self.trail:
            particle['life'] -= 1
            particle['radius'] *= 0.9
        
        # Xóa particle hết life
        self.trail = [p for p in self.trail if p['life'] > 0]
    
    def draw(self, screen):
        """Vẽ fireball với hiệu ứng lửa."""
        if not self.alive:
            return
        
        # Vẽ trail (phía sau)
        for particle in self.trail:
            alpha = int(255 * (particle['life'] / 15))
            r = max(1, int(particle['radius']))
            trail_surface = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            color = (*settings.COLOR_FIREBALL, min(alpha, 150))
            pygame.draw.circle(trail_surface, color, (r, r), r)
            screen.blit(trail_surface, (particle['x'] - r, particle['y'] - r))
        
        # Vẽ outer glow
        glow_radius = self.radius + 5 + int(math.sin(self.time * 0.3) * 3)
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surface, (*settings.COLOR_FIREBALL, 80),
            (glow_radius, glow_radius), glow_radius
        )
        screen.blit(glow_surface, (self.x - glow_radius, self.y - glow_radius))
        
        # Vẽ fireball chính (outer)
        pygame.draw.circle(screen, settings.COLOR_FIREBALL, (int(self.x), int(self.y)), self.radius)
        
        # Vẽ lõi sáng (inner core)
        core_radius = max(1, self.radius // 2)
        pygame.draw.circle(screen, settings.COLOR_FIREBALL_CORE, (int(self.x), int(self.y)), core_radius)
    
    def get_rect(self):
        """Trả về hitbox cho collision detection."""
        return self.rect
    
    def is_off_screen(self):
        """Kiểm tra fireball đã ra khỏi màn hình chưa."""
        return self.x - self.radius > settings.SCREEN_WIDTH
    
    def destroy(self):
        """Đánh dấu fireball đã bị phá hủy."""
        self.alive = False
