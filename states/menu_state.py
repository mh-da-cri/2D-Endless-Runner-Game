"""Main menu state."""

import math
import sys

import pygame

import settings
from utils.asset_loader import load_font, load_image, load_sound, play_sound


class MenuState:
    """Main menu with an ornate fantasy pixel-art style."""

    PANEL_DARK = (45, 37, 36)
    PANEL_MID = (78, 61, 52)
    PANEL_HOVER = (99, 75, 59)
    GOLD_DARK = (104, 70, 39)
    GOLD = (195, 133, 66)
    GOLD_LIGHT = (255, 214, 137)
    TEXT_GOLD = (255, 224, 163)
    TEXT_SHADOW = (78, 30, 34)

    def __init__(self, game_manager):
        if getattr(settings, 'IS_ADMIN_TEST_MODE', False):
            import importlib
            importlib.reload(settings)
            settings.IS_ADMIN_TEST_MODE = False
            import utils.score_manager
            utils.score_manager.reset_test_save()
            
        import importlib

        importlib.reload(settings)

        self.game_manager = game_manager
        self.screen = game_manager.screen
        self.background_image = self._load_background()

        self.logo_font = load_font(72, "georgia")
        self.logo_sub_font = load_font(40, "georgia")
        self.subtitle_font = load_font(30, "georgia")
        self.button_font = load_font(48, "georgia")
        self.tutorial_title_font = load_font(34, "georgia")
        self.tutorial_font = load_font(24)
        self.tutorial_key_font = load_font(22)

        center_x = settings.SCREEN_WIDTH // 2
        button_width = 560
        button_height = 66
        button_gap = 22
        button_y = 352

        self.play_button = pygame.Rect(center_x - button_width // 2, button_y, button_width, button_height)
        self.tutorial_button = self.play_button.move(0, button_height + button_gap)
        self.admin_button = self.tutorial_button.move(0, button_height + button_gap)
        self.exit_button = self.admin_button.move(0, button_height + button_gap)

        self.play_hovered = False
        self.tutorial_hovered = False
        self.admin_hovered = False
        self.exit_hovered = False
        self.tutorial_close_hovered = False

        self.show_tutorial = False
        self.tutorial_panel = pygame.Rect(0, 0, 520, 282)
        self.tutorial_panel.center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        self.tutorial_close_button = pygame.Rect(
            self.tutorial_panel.right - 45,
            self.tutorial_panel.top + 15,
            30,
            30,
        )

        self.title_y_offset = 0
        self.title_direction = 1
        self.frame_count = 0

        self.click_sound = load_sound(settings.UI_CLICK_SOUND)
        self._play_menu_music()

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()

        if self.show_tutorial:
            self._handle_tutorial_events(events, mouse_pos)
            return

        self.play_hovered = self.play_button.collidepoint(mouse_pos)
        self.tutorial_hovered = self.tutorial_button.collidepoint(mouse_pos)
        self.admin_hovered = self.admin_button.collidepoint(mouse_pos)
        self.exit_hovered = self.exit_button.collidepoint(mouse_pos)

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.play_hovered:
                    play_sound(self.click_sound, volume=0.5)
                    from states.character_select_state import CharacterSelectState

                    self.game_manager.change_state(CharacterSelectState(self.game_manager))

                elif self.tutorial_hovered:
                    play_sound(self.click_sound, volume=0.5)
                    self.show_tutorial = True

                elif self.admin_hovered:
                    play_sound(self.click_sound, volume=0.5)
                    from states.admin_config_state import AdminConfigState

                    self.game_manager.change_state(AdminConfigState(self.game_manager))

                elif self.exit_hovered:
                    play_sound(self.click_sound, volume=0.5)
                    pygame.quit()
                    sys.exit()

    def update(self):
        self.frame_count += 1

        if self.frame_count % 3 == 0:
            self.title_y_offset += self.title_direction * 0.45
            if abs(self.title_y_offset) > 4:
                self.title_direction *= -1

    def draw(self):
        self._draw_background()
        self._draw_title_banner()

        subtitle = self.subtitle_font.render("A High Fantasy Endless Runner", True, (233, 205, 177))
        self._draw_text_surface(subtitle, subtitle.get_rect(center=(settings.SCREEN_WIDTH // 2, 318)))

        self._draw_button(self.play_button, "PLAY", self.play_hovered)
        self._draw_button(self.tutorial_button, "TUTORIAL", self.tutorial_hovered)
        self._draw_button(self.admin_button, "ADMIN MODE", self.admin_hovered)
        self._draw_button(self.exit_button, "EXIT", self.exit_hovered)

        if self.show_tutorial:
            self._draw_tutorial_popup()

    def _handle_tutorial_events(self, events, mouse_pos):
        self.play_hovered = False
        self.tutorial_hovered = False
        self.admin_hovered = False
        self.exit_hovered = False
        self.tutorial_close_hovered = self.tutorial_close_button.collidepoint(mouse_pos)

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                play_sound(self.click_sound, volume=0.4)
                self.show_tutorial = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.tutorial_close_hovered or not self.tutorial_panel.collidepoint(mouse_pos):
                    play_sound(self.click_sound, volume=0.4)
                    self.show_tutorial = False

    def _draw_background(self):
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill(settings.COLOR_MENU_BG)

        haze = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        haze.fill((5, 12, 25, 78))
        self.screen.blit(haze, (0, 0))

        vignette = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(0, 190, 10):
            alpha = int(8 + i * 0.28)
            rect = pygame.Rect(i // 2, i // 2, settings.SCREEN_WIDTH - i, settings.SCREEN_HEIGHT - i)
            pygame.draw.rect(vignette, (0, 0, 0, alpha), rect, 10)
        self.screen.blit(vignette, (0, 0))

        sparkles = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(34):
            drift = self.frame_count * (0.08 + i * 0.004)
            x = int((i * 97 + drift) % settings.SCREEN_WIDTH)
            y = int((i * 53 + 22 + math.sin(self.frame_count * 0.012 + i) * 7) % settings.SCREEN_HEIGHT)
            pulse = 35 + int(22 * math.sin(self.frame_count * 0.035 + i * 0.8))
            radius = 1 + (i % 3 == 0)
            pygame.draw.circle(sparkles, (205, 213, 207, pulse), (x, y), radius)
        self.screen.blit(sparkles, (0, 0))

    def _draw_title_banner(self):
        top = 86 + int(self.title_y_offset)
        panel = pygame.Rect(0, top, 850, 178)
        panel.centerx = settings.SCREEN_WIDTH // 2
        cx = panel.centerx

        self._draw_crossed_swords(cx, top - 74)
        self._draw_ornate_panel(panel, self.PANEL_DARK, large=True)
        self._draw_title_scrollwork(panel)
        self._draw_shield(cx, top - 96, scale=0.84)

        title = self.logo_font.render("KNIGHT RUNNER", True, self.TEXT_GOLD)
        title_rect = title.get_rect(center=(cx, panel.y + 76))
        self._draw_text_surface(title, title_rect, shadow=(94, 30, 38), outline=(58, 28, 29))

        subtitle = self.logo_sub_font.render("Endless Fantasy", True, (234, 181, 146))
        subtitle_rect = subtitle.get_rect(center=(cx, panel.y + 128))
        self._draw_text_surface(subtitle, subtitle_rect, shadow=(60, 27, 26), outline=(45, 28, 28))

    def _draw_button(self, rect, text, is_hovered):
        draw_rect = rect.move(0, -3 if is_hovered else 0)
        if is_hovered:
            glow = pygame.Surface((draw_rect.width + 36, draw_rect.height + 28), pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 196, 96, 42), glow.get_rect(), border_radius=12)
            self.screen.blit(glow, (draw_rect.x - 18, draw_rect.y - 14))

        fill = self.PANEL_HOVER if is_hovered else self.PANEL_MID
        self._draw_ornate_panel(draw_rect, fill)
        self._draw_button_corners(draw_rect, bright=is_hovered)

        label = self.button_font.render(text, True, self.TEXT_GOLD if not is_hovered else (255, 236, 186))
        label_rect = label.get_rect(center=draw_rect.center)
        self._draw_text_surface(label, label_rect, shadow=self.TEXT_SHADOW, outline=(59, 25, 28))

    def _draw_ornate_panel(self, rect, fill, large=False):
        cut = 18 if large else 14
        outer = self._beveled_points(rect, cut)
        shadow = [(x + 6, y + 6) for x, y in outer]
        pygame.draw.polygon(self.screen, (16, 17, 18), shadow)
        pygame.draw.polygon(self.screen, (52, 43, 42), outer)
        pygame.draw.polygon(self.screen, self.GOLD_DARK, outer, 5)
        pygame.draw.polygon(self.screen, self.GOLD_LIGHT, outer, 2)

        mid = rect.inflate(-12, -12)
        mid_points = self._beveled_points(mid, max(6, cut - 5))
        pygame.draw.polygon(self.screen, self.GOLD, mid_points, 3)

        inner = rect.inflate(-24, -24)
        inner_points = self._beveled_points(inner, max(4, cut - 8))
        pygame.draw.polygon(self.screen, fill, inner_points)
        pygame.draw.polygon(self.screen, (73, 36, 38), inner_points, 2)

        pygame.draw.line(
            self.screen,
            (255, 225, 143),
            (inner.left + 22, inner.top + 6),
            (inner.right - 22, inner.top + 6),
            2,
        )
        pygame.draw.line(
            self.screen,
            (51, 31, 29),
            (inner.left + 22, inner.bottom - 7),
            (inner.right - 22, inner.bottom - 7),
            2,
        )

    def _draw_title_scrollwork(self, rect):
        gold = (214, 151, 86)
        dark = (85, 49, 37)
        y = rect.top + 33
        left_anchor = rect.left + 170
        right_anchor = rect.right - 170

        for sign, anchor in ((1, left_anchor), (-1, right_anchor)):
            pygame.draw.line(self.screen, dark, (anchor, y + 6), (anchor + sign * 115, y + 6), 4)
            pygame.draw.line(self.screen, gold, (anchor, y + 4), (anchor + sign * 115, y + 4), 2)
            pygame.draw.line(
                self.screen,
                gold,
                (anchor + sign * 26, y + 4),
                (anchor + sign * 40, y - 9),
                2,
            )
            pygame.draw.line(
                self.screen,
                gold,
                (anchor + sign * 50, y + 4),
                (anchor + sign * 62, y - 6),
                2,
            )

        self._draw_corner_scroll(rect.left + 33, rect.top + 36, 1, 1)
        self._draw_corner_scroll(rect.right - 33, rect.top + 36, -1, 1)
        self._draw_corner_scroll(rect.left + 33, rect.bottom - 36, 1, -1)
        self._draw_corner_scroll(rect.right - 33, rect.bottom - 36, -1, -1)

    def _draw_button_corners(self, rect, bright=False):
        color = self.GOLD_LIGHT if bright else (219, 156, 88)
        dark = (77, 42, 35)
        for x, y, sx, sy in (
            (rect.left + 35, rect.top + 20, 1, 1),
            (rect.right - 35, rect.top + 20, -1, 1),
            (rect.left + 35, rect.bottom - 20, 1, -1),
            (rect.right - 35, rect.bottom - 20, -1, -1),
        ):
            pygame.draw.line(self.screen, dark, (x, y), (x + sx * 28, y), 4)
            pygame.draw.line(self.screen, dark, (x, y), (x, y + sy * 13), 4)
            pygame.draw.line(self.screen, color, (x, y), (x + sx * 28, y), 2)
            pygame.draw.line(self.screen, color, (x, y), (x, y + sy * 13), 2)
            pygame.draw.line(self.screen, color, (x + sx * 10, y + sy * 2), (x + sx * 18, y + sy * 10), 2)

    def _draw_corner_scroll(self, x, y, sx, sy):
        color = (224, 160, 88)
        dark = (79, 45, 37)
        pygame.draw.line(self.screen, dark, (x, y), (x + sx * 65, y), 5)
        pygame.draw.line(self.screen, color, (x, y), (x + sx * 65, y), 2)
        pygame.draw.line(self.screen, color, (x, y), (x, y + sy * 30), 2)
        pygame.draw.line(self.screen, color, (x + sx * 16, y + sy * 2), (x + sx * 28, y + sy * 13), 2)
        pygame.draw.line(self.screen, color, (x + sx * 35, y + sy * 2), (x + sx * 48, y + sy * 11), 2)

    def _draw_crossed_swords(self, cx, y):
        swords = [
            ((cx - 120, y + 8), (cx + 32, y + 156), -1),
            ((cx + 120, y + 8), (cx - 32, y + 156), 1),
        ]
        for handle, tip, sign in swords:
            hx, hy = handle
            tx, ty = tip
            pygame.draw.line(self.screen, (47, 33, 29), (hx + 3, hy + 3), (tx + 3, ty + 3), 7)
            pygame.draw.line(self.screen, (180, 178, 165), (hx, hy), (tx, ty), 5)
            pygame.draw.line(self.screen, (245, 230, 186), (hx + sign * 4, hy + 6), (tx + sign * 4, ty - 6), 2)
            pygame.draw.line(self.screen, (84, 57, 42), (hx - sign * 20, hy + 20), (hx + sign * 18, hy + 55), 8)
            pygame.draw.line(self.screen, (167, 116, 75), (hx - sign * 16, hy + 19), (hx + sign * 14, hy + 51), 3)
            pygame.draw.circle(self.screen, (113, 74, 48), (hx, hy), 7)
            pygame.draw.circle(self.screen, self.GOLD_LIGHT, (hx, hy), 3)

    def _draw_shield(self, cx, y, scale=1.0):
        def point(dx, dy):
            return (cx + int(dx * scale), y + int(dy * scale))

        shadow_offset = max(3, int(5 * scale))
        shield = [
            point(0, 18),
            point(48, 40),
            point(42, 104),
            point(0, 144),
            point(-42, 104),
            point(-48, 40),
        ]
        pygame.draw.polygon(
            self.screen,
            (38, 28, 22),
            [(x + shadow_offset, yy + shadow_offset) for x, yy in shield],
        )
        pygame.draw.polygon(self.screen, (114, 79, 45), shield)
        pygame.draw.polygon(self.screen, (230, 169, 87), shield, 3)

        left_face = [point(0, 24), point(0, 137), point(-35, 99), point(-40, 47)]
        right_face = [point(0, 24), point(40, 47), point(35, 99), point(0, 137)]
        pygame.draw.polygon(self.screen, (156, 108, 58), left_face)
        pygame.draw.polygon(self.screen, (91, 64, 39), right_face)
        pygame.draw.line(self.screen, (246, 196, 112), point(0, 25), point(0, 136), 2)
        pygame.draw.arc(
            self.screen,
            (193, 137, 73),
            pygame.Rect(cx - int(28 * scale), y + int(46 * scale), max(1, int(24 * scale)), max(1, int(24 * scale))),
            4.6,
            6.2,
            2,
        )
        pygame.draw.arc(
            self.screen,
            (193, 137, 73),
            pygame.Rect(cx + int(4 * scale), y + int(46 * scale), max(1, int(24 * scale)), max(1, int(24 * scale))),
            3.1,
            4.8,
            2,
        )
        pygame.draw.line(self.screen, (82, 52, 34), point(-23, 92), point(-9, 106), 2)
        pygame.draw.line(self.screen, (82, 52, 34), point(23, 92), point(9, 106), 2)

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

    def _draw_tutorial_popup(self):
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        panel = self.tutorial_panel
        self._draw_ornate_panel(panel, self.PANEL_MID)

        title = self.tutorial_title_font.render("TUTORIAL", True, self.TEXT_GOLD)
        title_rect = title.get_rect(center=(panel.centerx, panel.y + 43))
        self._draw_text_surface(title, title_rect, shadow=self.TEXT_SHADOW, outline=(54, 26, 28))

        close_color = self.GOLD_LIGHT if self.tutorial_close_hovered else self.GOLD
        pygame.draw.rect(self.screen, (40, 31, 25), self.tutorial_close_button.move(2, 2), border_radius=3)
        pygame.draw.rect(self.screen, close_color, self.tutorial_close_button, border_radius=3)
        pygame.draw.rect(self.screen, (48, 39, 34), self.tutorial_close_button, 2, border_radius=3)
        x_text = self.tutorial_key_font.render("X", True, (34, 25, 21))
        self.screen.blit(x_text, x_text.get_rect(center=self.tutorial_close_button.center))

        rows = [
            ("SPACE", "Jump / Double Jump", "jump"),
            ("DOWN", "Duck", "down"),
            ("SHIFT", "Dash", "dash"),
            ("P / ESC", "Pause", "pause"),
        ]

        start_y = panel.y + 86
        for index, (key, action, icon) in enumerate(rows):
            row_y = start_y + index * 40
            icon_rect = pygame.Rect(panel.x + 42, row_y - 4, 36, 28)
            self._draw_tutorial_icon(icon_rect, icon)

            key_text = self.tutorial_font.render(f"{key}:", True, (113, 230, 232))
            action_text = self.tutorial_font.render(action, True, (250, 236, 210))
            text_x = panel.x + 96
            self._draw_tutorial_text(key_text, (text_x, row_y))
            self._draw_tutorial_text(action_text, (text_x + key_text.get_width() + 8, row_y))

        hint = self.tutorial_key_font.render("ESC / SPACE / click outside to close", True, (169, 139, 96))
        self.screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 30)))

    def _draw_tutorial_icon(self, rect, icon):
        pygame.draw.rect(self.screen, (24, 42, 43), rect.move(2, 2), border_radius=2)
        pygame.draw.rect(self.screen, (59, 89, 91), rect, border_radius=2)
        pygame.draw.rect(self.screen, (97, 210, 215), rect, 2, border_radius=2)

        cx, cy = rect.center
        color = (164, 245, 246)
        if icon == "jump":
            pygame.draw.polygon(
                self.screen,
                color,
                [(cx, cy - 9), (cx - 8, cy + 1), (cx - 3, cy + 1), (cx - 3, cy + 8), (cx + 3, cy + 8), (cx + 3, cy + 1), (cx + 8, cy + 1)],
            )
        elif icon == "down":
            pygame.draw.polygon(
                self.screen,
                color,
                [(cx, cy + 9), (cx - 8, cy - 1), (cx - 3, cy - 1), (cx - 3, cy - 8), (cx + 3, cy - 8), (cx + 3, cy - 1), (cx + 8, cy - 1)],
            )
        elif icon == "dash":
            pygame.draw.line(self.screen, color, (rect.left + 7, cy), (rect.right - 8, cy), 3)
            pygame.draw.polygon(self.screen, color, [(rect.right - 8, cy), (rect.right - 16, cy - 7), (rect.right - 16, cy + 7)])
            pygame.draw.line(self.screen, color, (rect.left + 5, cy - 6), (rect.left + 13, cy - 6), 2)
            pygame.draw.line(self.screen, color, (rect.left + 3, cy + 6), (rect.left + 11, cy + 6), 2)
        else:
            pygame.draw.rect(self.screen, color, (cx - 8, cy - 9, 5, 18))
            pygame.draw.rect(self.screen, color, (cx + 3, cy - 9, 5, 18))

    def _draw_tutorial_text(self, text_surface, pos):
        x, y = pos
        shadow = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
        shadow.blit(text_surface, (0, 0))
        shadow.fill((41, 27, 20, 210), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(shadow, (x + 2, y + 2))
        self.screen.blit(text_surface, (x, y))

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

    def _play_menu_music(self):
        import os

        try:
            music_path = os.path.join("assets", "audio", settings.MENU_MUSIC)
            pygame.mixer.music.stop()
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(settings.BACKGROUND_MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
        except (pygame.error, FileNotFoundError):
            pass
