"""
HUD - Heads-Up Display
Hiển thị điểm số, highscore, HP, skill cooldown, skill đồng hành trong lúc chơi.
"""

import pygame
import math
import settings
from utils.asset_loader import load_font


class HUD:
    """Hiển thị thông tin game trên màn hình."""
    
    def __init__(self):
        """Khởi tạo HUD với font và vị trí."""
        self.font = load_font(settings.HUD_FONT_SIZE)
        self.small_font = load_font(settings.HUD_FONT_SIZE - 6)
        self.hp_font = load_font(20)
        self.skill_font = load_font(18)
        self.frame_count = 0
    
    def draw(self, screen, score, highscore, game_speed=None, player=None, companions=None):
        """
        Vẽ HUD lên màn hình.
        
        Args:
            screen: pygame.Surface
            score: Điểm hiện tại
            highscore: Điểm cao nhất
            game_speed: Tốc độ game hiện tại
            player: Player instance
            companions: Danh sách Companion instances
        """
        self.frame_count += 1
        display_score = int(score)
        display_high = int(highscore)
        
        # === Điểm số (góc trên phải) ===
        score_text = self.font.render(
            f"Score: {display_score}", True, settings.COLOR_SCORE
        )
        score_rect = score_text.get_rect()
        score_rect.topright = (settings.SCREEN_WIDTH - 20, 15)
        
        # Nền bán trong suốt cho score
        bg_surface = pygame.Surface(
            (score_rect.width + 20, score_rect.height + 10), pygame.SRCALPHA
        )
        bg_surface.fill((0, 0, 0, 100))
        screen.blit(bg_surface, (score_rect.x - 10, score_rect.y - 5))
        screen.blit(score_text, score_rect)
        
        # === Highscore (bên dưới score) ===
        high_text = self.small_font.render(
            f"Best: {display_high}", True, settings.COLOR_TEXT
        )
        high_rect = high_text.get_rect()
        high_rect.topright = (settings.SCREEN_WIDTH - 20, score_rect.bottom + 8)
        screen.blit(high_text, high_rect)
        
        # === HP & Skill (góc trên trái) ===
        if player:
            self._draw_hp_bar(screen, player)
            self._draw_skill_indicator(screen, player, "[1]", 55)
            
            # Skill đồng hành
            if companions:
                for i, comp in enumerate(companions):
                    key_label = f"[{comp.companion_index + 2}]"
                    y_offset = 100 + i * 45
                    self._draw_companion_skill(screen, comp, key_label, y_offset)
        
        # === Hướng dẫn điều khiển (góc dưới trái) ===
        controls = [
            "SPACE: Jump / Double Jump",
            "DOWN: Duck",
            "SHIFT: Dash",
            "P / ESC: PAUSE",
        ]
        
        # Điều chỉnh để vẽ từ GROUND_Y - delta để tránh chạm đáy màn hình khi có nhiều dòng
        start_y = settings.GROUND_Y - 10
        for i, text in enumerate(controls):
            ctrl_text = self.small_font.render(text, True, (*settings.COLOR_TEXT[:3],))
            ctrl_surface = pygame.Surface(
                (ctrl_text.get_width() + 8, ctrl_text.get_height() + 4), pygame.SRCALPHA
            )
            ctrl_surface.fill((0, 0, 0, 60))
            draw_y = start_y + i * 25
            screen.blit(ctrl_surface, (8, draw_y))
            screen.blit(ctrl_text, (12, draw_y + 2))
    
    def _draw_hp_bar(self, screen, player):
        """Vẽ thanh HP dạng trái tim."""
        start_x = 20
        start_y = 15
        heart_size = 28
        heart_gap = 8
        
        # Nền bán trong suốt
        total_width = player.max_hp * (heart_size + heart_gap) + 10
        bg = pygame.Surface((total_width, heart_size + 16), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 100))
        screen.blit(bg, (start_x - 5, start_y - 5))
        
        # Nhãn HP
        hp_label = self.hp_font.render("HP", True, settings.COLOR_HP_FULL)
        screen.blit(hp_label, (start_x, start_y - 2))
        
        heart_start_x = start_x + 30
        
        for i in range(player.max_hp):
            hx = heart_start_x + i * (heart_size + heart_gap)
            hy = start_y + 2
            
            if i < player.hp:
                color = settings.COLOR_HP_FULL
                # Hiệu ứng đập nhẹ khi máu thấp
                if player.hp == 1:
                    pulse = 1 + 0.1 * math.sin(self.frame_count * 0.15)
                    self._draw_heart(screen, hx, hy, int(heart_size * pulse), color)
                else:
                    self._draw_heart(screen, hx, hy, heart_size, color)
            else:
                # Trái tim trống
                self._draw_heart(screen, hx, hy, heart_size, settings.COLOR_HP_EMPTY)
    
    def _draw_heart(self, screen, x, y, size, color):
        """Vẽ hình trái tim."""
        half = size // 2
        quarter = size // 4
        cx1 = x + quarter
        cx2 = x + quarter * 3
        cy = y + quarter
        r = quarter + 1
        
        pygame.draw.circle(screen, color, (cx1, cy), r)
        pygame.draw.circle(screen, color, (cx2, cy), r)
        
        # Tam giác phía dưới
        points = [
            (x - 1, cy),
            (x + half, y + size - 2),
            (x + size + 1, cy),
        ]
        pygame.draw.polygon(screen, color, points)
    
    def _draw_skill_indicator(self, screen, player, key_label, y_pos):
        """Vẽ chỉ báo cooldown skill nhân vật chính."""
        skill_x = 15  # Căn lề trái bằng lề thanh máu (tọa độ nền)
        skill_y = y_pos
        indicator_width = 180
        indicator_height = 40
        
        # Nền bán trong suốt
        bg = pygame.Surface((indicator_width, indicator_height), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 100))
        screen.blit(bg, (skill_x, skill_y))
        
        # Tên skill
        skill_names = {
            settings.CHARACTER_KNIGHT: "Shield",
            settings.CHARACTER_SORCERER: "Fireball",
            settings.CHARACTER_PRIEST: "Heal",
        }
        skill_name = skill_names.get(player.character_type, "Skill")
        
        if player.can_use_skill:
            # Skill sẵn sàng
            name_color = settings.COLOR_SKILL_READY
            status_text = "READY!"
            status_color = settings.COLOR_SKILL_READY
            
            # Hiệu ứng glow nhấp nháy
            glow_alpha = int(60 + 30 * math.sin(self.frame_count * 0.1))
            glow = pygame.Surface((indicator_width, indicator_height), pygame.SRCALPHA)
            glow.fill((*settings.COLOR_SKILL_READY, glow_alpha))
            screen.blit(glow, (skill_x, skill_y))
        elif player.skill_active and player.character_type == settings.CHARACTER_KNIGHT:
            # Knight shield đang active - hiển thị thời gian còn lại
            remaining = player.skill_duration_timer / settings.FPS
            status_text = f"ACTIVE {remaining:.0f}s"
            status_color = settings.COLOR_SHIELD_SKILL
            name_color = settings.COLOR_SHIELD_SKILL
        else:
            # Skill đang hồi
            name_color = settings.COLOR_SKILL_COOLDOWN
            remaining_seconds = player.skill_cooldown_timer / settings.FPS
            status_text = f"{remaining_seconds:.1f}s"
            status_color = settings.COLOR_SKILL_COOLDOWN
            
            # Thanh cooldown
            if player.skill_cooldown_max > 0:
                cooldown_ratio = 1 - (player.skill_cooldown_timer / player.skill_cooldown_max)
                bar_width = int((indicator_width - 10) * cooldown_ratio)
                bar_rect = pygame.Rect(skill_x + 5, skill_y + indicator_height - 6, bar_width, 3)
                pygame.draw.rect(screen, settings.COLOR_SKILL_READY, bar_rect)
        
        # Vẽ text (điều chỉnh lề trong +5px từ skill_x ban đầu 15)
        key_text = self.skill_font.render(key_label, True, (150, 140, 130))
        screen.blit(key_text, (skill_x + 8, skill_y + 6))
        
        name_text = self.skill_font.render(skill_name, True, name_color)
        screen.blit(name_text, (skill_x + 37, skill_y + 6))
        
        status = self.skill_font.render(status_text, True, status_color)
        status_rect = status.get_rect()
        status_rect.right = skill_x + indicator_width - 8
        status_rect.top = skill_y + 6
        screen.blit(status, status_rect)
    
    def _draw_companion_skill(self, screen, companion, key_label, y_pos):
        """Vẽ chỉ báo skill cooldown cho đồng hành."""
        skill_x = 15  # Căn lề trái bằng lề thanh máu
        skill_y = y_pos
        indicator_width = 180
        indicator_height = 36
        
        # Nền bán trong suốt
        bg = pygame.Surface((indicator_width, indicator_height), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 80))
        screen.blit(bg, (skill_x, skill_y))
        
        # Tên skill đồng hành
        skill_names = {
            settings.CHARACTER_KNIGHT: "Shield",
            settings.CHARACTER_SORCERER: "Fireball",
            settings.CHARACTER_PRIEST: "Heal",
        }
        skill_name = f"Ally {skill_names.get(companion.character_type, 'Skill')}"
        
        if companion.can_use_skill:
            # Skill sẵn sàng
            name_color = settings.COLOR_SKILL_READY
            status_text = "READY!"
            status_color = settings.COLOR_SKILL_READY
            
            # Hiệu ứng glow nhẹ
            glow_alpha = int(40 + 20 * math.sin(self.frame_count * 0.1))
            glow = pygame.Surface((indicator_width, indicator_height), pygame.SRCALPHA)
            glow.fill((*settings.COLOR_SKILL_READY, glow_alpha))
            screen.blit(glow, (skill_x, skill_y))
        elif companion.skill_active and companion.character_type == settings.CHARACTER_KNIGHT:
            # Khiên đồng hành đang active
            remaining = companion.skill_duration_timer / settings.FPS
            status_text = f"ACTIVE {remaining:.0f}s"
            status_color = settings.COLOR_SHIELD_SKILL
            name_color = settings.COLOR_SHIELD_SKILL
        else:
            # Skill đang hồi
            name_color = settings.COLOR_SKILL_COOLDOWN
            remaining = companion.skill_cooldown_timer / settings.FPS
            status_text = f"{remaining:.1f}s"
            status_color = settings.COLOR_SKILL_COOLDOWN
            
            # Thanh cooldown
            if companion.skill_cooldown_max > 0:
                ratio = 1 - (companion.skill_cooldown_timer / companion.skill_cooldown_max)
                bar_w = int((indicator_width - 10) * ratio)
                bar_rect = pygame.Rect(skill_x + 5, skill_y + indicator_height - 5, bar_w, 3)
                pygame.draw.rect(screen, settings.COLOR_SKILL_READY, bar_rect)
        
        # Vẽ text (điều chỉnh lề trong +5px từ skill_x ban đầu 15)
        key_text = self.skill_font.render(key_label, True, (150, 140, 130))
        screen.blit(key_text, (skill_x + 8, skill_y + 5))
        
        name_text = self.skill_font.render(skill_name, True, name_color)
        screen.blit(name_text, (skill_x + 37, skill_y + 5))
        
        status = self.skill_font.render(status_text, True, status_color)
        sr = status.get_rect()
        sr.right = skill_x + indicator_width - 8
        sr.top = skill_y + 5
        screen.blit(status, sr)
