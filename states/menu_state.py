"""
Menu State - Màn hình menu chính
Hiển thị tên game, 2 nút Play và Exit, điều khiển bằng chuột.
"""

import pygame
import sys
import settings
from utils.asset_loader import load_font, load_sound, play_sound
from utils.score_manager import load_highscore


class MenuState:
    """Trạng thái màn hình menu chính."""
    
    def __init__(self, game_manager):
        """
        Khởi tạo menu state.
        
        Args:
            game_manager: Reference đến GameManager để chuyển state
        """
        self.game_manager = game_manager
        self.screen = game_manager.screen
        
        # Fonts
        self.title_font = load_font(settings.TITLE_FONT_SIZE)
        self.subtitle_font = load_font(settings.HUD_FONT_SIZE)
        self.button_font = load_font(settings.BUTTON_FONT_SIZE)
        
        # Buttons
        center_x = settings.SCREEN_WIDTH // 2
        center_y = settings.SCREEN_HEIGHT // 2
        
        self.play_button = pygame.Rect(
            center_x - settings.BUTTON_WIDTH // 2,
            center_y + 20,
            settings.BUTTON_WIDTH,
            settings.BUTTON_HEIGHT
        )
        
        self.exit_button = pygame.Rect(
            center_x - settings.BUTTON_WIDTH // 2,
            center_y + 20 + settings.BUTTON_HEIGHT + 20,
            settings.BUTTON_WIDTH,
            settings.BUTTON_HEIGHT
        )
        
        # Hover state
        self.play_hovered = False
        self.exit_hovered = False
        
        # Animation
        self.title_y_offset = 0
        self.title_direction = 1
        self.frame_count = 0
        
        # Highscore
        self.highscore = load_highscore()
        self.click_sound = load_sound(settings.UI_CLICK_SOUND)
    
    def handle_events(self, events):
        """
        Xử lý sự kiện input.
        
        Args:
            events: List các pygame event
        """
        mouse_pos = pygame.mouse.get_pos()
        
        # Kiểm tra hover
        self.play_hovered = self.play_button.collidepoint(mouse_pos)
        self.exit_hovered = self.exit_button.collidepoint(mouse_pos)
        
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.play_hovered:
                    play_sound(self.click_sound, volume=0.5)
                    # Chuyển sang Character Select State
                    from states.character_select_state import CharacterSelectState
                    self.game_manager.change_state(CharacterSelectState(self.game_manager))
                
                elif self.exit_hovered:
                    play_sound(self.click_sound, volume=0.5)
                    pygame.quit()
                    sys.exit()
    
    def update(self):
        """Cập nhật animation."""
        self.frame_count += 1
        
        # Title bobbing animation
        if self.frame_count % 3 == 0:
            self.title_y_offset += self.title_direction * 0.5
            if abs(self.title_y_offset) > 5:
                self.title_direction *= -1
    
    def draw(self):
        """Vẽ màn hình menu."""
        # Nền
        self.screen.fill(settings.COLOR_MENU_BG)
        
        # Vẽ trang trí nền (particles / sparkles)
        self._draw_bg_decoration()
        
        # === Title ===
        title_text = self.title_font.render(
            settings.TITLE, True, settings.COLOR_TITLE
        )
        title_rect = title_text.get_rect()
        title_rect.centerx = settings.SCREEN_WIDTH // 2
        title_rect.centery = settings.SCREEN_HEIGHT // 4 + self.title_y_offset
        
        # Shadow cho title
        shadow_text = self.title_font.render(
            settings.TITLE, True, (30, 25, 15)
        )
        shadow_rect = shadow_text.get_rect(center=(title_rect.centerx + 3, title_rect.centery + 3))
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_text = self.subtitle_font.render(
            "A High Fantasy Endless Runner", True, settings.COLOR_TEXT
        )
        subtitle_rect = subtitle_text.get_rect()
        subtitle_rect.centerx = settings.SCREEN_WIDTH // 2
        subtitle_rect.top = title_rect.bottom + 15
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # === Highscore (Nếu có) ===
        if self.highscore > 0:
            hs_font = load_font(32)
            hs_text = hs_font.render(f"★ Best Score: {int(self.highscore)} ★", True, settings.COLOR_SCORE)
            hs_rect = hs_text.get_rect(center=(settings.SCREEN_WIDTH // 2, self.play_button.top - 50))
            self.screen.blit(hs_text, hs_rect)
        
        # === Play Button ===
        self._draw_button(
            self.play_button, "Play", self.play_hovered
        )
        
        # === Exit Button ===
        self._draw_button(
            self.exit_button, "Exit", self.exit_hovered
        )
        
        # === Footer ===
        footer_font = load_font(18)
        footer_text = footer_font.render(
            "Use mouse to select", True, (120, 115, 100)
        )
        footer_rect = footer_text.get_rect()
        footer_rect.centerx = settings.SCREEN_WIDTH // 2
        footer_rect.bottom = settings.SCREEN_HEIGHT - 20
        self.screen.blit(footer_text, footer_rect)
    
    def _draw_button(self, rect, text, is_hovered):
        """
        Vẽ một nút bấm.
        
        Args:
            rect: pygame.Rect - vị trí và kích thước nút
            text: Chữ trên nút
            is_hovered: Đang hover không
        """
        # Màu nền
        color = settings.COLOR_BUTTON_HOVER if is_hovered else settings.COLOR_BUTTON
        
        # Shadow
        shadow_rect = rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(
            self.screen, (20, 15, 30),
            shadow_rect, border_radius=settings.BUTTON_BORDER_RADIUS
        )
        
        # Nút chính
        pygame.draw.rect(
            self.screen, color,
            rect, border_radius=settings.BUTTON_BORDER_RADIUS
        )
        
        # Border
        border_color = settings.COLOR_TITLE if is_hovered else (90, 70, 120)
        pygame.draw.rect(
            self.screen, border_color,
            rect, 2, border_radius=settings.BUTTON_BORDER_RADIUS
        )
        
        # Text
        btn_text = self.button_font.render(text, True, settings.COLOR_BUTTON_TEXT)
        btn_rect = btn_text.get_rect(center=rect.center)
        self.screen.blit(btn_text, btn_rect)
        
        # Hiệu ứng hover: scale indicator
        if is_hovered:
            # Mũi tên nhỏ bên trái text
            arrow_x = btn_rect.left - 20
            arrow_y = rect.centery
            pygame.draw.polygon(self.screen, settings.COLOR_TITLE, [
                (arrow_x, arrow_y - 6),
                (arrow_x + 10, arrow_y),
                (arrow_x, arrow_y + 6),
            ])
    
    def _draw_bg_decoration(self):
        """Vẽ trang trí nền menu (các hạt sáng lấp lánh)."""
        import math
        
        for i in range(20):
            x = (i * 73 + self.frame_count * (0.3 + i * 0.05)) % settings.SCREEN_WIDTH
            y = (i * 47 + 50) % settings.SCREEN_HEIGHT
            
            # Nhấp nháy theo thời gian
            brightness = int(80 + 40 * math.sin(self.frame_count * 0.05 + i))
            size = 1 + int(math.sin(self.frame_count * 0.03 + i * 0.7) > 0.5)
            
            pygame.draw.circle(
                self.screen,
                (brightness, brightness, brightness - 10),
                (int(x), int(y)),
                size
            )
