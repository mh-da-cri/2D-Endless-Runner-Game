"""
Player - Nhân vật Knight
Xử lý di chuyển, nhảy (double jump), cúi, dash, và vẽ nhân vật.
Ban đầu dùng hình học placeholder, sau thay bằng sprite.
"""

import pygame
import math
import os
import settings
from utils.spritesheet import SpriteSheet
from utils.asset_loader import load_image


class Player:
    """Nhân vật chính - hỗ trợ Knight, Sorcerer, Priest."""
    
    def __init__(self, character_type=settings.CHARACTER_KNIGHT):
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
        
        # --- CHARACTER & HP SYSTEM ---
        self.character_type = character_type
        self.max_hp = settings.PLAYER_MAX_HP
        self.hp = self.max_hp
        self.invincible_timer = 0
        
        # --- SKILL SYSTEM ---
        self.skill_active = False
        self.skill_duration_timer = 0
        self.skill_cooldown_max = self._get_skill_cooldown()
        self.skill_cooldown_timer = 0
        self.can_use_skill = True
        
        # --- POWERUP SYSTEM ---
        self.active_powerups = {}         # {type: frames_remaining}
        
        # --- EFFECTS ---
        self.heal_effect_timer = 0
        self.shield_pulse = 0
        
        # --- ANIMATION SETUP (chỉ cho Knight) ---
        if self.character_type == settings.CHARACTER_KNIGHT:
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
        else:
            # Các nhân vật khác dùng hình học - không cần sprite sheet
            self.sprite_sheet = None
            self.animations = None
        
        self.frame_index = 0
        self.animation_state = 'idle'
        self.update_time = pygame.time.get_ticks()
        
        # --- AUDIO ---
        try:
            self.jump_sound = pygame.mixer.Sound('assets/audio/JumpSoundEffect.mp3')
            self.jump_sound.set_volume(0.3)
        except Exception:
            self.jump_sound = None
        
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
        if getattr(self, 'jump_sound', None):
            self.jump_sound.stop()
            self.jump_sound.play()

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
            if self.animations:
                self.animation_state = 'dead'
            return  # KHÓA toàn bộ di chuyển khi đã chết
            
        # --- TIMER UPDATES ---
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
        
        # Invincibility cooldown
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        
        # Powerup timers
        for p_type in list(self.active_powerups.keys()):
            self.active_powerups[p_type] -= 1
            if self.active_powerups[p_type] <= 0:
                del self.active_powerups[p_type]
        
        # Skill system: knight shield duration, then cooldown
        if self.skill_active:
            self.skill_duration_timer -= 1
            if self.skill_duration_timer <= 0:
                self.skill_active = False
                # Bắt đầu cooldown SAU KHI khiên hết
                self.skill_cooldown_timer = self.skill_cooldown_max
        elif not self.can_use_skill:
            self.skill_cooldown_timer -= 1
            if self.skill_cooldown_timer <= 0:
                self.can_use_skill = True
        
        # Heal effect
        if self.heal_effect_timer > 0:
            self.heal_effect_timer -= 1
        
        # --- ANIMATION LOGIC (chỉ cho Knight dùng sprite) ---
        if self.animations:
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
                if self.frame_index >= len(self.animations[self.animation_state]):
                    self.frame_index = 0
                
        # Cập nhật hitbox
        self.rect.update(self.x, self.y, self.width, self.height)
    
    def draw(self, screen):
        """Vẽ player lên màn hình - route theo loại nhân vật."""
        if self.character_type == settings.CHARACTER_SORCERER:
            self._draw_sorcerer(screen)
        elif self.character_type == settings.CHARACTER_PRIEST:
            self._draw_priest(screen)
        else:
            # Knight - dùng Sprite Sheet
            if self.is_dashing:
                self._draw_dash_effect(screen)
                
            # Kiểm tra kĩ index trước khi vẽ
            if self.frame_index >= len(self.animations[self.animation_state]):
                self.frame_index = 0
            current_image = self.animations[self.animation_state][self.frame_index]
            
            # Căn hình vào giữa dưới (midbottom) của hitbox
            image_rect = current_image.get_rect(midbottom=self.rect.midbottom)
            screen.blit(current_image, image_rect)
        
        # Bất tử (invincible) - nhấp nháy
        if self.invincible_timer > 0 and (self.invincible_timer // 6) % 2 == 0:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 60))
            screen.blit(flash, (self.x, self.y))
        
        # Skill shield Knight - vòng sáng
        if self.skill_active and self.character_type == settings.CHARACTER_KNIGHT:
            self.shield_pulse = (self.shield_pulse + 0.1) % (2 * math.pi)
            r = int(4 + 2 * math.sin(self.shield_pulse))
            shield_rect = self.rect.inflate(r * 2, r * 2)
            pygame.draw.rect(screen, settings.COLOR_SHIELD_SKILL, shield_rect, 2, border_radius=8)
        
        # Heal effect
        if self.heal_effect_timer > 0:
            self._draw_heal_effect(screen)
        
        # Cooldown indicator cho Dash
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
    
    def _get_skill_cooldown(self):
        """Trả về giá trị cooldown skill theo loại nhân vật."""
        if self.character_type == settings.CHARACTER_KNIGHT:
            return settings.SKILL_KNIGHT_COOLDOWN
        elif self.character_type == settings.CHARACTER_SORCERER:
            return settings.SKILL_SORCERER_COOLDOWN
        elif self.character_type == settings.CHARACTER_PRIEST:
            return settings.SKILL_PRIEST_COOLDOWN
        return 0
    
    def take_damage(self):
        """
        Nhận sát thương.
        Giảm 1 HP và kích hoạt invincibility frames.
        
        Returns:
            bool: True nếu nhân vật chết (HP <= 0)
        """
        # Kiểm tra miễn nhiễm
        if self.invincible_timer > 0:
            return False
        
        # Kiểm tra shield skill (Knight)
        if self.skill_active and self.character_type == settings.CHARACTER_KNIGHT:
            return False
        
        # Kiểm tra shield powerup
        if self.has_powerup('shield'):
            return False
        
        # Nhận sát thương
        self.hp -= 1
        
        if self.hp <= 0:
            return True  # Chết
        
        # Kích hoạt invincibility
        self.invincible_timer = settings.INVINCIBILITY_FRAMES
        return False
    
    def heal(self, amount=1):
        """
        Hồi máu.
        
        Args:
            amount: Số HP hồi lại
        """
        self.hp = min(self.hp + amount, self.max_hp)
        self.heal_effect_timer = 60  # Hiệu ứng 1 giây
    
    def use_skill(self):
        """
        Kích hoạt skill.
        Cooldown bắt đầu SAU KHI skill hết tác dụng (đối với skill có duration).
        
        Returns:
            str hoặc None: Loại skill được kích hoạt, None nếu không thể dùng
        """
        if not self.can_use_skill:
            return None
        
        self.can_use_skill = False
        
        if self.character_type == settings.CHARACTER_KNIGHT:
            # Bật khiên - cooldown sẽ bắt đầu SAU KHI khiên hết tác dụng
            self.skill_active = True
            self.skill_duration_timer = settings.SKILL_KNIGHT_DURATION
            self.skill_cooldown_timer = 0  # Chưa tính cooldown
            return "shield"
        
        elif self.character_type == settings.CHARACTER_SORCERER:
            # Bắn fireball - cooldown bắt đầu ngay (PlayState sẽ tạo fireball entities)
            self.skill_cooldown_timer = self.skill_cooldown_max
            return "fireball"
        
        elif self.character_type == settings.CHARACTER_PRIEST:
            # Hồi máu - cooldown bắt đầu ngay
            if self.hp < self.max_hp:
                self.heal(1)
                self.skill_cooldown_timer = self.skill_cooldown_max
                return "heal"
            else:
                # Đầy máu rồi, hoàn cooldown
                self.can_use_skill = True
                self.skill_cooldown_timer = 0
                return None
        
        return None
    
    def activate_powerup(self, p_type):
        """Kích hoạt một power-up."""
        self.active_powerups[p_type] = settings.POWERUP_DURATION
        
    def has_powerup(self, p_type):
        """Kiểm tra xem power-up có đang kích hoạt không."""
        return self.active_powerups.get(p_type, 0) > 0
    
    def is_invincible(self):
        """Kiểm tra nhân vật có đang bất tử không (bao gồm tất cả các nguồn)."""
        if self.invincible_timer > 0:
            return True
        if self.is_dashing:
            return True
        if self.has_powerup('shield'):
            return True
        if self.skill_active and self.character_type == settings.CHARACTER_KNIGHT:
            return True
        return False
    
    def _draw_sorcerer(self, screen):
        """Vẽ nhân vật Sorcerer (Pháp sư)."""
        body_color = settings.COLOR_SORCERER
        
        # Powerup shield aura
        if self.has_powerup('shield'):
            body_color = settings.COLOR_POWERUP_SHIELD
            aura_rect = self.rect.inflate(10, 10)
            pygame.draw.rect(screen, settings.COLOR_POWERUP_SHIELD, aura_rect, 2, border_radius=6)
        
        # Áo choàng (thân chính) - hình thang
        robe_points = [
            (self.x + 5, self.y + 15),           # Vai trái
            (self.x + self.width - 5, self.y + 15),  # Vai phải
            (self.x + self.width + 3, self.y + self.height),  # Chân phải (rộng hơn)
            (self.x - 3, self.y + self.height),    # Chân trái (rộng hơn)
        ]
        pygame.draw.polygon(screen, body_color, robe_points)
        pygame.draw.polygon(screen, settings.COLOR_BLACK, robe_points, 2)
        
        # Mũ phù thủy (tam giác nhọn)
        hat_height = 25 if not self.is_ducking else 12
        hat_points = [
            (self.x + 3, self.y + 15),
            (self.x + self.width // 2, self.y - hat_height),
            (self.x + self.width - 3, self.y + 15),
        ]
        pygame.draw.polygon(screen, settings.COLOR_SORCERER_HAT, hat_points)
        pygame.draw.polygon(screen, settings.COLOR_BLACK, hat_points, 2)
        
        # Vành mũ
        brim_rect = pygame.Rect(self.x - 3, self.y + 12, self.width + 6, 6)
        pygame.draw.ellipse(screen, settings.COLOR_SORCERER_HAT, brim_rect)
        
        # Mắt sáng (phát sáng ma thuật)
        eye_y = self.y + (20 if not self.is_ducking else 8)
        glow_color = settings.COLOR_SORCERER_ACCENT
        pygame.draw.circle(screen, glow_color, (self.x + 28, eye_y), 3)
        pygame.draw.circle(screen, glow_color, (self.x + 38, eye_y), 3)
        # Glow effect
        glow_surface = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*glow_color, 60), (6, 6), 6)
        screen.blit(glow_surface, (self.x + 22, eye_y - 6))
        screen.blit(glow_surface, (self.x + 32, eye_y - 6))
        
        # Ngôi sao trang trí trên áo
        star_x = self.x + self.width // 2
        star_y = self.y + self.height // 2
        self._draw_small_star(screen, star_x, star_y, settings.COLOR_SORCERER_ACCENT)
        
        # Indicator khi đang cúi
        if self.is_ducking:
            arrow_x = self.x + self.width // 2
            arrow_y = self.y - 10
            pygame.draw.polygon(screen, settings.COLOR_SCORE, [
                (arrow_x - 5, arrow_y - 5),
                (arrow_x + 5, arrow_y - 5),
                (arrow_x, arrow_y + 2)
            ])
    
    def _draw_priest(self, screen):
        """Vẽ nhân vật Priest (Nữ tu)."""
        body_color = settings.COLOR_PRIEST
        
        # Powerup shield aura
        if self.has_powerup('shield'):
            body_color = settings.COLOR_POWERUP_SHIELD
            aura_rect = self.rect.inflate(10, 10)
            pygame.draw.rect(screen, settings.COLOR_POWERUP_SHIELD, aura_rect, 2, border_radius=6)
        
        # Áo tu (thân chính) - hình chữ nhật bo góc
        pygame.draw.rect(screen, body_color, self.rect, border_radius=6)
        
        # Hood (mũ trùm)
        hood_height = 20 if not self.is_ducking else 10
        hood_rect = pygame.Rect(
            self.x - 2, self.y,
            self.width + 4, hood_height
        )
        pygame.draw.ellipse(screen, settings.COLOR_PRIEST_HOOD, hood_rect)
        pygame.draw.ellipse(screen, settings.COLOR_BLACK, hood_rect, 2)
        
        # Mắt hiền (nhỏ hơn, dịu hơn)
        eye_y = self.y + (12 if not self.is_ducking else 6)
        pygame.draw.circle(screen, (80, 60, 40), (self.x + 28, eye_y), 2)
        pygame.draw.circle(screen, (80, 60, 40), (self.x + 38, eye_y), 2)
        
        # Thánh giá trên ngực
        cross_x = self.x + self.width // 2
        cross_y = self.y + self.height // 2 - 5
        cross_color = settings.COLOR_PRIEST_ACCENT
        # Ngang
        pygame.draw.line(screen, cross_color, (cross_x - 6, cross_y), (cross_x + 6, cross_y), 2)
        # Dọc
        pygame.draw.line(screen, cross_color, (cross_x, cross_y - 8), (cross_x, cross_y + 8), 2)
        
        # Viền
        pygame.draw.rect(screen, settings.COLOR_BLACK, self.rect, 2, border_radius=6)
        
        # Halo (vầng sáng trên đầu) cho Priest
        halo_y = self.y - 8
        halo_rect = pygame.Rect(self.x + 10, halo_y, self.width - 20, 8)
        pygame.draw.ellipse(screen, settings.COLOR_PRIEST_ACCENT, halo_rect, 2)
        
        # Indicator khi đang cúi
        if self.is_ducking:
            arrow_x = self.x + self.width // 2
            arrow_y = self.y - 15
            pygame.draw.polygon(screen, settings.COLOR_SCORE, [
                (arrow_x - 5, arrow_y - 5),
                (arrow_x + 5, arrow_y - 5),
                (arrow_x, arrow_y + 2)
            ])
    
    def _draw_small_star(self, screen, cx, cy, color):
        """Vẽ ngôi sao nhỏ trang trí."""
        size = 5
        points = []
        for i in range(5):
            angle = math.radians(i * 72 - 90)
            points.append((cx + math.cos(angle) * size, cy + math.sin(angle) * size))
            angle2 = math.radians(i * 72 + 36 - 90)
            points.append((cx + math.cos(angle2) * size * 0.4, cy + math.sin(angle2) * size * 0.4))
        pygame.draw.polygon(screen, color, points)
    
    def _draw_heal_effect(self, screen):
        """Vẽ hiệu ứng hồi máu."""
        ratio = self.heal_effect_timer / 60
        # Các hạt sáng bay lên
        for i in range(5):
            px = self.x + self.width // 2 + math.sin(i * 1.2 + self.heal_effect_timer * 0.2) * 20
            py = self.y + self.height - (1 - ratio) * 60 - i * 10
            particle_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
            alpha = int(200 * ratio)
            pygame.draw.circle(particle_surface, (*settings.COLOR_HEAL, alpha), (4, 4), 4)
            screen.blit(particle_surface, (px - 4, py - 4))
        
        # Dấu "+" bay lên
        plus_y = self.y - 20 - (1 - ratio) * 30
        font = pygame.font.Font(None, 24)
        text = font.render("+1", True, settings.COLOR_HEAL)
        screen.blit(text, (self.x + self.width // 2 - 8, plus_y))
    
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
        self.jump_buffer_timer = 0
        self.is_ducking = False
        self.is_dashing = False
        self.is_dead = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.can_dash = True
        self.hp = self.max_hp
        self.invincible_timer = 0
        self.skill_cooldown_timer = 0
        self.skill_cooldown_max = self._get_skill_cooldown()
        self.skill_active = False
        self.skill_duration_timer = 0
        self.can_use_skill = True
        self.heal_effect_timer = 0
        self.shield_pulse = 0
        self.active_powerups = {}
        self.frame_index = 0
        self.animation_state = 'idle'
        self.rect.update(self.x, self.y, self.width, self.height)
