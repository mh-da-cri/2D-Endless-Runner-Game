"""Game over state."""

import math
import sys

import pygame

import settings
from utils.asset_loader import load_font, load_image, load_sound, play_sound
from utils.music_manager import play_music
from utils.score_manager import load_save_data, save_save_data

GAMEOVER_TITLE_IMAGE = "gameover_ha_cut.png"
GAMEOVER_TITLE_FALLBACK_IMAGE = "gameover_ha.png"
GAMEOVER_TITLE_SCALE = 1.2


class GameOverState:
    """Shows final score and retry/menu actions."""

    PANEL_MID = (78, 61, 52)
    PANEL_HOVER = (99, 75, 59)
    GOLD_DARK = (104, 70, 39)
    GOLD = (195, 133, 66)
    GOLD_LIGHT = (255, 214, 137)
    TEXT_GOLD = (255, 224, 163)
    TEXT_SHADOW = (78, 30, 34)

    def __init__(self, game_manager, final_score, previous_highscore, bg_snapshot=None, previous_play_state=None):
        self.game_manager = game_manager
        self.screen = game_manager.screen
        self.bg_snapshot = bg_snapshot
        self.previous_play_state = previous_play_state

        self.final_score = int(final_score)
        
        save_data = load_save_data()
        self.previous_highscore = save_data.get('highscore', 0)
        self.is_new_record = self.final_score > self.previous_highscore
        self.highscore = max(self.final_score, self.previous_highscore)
        save_data['highscore'] = self.highscore
        
        # Calculate money
        self.earned_money = math.ceil(self.final_score / 2)
        save_data['money'] = save_data.get('money', 0) + self.earned_money
        
        self.inventory = save_data.get('inventory', {})
        
        can_revive_this_run = not self.previous_play_state or not getattr(self.previous_play_state, 'has_revived_this_run', False)
        self.has_revive = self.inventory.get('revive', 0) > 0 and can_revive_this_run
        save_save_data(save_data)

        self.title_font = load_font(72, "georgia")
        self.score_font = load_font(34, "georgia")
        self.hint_font = load_font(settings.GAMEOVER_HINT_SIZE)
        self.button_font = load_font(42, "georgia")
        self.title_sprite = self._load_title_sprite()

        center_x = settings.SCREEN_WIDTH // 2
        center_y = settings.SCREEN_HEIGHT // 2
        button_width = 420
        button_height = 64

        self.retry_button = pygame.Rect(
            center_x - button_width // 2,
            center_y + 80,
            button_width,
            button_height,
        )
        self.menu_button = pygame.Rect(
            center_x - button_width // 2,
            center_y + 80 + button_height + 18,
            button_width,
            button_height,
        )

        self.retry_hovered = False
        self.menu_hovered = False
        self.revive_hovered = False
        self.frame_count = 0
        self.fade_alpha = 0
        self.click_sound = load_sound(settings.UI_CLICK_SOUND)

        play_music(settings.GAMEOVER_MUSIC, settings.BACKGROUND_MUSIC_VOLUME)

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        self.retry_hovered = self.retry_button.collidepoint(mouse_pos)
        self.menu_hovered = self.menu_button.collidepoint(mouse_pos)

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.retry_hovered:
                    play_sound(self.click_sound, volume=0.5)
                    if self.has_revive and self.previous_play_state:
                        # Revive
                        self.inventory['revive'] -= 1
                        save_data = load_save_data()
                        save_data['inventory']['revive'] = self.inventory['revive']
                        save_save_data(save_data)
                        
                        self.previous_play_state.has_revived_this_run = True
                        
                        self.previous_play_state.player.hp = self.previous_play_state.player.max_hp
                        self.previous_play_state.player.is_dead = False
                        self.previous_play_state.player.invincible_timer = settings.INVINCIBILITY_FRAMES
                        self.previous_play_state.hit_stop_timer = 0
                        self.previous_play_state.pending_game_over = False
                        self.previous_play_state.obstacles.clear()
                        
                        self.game_manager.change_state(self.previous_play_state)
                        play_music(settings.COMBAT_MUSIC, settings.BACKGROUND_MUSIC_VOLUME)
                    else:
                        from states.character_select_state import CharacterSelectState
                        self.game_manager.change_state(CharacterSelectState(self.game_manager))
                elif self.menu_hovered:
                    play_sound(self.click_sound, volume=0.5)
                    from states.menu_state import MenuState
                    self.game_manager.change_state(MenuState(self.game_manager))

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    from states.character_select_state import CharacterSelectState

                    self.game_manager.change_state(CharacterSelectState(self.game_manager))
                elif event.key == pygame.K_ESCAPE:
                    from states.menu_state import MenuState

                    self.game_manager.change_state(MenuState(self.game_manager))

    def update(self):
        self.frame_count += 1
        if self.fade_alpha < 180:
            self.fade_alpha = min(180, self.fade_alpha + 5)

    def draw(self):
        if self.bg_snapshot:
            self.screen.blit(self.bg_snapshot, (0, 0))
        else:
            self.screen.fill((4, 7, 10))

        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.fade_alpha))
        self.screen.blit(overlay, (0, 0))

        center_x = settings.SCREEN_WIDTH // 2

        title_rect = self._draw_title(center_x)

        score_text = self.score_font.render(f"Score: {self.final_score}", True, self.TEXT_GOLD)
        score_rect = score_text.get_rect(center=(center_x, title_rect.bottom + 16))
        self._draw_text_surface(score_text, score_rect, shadow=self.TEXT_SHADOW, outline=(45, 27, 22))

        high_text = self.score_font.render(f"Best: {self.highscore}", True, (238, 223, 196))
        high_rect = high_text.get_rect(center=(center_x, score_rect.bottom + 32))
        self._draw_text_surface(high_text, high_rect, shadow=(39, 27, 22))

        if self.is_new_record and math.sin(self.frame_count * 0.1) > 0:
            record_text = self.hint_font.render("NEW RECORD!", True, self.GOLD_LIGHT)
            record_rect = record_text.get_rect(center=(center_x, high_rect.bottom + 30))
            self._draw_text_surface(record_text, record_rect, shadow=self.TEXT_SHADOW)
            
        money_text = self.score_font.render(f"+ {self.earned_money} Money", True, (255, 215, 0))
        money_rect = money_text.get_rect(center=(center_x, high_rect.bottom + (48 if self.is_new_record else 18)))
        self._draw_text_surface(money_text, money_rect, shadow=self.TEXT_SHADOW)

        retry_text = "REVIVE" if self.has_revive and self.previous_play_state else "PLAY AGAIN"
        self._draw_button(self.retry_button, retry_text, self.retry_hovered)
        self._draw_button(self.menu_button, "MAIN MENU", self.menu_hovered)

        hint_text = self.hint_font.render("SPACE to retry  |  ESC for menu", True, (177, 148, 103))
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = center_x
        hint_rect.bottom = settings.SCREEN_HEIGHT - 20
        self._draw_text_surface(hint_text, hint_rect, shadow=(42, 29, 22))

    def _draw_title(self, center_x):
        if self.title_sprite:
            title_rect = self.title_sprite.get_rect(center=(center_x, 152))
            shadow = self.title_sprite.copy()
            shadow.fill((90, 18, 18, 180), special_flags=pygame.BLEND_RGBA_MULT)
            shadow.set_alpha(165)
            self.screen.blit(shadow, title_rect.move(8, 9))
            self.screen.blit(self.title_sprite, title_rect)
            return title_rect

        title_text = self.title_font.render("GAME OVER", True, (232, 54, 50))
        scaled_title = pygame.transform.smoothscale(
            title_text,
            (
                max(1, int(title_text.get_width() * GAMEOVER_TITLE_SCALE)),
                max(1, int(title_text.get_height() * GAMEOVER_TITLE_SCALE)),
            ),
        )
        title_rect = scaled_title.get_rect(center=(center_x, settings.SCREEN_HEIGHT // 4 + 10))
        self._draw_text_surface(scaled_title, title_rect, shadow=(72, 13, 15), outline=(28, 18, 18))
        return title_rect

    def _load_title_sprite(self):
        for filename in (GAMEOVER_TITLE_IMAGE, GAMEOVER_TITLE_FALLBACK_IMAGE):
            try:
                sprite = load_image(filename, convert_alpha=True).copy()
                bounds = sprite.get_bounding_rect(min_alpha=8)
                if bounds.width <= 0 or bounds.height <= 0:
                    continue

                sprite = sprite.subsurface(bounds).copy()
                max_width = int(settings.SCREEN_WIDTH * 0.72)
                max_height = int(settings.SCREEN_HEIGHT * 0.35)
                scale = min(max_width / sprite.get_width(), max_height / sprite.get_height())
                if scale <= 0:
                    continue
                scale *= GAMEOVER_TITLE_SCALE

                size = (
                    max(1, int(sprite.get_width() * scale)),
                    max(1, int(sprite.get_height() * scale)),
                )
                return pygame.transform.smoothscale(sprite, size)
            except Exception:
                continue
        return None

    def _draw_button(self, rect, text, is_hovered):
        draw_rect = rect.move(0, -3 if is_hovered else 0)
        if is_hovered:
            glow = pygame.Surface((draw_rect.width + 34, draw_rect.height + 26), pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 196, 96, 42), glow.get_rect(), border_radius=12)
            self.screen.blit(glow, (draw_rect.x - 17, draw_rect.y - 13))

        fill = self.PANEL_HOVER if is_hovered else self.PANEL_MID
        self._draw_ornate_panel(draw_rect, fill)
        self._draw_button_corners(draw_rect, bright=is_hovered)

        btn_text = self.button_font.render(text, True, self.TEXT_GOLD if not is_hovered else (255, 236, 186))
        btn_rect = btn_text.get_rect(center=draw_rect.center)
        self._draw_text_surface(btn_text, btn_rect, shadow=self.TEXT_SHADOW, outline=(59, 25, 28))

    def _draw_ornate_panel(self, rect, fill):
        cut = 14
        outer = self._beveled_points(rect, cut)
        shadow = [(x + 6, y + 6) for x, y in outer]
        pygame.draw.polygon(self.screen, (16, 17, 18), shadow)
        pygame.draw.polygon(self.screen, (52, 43, 42), outer)
        pygame.draw.polygon(self.screen, self.GOLD_DARK, outer, 5)
        pygame.draw.polygon(self.screen, self.GOLD_LIGHT, outer, 2)

        mid = rect.inflate(-12, -12)
        pygame.draw.polygon(self.screen, self.GOLD, self._beveled_points(mid, 9), 3)

        inner = rect.inflate(-24, -24)
        inner_points = self._beveled_points(inner, 6)
        pygame.draw.polygon(self.screen, fill, inner_points)
        pygame.draw.polygon(self.screen, (73, 36, 38), inner_points, 2)

        pygame.draw.line(self.screen, (255, 225, 143), (inner.left + 22, inner.top + 6), (inner.right - 22, inner.top + 6), 2)
        pygame.draw.line(self.screen, (51, 31, 29), (inner.left + 22, inner.bottom - 7), (inner.right - 22, inner.bottom - 7), 2)

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
