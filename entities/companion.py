"""
Companion - Nhân vật đồng hành di chuyển sau lưng player chính.
Xuất hiện từ item đặc biệt tại các mốc điểm 200 và 500.
Sao chép chuyển động của player và có skill riêng.
"""

import pygame
import math
import settings
from utils.spritesheet import SpriteSheet
from utils.asset_loader import load_image


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
        self.heal_effect_timer = 0
        self.skill_cast_timer = 0
        
        # --- SPRITE SYSTEM ---
        # Load dead sheet cho tất cả nhân vật
        dead_img = load_image(settings.SPRITE_DEAD_IMAGE, convert_alpha=True)
        self.dead_sheet = SpriteSheet(dead_img)
        
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
            
        self.frame_index = 0
        self.animation_state = 'idle'
        self.update_time = pygame.time.get_ticks()
    
        self.update_time = pygame.time.get_ticks()
        
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
        self.animations['dead'].append(self.dead_sheet.get_image(0, 0, 32, 64, s))

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
        self.animations['dead'].append(self.dead_sheet.get_image(0, 0, 32, 64, s))

    def _clear_colorkey_pixels(self, image, colorkey):
        image = image.copy().convert_alpha()
        kr, kg, kb = colorkey
        for y in range(image.get_height()):
            for x in range(image.get_width()):
                r, g, b, a = image.get_at((x, y))
                if abs(r - kr) <= 2 and abs(g - kg) <= 2 and abs(b - kb) <= 2:
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
            return "shield"
        
        elif self.character_type == settings.CHARACTER_SORCERER:
            # Bắn fireball - cooldown bắt đầu ngay
            self.skill_cast_timer = settings.SORCERER_SKILL_CAST_FRAMES
            self.skill_cooldown_timer = self.skill_cooldown_max
            return "fireball"
        
        elif self.character_type == settings.CHARACTER_PRIEST:
            # Hồi máu cho player chính - cooldown bắt đầu ngay
            if self.main_player.hp < self.main_player.max_hp:
                self.main_player.heal(1)
                self.heal_effect_timer = 60
                self.skill_cooldown_timer = self.skill_cooldown_max
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
            self.animation_state = self.main_player.animation_state
            
            # Trình trạng đặc thù: Skill cast cho Sorcerer đồng hành
            if self.character_type == settings.CHARACTER_SORCERER and getattr(self, 'skill_cast_timer', 0) > 0:
                self.animation_state = 'skill'
                self.skill_cast_timer -= 1
            
            if previous_state != self.animation_state:
                self.frame_index = 0
                self.update_time = pygame.time.get_ticks()
            
            # Chuyển frame
            current_time = pygame.time.get_ticks()
            cooldown = settings.SORCERER_ANIMATION_COOLDOWN if self.character_type == settings.CHARACTER_SORCERER else settings.ANIMATION_COOLDOWN
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
        
        # Hiệu ứng hồi máu
        if self.heal_effect_timer > 0:
            self.heal_effect_timer -= 1
        
        # Cập nhật hitbox
        self.rect.update(self.x, self.y, self.width, self.height)
    
    def draw(self, screen):
        """Vẽ đồng hành lên màn hình."""
        if self.spawn_timer > 0:
            alpha = int(255 * (1 - self.spawn_timer / 60))
        else:
            alpha = 255
        
        self._draw_character(screen, alpha)
    
    def _draw_character(self, screen, alpha=255):
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
                
            screen.blit(current_image, image_rect)
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
        if self.skill_active and self.character_type == settings.CHARACTER_KNIGHT:
            pulse = int(math.sin(self.shield_pulse) * 4)
            sr = self.rect.inflate(12 + pulse, 12 + pulse)
            ss = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
            sa = min(int(80 + 30 * math.sin(self.shield_pulse * 2)), 255)
            pygame.draw.rect(ss, (*settings.COLOR_SHIELD_SKILL, sa),
                           (0, 0, sr.width, sr.height), border_radius=8)
            pygame.draw.rect(ss, (*settings.COLOR_SHIELD_SKILL, min(sa + 40, 255)),
                           (0, 0, sr.width, sr.height), 2, border_radius=8)
            screen.blit(ss, sr.topleft)
        
        # Hiệu ứng hồi máu
        if self.heal_effect_timer > 0:
            ratio = self.heal_effect_timer / 60
            py = self.y - 15 - (1 - ratio) * 25
            font = pygame.font.Font(None, 20)
            text = font.render("+1", True, settings.COLOR_HEAL)
            screen.blit(text, (self.x + self.width // 2 - 6, py))
        
        # Chỉ báo phím skill
        key_num = "2" if self.companion_index == 0 else "3"
        kf = pygame.font.Font(None, 18)
        kt = kf.render(f"[{key_num}]", True, (180, 170, 160))
        screen.blit(kt, (self.x + self.width // 2 - 8, self.y - 16))
    
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
