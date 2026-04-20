"""
Player - Nhân vật Knight
Xử lý di chuyển, nhảy (double jump), cúi, dash, và vẽ nhân vật.
Ban đầu dùng hình học placeholder, sau thay bằng sprite.
"""

import pygame
import settings
from utils.spritesheet import SpriteSheet
from utils.asset_loader import load_image


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
        self.jump_buffer_timer = 0        # Timer lưu lại nút bấm nhảy
        
        # Duck / Cúi
        self.is_ducking = False
        self.is_dead = False
        
        # Dash
        self.is_dashing = False
        self.dash_timer = 0               # Đếm ngược thời gian dash
        self.dash_cooldown_timer = 0      # Đếm ngược cooldown
        self.can_dash = True
        
        # Hitbox rect (cập nhật mỗi frame)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # --- ANIMATION SETUP ---
        self.sprite_sheet_image = load_image(settings.SPRITE_IMAGE, convert_alpha=True)
        self.sprite_sheet = SpriteSheet(self.sprite_sheet_image)
        
        crouch_img = load_image(settings.SPRITE_CROUCH_IMAGE, convert_alpha=True)
        self.crouch_sheet = SpriteSheet(crouch_img)
        
        dead_img = load_image(settings.SPRITE_DEAD_IMAGE, convert_alpha=True)
        self.dead_sheet = SpriteSheet(dead_img)
        
        self.animations = {
            'idle': [],
            'run': [],
            'jump': [],
            'fall': [],
            'duck': [],
            'dash': [],
            'dead': []
        }
        self._load_animations()
        
        self.frame_index = 0
        self.animation_state = 'idle'
        self.update_time = pygame.time.get_ticks()
        
    def _load_animations(self):
        """Cắt ảnh từ Sprite Sheet."""
        w = settings.SPRITE_FRAME_WIDTH
        h = settings.SPRITE_FRAME_HEIGHT
        s = settings.SPRITE_SCALE
        
        # Idle: Cột 0, Hàng 0
        self.animations['idle'].append(self.sprite_sheet.get_image(0, 0, w, h, s))
        # Jump: Cột 1, Hàng 0
        self.animations['jump'].append(self.sprite_sheet.get_image(1, 0, w, h, s))
        # Fall: Cột 2, Hàng 0
        self.animations['fall'].append(self.sprite_sheet.get_image(2, 0, w, h, s))
        # Run: Cột 3 đến 8, Hàng 0
        for i in range(3, 9):
            self.animations['run'].append(self.sprite_sheet.get_image(i, 0, w, h, s))
            
        # Duck: Lấy từ ảnh crouch độc lập (kích thước gốc 44x44)
        self.animations['duck'].append(self.crouch_sheet.get_image(0, 0, 44, 44, s))
        
        # Dash: Hàng dưới gần chữ của Sprite Sheet (pixel Y = 1768, height=35 để dừng đúng y=1803 là mũi chân hiệp sĩ).
        for i in range(3, 9):
            pixel_x = i * w
            self.animations['dash'].append(self.sprite_sheet.get_image_at(pixel_x, 1768, w, 35, s))
            
        # Dead: Lấy từ ảnh chết độc lập (kích thước gốc 32x64)
        self.animations['dead'].append(self.dead_sheet.get_image(0, 0, 32, 64, s))
    
    def _execute_jump(self):
        """Hàm con thực thi nhảy lập tức khi hợp lệ."""
        if self.jump_count == 0:
            self.vel_y = settings.JUMP_FORCE
        else:
            self.vel_y = settings.DOUBLE_JUMP_FORCE
        
        self.jump_count += 1
        self.is_on_ground = False

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
            self._execute_jump()
        else:
            self.jump_buffer_timer = settings.JUMP_BUFFER_FRAMES
    
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
            
            # Nếu có jump buffer, nhảy ngay lập tức khi vừa chạm đất
            if self.jump_buffer_timer > 0 and not self.is_ducking:
                self._execute_jump()
                self.jump_buffer_timer = 0
        else:
            self.is_on_ground = False
    
    def update(self):
        """Cập nhật physics, logic kiểm tra và hoạt ảnh."""
        if self.is_dead:
            self.animation_state = 'dead'
            return # KHÓA toàn bộ di chuyển khi đã chết
            
        # --- TIMER UPDATES ---dần
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= 1
            
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
        
        # --- ANIMATION LOGIC ---
        # 1. Cập nhật trạng thái
        if self.is_dashing:
            self.animation_state = 'dash'
        elif self.vel_y < 0:
            self.animation_state = 'jump'
        elif self.vel_y > 0 and not self.is_on_ground:
            self.animation_state = 'fall'
        elif self.is_on_ground:
            if self.is_ducking:
                self.animation_state = 'duck'
            else:
                self.animation_state = 'run'
                
        # 2. Chuyển frame liên tục
        current_time = pygame.time.get_ticks()
        if current_time - self.update_time > settings.ANIMATION_COOLDOWN:
            self.update_time = current_time
            self.frame_index += 1
            # Tránh lỗi văng Index khi danh sách rỗng (nên đã lo liệu)
            if self.frame_index >= len(self.animations[self.animation_state]):
                self.frame_index = 0
                
        # Cập nhật hitbox
        self.rect.update(self.x, self.y, self.width, self.height)
    
    def draw(self, screen):
        """Vẽ player (sprite) lên màn hình."""
        if self.is_dashing:
            self._draw_dash_effect(screen)
            
        # Kiểm tra kĩ index trước khi vẽ
        if self.frame_index >= len(self.animations[self.animation_state]):
            self.frame_index = 0
        current_image = self.animations[self.animation_state][self.frame_index]
        
        # Căn hình vào giữa dưới (midbottom) của hitbox thay vì dùng x, y mặc định
        image_rect = current_image.get_rect(midbottom=self.rect.midbottom)
        
        # Vẽ nhân vật
        screen.blit(current_image, image_rect)
        
        # Nếu muốn thấy hitbox (để dễ thiết kế), thêm hashtag '#' để xoá dòng này
        # pygame.draw.rect(screen, settings.COLOR_BLACK, self.rect, 1)
        
        # Vẽ Cooldown indicator cho phép lướt (dash)
        if not self.can_dash:
            cooldown_ratio = self.dash_cooldown_timer / settings.DASH_COOLDOWN
            bar_width = self.width * (1 - cooldown_ratio)
            bar_rect = pygame.Rect(self.x, self.y - 12, bar_width, 4)
            pygame.draw.rect(screen, settings.COLOR_SCORE, bar_rect)
            
    def _draw_dash_effect(self, screen):
        """Vẽ hiệu ứng afterimage khi dash bằng sprite."""
        # Chỉ vẽ hiệu ứng mờ nhân bản khi đang ở trạng thái dash tránh lỗi văng index
        if self.animation_state != 'dash' or self.frame_index >= len(self.animations['dash']):
            return
            
        current_image = self.animations['dash'][self.frame_index].copy()
        for i in range(3):
            # Tạo hiệu ứng mờ dần
            alpha = max(100 - (i * 30), 0)
            current_image.set_alpha(alpha)
            
            trail_x = self.x - (i + 1) * 15
            image_rect = current_image.get_rect(midbottom=self.rect.midbottom)
            image_rect.x = trail_x
            screen.blit(current_image, image_rect)
    
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
    
        """Reset player về trạng thái ban đầu (khi chơi lại)."""
        self.y = settings.GROUND_Y - settings.PLAYER_HEIGHT
        self.height = settings.PLAYER_HEIGHT
        self.width = settings.PLAYER_WIDTH
        self.vel_y = 0
        self.is_on_ground = True
        self.jump_count = 0
        self.jump_buffer_timer = 0
        self.is_ducking = False
        self.is_ducking = False
        self.is_dashing = False
        self.is_dead = False
        
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.can_dash = True
        self.rect.update(self.x, self.y, self.width, self.height)
