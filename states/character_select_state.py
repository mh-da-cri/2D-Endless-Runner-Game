"""Character selection state."""

import math
import random
import sys

import pygame

import settings
from utils.asset_loader import load_font, load_image, load_sound, play_sound
from utils.music_manager import play_music


class CharacterSelectState:
    """Hero selection screen with an ornate fantasy menu style."""

    PANEL_DARK = (45, 37, 36)
    PANEL_MID = (78, 61, 52)
    PANEL_HOVER = (99, 75, 59)
    GOLD_DARK = (104, 70, 39)
    GOLD = (195, 133, 66)
    GOLD_LIGHT = (255, 214, 137)
    TEXT_GOLD = (255, 224, 163)
    TEXT_SHADOW = (78, 30, 34)

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
        self.game_manager = game_manager
        self.screen = game_manager.screen
        self.background_image = self._load_background()

        self.title_font = load_font(58, "georgia")
        self.name_font = load_font(36, "georgia")
        self.desc_font = load_font(22, "georgia")
        self.small_font = load_font(17)
        self.hint_font = load_font(settings.GAMEOVER_HINT_SIZE)
        self.button_font = load_font(25, "georgia")
        self.badge_font = load_font(18)
        self.question_font = load_font(82, "georgia")

        self.card_width = 248
        self.card_height = 374
        self.card_gap = 26
        total_width = self.card_width * 4 + self.card_gap * 3
        start_x = (settings.SCREEN_WIDTH - total_width) // 2
        card_y = 232
        self.card_rects = [
            pygame.Rect(start_x + i * (self.card_width + self.card_gap), card_y, self.card_width, self.card_height)
            for i in range(4)
        ]

        self.back_button = pygame.Rect(34, settings.SCREEN_HEIGHT - 76, 170, 54)
        self.hovered_card = -1
        self.back_hovered = False
        self.frame_count = 0
        self.selected_card = -1
        self.select_timer = 0

        self._load_preview_sprites()
        self.click_sound = load_sound(settings.UI_CLICK_SOUND)
        play_music(settings.MENU_MUSIC, settings.BACKGROUND_MUSIC_VOLUME)

    def _load_preview_sprites(self):
        self.knight_preview = None
        self.sorcerer_preview = None
        self.priest_preview = None
        target_h = 116

        try:
            from utils.spritesheet import SpriteSheet

            w, h = settings.SPRITE_FRAME_WIDTH, settings.SPRITE_FRAME_HEIGHT
            knight_img = load_image(settings.SPRITE_IMAGE, convert_alpha=True)
            knight_sheet = SpriteSheet(knight_img)
            self.knight_preview = knight_sheet.get_image(0, 0, w, h, target_h / h)
        except Exception:
            pass

        try:
            from utils.spritesheet import SpriteSheet

            priest_img = load_image(settings.PRIEST_SPRITE_IMAGE, convert_alpha=True)
            priest_sheet = SpriteSheet(priest_img)
            inset = 2
            x, y, w, h = 33, 67, 120, 106
            frame = priest_sheet.get_image_at(x + inset, y + inset, w - inset * 2, h - inset * 2, 1)
            frame = frame.copy().convert_alpha()
            self._clear_color(frame, settings.PRIEST_SHEET_COLORKEY, tolerance=3)
            self._clear_edge_color(frame, settings.PRIEST_SHEET_COLORKEY, tolerance=10)
            scale = target_h / frame.get_height()
            self.priest_preview = pygame.transform.scale(
                frame,
                (int(frame.get_width() * scale), target_h),
            )
        except Exception:
            pass

        try:
            from utils.spritesheet import SpriteSheet

            sorc_img = load_image(settings.SORCERER_SPRITE_IMAGE, convert_alpha=True)
            sorc_sheet = SpriteSheet(sorc_img)
            inset = 2
            fw, fh = 76 - inset * 2, 76 - inset * 2
            frame = sorc_sheet.get_image_at(47 + inset, 14 + inset, fw, fh, 1)
            frame = frame.copy().convert_alpha()
            self._clear_color(frame, settings.SORCERER_SHEET_COLORKEY, tolerance=2)
            scale = target_h / fh
            self.sorcerer_preview = pygame.transform.scale(
                frame,
                (int(fw * scale), target_h),
            )
        except Exception:
            pass

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
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
                elif event.key == pygame.K_1:
                    self._select_character(0)
                elif event.key == pygame.K_2:
                    self._select_character(1)
                elif event.key == pygame.K_3:
                    self._select_character(2)
                elif event.key == pygame.K_4:
                    self._select_character(3)

    def _select_character(self, index):
        if index < 3:
            char_type = self.CHARACTERS[index]["type"]
        else:
            char_type = random.choice([
                settings.CHARACTER_KNIGHT,
                settings.CHARACTER_SORCERER,
                settings.CHARACTER_PRIEST,
            ])

        from states.play_state import PlayState

        self.game_manager.change_state(PlayState(self.game_manager, character_type=char_type))

    def update(self):
        self.frame_count += 1

    def draw(self):
        self._draw_background()
        self._draw_header()

        for i, char_info in enumerate(self.CHARACTERS):
            self._draw_character_card(i, char_info)
        self._draw_random_card()
        self._draw_back_button()

        footer_text = self.hint_font.render(
            "Click to select  |  1-4 Quick Select  |  ESC to go back",
            True,
            (177, 148, 103),
        )
        footer_rect = footer_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT - 25))
        self._draw_text_surface(footer_text, footer_rect, shadow=(42, 29, 22))

    def _draw_background(self):
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill(settings.COLOR_MENU_BG)

        haze = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        haze.fill((5, 12, 25, 96))
        self.screen.blit(haze, (0, 0))

        vignette = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(0, 190, 10):
            alpha = int(9 + i * 0.3)
            rect = pygame.Rect(i // 2, i // 2, settings.SCREEN_WIDTH - i, settings.SCREEN_HEIGHT - i)
            pygame.draw.rect(vignette, (0, 0, 0, alpha), rect, 10)
        self.screen.blit(vignette, (0, 0))

        sparkles = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(30):
            drift = self.frame_count * (0.07 + i * 0.003)
            x = int((i * 83 + drift) % settings.SCREEN_WIDTH)
            y = int((i * 47 + 31 + math.sin(self.frame_count * 0.012 + i) * 8) % settings.SCREEN_HEIGHT)
            pulse = 30 + int(20 * math.sin(self.frame_count * 0.035 + i * 0.8))
            pygame.draw.circle(sparkles, (205, 213, 207, pulse), (x, y), 1 + (i % 4 == 0))
        self.screen.blit(sparkles, (0, 0))

    def _draw_header(self):
        panel = pygame.Rect(0, 54, 700, 116)
        panel.centerx = settings.SCREEN_WIDTH // 2
        self._draw_ornate_panel(panel, self.PANEL_DARK, large=True)
        self._draw_header_scrollwork(panel)

        title = self.title_font.render("CHOOSE YOUR HERO", True, self.TEXT_GOLD)
        title_rect = title.get_rect(center=(panel.centerx, panel.centery - 3))
        self._draw_text_surface(title, title_rect, shadow=self.TEXT_SHADOW, outline=(58, 28, 29))

        subtitle = self.small_font.render("Pick a champion before entering the forest pass", True, (220, 179, 126))
        subtitle_rect = subtitle.get_rect(center=(panel.centerx, panel.bottom + 27))
        self._draw_text_surface(subtitle, subtitle_rect, shadow=(39, 28, 23))

    def _draw_character_card(self, index, char_info):
        rect = self.card_rects[index]
        is_hovered = self.hovered_card == index
        draw_rect = rect.move(0, -10 if is_hovered else 0)

        if is_hovered:
            glow = pygame.Surface((draw_rect.width + 34, draw_rect.height + 34), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*char_info["accent"], 42), glow.get_rect(), border_radius=16)
            self.screen.blit(glow, (draw_rect.x - 17, draw_rect.y - 17))

        fill = self.PANEL_HOVER if is_hovered else self.PANEL_DARK
        self._draw_ornate_panel(draw_rect, fill)
        self._draw_card_corners(draw_rect, char_info["accent"], is_hovered)
        self._draw_key_badge(draw_rect.x + 18, draw_rect.y + 17, str(index + 1), is_hovered)

        preview_cx = draw_rect.centerx
        preview_cy = draw_rect.y + 93
        preview_glow = pygame.Surface((150, 122), pygame.SRCALPHA)
        pygame.draw.ellipse(preview_glow, (*char_info["accent"], 28 if is_hovered else 16), preview_glow.get_rect())
        self.screen.blit(preview_glow, (preview_cx - 75, preview_cy - 58))
        self._draw_character_preview(preview_cx, preview_cy, char_info, is_hovered)

        name_text = self.name_font.render(char_info["name"].upper(), True, self.TEXT_GOLD)
        name_rect = name_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 181))
        self._draw_text_surface(name_text, name_rect, shadow=self.TEXT_SHADOW, outline=(55, 25, 26))

        subtitle_text = self.small_font.render(char_info["subtitle"], True, char_info["accent"])
        subtitle_rect = subtitle_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 213))
        self._draw_text_surface(subtitle_text, subtitle_rect, shadow=(31, 25, 24))

        self._draw_separator(draw_rect, draw_rect.y + 238)

        skill_label = self.desc_font.render(f"Skill: {char_info['skill_name']}", True, self.TEXT_GOLD)
        skill_rect = skill_label.get_rect(center=(draw_rect.centerx, draw_rect.y + 268))
        self._draw_text_surface(skill_label, skill_rect, shadow=self.TEXT_SHADOW)

        desc_text = self.small_font.render(char_info["skill_desc"], True, (235, 218, 190))
        desc_rect = desc_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 303))
        self._draw_text_surface(desc_text, desc_rect, shadow=(39, 27, 22))

        cd_text = self.small_font.render(f"Cooldown: {char_info['cooldown']}", True, (178, 146, 100))
        cd_rect = cd_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 333))
        self._draw_text_surface(cd_text, cd_rect, shadow=(39, 27, 22))

    def _draw_character_preview(self, cx, cy, char_info, is_hovered):
        float_offset = math.sin(self.frame_count * 0.05) * 3 if is_hovered else 0
        cy += float_offset
        char_type = char_info["type"]

        if char_type == settings.CHARACTER_KNIGHT and self.knight_preview:
            img_rect = self.knight_preview.get_rect(center=(int(cx), int(cy)))
            self.screen.blit(self.knight_preview, img_rect)
            return

        if char_type == settings.CHARACTER_SORCERER and self.sorcerer_preview:
            img_rect = self.sorcerer_preview.get_rect(center=(int(cx), int(cy)))
            self.screen.blit(self.sorcerer_preview, img_rect)
            return

        if char_type == settings.CHARACTER_PRIEST and self.priest_preview:
            img_rect = self.priest_preview.get_rect(center=(int(cx), int(cy)))
            self.screen.blit(self.priest_preview, img_rect)
            return

        self._draw_fallback_preview(int(cx), int(cy), char_info)

    def _draw_random_card(self):
        rect = self.card_rects[3]
        is_hovered = self.hovered_card == 3
        draw_rect = rect.move(0, -10 if is_hovered else 0)

        t = self.frame_count * 0.025
        r = int(158 + 58 * math.sin(t))
        g = int(142 + 48 * math.sin(t + 2.1))
        b = int(118 + 38 * math.sin(t + 4.2))
        accent = (r, g, b)

        if is_hovered:
            glow = pygame.Surface((draw_rect.width + 34, draw_rect.height + 34), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*accent, 42), glow.get_rect(), border_radius=16)
            self.screen.blit(glow, (draw_rect.x - 17, draw_rect.y - 17))

        fill = self.PANEL_HOVER if is_hovered else self.PANEL_DARK
        self._draw_ornate_panel(draw_rect, fill)
        self._draw_card_corners(draw_rect, accent, is_hovered)
        self._draw_key_badge(draw_rect.x + 18, draw_rect.y + 17, "4", is_hovered)

        question = self.question_font.render("?", True, self.GOLD_LIGHT if is_hovered else self.TEXT_GOLD)
        q_rect = question.get_rect(center=(draw_rect.centerx, draw_rect.y + 95))
        if is_hovered:
            q_rect.y += int(math.sin(self.frame_count * 0.08) * 5)
        self._draw_text_surface(question, q_rect, shadow=self.TEXT_SHADOW, outline=(58, 28, 29))

        name_text = self.name_font.render("RANDOM", True, self.TEXT_GOLD)
        name_rect = name_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 181))
        self._draw_text_surface(name_text, name_rect, shadow=self.TEXT_SHADOW, outline=(55, 25, 26))

        subtitle_text = self.small_font.render("Surprise Me!", True, self.GOLD_LIGHT)
        subtitle_rect = subtitle_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 213))
        self._draw_text_surface(subtitle_text, subtitle_rect, shadow=(31, 25, 24))

        self._draw_separator(draw_rect, draw_rect.y + 238)

        lines = ["The system will randomly", "pick one of 3 heroes", "for you!"]
        for i, line in enumerate(lines):
            text = self.small_font.render(line, True, (235, 218, 190))
            text_rect = text.get_rect(center=(draw_rect.centerx, draw_rect.y + 276 + i * 30))
            self._draw_text_surface(text, text_rect, shadow=(39, 27, 22))

    def _draw_back_button(self):
        draw_rect = self.back_button.move(0, -3 if self.back_hovered else 0)
        if self.back_hovered:
            glow = pygame.Surface((draw_rect.width + 28, draw_rect.height + 24), pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 196, 96, 42), glow.get_rect(), border_radius=10)
            self.screen.blit(glow, (draw_rect.x - 14, draw_rect.y - 12))

        self._draw_ornate_panel(draw_rect, self.PANEL_HOVER if self.back_hovered else self.PANEL_MID)
        label = self.button_font.render("< BACK", True, self.TEXT_GOLD)
        self._draw_text_surface(
            label,
            label.get_rect(center=draw_rect.center),
            shadow=self.TEXT_SHADOW,
            outline=(58, 28, 29),
        )

    def _draw_ornate_panel(self, rect, fill, large=False):
        cut = 18 if large else 14
        outer = self._beveled_points(rect, cut)
        shadow = [(x + 6, y + 6) for x, y in outer]
        pygame.draw.polygon(self.screen, (16, 17, 18), shadow)
        pygame.draw.polygon(self.screen, (52, 43, 42), outer)
        pygame.draw.polygon(self.screen, self.GOLD_DARK, outer, 5)
        pygame.draw.polygon(self.screen, self.GOLD_LIGHT, outer, 2)

        mid = rect.inflate(-12, -12)
        pygame.draw.polygon(self.screen, self.GOLD, self._beveled_points(mid, max(6, cut - 5)), 3)

        inner = rect.inflate(-24, -24)
        inner_points = self._beveled_points(inner, max(4, cut - 8))
        pygame.draw.polygon(self.screen, fill, inner_points)
        pygame.draw.polygon(self.screen, (73, 36, 38), inner_points, 2)

        pygame.draw.line(self.screen, (255, 225, 143), (inner.left + 18, inner.top + 6), (inner.right - 18, inner.top + 6), 2)
        pygame.draw.line(self.screen, (51, 31, 29), (inner.left + 18, inner.bottom - 7), (inner.right - 18, inner.bottom - 7), 2)

    def _draw_card_corners(self, rect, accent, bright=False):
        color = self.GOLD_LIGHT if bright else self.GOLD
        for x, y, sx, sy in (
            (rect.left + 32, rect.top + 24, 1, 1),
            (rect.right - 32, rect.top + 24, -1, 1),
            (rect.left + 32, rect.bottom - 24, 1, -1),
            (rect.right - 32, rect.bottom - 24, -1, -1),
        ):
            pygame.draw.line(self.screen, (73, 42, 35), (x, y), (x + sx * 29, y), 4)
            pygame.draw.line(self.screen, (73, 42, 35), (x, y), (x, y + sy * 14), 4)
            pygame.draw.line(self.screen, color, (x, y), (x + sx * 29, y), 2)
            pygame.draw.line(self.screen, color, (x, y), (x, y + sy * 14), 2)
        pygame.draw.rect(self.screen, (*accent, 45 if bright else 24), rect.inflate(-30, -30), 1, border_radius=8)

    def _draw_header_scrollwork(self, rect):
        for x, sx in ((rect.left + 55, 1), (rect.right - 55, -1)):
            self._draw_scroll(x, rect.centery, sx)

    def _draw_scroll(self, x, y, sx):
        color = (224, 160, 88)
        pygame.draw.line(self.screen, (79, 45, 37), (x, y), (x + sx * 75, y), 5)
        pygame.draw.line(self.screen, color, (x, y), (x + sx * 75, y), 2)
        for i in range(2):
            arc = pygame.Rect(x + sx * (18 + i * 28), y - 24 + i * 2, 38, 34)
            if sx < 0:
                arc.right = x - (18 + i * 28)
            pygame.draw.arc(self.screen, color, arc, 0, math.pi * 1.4, 2)

    def _draw_key_badge(self, x, y, label, is_hovered):
        rect = pygame.Rect(x, y, 34, 26)
        pygame.draw.rect(self.screen, (31, 25, 22), rect.move(2, 2), border_radius=3)
        pygame.draw.rect(self.screen, self.GOLD_LIGHT if is_hovered else self.GOLD, rect, border_radius=3)
        pygame.draw.rect(self.screen, (70, 43, 33), rect, 2, border_radius=3)
        text = self.badge_font.render(f"[{label}]", True, (46, 29, 24))
        self.screen.blit(text, text.get_rect(center=rect.center))

    def _draw_separator(self, rect, y):
        pygame.draw.line(self.screen, (59, 37, 32), (rect.x + 32, y + 2), (rect.right - 32, y + 2), 3)
        pygame.draw.line(self.screen, self.GOLD, (rect.x + 34, y), (rect.right - 34, y), 1)
        pygame.draw.circle(self.screen, self.GOLD_LIGHT, (rect.centerx, y), 3)

    def _draw_text_surface(self, surface, rect, shadow=(47, 31, 30), outline=None):
        if outline:
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)):
                outline_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                outline_surface.blit(surface, (0, 0))
                outline_surface.fill((*outline, 255), special_flags=pygame.BLEND_RGBA_MULT)
                self.screen.blit(outline_surface, rect.move(dx, dy))

        shadow_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shadow_surface.blit(surface, (0, 0))
        shadow_surface.fill((*shadow, 230), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(shadow_surface, rect.move(3, 4))
        self.screen.blit(surface, rect)

    def _draw_fallback_preview(self, cx, cy, char_info):
        w, h = 42, 62
        body_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
        pygame.draw.rect(self.screen, char_info["color"], body_rect, border_radius=6)
        pygame.draw.rect(self.screen, (23, 20, 22), body_rect, 2, border_radius=6)
        pygame.draw.circle(self.screen, char_info["accent"], (cx + 8, cy - h // 2 + 16), 4)

    def _clear_color(self, surface, color, tolerance=3):
        kr, kg, kb = color
        for y in range(surface.get_height()):
            for x in range(surface.get_width()):
                r, g, b, a = surface.get_at((x, y))
                if abs(r - kr) <= tolerance and abs(g - kg) <= tolerance and abs(b - kb) <= tolerance:
                    surface.set_at((x, y), (r, g, b, 0))

    def _clear_edge_color(self, surface, color, tolerance=10):
        kr, kg, kb = color
        stack = []
        visited = set()
        width, height = surface.get_size()
        for edge_x in range(width):
            stack.extend([(edge_x, 0), (edge_x, height - 1)])
        for edge_y in range(height):
            stack.extend([(0, edge_y), (width - 1, edge_y)])

        while stack:
            x, y = stack.pop()
            if (x, y) in visited or x < 0 or y < 0 or x >= width or y >= height:
                continue
            visited.add((x, y))
            r, g, b, a = surface.get_at((x, y))
            if a == 0:
                continue
            if abs(r - kr) > tolerance or abs(g - kg) > tolerance or abs(b - kb) > tolerance:
                continue
            surface.set_at((x, y), (r, g, b, 0))
            stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

    def _beveled_points(self, rect, cut):
        return [
            (rect.left + cut, rect.top),
            (rect.right - cut, rect.top),
            (rect.right, rect.top + cut),
            (rect.right, rect.bottom - cut),
            (rect.right - cut, rect.bottom),
            (rect.left + cut, rect.bottom),
            (rect.left, rect.bottom - cut),
            (rect.left, rect.top + cut),
        ]

    def _load_background(self):
        try:
            image = load_image("BG_2.jpg", convert_alpha=False)
            target_size = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
            if image.get_size() == target_size:
                return image

            image_w, image_h = image.get_size()
            scale = max(settings.SCREEN_WIDTH / image_w, settings.SCREEN_HEIGHT / image_h)
            scaled_size = (int(image_w * scale), int(image_h * scale))
            image = pygame.transform.smoothscale(image, scaled_size)

            background = pygame.Surface(target_size)
            x = (settings.SCREEN_WIDTH - scaled_size[0]) // 2
            y = (settings.SCREEN_HEIGHT - scaled_size[1]) // 2
            background.blit(image, (x, y))
            return background
        except Exception:
            return None
