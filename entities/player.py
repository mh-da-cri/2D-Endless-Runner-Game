"""
Player - Nhân vật Knight
Xử lý di chuyển, nhảy (double jump), cúi, dash, và vẽ nhân vật.
Ban đầu dùng hình học placeholder, sau thay bằng sprite.
"""

import pygame
import settings


class Player:
    """Nhân vật chính - Knight."""
    
    def __init__(self):
        """Khởi tạo player tại vị trí bắt đầu."""
        self.x = settings.PLAYER_START_X
        self.y = settings.GROUND_Y - settings.PLAYER_HEIGHT
        self.width = settings.PLAYER_WIDTH
        self.height = settings.PLAYER_HEIGHT
        
        # Physics
        self.vel_y = 0                    # Vận tốc theo trục Y
        self.is_on_ground = True          # Đang đứng trên mặt đất?
        
        # Jump
        self.jump_count = 0               # Số lần đã nhảy (max = MAX_JUMPS)
        
        # Duck / Cúi
        self.is_ducking = False
        
        # Dash
        self.is_dashing = False
        self.dash_timer = 0               # Đếm ngược thời gian dash
        self.dash_cooldown_timer = 0      # Đếm ngược cooldown
        self.can_dash = True
        
        # Hitbox rect (cập nhật mỗi frame)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def jump(self):
        """
        Thực hiện nhảy.
        - Lần 1: nhảy bình thường (JUMP_FORCE)
        - Lần 2: double jump (DOUBLE_JUMP_FORCE, yếu hơn)
        - Không thể nhảy khi đang cúi
        """
        if self.is_ducking:
            return
        
        if self.jump_count < settings.MAX_JUMPS:
            if self.jump_count == 0:
                self.vel_y = settings.JUMP_FORCE
            else:
                self.vel_y = settings.DOUBLE_JUMP_FORCE
            
            self.jump_count += 1
            self.is_on_ground = False
    
    def duck(self, is_pressing):
        """
        Cúi xuống để né chướng ngại vật bay.
        Chỉ có thể cúi khi đang trên mặt đất.
        
        Args:
            is_pressing: True nếu đang giữ phím DOWN
        """
        if is_pressing and self.is_on_ground and not self.is_dashing:
            if not self.is_ducking:
                # Chuyển sang trạng thái cúi
                self.is_ducking = True
                # Điều chỉnh vị trí và kích thước hitbox
                old_height = self.height
                self.height = settings.PLAYER_DUCK_HEIGHT
                self.y += (old_height - self.height)  # Giữ chân ở đúng vị trí
        else:
            if self.is_ducking:
                # Đứng lại
                self.is_ducking = False
                old_height = self.height
                self.height = settings.PLAYER_HEIGHT
                self.y -= (self.height - old_height)  # Giữ chân ở đúng vị trí
    
    def dash(self):
        """
        Thực hiện dash (lao nhanh về phía trước).
        Có cooldown để không spam.
        """
        if self.can_dash and not self.is_ducking and not self.is_dashing:
            self.is_dashing = True
            self.dash_timer = settings.DASH_DURATION
            self.can_dash = False
            self.dash_cooldown_timer = settings.DASH_COOLDOWN
    
    def apply_gravity(self):
        """Áp dụng trọng lực mỗi frame."""
        if not self.is_dashing:  # Không rơi khi đang dash (giữ nguyên độ cao)
            self.vel_y += settings.GRAVITY
            self.y += self.vel_y
        
        # Kiểm tra chạm đất
        ground_contact_y = settings.GROUND_Y - self.height
        if self.y >= ground_contact_y:
            self.y = ground_contact_y
            self.vel_y = 0
            self.is_on_ground = True
            self.jump_count = 0
        else:
            self.is_on_ground = False
    
    def update(self):
        """Cập nhật trạng thái player mỗi frame."""
        # Gravity
        self.apply_gravity()
        
        # Dash timer
        if self.is_dashing:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False
        
        # Dash cooldown
        if not self.can_dash:
            self.dash_cooldown_timer -= 1
            if self.dash_cooldown_timer <= 0:
                self.can_dash = True
        
        # Cập nhật hitbox
        self.rect.update(self.x, self.y, self.width, self.height)
    
    def draw(self, screen):
        """
        Vẽ player lên màn hình.
        Ban đầu dùng hình chữ nhật placeholder, sau thay bằng sprite.
        
        Args:
            screen: pygame.Surface - màn hình game
        """
        if self.is_dashing:
            # Vẽ hiệu ứng dash (hơi trong suốt + trail)
            self._draw_dash_effect(screen)
        
        # Thân knight (hình chữ nhật chính)
        body_color = settings.COLOR_PLAYER
        pygame.draw.rect(screen, body_color, self.rect, border_radius=4)
        
        # Phần mũ giáp (visor) - phần trên
        visor_height = 15 if not self.is_ducking else 10
        visor_rect = pygame.Rect(
            self.x, self.y,
            self.width, visor_height
        )
        pygame.draw.rect(screen, settings.COLOR_PLAYER_VISOR, visor_rect, border_radius=4)
        
        # Vẽ mắt (2 chấm nhỏ)
        eye_y = self.y + (8 if not self.is_ducking else 5)
        pygame.draw.circle(screen, settings.COLOR_WHITE, (self.x + 30, eye_y), 3)
        pygame.draw.circle(screen, settings.COLOR_WHITE, (self.x + 40, eye_y), 3)
        
        # Viền outline
        pygame.draw.rect(screen, settings.COLOR_BLACK, self.rect, 2, border_radius=4)
        
        # Indicator trạng thái
        if self.is_ducking:
            # Vẽ mũi tên xuống nhỏ
            arrow_x = self.x + self.width // 2
            arrow_y = self.y - 10
            pygame.draw.polygon(screen, settings.COLOR_SCORE, [
                (arrow_x - 5, arrow_y - 5),
                (arrow_x + 5, arrow_y - 5),
                (arrow_x, arrow_y + 2)
            ])
        
        # Cooldown indicator cho dash
        if not self.can_dash:
            cooldown_ratio = self.dash_cooldown_timer / settings.DASH_COOLDOWN
            bar_width = self.width * (1 - cooldown_ratio)
            bar_rect = pygame.Rect(self.x, self.y - 8, bar_width, 4)
            pygame.draw.rect(screen, settings.COLOR_SCORE, bar_rect)
    
    def _draw_dash_effect(self, screen):
        """Vẽ hiệu ứng afterimage khi dash."""
        for i in range(3):
            alpha = 40 - (i * 12)
            trail_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            trail_surface.fill((*settings.COLOR_PLAYER, max(alpha, 0)))
            trail_x = self.x - (i + 1) * 15
            screen.blit(trail_surface, (trail_x, self.y))
    
    def get_rect(self):
        """
        Trả về hitbox hiện tại của player.
        
        Returns:
            pygame.Rect: Hitbox thu nhỏ hơn visual một chút (forgiving collision)
        """
        # Hitbox nhỏ hơn visual 4px mỗi bên → collision "dễ chịu" hơn
        shrink = 4
        return pygame.Rect(
            self.rect.x + shrink,
            self.rect.y + shrink,
            self.rect.width - shrink * 2,
            self.rect.height - shrink * 2
        )
    
    def reset(self):
        """Reset player về trạng thái ban đầu (khi chơi lại)."""
        self.y = settings.GROUND_Y - settings.PLAYER_HEIGHT
        self.height = settings.PLAYER_HEIGHT
        self.width = settings.PLAYER_WIDTH
        self.vel_y = 0
        self.is_on_ground = True
        self.jump_count = 0
        self.is_ducking = False
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.can_dash = True
        self.rect.update(self.x, self.y, self.width, self.height)
