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
from utils.asset_loader import load_image, load_font, load_sound, play_sound


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
        self.death_sound_played = False
        
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
        self.label_font = load_font(16)
        self.powerup_info = {
            'shield': {'label': 'Shield', 'color': settings.COLOR_POWERUP_SHIELD},
            'double_score': {'label': '2x Score', 'color': settings.COLOR_POWERUP_SCORE},
            'slow_down': {'label': 'Slow Down', 'color': settings.COLOR_POWERUP_SLOW},
            'speed_up': {'label': 'Speed Up', 'color': settings.COLOR_POWERUP_SPEED},
            'high_jump': {'label': 'High Jump', 'color': settings.COLOR_POWERUP_JUMP},
            'counter_shield': {'label': 'Counter Shield', 'color': settings.COLOR_COUNTER_SHIELD}
        }
        
        # --- EFFECTS ---
        self.heal_effect_timer = 0
        self.shield_pulse = 0
        self.skill_cast_timer = 0
        self.priest_dash_effect = []
        self.priest_duck_effect = []
        self.priest_skill_effect = []
        self.shield_sprite = None
        
        # --- DEAD SPRITE / EFFECT ---
        self.dead_frame = self._load_dead_frame()
        
        # --- ANIMATION SETUP ---
        if self.character_type == settings.CHARACTER_KNIGHT:
            self.sprite_sheet_image = load_image(settings.SPRITE_IMAGE, convert_alpha=True)
            self.sprite_sheet = SpriteSheet(self.sprite_sheet_image)
            
            crouch_img = load_image(settings.SPRITE_CROUCH_IMAGE, convert_alpha=True)
            self.crouch_sheet = SpriteSheet(crouch_img)
            
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
        elif self.character_type == settings.CHARACTER_SORCERER:
            self.sprite_sheet_image = load_image(settings.SORCERER_SPRITE_IMAGE, convert_alpha=True)
            self.sprite_sheet = SpriteSheet(self.sprite_sheet_image)
            self.animations = {
                'idle': [],
                'run': [],
                'jump': [],
                'fall': [],
                'duck': [],
                'dash': [],
                'skill': [],
                'dead': []
            }
            self._load_sorcerer_animations()
        elif self.character_type == settings.CHARACTER_PRIEST:
            self.sprite_sheet_image = load_image(settings.PRIEST_SPRITE_IMAGE, convert_alpha=True)
            self.sprite_sheet = SpriteSheet(self.sprite_sheet_image)
            self.priest_skill_sheet_image = load_image(settings.PRIEST_SKILLS_IMAGE, convert_alpha=True)
            self.priest_skill_sheet = SpriteSheet(self.priest_skill_sheet_image)
            self.animations = {
                'idle': [],
                'run': [],
                'jump': [],
                'fall': [],
                'duck': [],
                'dash': [],
                'skill': [],
                'dead': []
            }
            self._load_priest_animations()
        else:
            # Các nhân vật khác dùng hình học - không cần sprite sheet
            self.sprite_sheet = None
            self.animations = None
        
        self.frame_index = 0
        self.animation_state = 'idle'
        self.update_time = pygame.time.get_ticks()

        try:
            self.shield_sprite = load_image(settings.SHIELD_SPRITE_IMAGE, convert_alpha=True)
            self.shield_sprite = self._prepare_shield_sprite(self.shield_sprite)
        except Exception:
            self.shield_sprite = None
        
        # --- AUDIO ---
        try:
            self.jump_sound = pygame.mixer.Sound('assets/audio/JumpSoundEffect.mp3')
            self.jump_sound.set_volume(0.3)
        except Exception:
            self.jump_sound = None
        self.shield_sound = load_sound(settings.SHIELD_SOUND)
        self.heal_sound = load_sound(settings.PRIEST_HEAL_SOUND)
        self.sorcerer_skill_sound = load_sound(settings.SORCERER_SKILL_SOUND)
        self.powerup_pickup_sound = load_sound(settings.POWERUP_PICKUP_SOUND)
        self.death_sound = self._load_death_sound()
        
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
        self.animations['dead'].append(self.dead_frame)
    
    def _load_sorcerer_animations(self):
        """Cắt animation Sorcerer từ sorlosheet.png."""
        s = settings.SORCERER_SPRITE_SCALE
        key = settings.SORCERER_SHEET_COLORKEY
        
        def frame(x, y, w=76, h=76, inset=2):
            image = self.sprite_sheet.get_image_at(
                x + inset, y + inset, w - inset * 2, h - inset * 2, 1, colorkey=key
            )
            image = self._clear_colorkey_pixels(image, key)
            image = self._clear_edge_border_pixels(image)
            if s != 1:
                image = pygame.transform.scale(
                    image,
                    (int(image.get_width() * s), int(image.get_height() * s))
                )
            return image
        
        self.animations['idle'].append(frame(47, 14, 76, 76))
        
        jump_frames = [
            (558, 255, 46, 63),
            (622, 241, 43, 78),
            (689, 240, 44, 79),
            (767, 221, 42, 104),
            (833, 200, 43, 166),
        ]
        fall_frames = [
            (897, 220, 42, 107),
            (969, 239, 44, 88),
            (1036, 253, 43, 83),
            (1099, 269, 46, 63),
        ]
        for rect in jump_frames:
            self.animations['jump'].append(frame(*rect, inset=0))
        for rect in fall_frames:
            self.animations['fall'].append(frame(*rect, inset=0))
        
        for rect in [
            (24, 103, 76, 76),
            (104, 103, 76, 76),
            (186, 103, 76, 76),
            (263, 103, 76, 76),
        ]:
            self.animations['run'].append(frame(*rect))
        
        for rect in [
            (24, 379, 76, 76),
            (92, 379, 76, 76),
            (160, 379, 76, 76),
            (234, 379, 110, 76),
            (372, 379, 120, 76),
            (498, 379, 120, 76),
        ]:
            self.animations['dash'].append(frame(*rect))
        
        for rect in [
            (86, 553, 64, 76),
            (150, 553, 70, 76),
            (232, 553, 74, 76),
            (310, 553, 64, 76),
        ]:
            self.animations['skill'].append(frame(*rect))
        
        self.animations['duck'].append(frame(1007, 473, 57, 60, inset=0))
        self.animations['dead'].append(self.dead_frame)

    def _load_priest_animations(self):
        """Cáº¯t animation Priest tá»« Priest.png vÃ  Priest-skills.png."""
        s = settings.PRIEST_SPRITE_SCALE
        key = settings.PRIEST_SHEET_COLORKEY

        def main_frame(rect, inset=2):
            x, y, w, h = rect
            image = self.sprite_sheet.get_image_at(
                x + inset, y + inset, w - inset * 2, h - inset * 2, 1, colorkey=key
            )
            image = self._clear_colorkey_pixels(image, key, tolerance=3)
            image = self._clear_bg_border_pixels(image, key, tolerance=10)
            if s != 1:
                image = pygame.transform.scale(
                    image,
                    (int(image.get_width() * s), int(image.get_height() * s))
                )
            return image

        def fx_frame(rect):
            x, y, w, h = rect
            image = self.priest_skill_sheet.get_image_at(x, y, w, h, 1, colorkey=key)
            image = self._clear_colorkey_pixels(image, key, tolerance=3)
            image = self._clear_bg_border_pixels(image, key, tolerance=10)
            if s != 1:
                image = pygame.transform.scale(
                    image,
                    (int(image.get_width() * s), int(image.get_height() * s))
                )
            return image

        idle_frames = [
            (33, 67, 120, 106),
            (147, 65, 120, 108),
            (261, 65, 120, 108),
            (375, 65, 120, 108),
            (489, 67, 120, 106),
        ]
        move_frames = [
            (33, 263, 108, 106),
            (139, 265, 110, 104),
            (245, 267, 108, 104),
            (359, 263, 106, 108),
            (469, 265, 106, 106),
            (577, 267, 104, 104),
        ]
        skill1_frames = [
            (33, 687, 106, 106),
            (141, 679, 94, 116),
            (249, 671, 86, 122),
            (357, 667, 86, 126),
            (465, 661, 86, 132),
            (573, 659, 86, 134),
            (681, 659, 86, 134),
            (781, 671, 94, 122),
            (889, 671, 94, 122),
            (1001, 671, 90, 122),
            (33, 801, 86, 122),
            (141, 801, 86, 122),
            (249, 801, 86, 122),
            (357, 801, 86, 122),
            (465, 809, 94, 116),
            (573, 817, 106, 106),
        ]
        skill2_frames = [
            (33, 1043, 106, 106),
            (157, 1045, 106, 104),
            (299, 1047, 106, 102),
            (443, 1047, 106, 102),
            (617, 1015, 120, 134),
            (761, 1017, 120, 132),
            (905, 1017, 120, 132),
            (41, 1147, 120, 132),
            (187, 1165, 102, 116),
            (339, 1173, 106, 106),
        ]

        dash_fx_frames = [
            (33, 786, 60, 59),
            (183, 768, 108, 95),
            (343, 756, 136, 119),
            (496, 744, 178, 143),
            (684, 756, 150, 118),
        ]
        duck_fx_frames = [
            (33, 987, 162, 36),
            (216, 983, 179, 42),
            (399, 977, 104, 48),
            (494, 977, 133, 48),
            (640, 980, 170, 44),
            (856, 986, 110, 38),
        ]
        skill_fx_frames = [
            (33, 1999, 102, 36),
            (137, 1937, 116, 102),
            (257, 1815, 104, 224),
            (363, 1787, 106, 254),
            (485, 1778, 208, 262),
        ]

        self.animations['idle'] = [main_frame(rect) for rect in idle_frames]
        self.animations['run'] = [main_frame(rect) for rect in move_frames]
        self.animations['jump'] = [main_frame(rect) for rect in skill1_frames[:8]]
        self.animations['fall'] = [main_frame(rect) for rect in skill1_frames[8:]]
        self.animations['skill'] = [main_frame(rect) for rect in skill2_frames]
        self.priest_dash_effect = [fx_frame(rect) for rect in dash_fx_frames]
        self.priest_duck_effect = [fx_frame(rect) for rect in duck_fx_frames]
        self.priest_skill_effect = [fx_frame(rect) for rect in skill_fx_frames]
        self.animations['dash'] = [self.animations['run'][i % len(self.animations['run'])] for i in range(len(self.priest_dash_effect))]
        self.animations['duck'] = [self.animations['idle'][i % len(self.animations['idle'])] for i in range(len(self.priest_duck_effect))]
        self.animations['dead'].append(self.dead_frame)

    def _load_dead_frame(self):
        """Load dead frame/effect theo loại nhân vật."""
        if self.character_type == settings.CHARACTER_PRIEST:
            return self._load_effect_dead_frame((325, 1517, 150, 162), int(settings.PLAYER_HEIGHT * 1.2))
        if self.character_type == settings.CHARACTER_SORCERER:
            return self._load_effect_dead_frame((117, 409, 86, 84), int(settings.PLAYER_HEIGHT * 1.1))

        dead_img = load_image(settings.SPRITE_DEAD_IMAGE, convert_alpha=True)
        dead_sheet = SpriteSheet(dead_img)
        return dead_sheet.get_image(0, 0, 32, 64, settings.SPRITE_SCALE)

    def _load_effect_dead_frame(self, rect, target_height):
        """Crop một effect frame từ Priest-skills.png để dùng làm dead."""
        key = settings.PRIEST_SHEET_COLORKEY
        effect_sheet = SpriteSheet(load_image(settings.PRIEST_SKILLS_IMAGE, convert_alpha=True))
        x, y, w, h = rect
        image = effect_sheet.get_image_at(x, y, w, h, 1, colorkey=key)
        image = self._clear_colorkey_pixels(image, key, tolerance=4)
        image = self._clear_bg_border_pixels(image, key, tolerance=10)
        if image.get_height() != target_height:
            scale = target_height / image.get_height()
            image = pygame.transform.scale(image, (int(image.get_width() * scale), target_height))
        return image

    def _get_effect_frame(self, effect_frames, state_name):
        """Äá»“ng bá»™ frame hiá»‡u á»©ng vá»›i animation hiá»‡n táº¡i."""
        if not effect_frames or state_name not in self.animations or not self.animations[state_name]:
            return None

        total_state_frames = len(self.animations[state_name])
        effect_index = min(
            len(effect_frames) - 1,
            int(self.frame_index * len(effect_frames) / max(total_state_frames, 1))
        )
        return effect_frames[effect_index]
    
    def _clear_colorkey_pixels(self, image, colorkey, tolerance=2):
        """Xóa nền xám của spritesheet trước khi scale để không còn ô vuông."""
        image = image.copy().convert_alpha()
        key_r, key_g, key_b = colorkey
        for y in range(image.get_height()):
            for x in range(image.get_width()):
                r, g, b, a = image.get_at((x, y))
                if abs(r - key_r) <= tolerance and abs(g - key_g) <= tolerance and abs(b - key_b) <= tolerance:
                    image.set_at((x, y), (r, g, b, 0))
        return image
    
    def _clear_edge_border_pixels(self, image):
        """Xóa đường kẻ frame màu đen nối với mép ảnh, giữ outline nhân vật bên trong."""
        image = image.copy().convert_alpha()
        width, height = image.get_size()
        stack = []
        visited = set()
        
        for x in range(width):
            stack.append((x, 0))
            stack.append((x, height - 1))
        for y in range(height):
            stack.append((0, y))
            stack.append((width - 1, y))
        
        while stack:
            x, y = stack.pop()
            if (x, y) in visited or x < 0 or y < 0 or x >= width or y >= height:
                continue
            visited.add((x, y))
            
            r, g, b, a = image.get_at((x, y))
            if a == 0 or r > 8 or g > 8 or b > 8:
                continue
            
            image.set_at((x, y), (r, g, b, 0))
            stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        
        return image

    def _clear_bg_border_pixels(self, image, colorkey, tolerance=10):
        """Xóa viền nền còn sót nếu nó nối trực tiếp với mép ảnh."""
        image = image.copy().convert_alpha()
        width, height = image.get_size()
        key_r, key_g, key_b = colorkey
        stack = []
        visited = set()

        for x in range(width):
            stack.append((x, 0))
            stack.append((x, height - 1))
        for y in range(height):
            stack.append((0, y))
            stack.append((width - 1, y))

        while stack:
            x, y = stack.pop()
            if (x, y) in visited or x < 0 or y < 0 or x >= width or y >= height:
                continue
            visited.add((x, y))

            r, g, b, a = image.get_at((x, y))
            if a == 0:
                continue
            if abs(r - key_r) > tolerance or abs(g - key_g) > tolerance or abs(b - key_b) > tolerance:
                continue

            image.set_at((x, y), (r, g, b, 0))
            stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

        return image

    def _prepare_shield_sprite(self, image):
        """Xoa nen vuong con dinh o mep cua sprite khien."""
        image = image.copy().convert_alpha()
        bg_r, bg_g, bg_b, _ = image.get_at((0, 0))
        return self._clear_bg_border_pixels(image, (bg_r, bg_g, bg_b), tolerance=18)
    
    def _execute_jump(self):
        """Hàm con thực thi nhảy lập tức khi hợp lệ."""
        jump_mult = settings.POWERUP_JUMP_MULTIPLIER if self.has_powerup('high_jump') else 1.0
        
        if self.jump_count == 0:
            self.vel_y = settings.JUMP_FORCE * jump_mult
        else:
            self.vel_y = settings.DOUBLE_JUMP_FORCE * jump_mult
        
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
        
        if self.skill_cast_timer > 0:
            self.skill_cast_timer -= 1
        
        # --- ANIMATION LOGIC ---
        if self.animations:
            previous_animation_state = self.animation_state
            
            # 1. Cập nhật trạng thái
            if self.is_dashing:
                self.animation_state = 'dash'
            elif self.skill_cast_timer > 0 and 'skill' in self.animations:
                self.animation_state = 'skill'
            elif self.vel_y < 0:
                self.animation_state = 'jump'
            elif self.vel_y > 0 and not self.is_on_ground:
                self.animation_state = 'fall'
            elif self.is_on_ground:
                if self.is_ducking:
                    self.animation_state = 'duck'
                else:
                    self.animation_state = 'run'
            
            if previous_animation_state != self.animation_state:
                self.frame_index = 0
                self.update_time = pygame.time.get_ticks()
                    
            # 2. Chuyển frame liên tục
            current_time = pygame.time.get_ticks()
            if self.character_type == settings.CHARACTER_SORCERER:
                animation_cooldown = settings.SORCERER_ANIMATION_COOLDOWN
            elif self.character_type == settings.CHARACTER_PRIEST:
                animation_cooldown = settings.PRIEST_ANIMATION_COOLDOWN
            else:
                animation_cooldown = settings.ANIMATION_COOLDOWN
            if current_time - self.update_time > animation_cooldown:
                self.update_time = current_time
                self.frame_index += 1
                if self.frame_index >= len(self.animations[self.animation_state]):
                    self.frame_index = 0
                
        # Cập nhật hitbox
        self.rect.update(self.x, self.y, self.width, self.height)
    
    def draw(self, screen, draw_individual_shield=True):
        """Vẽ player lên màn hình - route theo loại nhân vật."""
        
        # --- XÁC CHẾT (tất cả nhân vật dùng dead_frame) ---
        if self.is_dead:
            image_rect = self.dead_frame.get_rect(midbottom=self.rect.midbottom)
            screen.blit(self.dead_frame, image_rect)
            return  # Không vẽ thêm gì
        
        is_flashing = self.invincible_timer > 0 and (self.invincible_timer // 6) % 2 == 0
        
        # --- Vẽ bình thường theo loại nhân vật ---
        if self.character_type == settings.CHARACTER_SORCERER and self.animations:
            if self.is_dashing:
                self._draw_dash_effect(screen)
            
            if not is_flashing:
                if self.frame_index >= len(self.animations[self.animation_state]):
                    self.frame_index = 0
                current_image = self.animations[self.animation_state][self.frame_index]
                image_rect = current_image.get_rect(midbottom=self.rect.midbottom)
                if self.animation_state == 'dash':
                    image_rect.x += 15
                screen.blit(current_image, image_rect)
                
        elif self.character_type == settings.CHARACTER_SORCERER:
            if not is_flashing:
                self._draw_sorcerer(screen)
                
        elif self.character_type == settings.CHARACTER_PRIEST and self.animations:
            if not is_flashing:
                if self.frame_index >= len(self.animations[self.animation_state]):
                    self.frame_index = 0
                current_image = self.animations[self.animation_state][self.frame_index]
                image_rect = current_image.get_rect(midbottom=self.rect.midbottom)
                if self.animation_state == 'duck':
                    image_rect.y += 12
                if self.animation_state not in ('dash', 'duck'):
                    screen.blit(current_image, image_rect)
                self._draw_priest_state_effect(screen, image_rect)
        elif self.character_type == settings.CHARACTER_PRIEST:
            if not is_flashing:
                self._draw_priest(screen)
                
        else:
            # Knight - dùng Sprite Sheet
            if self.is_dashing:
                self._draw_dash_effect(screen)
                
            if not is_flashing:
                # Kiểm tra kĩ index trước khi vẽ
                if self.frame_index >= len(self.animations[self.animation_state]):
                    self.frame_index = 0
                current_image = self.animations[self.animation_state][self.frame_index]
                
                # Căn hình vào giữa dưới (midbottom) của hitbox
                image_rect = current_image.get_rect(midbottom=self.rect.midbottom)
                screen.blit(current_image, image_rect)
        
        # Skill shield Knight - vòng tròn bọc quanh nhân vật
        if not is_flashing and draw_individual_shield and self.skill_active and self.character_type == settings.CHARACTER_KNIGHT:
            self.shield_pulse = (self.shield_pulse + 0.1) % (2 * math.pi)
            self._draw_shield_sprite(screen, settings.COLOR_SHIELD_SKILL)
        
        # Powerup shield - vòng tròn xanh dương bọc quanh nhân vật (tất cả nhân vật sprite)
        if not is_flashing and draw_individual_shield and self.has_powerup('shield') and self.animations:
            if not (self.skill_active and self.character_type == settings.CHARACTER_KNIGHT):
                self.shield_pulse = (self.shield_pulse + 0.08) % (2 * math.pi)
            self._draw_shield_sprite(screen, settings.COLOR_POWERUP_SHIELD, base_padding=24)
            
        
        # Heal effect
        if self.heal_effect_timer > 0:
            self._draw_heal_effect(screen)
        
        # Cooldown indicator cho Dash
        if not self.can_dash:
            cooldown_ratio = self.dash_cooldown_timer / settings.DASH_COOLDOWN
            bar_width = self.width * (1 - cooldown_ratio)
            bar_rect = pygame.Rect(self.x, self.y - 12, bar_width, 4)
            pygame.draw.rect(screen, settings.COLOR_SCORE, bar_rect)
            
        # --- VẼ NHÃN POWER-UP ĐANG ACTIVE ---
        if self.active_powerups:
            # Điểm bắt đầu vẽ (phía trên dash bar nếu có)
            current_label_y = self.y - (25 if not self.can_dash else 15)
            
            # Vẽ các power-up đang active (xếp chồng lên nhau)
            for p_type in sorted(self.active_powerups.keys()):
                info = self.powerup_info.get(p_type, {'label': p_type.title(), 'color': settings.COLOR_WHITE})
                label_surf = self.label_font.render(info['label'], True, info['color'])
                label_rect = label_surf.get_rect(centerx=self.rect.centerx, bottom=current_label_y)
                screen.blit(label_surf, label_rect)
                current_label_y -= 14  # Khoảng cách giữa các dòng
            
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
            
            image_rect = current_image.get_rect(midbottom=self.rect.midbottom)
            if self.character_type == settings.CHARACTER_SORCERER:
                image_rect.x += 15 - (i + 1) * 8
            else:
                image_rect.x = self.x - (i + 1) * 15
            screen.blit(current_image, image_rect)

    def _draw_priest_state_effect(self, screen, image_rect):
        """Váº½ FX riÃªng cho Priest theo state hiá»‡n táº¡i."""
        effect_image = None
        effect_rect = None

        if self.animation_state == 'dash':
            effect_image = self._get_effect_frame(self.priest_dash_effect, 'dash')
            if effect_image:
                effect_rect = effect_image.get_rect(center=image_rect.center)
                effect_rect.x += 38
        elif self.animation_state == 'duck':
            effect_image = self._get_effect_frame(self.priest_duck_effect, 'duck')
            if effect_image:
                effect_rect = effect_image.get_rect(midbottom=(image_rect.centerx, settings.GROUND_Y + 15))
        elif self.animation_state == 'skill':
            effect_image = self._get_effect_frame(self.priest_skill_effect, 'skill')
            if effect_image:
                effect_rect = effect_image.get_rect(midbottom=(image_rect.centerx + 8, self.rect.bottom + 6))

        if effect_image and effect_rect:
            screen.blit(effect_image, effect_rect)
    
    def _draw_circle_shield(self, screen, color, base_padding=18, pulse_amplitude=5):
        """Vẽ lá chắn hình tròn có hiệu ứng glow bọc quanh nhân vật."""
        cx = self.rect.centerx
        cy = self.rect.centery
        base_r = max(self.width, self.height) // 2 + base_padding
        r = base_r + int(pulse_amplitude * math.sin(self.shield_pulse))
        
        # Lớp glow mờ bên ngoài (SRCALPHA)
        glow_r = r + 14
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, 28), (glow_r, glow_r), glow_r)
        pygame.draw.circle(glow_surf, (*color, 18), (glow_r, glow_r), glow_r - 4)
        screen.blit(glow_surf, (cx - glow_r, cy - glow_r))
        
        # Vòng tròn chính
        pygame.draw.circle(screen, color, (cx, cy), r, 2)
        # Vòng tròn phụ bên trong (mờ hơn, dùng surface)
        inner_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(inner_surf, (*color, 60), (r, r), r - 6, 1)
        screen.blit(inner_surf, (cx - r, cy - r))

    def _draw_shield_sprite(self, screen, color, base_padding=18, pulse_amplitude=5):
        """Vẽ khiên bằng sprite, fallback về vòng tròn nếu asset lỗi."""
        if not self.shield_sprite:
            self._draw_circle_shield(screen, color, base_padding, pulse_amplitude)
            return

        cx = self.rect.centerx
        cy = self.rect.centery
        base_size = max(self.width, self.height) + base_padding * 2
        pulse_size = int(pulse_amplitude * 3 * math.sin(self.shield_pulse))
        size = max(24, base_size + pulse_size)

        shield_image = pygame.transform.smoothscale(self.shield_sprite, (size, size))
        shield_image = shield_image.copy()
        tint = pygame.Surface((size, size), pygame.SRCALPHA)
        tint.fill((*color, 70))
        shield_image.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        shield_image.set_alpha(190)
        shield_rect = shield_image.get_rect(center=(cx, cy))
        screen.blit(shield_image, shield_rect)
    
    def _get_skill_cooldown(self):
        """Trả về giá trị cooldown skill theo loại nhân vật."""
        if self.character_type == settings.CHARACTER_KNIGHT:
            return settings.SKILL_KNIGHT_COOLDOWN
        elif self.character_type == settings.CHARACTER_SORCERER:
            return settings.SKILL_SORCERER_COOLDOWN
        elif self.character_type == settings.CHARACTER_PRIEST:
            return settings.SKILL_PRIEST_COOLDOWN
        return 0

    def _load_death_sound(self):
        """Load death scream based on the selected character."""
        if self.character_type == settings.CHARACTER_KNIGHT:
            return load_sound(settings.KNIGHT_DEATH_SOUND)
        if self.character_type == settings.CHARACTER_SORCERER:
            return load_sound(settings.SORCERER_DEATH_SOUND)
        if self.character_type == settings.CHARACTER_PRIEST:
            return load_sound(settings.PRIEST_DEATH_SOUND)
        return None

    def _play_death_sound(self):
        """Play the death scream only once for the current life."""
        if self.death_sound_played:
            return

        play_sound(self.death_sound, volume=0.55)
        self.death_sound_played = True
    
    def take_damage(self, amount=1):
        """
        Nhận sát thương.
        Giảm HP và kích hoạt invincibility frames.
        
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
        self.hp -= amount
        
        if self.hp <= 0:
            self._play_death_sound()
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
            play_sound(self.shield_sound, volume=0.5)
            return "shield"
        
        elif self.character_type == settings.CHARACTER_SORCERER:
            # Bắn fireball - cooldown bắt đầu ngay (PlayState sẽ tạo fireball entities)
            self.skill_cast_timer = settings.SORCERER_SKILL_CAST_FRAMES
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
            self.skill_cooldown_timer = self.skill_cooldown_max
            play_sound(self.sorcerer_skill_sound, volume=0.5)
            return "fireball"
        
        elif self.character_type == settings.CHARACTER_PRIEST:
            # Hồi máu - cooldown bắt đầu ngay
            if self.hp < self.max_hp:
                self.skill_cast_timer = settings.PRIEST_SKILL_CAST_FRAMES
                self.frame_index = 0
                self.update_time = pygame.time.get_ticks()
                self.heal(1)
                self.skill_cooldown_timer = self.skill_cooldown_max
                play_sound(self.heal_sound, volume=0.5)
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
        play_sound(self.powerup_pickup_sound, volume=0.5)
        
    def has_powerup(self, p_type):
        """Kiểm tra xem power-up có đang kích hoạt không."""
        return self.active_powerups.get(p_type, 0) > 0

    def is_priest_burrowed(self):
        """Priest đang ẩn dưới đất khi cúi trên mặt đất."""
        return (
            self.character_type == settings.CHARACTER_PRIEST
            and self.is_ducking
            and self.is_on_ground
            and not self.is_dashing
            and not self.is_dead
        )
    
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
        
        # Powerup shield - đổi màu thân (vòng tròn shield vẽ trong draw())
        if self.has_powerup('shield'):
            body_color = settings.COLOR_POWERUP_SHIELD
        
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
        
        # Powerup shield - đổi màu thân (vòng tròn shield vẽ trong draw())
        if self.has_powerup('shield'):
            body_color = settings.COLOR_POWERUP_SHIELD
        
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
        if self.is_priest_burrowed():
            burrow_height = 15
            return pygame.Rect(
                self.rect.x + 6,
                settings.GROUND_Y - burrow_height,
                self.rect.width - 12,
                burrow_height
            )

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
        self.death_sound_played = False
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
        self.skill_cast_timer = 0
        self.active_powerups = {}
        self.frame_index = 0
        self.animation_state = 'idle'
        self.rect.update(self.x, self.y, self.width, self.height)
