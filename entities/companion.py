"""
Companion - Nhân vật đồng hành di chuyển sau lưng player chính.
Xuất hiện từ item đặc biệt tại các mốc điểm 200 và 500.
Sao chép chuyển động của player và có skill riêng.
"""

import pygame
import math
import settings
from utils.spritesheet import SpriteSheet
from utils.asset_loader import load_image, load_sound, play_sound


class Companion:
    """Nhân vật đồng hành - đi sau lưng player chính."""
    
    def __init__(self, character_type, companion_index, main_player):
        """
        Khởi tạo đồng hành.
        
        Args:
            character_type: Loại nhân vật (knight/sorcerer/priest)
            companion_index: 0 cho đồng hành thứ 1, 1 cho đồng hành thứ 2
            main_player: Tham chiếu đến Player chính
        """
        self.character_type = character_type
        self.companion_index = companion_index
        self.main_player = main_player
        
        # Vị trí (theo sau player chính)
        self.offset_x = settings.COMPANION_OFFSET_X * (companion_index + 1)
        self.scale = settings.COMPANION_SCALE
        self.width = int(settings.PLAYER_WIDTH * self.scale)
        self.height = int(settings.PLAYER_HEIGHT * self.scale)
        self.duck_height = int(settings.PLAYER_DUCK_HEIGHT * self.scale)
        
        self.x = main_player.x + self.offset_x
        self.y = main_player.y + (settings.PLAYER_HEIGHT - self.height)
        
        # Trạng thái (sao chép từ player chính)
        self.is_ducking = False
        
        # Hệ thống skill
        self.skill_cooldown_timer = 0
        self.skill_cooldown_max = self._get_skill_cooldown()
        self.can_use_skill = True
        self.skill_active = False       # Cho Knight shield
        self.skill_duration_timer = 0
        self.shield_pulse = 0
        
        # Phím kích hoạt skill
        if companion_index == 0:
            self.skill_key = settings.SKILL_KEY_COMPANION_1
        else:
            self.skill_key = settings.SKILL_KEY_COMPANION_2
        
        # Hitbox
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Hoạt ảnh
        self.spawn_timer = 60  # Hiệu ứng fade-in khi xuất hiện

        self.skill_cast_timer = 0
        self.priest_dash_effect = []
        self.priest_duck_effect = []
        self.priest_skill_effect = []
        self.shield_sprite = None
        
        # --- SPRITE SYSTEM ---
        self.dead_frame = self._load_dead_frame()
        
        self.animations = None
        if self.character_type == settings.CHARACTER_KNIGHT:
            self.sprite_sheet_image = load_image(settings.SPRITE_IMAGE, convert_alpha=True)
            self.sprite_sheet = SpriteSheet(self.sprite_sheet_image)
            crouch_img = load_image(settings.SPRITE_CROUCH_IMAGE, convert_alpha=True)
            self.crouch_sheet = SpriteSheet(crouch_img)
            
            self.animations = {state: [] for state in ['idle', 'run', 'jump', 'fall', 'duck', 'dash', 'dead']}
            self._load_knight_animations()
        elif self.character_type == settings.CHARACTER_SORCERER:
            self.sprite_sheet_image = load_image(settings.SORCERER_SPRITE_IMAGE, convert_alpha=True)
            self.sprite_sheet = SpriteSheet(self.sprite_sheet_image)
            
            self.animations = {state: [] for state in ['idle', 'run', 'jump', 'fall', 'duck', 'dash', 'skill', 'dead']}
            self._load_sorcerer_animations()
            
        elif self.character_type == settings.CHARACTER_PRIEST:
            self.sprite_sheet_image = load_image(settings.PRIEST_SPRITE_IMAGE, convert_alpha=True)
            self.sprite_sheet = SpriteSheet(self.sprite_sheet_image)
            self.priest_skill_sheet_image = load_image(settings.PRIEST_SKILLS_IMAGE, convert_alpha=True)
            self.priest_skill_sheet = SpriteSheet(self.priest_skill_sheet_image)
            self.animations = {state: [] for state in ['idle', 'run', 'jump', 'fall', 'duck', 'dash', 'skill', 'dead']}
            self._load_priest_animations()

        self.frame_index = 0
        self.animation_state = 'idle'
        self.update_time = pygame.time.get_ticks()
    
        self.update_time = pygame.time.get_ticks()
        try:
            self.shield_sprite = load_image(settings.SHIELD_SPRITE_IMAGE, convert_alpha=True)
            self.shield_sprite = self._prepare_shield_sprite(self.shield_sprite)
        except Exception:
            self.shield_sprite = None
        self.shield_sound = load_sound(settings.SHIELD_SOUND)
        self.heal_sound = load_sound(settings.PRIEST_HEAL_SOUND)
        self.sorcerer_skill_sound = load_sound(settings.SORCERER_SKILL_SOUND)

    def _load_dead_frame(self):
        """Load dead frame/effect theo loại companion."""
        target_height = int(settings.PLAYER_HEIGHT * self.scale * 1.15)
        if self.character_type == settings.CHARACTER_PRIEST:
            return self._load_effect_dead_frame((325, 1517, 150, 162), target_height)
        if self.character_type == settings.CHARACTER_SORCERER:
            return self._load_effect_dead_frame((117, 409, 86, 84), target_height)

        dead_img = load_image(settings.SPRITE_DEAD_IMAGE, convert_alpha=True)
        dead_sheet = SpriteSheet(dead_img)
        return dead_sheet.get_image(0, 0, 32, 64, settings.SPRITE_SCALE * self.scale)

    def _load_effect_dead_frame(self, rect, target_height):
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
        
    def _load_knight_animations(self):
        """Cắt ảnh từ Sprite Sheet cho Knight đồng hành."""
        w = settings.SPRITE_FRAME_WIDTH
        h = settings.SPRITE_FRAME_HEIGHT
        # Tỉ lệ scale thực tế = scale nhân vật chính * scale đồng hành
        s = settings.SPRITE_SCALE * self.scale
        
        self.animations['idle'].append(self.sprite_sheet.get_image(0, 0, w, h, s))
        self.animations['jump'].append(self.sprite_sheet.get_image(1, 0, w, h, s))
        self.animations['fall'].append(self.sprite_sheet.get_image(2, 0, w, h, s))
        for i in range(3, 9):
            self.animations['run'].append(self.sprite_sheet.get_image(i, 0, w, h, s))
        self.animations['duck'].append(self.crouch_sheet.get_image(0, 0, 44, 44, s))
        for i in range(3, 9):
            self.animations['dash'].append(self.sprite_sheet.get_image_at(i * w, 1768, w, 35, s))
        self.animations['dead'].append(self.dead_frame)

    def _load_priest_animations(self):
        """Cáº¯t animation Priest cho Ä‘á»“ng hÃ nh."""
        s = settings.PRIEST_SPRITE_SCALE * self.scale
        key = settings.PRIEST_SHEET_COLORKEY

        def main_frame(rect, inset=2):
            x, y, w, h = rect
            image = self.sprite_sheet.get_image_at(
                x + inset, y + inset, w - inset * 2, h - inset * 2, 1, colorkey=key
            )
            image = self._clear_colorkey_pixels(image, key, tolerance=3)
            image = self._clear_bg_border_pixels(image, key, tolerance=10)
            if s != 1:
                image = pygame.transform.scale(image, (int(image.get_width() * s), int(image.get_height() * s)))
            return image

        def fx_frame(rect):
            x, y, w, h = rect
            image = self.priest_skill_sheet.get_image_at(x, y, w, h, 1, colorkey=key)
            image = self._clear_colorkey_pixels(image, key, tolerance=3)
            image = self._clear_bg_border_pixels(image, key, tolerance=10)
            if s != 1:
                image = pygame.transform.scale(image, (int(image.get_width() * s), int(image.get_height() * s)))
            return image

        idle_frames = [(33, 67, 120, 106), (147, 65, 120, 108), (261, 65, 120, 108), (375, 65, 120, 108), (489, 67, 120, 106)]
        move_frames = [(33, 263, 108, 106), (139, 265, 110, 104), (245, 267, 108, 104), (359, 263, 106, 108), (469, 265, 106, 106), (577, 267, 104, 104)]
        skill1_frames = [
            (33, 687, 106, 106), (141, 679, 94, 116), (249, 671, 86, 122), (357, 667, 86, 126),
            (465, 661, 86, 132), (573, 659, 86, 134), (681, 659, 86, 134), (781, 671, 94, 122),
            (889, 671, 94, 122), (1001, 671, 90, 122), (33, 801, 86, 122), (141, 801, 86, 122),
            (249, 801, 86, 122), (357, 801, 86, 122), (465, 809, 94, 116), (573, 817, 106, 106),
        ]
        skill2_frames = [
            (33, 1043, 106, 106), (157, 1045, 106, 104), (299, 1047, 106, 102), (443, 1047, 106, 102),
            (617, 1015, 120, 134), (761, 1017, 120, 132), (905, 1017, 120, 132), (41, 1147, 120, 132),
            (187, 1165, 102, 116), (339, 1173, 106, 106),
        ]
        dash_fx_frames = [(33, 786, 60, 59), (183, 768, 108, 95), (343, 756, 136, 119), (496, 744, 178, 143), (684, 756, 150, 118)]
        duck_fx_frames = [(33, 987, 162, 36), (216, 983, 179, 42), (399, 977, 104, 48), (494, 977, 133, 48), (640, 980, 170, 44), (856, 986, 110, 38)]
        skill_fx_frames = [(33, 1999, 102, 36), (137, 1937, 116, 102), (257, 1815, 104, 224), (363, 1787, 106, 254), (485, 1778, 208, 262)]

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

    def _get_effect_frame(self, effect_frames, state_name):
        if not effect_frames or state_name not in self.animations or not self.animations[state_name]:
            return None
        total_state_frames = len(self.animations[state_name])
        effect_index = min(len(effect_frames) - 1, int(self.frame_index * len(effect_frames) / max(total_state_frames, 1)))
        return effect_frames[effect_index]

    def _resolve_supported_state(self, requested_state):
        """Trả về animation state an toàn cho companion hiện tại."""
        if requested_state in self.animations and self.animations[requested_state]:
            return requested_state

        if requested_state == 'skill':
            if self.main_player.is_on_ground:
                return 'duck' if self.main_player.is_ducking and 'duck' in self.animations else 'run'
            return 'jump' if self.main_player.vel_y < 0 else 'fall'

        if self.main_player.is_on_ground:
            return 'duck' if self.main_player.is_ducking and 'duck' in self.animations else 'run'
        return 'jump' if self.main_player.vel_y < 0 else 'fall'

    def _load_sorcerer_animations(self):
        """Cắt animation Sorcerer cho đồng hành."""
        # Tỉ lệ scale thực tế
        s = settings.SORCERER_SPRITE_SCALE * self.scale
        key = settings.SORCERER_SHEET_COLORKEY
        
        def frame(x, y, w=76, h=76, inset=2):
            image = self.sprite_sheet.get_image_at(x + inset, y + inset, w - inset * 2, h - inset * 2, 1, colorkey=key)
            image = self._clear_colorkey_pixels(image, key)
            image = self._clear_edge_border_pixels(image)
            if s != 1:
                image = pygame.transform.scale(image, (int(image.get_width() * s), int(image.get_height() * s)))
            return image
        
        self.animations['idle'].append(frame(47, 14))
        for r in [(558, 255, 46, 63), (622, 241, 43, 78), (689, 240, 44, 79), (767, 221, 42, 104), (833, 200, 43, 166)]:
            self.animations['jump'].append(frame(*r, inset=0))
        for r in [(897, 220, 42, 107), (969, 239, 44, 88), (1036, 253, 43, 83), (1099, 269, 46, 63)]:
            self.animations['fall'].append(frame(*r, inset=0))
        for r in [(24, 103, 76, 76), (104, 103, 76, 76), (186, 103, 76, 76), (263, 103, 76, 76)]:
            self.animations['run'].append(frame(*r))
        for r in [(24, 379, 76, 76), (92, 379, 76, 76), (160, 379, 76, 76), (234, 379, 110, 76), (372, 379, 120, 76), (498, 379, 120, 76)]:
            self.animations['dash'].append(frame(*r))
        for r in [(86, 553, 64, 76), (150, 553, 70, 76), (232, 553, 74, 76), (310, 553, 64, 76)]:
            self.animations['skill'].append(frame(*r))
        self.animations['duck'].append(frame(1007, 473, 57, 60, inset=0))
        self.animations['dead'].append(self.dead_frame)

    def _clear_colorkey_pixels(self, image, colorkey, tolerance=2):
        image = image.copy().convert_alpha()
        kr, kg, kb = colorkey
        for y in range(image.get_height()):
            for x in range(image.get_width()):
                r, g, b, a = image.get_at((x, y))
                if abs(r - kr) <= tolerance and abs(g - kg) <= tolerance and abs(b - kb) <= tolerance:
                    image.set_at((x, y), (r, g, b, 0))
        return image

    def _clear_edge_border_pixels(self, image):
        image = image.copy().convert_alpha()
        w, h = image.get_size()
        stack, visited = [], set()
        for x in range(w): stack.extend([(x, 0), (x, h - 1)])
        for y in range(h): stack.extend([(0, y), (w - 1, y)])
        while stack:
            x, y = stack.pop(); 
            if (x, y) in visited or x < 0 or y < 0 or x >= w or y >= h: continue
            visited.add((x, y))
            r, g, b, a = image.get_at((x, y))
            if r < 50 and g < 50 and b < 50 and a > 0:
                image.set_at((x, y), (0, 0, 0, 0))
                stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
        return image

    def _clear_bg_border_pixels(self, image, colorkey, tolerance=10):
        image = image.copy().convert_alpha()
        w, h = image.get_size()
        kr, kg, kb = colorkey
        stack, visited = [], set()
        for x in range(w): stack.extend([(x, 0), (x, h - 1)])
        for y in range(h): stack.extend([(0, y), (w - 1, y)])
        while stack:
            x, y = stack.pop()
            if (x, y) in visited or x < 0 or y < 0 or x >= w or y >= h:
                continue
            visited.add((x, y))
            r, g, b, a = image.get_at((x, y))
            if a == 0:
                continue
            if abs(r - kr) > tolerance or abs(g - kg) > tolerance or abs(b - kb) > tolerance:
                continue
            image.set_at((x, y), (r, g, b, 0))
            stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
        return image

    def _prepare_shield_sprite(self, image):
        """Xoa nen vuong con dinh o mep cua sprite khien."""
        image = image.copy().convert_alpha()
        bg_r, bg_g, bg_b, _ = image.get_at((0, 0))
        return self._clear_bg_border_pixels(image, (bg_r, bg_g, bg_b), tolerance=18)

    def _get_skill_cooldown(self):
        """Trả về giá trị cooldown skill theo loại nhân vật."""
        if self.character_type == settings.CHARACTER_KNIGHT:
            return settings.SKILL_KNIGHT_COOLDOWN
        elif self.character_type == settings.CHARACTER_SORCERER:
            return settings.SKILL_SORCERER_COOLDOWN
        elif self.character_type == settings.CHARACTER_PRIEST:
            return settings.SKILL_PRIEST_COOLDOWN
        return 0
    
    def use_skill(self):
        """
        Kích hoạt skill của đồng hành.
        Cooldown bắt đầu SAU KHI skill hết tác dụng (đối với skill có duration).
        
        Returns:
            str hoặc None: Loại skill được kích hoạt, None nếu không thể dùng
        """
        if not self.can_use_skill:
            return None
        
        self.can_use_skill = False
        
        if self.character_type == settings.CHARACTER_KNIGHT:
            # Bật khiên - cooldown tính SAU KHI khiên hết
            self.skill_active = True
            self.skill_duration_timer = settings.SKILL_KNIGHT_DURATION
            self.skill_cooldown_timer = 0  # Chưa tính cooldown
            play_sound(self.shield_sound, volume=0.5)
            return "shield"
        
        elif self.character_type == settings.CHARACTER_SORCERER:
            # Bắn fireball - cooldown bắt đầu ngay
            self.skill_cast_timer = settings.SORCERER_SKILL_CAST_FRAMES
            self.skill_cooldown_timer = self.skill_cooldown_max
            play_sound(self.sorcerer_skill_sound, volume=0.5)
            return "fireball"
        
        elif self.character_type == settings.CHARACTER_PRIEST:
            # Hồi máu cho player chính - cooldown bắt đầu ngay
            if self.main_player.hp < self.main_player.max_hp:
                self.skill_cast_timer = settings.PRIEST_SKILL_CAST_FRAMES
                self.frame_index = 0
                self.update_time = pygame.time.get_ticks()
                self.main_player.heal(1)

                self.skill_cooldown_timer = self.skill_cooldown_max
                play_sound(self.heal_sound, volume=0.5)
                return "heal"
            else:
                # Đầy máu rồi, hoàn cooldown
                self.can_use_skill = True
                self.skill_cooldown_timer = 0
                return None
        
        return None
    
    def has_active_shield(self):
        """Kiểm tra đồng hành có đang bật khiên không."""
        return self.skill_active and self.character_type == settings.CHARACTER_KNIGHT
    
    def update(self):
        """Cập nhật vị trí và trạng thái đồng hành mỗi frame."""
        # Theo sau vị trí player chính
        self.x = self.main_player.x + self.offset_x
        
        # Sao chép trạng thái cúi
        self.is_ducking = self.main_player.is_ducking
        if self.is_ducking:
            self.height = self.duck_height
        else:
            self.height = int(settings.PLAYER_HEIGHT * self.scale)
        
        # Căn chỉnh chân với player chính
        main_foot_y = self.main_player.y + (
            settings.PLAYER_DUCK_HEIGHT if self.main_player.is_ducking 
            else settings.PLAYER_HEIGHT
        )
        self.y = main_foot_y - self.height
        
        # Thời lượng skill (Knight shield)
        if self.skill_active:
            self.skill_duration_timer -= 1
            self.shield_pulse += 0.1
            if self.skill_duration_timer <= 0:
                self.skill_active = False
                self.shield_pulse = 0
                # Cooldown bắt đầu SAU KHI skill hết tác dụng
                self.skill_cooldown_timer = self.skill_cooldown_max
        
        # --- CẬP NHẬT ANIMATION ---
        if self.animations:
            previous_state = self.animation_state
            # Đồng bộ trạng thái với player chính
            self.animation_state = self._resolve_supported_state(self.main_player.animation_state)
            
            # Trình trạng đặc thù: Skill cast cho Sorcerer đồng hành
            if self.character_type in (settings.CHARACTER_SORCERER, settings.CHARACTER_PRIEST) and getattr(self, 'skill_cast_timer', 0) > 0:
                self.animation_state = 'skill'
                self.skill_cast_timer -= 1
            
            if previous_state != self.animation_state:
                self.frame_index = 0
                self.update_time = pygame.time.get_ticks()
            
            # Chuyển frame
            current_time = pygame.time.get_ticks()
            if self.character_type == settings.CHARACTER_SORCERER:
                cooldown = settings.SORCERER_ANIMATION_COOLDOWN
            elif self.character_type == settings.CHARACTER_PRIEST:
                cooldown = settings.PRIEST_ANIMATION_COOLDOWN
            else:
                cooldown = settings.ANIMATION_COOLDOWN
            if current_time - self.update_time > cooldown:
                self.update_time = current_time
                self.frame_index += 1
                if self.frame_index >= len(self.animations[self.animation_state]):
                    self.frame_index = 0
                    
        # Đếm ngược cooldown skill (chỉ đếm khi skill không đang active)
        if not self.can_use_skill and not self.skill_active:
            if self.skill_cooldown_timer > 0:
                self.skill_cooldown_timer -= 1
                if self.skill_cooldown_timer <= 0:
                    self.can_use_skill = True
        
        # Hoạt ảnh xuất hiện
        if self.spawn_timer > 0:
            self.spawn_timer -= 1
        

        
        # Cập nhật hitbox
        self.rect.update(self.x, self.y, self.width, self.height)
    
    def draw(self, screen, draw_individual_shield=True):
        """Vẽ đồng hành lên màn hình."""
        if self.main_player.is_dead:
            image_rect = self.dead_frame.get_rect(midbottom=self.rect.midbottom)
            screen.blit(self.dead_frame, image_rect)
            return

        if self.spawn_timer > 0:
            alpha = int(255 * (1 - self.spawn_timer / 60))
        else:
            alpha = 255
            
        # Hiệu ứng nhấp nháy khi player bất tử (sau khi trúng đòn)
        if self.main_player.invincible_timer > 0 and (self.main_player.invincible_timer // 6) % 2 == 0:
            return
        
        self._draw_character(screen, alpha, draw_individual_shield=draw_individual_shield)
    
    def _draw_character(self, screen, alpha=255, draw_individual_shield=True):
        """Vẽ nhân vật đồng hành theo loại."""
        if self.animations:
            # Vẽ bằng Sprite
            state = self.animation_state
            if self.frame_index >= len(self.animations[state]):
                self.frame_index = 0
            current_image = self.animations[state][self.frame_index].copy()
            
            # Xử lý alpha cho hiệu ứng spawn
            if alpha < 255:
                current_image.set_alpha(alpha)
            
            # Vẽ sprite căn chỉnh vào trung tâm hitbox
            image_rect = current_image.get_rect(midbottom=self.rect.midbottom)
            
            # Fix vị trí đặc thù cho sorcerer dash
            if self.character_type == settings.CHARACTER_SORCERER and state == 'dash':
                image_rect.x += 12 # scaled offset
            elif self.character_type == settings.CHARACTER_PRIEST and state == 'duck':
                image_rect.y += 10

            if not (self.character_type == settings.CHARACTER_PRIEST and state in ('dash', 'duck')):
                screen.blit(current_image, image_rect)
            if self.character_type == settings.CHARACTER_PRIEST:
                self._draw_priest_state_effect(screen, image_rect, alpha)
        else:
            # Fallback về hình học (cho Priest)
            surf = pygame.Surface((self.width + 20, self.height + 40), pygame.SRCALPHA)
            ox, oy = 10, 20
            
            if self.character_type == settings.CHARACTER_KNIGHT:
                self._draw_knight_on(surf, ox, oy, alpha)
            elif self.character_type == settings.CHARACTER_SORCERER:
                self._draw_sorcerer_on(surf, ox, oy, alpha)
            elif self.character_type == settings.CHARACTER_PRIEST:
                self._draw_priest_on(surf, ox, oy, alpha)
            
            screen.blit(surf, (self.x - 10, self.y - 20))
        
        # Hiệu ứng khiên
        if draw_individual_shield and self.skill_active and self.character_type == settings.CHARACTER_KNIGHT:
            self._draw_shield_sprite(screen, settings.COLOR_SHIELD_SKILL, alpha=alpha)
        

        
        # Chỉ báo phím skill
        key_num = "2" if self.companion_index == 0 else "3"
        kf = pygame.font.Font(None, 18)
        kt = kf.render(f"[{key_num}]", True, (180, 170, 160))
        screen.blit(kt, (self.x + self.width // 2 - 8, self.y - 16))

    def _draw_shield_sprite(self, screen, color, base_padding=16, pulse_amplitude=4, alpha=255):
        if not self.shield_sprite:
            pulse = int(math.sin(self.shield_pulse) * 4)
            sr = self.rect.inflate(12 + pulse, 12 + pulse)
            ss = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
            sa = min(int(80 + 30 * math.sin(self.shield_pulse * 2)), 255)
            pygame.draw.rect(ss, (*color, sa), (0, 0, sr.width, sr.height), border_radius=8)
            pygame.draw.rect(ss, (*color, min(sa + 40, 255)), (0, 0, sr.width, sr.height), 2, border_radius=8)
            screen.blit(ss, sr.topleft)
            return

        base_size = max(self.width, self.height) + base_padding * 2
        pulse_size = int(pulse_amplitude * 3 * math.sin(self.shield_pulse))
        size = max(20, base_size + pulse_size)
        shield_image = pygame.transform.smoothscale(self.shield_sprite, (size, size))
        shield_image = shield_image.copy()
        tint = pygame.Surface((size, size), pygame.SRCALPHA)
        tint.fill((*color, 70))
        shield_image.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        shield_image.set_alpha(min(alpha, 190))
        shield_rect = shield_image.get_rect(center=self.rect.center)
        screen.blit(shield_image, shield_rect)

    def _draw_priest_state_effect(self, screen, image_rect, alpha=255):
        """Váº½ FX riÃªng cho Priest Ä‘á»“ng hÃ nh."""
        effect_image = None
        effect_rect = None

        if self.animation_state == 'dash':
            effect_image = self._get_effect_frame(self.priest_dash_effect, 'dash')
            if effect_image:
                effect_image = effect_image.copy()
                effect_rect = effect_image.get_rect(center=image_rect.center)
                effect_rect.x += 30
        elif self.animation_state == 'duck':
            effect_image = self._get_effect_frame(self.priest_duck_effect, 'duck')
            if effect_image:
                effect_image = effect_image.copy()
                effect_rect = effect_image.get_rect(midbottom=(image_rect.centerx, settings.GROUND_Y + 15))
        elif self.animation_state == 'skill':
            effect_image = self._get_effect_frame(self.priest_skill_effect, 'skill')
            if effect_image:
                effect_image = effect_image.copy()
                effect_rect = effect_image.get_rect(midbottom=(image_rect.centerx + 6, self.rect.bottom + 4))

        if effect_image and effect_rect:
            if alpha < 255:
                effect_image.set_alpha(alpha)
            screen.blit(effect_image, effect_rect)
    
    def _draw_knight_on(self, surf, ox, oy, alpha):
        """Vẽ Knight đồng hành."""
        w, h = self.width, self.height
        body = pygame.Rect(ox, oy, w, h)
        pygame.draw.rect(surf, (*settings.COLOR_PLAYER, alpha), body, border_radius=3)
        # Mũ giáp
        vh = 12 if not self.is_ducking else 7
        pygame.draw.rect(surf, (*settings.COLOR_PLAYER_VISOR, alpha),
                        pygame.Rect(ox, oy, w, vh), border_radius=3)
        # Mắt
        ey = oy + (6 if not self.is_ducking else 4)
        pygame.draw.circle(surf, (*settings.COLOR_WHITE, alpha), (ox + int(w*0.6), ey), 2)
        pygame.draw.circle(surf, (*settings.COLOR_WHITE, alpha), (ox + int(w*0.8), ey), 2)
        # Viền
        pygame.draw.rect(surf, (*settings.COLOR_BLACK, alpha), body, 2, border_radius=3)
    
    def _draw_sorcerer_on(self, surf, ox, oy, alpha):
        """Vẽ Sorcerer đồng hành."""
        w, h = self.width, self.height
        # Áo choàng
        robe = [(ox+4, oy+10), (ox+w-4, oy+10), (ox+w+2, oy+h), (ox-2, oy+h)]
        pygame.draw.polygon(surf, (*settings.COLOR_SORCERER, alpha), robe)
        pygame.draw.polygon(surf, (*settings.COLOR_BLACK, alpha), robe, 2)
        # Mũ phù thủy
        hh = 18 if not self.is_ducking else 8
        hat = [(ox+2, oy+12), (ox+w//2, oy-hh), (ox+w-2, oy+12)]
        pygame.draw.polygon(surf, (*settings.COLOR_SORCERER_HAT, alpha), hat)
        pygame.draw.polygon(surf, (*settings.COLOR_BLACK, alpha), hat, 2)
        # Vành mũ
        pygame.draw.ellipse(surf, (*settings.COLOR_SORCERER_HAT, alpha),
                           pygame.Rect(ox-2, oy+9, w+4, 5))
        # Mắt phát sáng
        ey = oy + (15 if not self.is_ducking else 6)
        pygame.draw.circle(surf, (*settings.COLOR_SORCERER_ACCENT, alpha), (ox+int(w*0.55), ey), 2)
        pygame.draw.circle(surf, (*settings.COLOR_SORCERER_ACCENT, alpha), (ox+int(w*0.75), ey), 2)
    
    def _draw_priest_on(self, surf, ox, oy, alpha):
        """Vẽ Priest đồng hành."""
        w, h = self.width, self.height
        # Áo tu
        body = pygame.Rect(ox, oy, w, h)
        pygame.draw.rect(surf, (*settings.COLOR_PRIEST, alpha), body, border_radius=5)
        # Mũ trùm (hood)
        hh = 15 if not self.is_ducking else 8
        hood = pygame.Rect(ox-1, oy, w+2, hh)
        pygame.draw.ellipse(surf, (*settings.COLOR_PRIEST_HOOD, alpha), hood)
        pygame.draw.ellipse(surf, (*settings.COLOR_BLACK, alpha), hood, 2)
        # Mắt hiền
        ey = oy + (9 if not self.is_ducking else 5)
        pygame.draw.circle(surf, (80, 60, 40, alpha), (ox+int(w*0.55), ey), 2)
        pygame.draw.circle(surf, (80, 60, 40, alpha), (ox+int(w*0.75), ey), 2)
        # Thánh giá
        cx, cy = ox + w//2, oy + h//2 - 3
        pygame.draw.line(surf, (*settings.COLOR_PRIEST_ACCENT, alpha), (cx-4, cy), (cx+4, cy), 2)
        pygame.draw.line(surf, (*settings.COLOR_PRIEST_ACCENT, alpha), (cx, cy-6), (cx, cy+6), 2)
        # Vầng sáng
        pygame.draw.ellipse(surf, (*settings.COLOR_PRIEST_ACCENT, alpha),
                           pygame.Rect(ox+6, oy-5, w-12, 6), 2)
        # Viền
        pygame.draw.rect(surf, (*settings.COLOR_BLACK, alpha), body, 2, border_radius=5)
