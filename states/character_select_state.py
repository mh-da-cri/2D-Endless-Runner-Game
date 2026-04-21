"""
Character Select State - Màn hình chọn nhân vật
Hiển thị 3 nhân vật + 1 slot Random để chọn trước khi vào game.
"""

import pygame
import sys
import math
import random
import settings
from utils.asset_loader import load_font, load_sound, play_sound


class CharacterSelectState:
    """Trạng thái màn hình chọn nhân vật."""
    
    # Thông tin các nhân vật
    CHARACTERS = [
        {
            "type": settings.CHARACTER_KNIGHT,
            "name": "Knight",
            "subtitle": "Tank Warrior",
            "skill_name": "Shield",
            "skill_desc": "Immune to damage for 10s",
            "cooldown": "30s",
            "color": settings.COLOR_PLAYER,
            "accent": settings.COLOR_PLAYER_VISOR,
        },
        {
            "type": settings.CHARACTER_SORCERER,
            "name": "Sorcerer",
            "subtitle": "Fire Mage",
            "skill_name": "Fireball",
            "skill_desc": "Shoots 3 fireballs",
            "cooldown": "5s",
            "color": settings.COLOR_SORCERER,
            "accent": settings.COLOR_SORCERER_ACCENT,
        },
        {
            "type": settings.CHARACTER_PRIEST,
            "name": "Priest",
            "subtitle": "Holy Healer",
            "skill_name": "Heal",
            "skill_desc": "Restores 1 HP",
            "cooldown": "60s",
            "color": settings.COLOR_PRIEST,
            "accent": settings.COLOR_PRIEST_ACCENT,
        },
    ]
    
    def __init__(self, game_manager):
        """
        Khởi tạo character select state.
        
        Args:
            game_manager: Reference đến GameManager
        """
        self.game_manager = game_manager
        self.screen = game_manager.screen
        
        # Fonts
        self.title_font = load_font(settings.TITLE_FONT_SIZE)
        self.name_font = load_font(36)
        self.desc_font = load_font(20)
        self.small_font = load_font(16)
        self.hint_font = load_font(settings.GAMEOVER_HINT_SIZE)
        
        # Card layout
        self.card_width = 220
        self.card_height = 340
        self.card_gap = 30
        total_width = self.card_width * 4 + self.card_gap * 3
        start_x = (settings.SCREEN_WIDTH - total_width) // 2
        card_y = settings.SCREEN_HEIGHT // 2 - self.card_height // 2 + 30
        
        # Tạo 4 card rects (3 nhân vật + 1 random)
        self.card_rects = []
        for i in range(4):
            x = start_x + i * (self.card_width + self.card_gap)
            self.card_rects.append(pygame.Rect(x, card_y, self.card_width, self.card_height))
        
        # Back button
        self.back_button = pygame.Rect(
            20, settings.SCREEN_HEIGHT - 70,
            120, 45
        )
        
        # Hover state
        self.hovered_card = -1
        self.back_hovered = False
        
        # Animation
        self.frame_count = 0
        self.selected_card = -1  # Card đang được chọn (animation)
        self.select_timer = 0
        
        # Load sprite previews cho Knight và Sorcerer
        self._load_preview_sprites()
        self.click_sound = load_sound(settings.UI_CLICK_SOUND)
    
    def _load_preview_sprites(self):
        """Load sprite frame idle dùng cho preview trong card chọn nhân vật."""
        self.knight_preview = None
        self.sorcerer_preview = None
        self.priest_preview = None
        target_h = 115  # Chiều cao hiển thị trong card
        
        # Knight - idle frame (cột 0, hàng 0)
        try:
            from utils.spritesheet import SpriteSheet
            from utils.asset_loader import load_image
            w, h = settings.SPRITE_FRAME_WIDTH, settings.SPRITE_FRAME_HEIGHT
            knight_img = load_image(settings.SPRITE_IMAGE, convert_alpha=True)
            knight_sheet = SpriteSheet(knight_img)
            self.knight_preview = knight_sheet.get_image(0, 0, w, h, target_h / h)
        except Exception:
            pass

        # Priest - idle frame Ä‘áº§u tiÃªn trong Priest.png
        try:
            from utils.spritesheet import SpriteSheet
            from utils.asset_loader import load_image
            priest_img = load_image(settings.PRIEST_SPRITE_IMAGE, convert_alpha=True)
            priest_sheet = SpriteSheet(priest_img)
            key = settings.PRIEST_SHEET_COLORKEY
            inset = 2
            x, y, w, h = 33, 67, 120, 106
            frame = priest_sheet.get_image_at(x + inset, y + inset, w - inset * 2, h - inset * 2, 1)
            frame = frame.copy().convert_alpha()
            kr, kg, kb = key
            for y_px in range(frame.get_height()):
                for x_px in range(frame.get_width()):
                    r, g, b, a = frame.get_at((x_px, y_px))
                    if abs(r - kr) <= 3 and abs(g - kg) <= 3 and abs(b - kb) <= 3:
                        frame.set_at((x_px, y_px), (r, g, b, 0))
            stack = []
            visited = set()
            fw, fh = frame.get_size()
            for edge_x in range(fw):
                stack.extend([(edge_x, 0), (edge_x, fh - 1)])
            for edge_y in range(fh):
                stack.extend([(0, edge_y), (fw - 1, edge_y)])
            while stack:
                px, py = stack.pop()
                if (px, py) in visited or px < 0 or py < 0 or px >= fw or py >= fh:
                    continue
                visited.add((px, py))
                r, g, b, a = frame.get_at((px, py))
                if a == 0:
                    continue
                if abs(r - kr) > 10 or abs(g - kg) > 10 or abs(b - kb) > 10:
                    continue
                frame.set_at((px, py), (r, g, b, 0))
                stack.extend([(px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)])
            scale = target_h / frame.get_height()
            self.priest_preview = pygame.transform.scale(
                frame, (int(frame.get_width() * scale), target_h)
            )
        except Exception:
            pass
        
        # Sorcerer - idle frame tại pixel (47, 14), 76x76, inset=2
        try:
            from utils.spritesheet import SpriteSheet
            from utils.asset_loader import load_image
            sorc_img = load_image(settings.SORCERER_SPRITE_IMAGE, convert_alpha=True)
            sorc_sheet = SpriteSheet(sorc_img)
            key = settings.SORCERER_SHEET_COLORKEY
            inset = 2
            fw, fh = 76 - inset * 2, 76 - inset * 2
            frame = sorc_sheet.get_image_at(47 + inset, 14 + inset, fw, fh, 1)
            frame = frame.copy().convert_alpha()
            # Xóa nền xám thủ công (fuzzy match)
            kr, kg, kb = key
            for y_px in range(frame.get_height()):
                for x_px in range(frame.get_width()):
                    r, g, b, a = frame.get_at((x_px, y_px))
                    if abs(r - kr) <= 2 and abs(g - kg) <= 2 and abs(b - kb) <= 2:
                        frame.set_at((x_px, y_px), (r, g, b, 0))
            scale = target_h / fh
            self.sorcerer_preview = pygame.transform.scale(
                frame, (int(fw * scale), target_h)
            )
        except Exception:
            pass
    
    def handle_events(self, events):
        """Xử lý input."""
        mouse_pos = pygame.mouse.get_pos()
        
        # Kiểm tra hover
        self.hovered_card = -1
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_card = i
                break
        
        self.back_hovered = self.back_button.collidepoint(mouse_pos)
        
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hovered_card >= 0:
                    play_sound(self.click_sound, volume=0.5)
                    self._select_character(self.hovered_card)
                
                elif self.back_hovered:
                    play_sound(self.click_sound, volume=0.5)
                    from states.menu_state import MenuState
                    self.game_manager.change_state(MenuState(self.game_manager))
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    from states.menu_state import MenuState
                    self.game_manager.change_state(MenuState(self.game_manager))
                
                # Phím 1-4 để chọn nhanh
                if event.key == pygame.K_1:
                    self._select_character(0)
                elif event.key == pygame.K_2:
                    self._select_character(1)
                elif event.key == pygame.K_3:
                    self._select_character(2)
                elif event.key == pygame.K_4:
                    self._select_character(3)
    
    def _select_character(self, index):
        """Chọn nhân vật và vào game."""
        if index < 3:
            char_type = self.CHARACTERS[index]["type"]
        else:
            # Random
            char_type = random.choice([
                settings.CHARACTER_KNIGHT,
                settings.CHARACTER_SORCERER,
                settings.CHARACTER_PRIEST
            ])
        
        from states.play_state import PlayState
        self.game_manager.change_state(PlayState(self.game_manager, character_type=char_type))
    
    def update(self):
        """Cập nhật animation."""
        self.frame_count += 1
    
    def draw(self):
        """Vẽ màn hình chọn nhân vật."""
        # Nền
        self.screen.fill(settings.COLOR_MENU_BG)
        
        # Particles trang trí
        self._draw_bg_particles()
        
        # Title
        title_text = self.title_font.render("Choose Your Hero", True, settings.COLOR_TITLE)
        title_shadow = self.title_font.render("Choose Your Hero", True, (30, 25, 15))
        title_rect = title_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 70))
        shadow_rect = title_shadow.get_rect(center=(title_rect.centerx + 3, title_rect.centery + 3))
        self.screen.blit(title_shadow, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        # Vẽ 3 character cards
        for i, char_info in enumerate(self.CHARACTERS):
            self._draw_character_card(i, char_info)
        
        # Vẽ Random card
        self._draw_random_card()
        
        # Back button
        self._draw_back_button()
        
        # Footer hint
        footer_text = self.hint_font.render(
            "Click to select  |  1-4 Quick Select  |  ESC to go back", 
            True, (120, 115, 100)
        )
        footer_rect = footer_text.get_rect(
            center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT - 25)
        )
        self.screen.blit(footer_text, footer_rect)
    
    def _draw_character_card(self, index, char_info):
        """Vẽ card nhân vật."""
        rect = self.card_rects[index]
        is_hovered = self.hovered_card == index
        
        # Hover offset
        draw_rect = rect.copy()
        if is_hovered:
            draw_rect.y -= 8
        
        # Shadow
        shadow_rect = draw_rect.copy()
        shadow_rect.y += 6
        pygame.draw.rect(self.screen, (15, 12, 25), shadow_rect, border_radius=16)
        
        # Card background
        card_bg = (40, 35, 60) if not is_hovered else (55, 48, 80)
        pygame.draw.rect(self.screen, card_bg, draw_rect, border_radius=16)
        
        # Border
        border_color = char_info["accent"] if is_hovered else (70, 60, 90)
        border_width = 3 if is_hovered else 2
        pygame.draw.rect(self.screen, border_color, draw_rect, border_width, border_radius=16)
        
        # Số thứ tự
        num_text = self.small_font.render(f"[{index + 1}]", True, (100, 90, 120))
        self.screen.blit(num_text, (draw_rect.x + 10, draw_rect.y + 10))
        
        # Character preview - vẽ placeholder nhân vật
        preview_cx = draw_rect.centerx
        preview_cy = draw_rect.y + 90
        self._draw_character_preview(preview_cx, preview_cy, char_info, is_hovered)
        
        # Tên nhân vật
        name_text = self.name_font.render(char_info["name"], True, settings.COLOR_WHITE)
        name_rect = name_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 170))
        self.screen.blit(name_text, name_rect)
        
        # Subtitle
        vn_text = self.small_font.render(char_info["subtitle"], True, char_info["accent"])
        vn_rect = vn_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 195))
        self.screen.blit(vn_text, vn_rect)
        
        # Divider line
        pygame.draw.line(
            self.screen, (70, 60, 90),
            (draw_rect.x + 20, draw_rect.y + 215),
            (draw_rect.right - 20, draw_rect.y + 215),
            1
        )
        
        # Skill name
        skill_label = self.desc_font.render(f"Skill: {char_info['skill_name']}", True, char_info["accent"])
        skill_rect = skill_label.get_rect(center=(draw_rect.centerx, draw_rect.y + 240))
        self.screen.blit(skill_label, skill_rect)
        
        # Skill description
        desc_text = self.small_font.render(char_info["skill_desc"], True, settings.COLOR_TEXT)
        desc_rect = desc_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 268))
        self.screen.blit(desc_text, desc_rect)
        
        # Cooldown
        cd_text = self.small_font.render(f"Cooldown: {char_info['cooldown']}", True, (150, 140, 130))
        cd_rect = cd_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 293))
        self.screen.blit(cd_text, cd_rect)
        
        # Hover glow
        if is_hovered:
            glow = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*char_info["accent"], 20), 
                           (0, 0, draw_rect.width, draw_rect.height), border_radius=16)
            self.screen.blit(glow, draw_rect.topleft)
    
    def _draw_character_preview(self, cx, cy, char_info, is_hovered):
        """Vẽ preview nhân vật trong card - sprite thực cho Knight và Sorcerer."""
        float_offset = math.sin(self.frame_count * 0.05) * 3 if is_hovered else 0
        cy += float_offset
        char_type = char_info["type"]
        
        # Knight - dùng sprite idle thực
        if char_type == settings.CHARACTER_KNIGHT and self.knight_preview:
            img_rect = self.knight_preview.get_rect(center=(int(cx), int(cy)))
            self.screen.blit(self.knight_preview, img_rect)
            return
        
        # Sorcerer - dùng sprite idle thực
        if char_type == settings.CHARACTER_SORCERER and self.sorcerer_preview:
            img_rect = self.sorcerer_preview.get_rect(center=(int(cx), int(cy)))
            self.screen.blit(self.sorcerer_preview, img_rect)
            return
        
        if char_type == settings.CHARACTER_PRIEST and self.priest_preview:
            img_rect = self.priest_preview.get_rect(center=(int(cx), int(cy)))
            self.screen.blit(self.priest_preview, img_rect)
            return

        # Fallback placeholder (Priest + khi sprite lỗi)
        cy = int(cy)
        w, h = 40, 60
        
        if char_type == settings.CHARACTER_KNIGHT:
            body_rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
            pygame.draw.rect(self.screen, settings.COLOR_PLAYER, body_rect, border_radius=4)
            visor_rect = pygame.Rect(cx - w//2, cy - h//2, w, 12)
            pygame.draw.rect(self.screen, settings.COLOR_PLAYER_VISOR, visor_rect, border_radius=4)
            pygame.draw.circle(self.screen, settings.COLOR_WHITE, (cx + 3, cy - h//2 + 8), 2)
            pygame.draw.circle(self.screen, settings.COLOR_WHITE, (cx + 10, cy - h//2 + 8), 2)
            pygame.draw.rect(self.screen, settings.COLOR_BLACK, body_rect, 2, border_radius=4)
        
        elif char_type == settings.CHARACTER_SORCERER:
            robe_points = [
                (cx - w//2 + 4, cy - h//2 + 12),
                (cx + w//2 - 4, cy - h//2 + 12),
                (cx + w//2 + 2, cy + h//2),
                (cx - w//2 - 2, cy + h//2),
            ]
            pygame.draw.polygon(self.screen, settings.COLOR_SORCERER, robe_points)
            pygame.draw.polygon(self.screen, settings.COLOR_BLACK, robe_points, 2)
            hat_points = [
                (cx - w//2 + 2, cy - h//2 + 14),
                (cx, cy - h//2 - 18),
                (cx + w//2 - 2, cy - h//2 + 14),
            ]
            pygame.draw.polygon(self.screen, settings.COLOR_SORCERER_HAT, hat_points)
            pygame.draw.polygon(self.screen, settings.COLOR_BLACK, hat_points, 2)
            pygame.draw.circle(self.screen, settings.COLOR_SORCERER_ACCENT, (cx + 2, cy - h//2 + 18), 2)
            pygame.draw.circle(self.screen, settings.COLOR_SORCERER_ACCENT, (cx + 10, cy - h//2 + 18), 2)
        
        elif char_type == settings.CHARACTER_PRIEST:
            body_rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
            pygame.draw.rect(self.screen, settings.COLOR_PRIEST, body_rect, border_radius=6)
            hood_rect = pygame.Rect(cx - w//2 - 1, cy - h//2, w + 2, 16)
            pygame.draw.ellipse(self.screen, settings.COLOR_PRIEST_HOOD, hood_rect)
            pygame.draw.ellipse(self.screen, settings.COLOR_BLACK, hood_rect, 2)
            pygame.draw.circle(self.screen, (80, 60, 40), (cx + 2, cy - h//2 + 10), 2)
            pygame.draw.circle(self.screen, (80, 60, 40), (cx + 10, cy - h//2 + 10), 2)
            pygame.draw.line(self.screen, settings.COLOR_PRIEST_ACCENT, (cx + 6, cy - 3), (cx + 6, cy + 9), 2)
            pygame.draw.line(self.screen, settings.COLOR_PRIEST_ACCENT, (cx, cy + 3), (cx + 12, cy + 3), 2)
            halo_rect = pygame.Rect(cx - 8, cy - h//2 - 6, 24, 6)
            pygame.draw.ellipse(self.screen, settings.COLOR_PRIEST_ACCENT, halo_rect, 2)
            pygame.draw.rect(self.screen, settings.COLOR_BLACK, body_rect, 2, border_radius=6)
    
    def _draw_random_card(self):
        """Vẽ card Random."""
        rect = self.card_rects[3]
        is_hovered = self.hovered_card == 3
        
        draw_rect = rect.copy()
        if is_hovered:
            draw_rect.y -= 8
        
        # Shadow
        shadow_rect = draw_rect.copy()
        shadow_rect.y += 6
        pygame.draw.rect(self.screen, (15, 12, 25), shadow_rect, border_radius=16)
        
        # Card background (gradient-ish)
        card_bg = (50, 40, 65) if not is_hovered else (65, 55, 85)
        pygame.draw.rect(self.screen, card_bg, draw_rect, border_radius=16)
        
        # Rainbow border effect
        t = self.frame_count * 0.02
        r = int(130 + 60 * math.sin(t))
        g = int(130 + 60 * math.sin(t + 2.1))
        b = int(130 + 60 * math.sin(t + 4.2))
        border_color = (r, g, b) if is_hovered else (90, 80, 110)
        border_width = 3 if is_hovered else 2
        pygame.draw.rect(self.screen, border_color, draw_rect, border_width, border_radius=16)
        
        # Số thứ tự
        num_text = self.small_font.render("[4]", True, (100, 90, 120))
        self.screen.blit(num_text, (draw_rect.x + 10, draw_rect.y + 10))
        
        # Dấu hỏi lớn
        question_font = load_font(72)
        q_color = (r, g, b) if is_hovered else settings.COLOR_TITLE
        question_text = question_font.render("?", True, q_color)
        q_rect = question_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 90))
        
        # Floating animation
        if is_hovered:
            q_rect.y += int(math.sin(self.frame_count * 0.08) * 5)
        
        self.screen.blit(question_text, q_rect)
        
        # Name
        name_text = self.name_font.render("Random", True, settings.COLOR_WHITE)
        name_rect = name_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 170))
        self.screen.blit(name_text, name_rect)
        
        # Subtitle
        sub_text = self.small_font.render("Surprise Me!", True, settings.COLOR_TITLE)
        sub_rect = sub_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 195))
        self.screen.blit(sub_text, sub_rect)
        
        # Divider
        pygame.draw.line(
            self.screen, (70, 60, 90),
            (draw_rect.x + 20, draw_rect.y + 215),
            (draw_rect.right - 20, draw_rect.y + 215),
            1
        )
        
        # Description
        desc1 = self.small_font.render("The system will randomly", True, settings.COLOR_TEXT)
        desc2 = self.small_font.render("pick one of 3 heroes", True, settings.COLOR_TEXT)
        desc3 = self.small_font.render("for you!", True, settings.COLOR_TEXT)
        desc1_rect = desc1.get_rect(center=(draw_rect.centerx, draw_rect.y + 245))
        desc2_rect = desc2.get_rect(center=(draw_rect.centerx, draw_rect.y + 268))
        desc3_rect = desc3.get_rect(center=(draw_rect.centerx, draw_rect.y + 291))
        self.screen.blit(desc1, desc1_rect)
        self.screen.blit(desc2, desc2_rect)
        self.screen.blit(desc3, desc3_rect)
        
        # Hover glow
        if is_hovered:
            glow = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow, (r, g, b, 15),
                           (0, 0, draw_rect.width, draw_rect.height), border_radius=16)
            self.screen.blit(glow, draw_rect.topleft)
    
    def _draw_back_button(self):
        """Vẽ nút Back."""
        color = settings.COLOR_BUTTON_HOVER if self.back_hovered else settings.COLOR_BUTTON
        
        # Shadow
        shadow = self.back_button.copy()
        shadow.y += 3
        pygame.draw.rect(self.screen, (20, 15, 30), shadow, border_radius=8)
        
        # Button
        pygame.draw.rect(self.screen, color, self.back_button, border_radius=8)
        
        # Border
        border_color = settings.COLOR_TITLE if self.back_hovered else (90, 70, 120)
        pygame.draw.rect(self.screen, border_color, self.back_button, 2, border_radius=8)
        
        # Text
        btn_font = load_font(22)
        btn_text = btn_font.render("← Back", True, settings.COLOR_BUTTON_TEXT)
        btn_rect = btn_text.get_rect(center=self.back_button.center)
        self.screen.blit(btn_text, btn_rect)
    
    def _draw_bg_particles(self):
        """Vẽ particles trang trí nền."""
        for i in range(25):
            x = (i * 67 + self.frame_count * (0.2 + i * 0.04)) % settings.SCREEN_WIDTH
            y = (i * 41 + 30) % settings.SCREEN_HEIGHT
            
            brightness = int(60 + 30 * math.sin(self.frame_count * 0.04 + i * 0.8))
            size = 1 + int(math.sin(self.frame_count * 0.025 + i * 0.6) > 0.6)
            
            pygame.draw.circle(
                self.screen,
                (brightness, brightness, brightness - 8),
                (int(x), int(y)),
                size
            )
