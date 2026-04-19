"""
Play State - Trạng thái đang chơi game
Logic chính: điều khiển player, spawn obstacles, collision, scoring.
"""

import random
import pygame
import sys
import settings
from entities.player import Player
from entities.obstacle import Obstacle
from entities.ground import Ground
from entities.powerup import PowerUp
from ui.background import Background
from ui.hud import HUD
from utils.score_manager import load_highscore
from utils.asset_loader import load_font


class PlayState:
    """Trạng thái game chính - đang chơi."""
    
    def __init__(self, game_manager):
        """
        Khởi tạo play state.
        
        Args:
            game_manager: Reference đến GameManager
        """
        self.game_manager = game_manager
        self.screen = game_manager.screen
        
        # Game objects
        self.player = Player()
        self.ground = Ground()
        self.background = Background()
        self.hud = HUD()
        
        # Obstacles
        self.obstacles = []
        self.spawn_timer = 0
        self.next_spawn_delay = random.randint(
            settings.MIN_SPAWN_DELAY, settings.MAX_SPAWN_DELAY
        )
        
        # Power-ups
        self.powerups = []
        self.powerup_spawn_timer = 0
        self.next_powerup_spawn_delay = random.randint(
            settings.MIN_POWERUP_SPAWN_DELAY, settings.MAX_POWERUP_SPAWN_DELAY
        )
        
        # Game state
        self.score = 0
        self.highscore = load_highscore()
        self.game_speed = settings.INITIAL_GAME_SPEED
        
        # Flags
        self.is_paused = False
    
    def handle_events(self, events):
        """
        Xử lý input.
        
        Args:
            events: List các pygame event
        """
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.is_paused = not self.is_paused
                    
                if self.is_paused:
                    if event.key == pygame.K_SPACE:
                        self.is_paused = False  # Resume
                    elif event.key == pygame.K_ESCAPE:
                        from states.menu_state import MenuState
                        self.game_manager.change_state(MenuState(self.game_manager))
                        return
                    continue  # Bỏ qua các phím khác khi đang pause
                
                # Input khi đang chơi bình thường
                if event.key == pygame.K_SPACE:
                    self.player.jump()
                
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    self.player.dash()
                
                if event.key == pygame.K_ESCAPE:
                    # Bật menu pause khi bấm ESC
                    self.is_paused = True
        
        if not self.is_paused:
            # Kiểm tra phím đang giữ (cho duck - cần giữ liên tục)
            keys = pygame.key.get_pressed()
            is_duck_pressed = keys[pygame.K_DOWN] or keys[pygame.K_s]
            self.player.duck(is_duck_pressed)
    
    def update(self):
        """Cập nhật logic game mỗi frame."""
        if self.is_paused:
            return
        
        # --- Cập nhật game speed (tăng dần) ---
        if self.game_speed < settings.MAX_GAME_SPEED:
            self.game_speed += settings.SPEED_INCREMENT
        
        # --- Cập nhật player ---
        self.player.update()
        
        # Tính toán tốc độ thực tế (tăng tốc theo hệ số DASH_SPEED nếu đang lướt)
        active_speed = self.game_speed * settings.DASH_SPEED if self.player.is_dashing else self.game_speed
        
        # Áp dụng hiêu ứng slow down từ powerup
        if self.player.has_powerup('slow_down'):
            active_speed *= 0.7
        
        # --- Cập nhật obstacles ---
        for obstacle in self.obstacles:
            obstacle.update(active_speed)
        
        # Xóa obstacles đã ra khỏi màn hình
        self.obstacles = [obs for obs in self.obstacles if not obs.is_off_screen()]
        
        # --- Cập nhật powerups ---
        for powerup in self.powerups:
            powerup.update(active_speed)
            
        self.powerups = [p for p in self.powerups if not p.is_off_screen()]
        
        # --- Spawn obstacle mới ---
        self.spawn_timer += 1
        # Nếu đang lướt, timer đếm nhanh hơn thuận theo hệ số DASH_SPEED để duy trì mật độ quái
        if self.player.is_dashing:
            self.spawn_timer += (settings.DASH_SPEED - 1.0)
            
        if self.spawn_timer >= self.next_spawn_delay:
            self._spawn_obstacle()
            self.spawn_timer = 0
            # Random delay tiếp theo (giảm dần khi tốc độ tăng)
            speed_factor = active_speed / settings.INITIAL_GAME_SPEED
            min_delay = max(30, int(settings.MIN_SPAWN_DELAY / speed_factor))
            max_delay = max(60, int(settings.MAX_SPAWN_DELAY / speed_factor))
            self.next_spawn_delay = random.randint(min_delay, max_delay)
            
        # --- Spawn powerups ---
        self.powerup_spawn_timer += 1
        if self.powerup_spawn_timer >= self.next_powerup_spawn_delay:
            self._spawn_powerup()
            self.powerup_spawn_timer = 0
            self.next_powerup_spawn_delay = random.randint(
                settings.MIN_POWERUP_SPAWN_DELAY, settings.MAX_POWERUP_SPAWN_DELAY
            )
        
        # --- Collision Detection ---
        player_rect = self.player.get_rect()
        
        # Va chạm với powerups
        for powerup in self.powerups[:]:
            if player_rect.colliderect(powerup.get_rect()):
                self.player.activate_powerup(powerup.type)
                self.powerups.remove(powerup)
                
        # Va chạm với chướng ngại vật
        for obstacle in self.obstacles:
            if player_rect.colliderect(obstacle.get_rect()):
                # Nếu đang dash hoặc có khiên → bất tử (dash xuyên qua)
                if self.player.is_dashing or self.player.has_powerup('shield'):
                    continue
                
                # GAME OVER
                self._game_over()
                return
        
        # --- Cập nhật score ---
        score_multiplier = 2 if self.player.has_powerup('double_score') else 1
        self.score += settings.SCORE_INCREMENT * (active_speed / settings.INITIAL_GAME_SPEED) * score_multiplier
        if self.score > self.highscore:
            self.highscore = self.score
        
        # --- Cập nhật background & ground ---
        self.background.update(active_speed)
        self.ground.update(active_speed)
    
    def draw(self):
        """Vẽ mọi thứ lên màn hình (theo thứ tự lớp)."""
        # 1. Background (lớp xa nhất)
        self.background.draw(self.screen)
        
        # 2. Ground
        self.ground.draw(self.screen)
        
        # 3. Obstacles và Powerups
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
        for powerup in self.powerups:
            powerup.draw(self.screen)
        
        # 4. Player
        self.player.draw(self.screen)
        
        # 5. HUD (lớp trên cùng)
        self.hud.draw(self.screen, self.score, self.highscore, self.game_speed)
        
        # 6. Pause UI
        if self.is_paused:
            # Lớp sương mù đen bóng làm mờ game
            overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            
            # Khởi tạo font để vẽ chữ
            font_title = load_font(72)
            font_hint  = load_font(28)
            
            # Tiêu đề
            title_text = font_title.render("PAUSED", True, settings.COLOR_TITLE)
            title_rect = title_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 40))
            
            # Hướng dẫn
            hint_text = font_hint.render("SPACE / P to Resume  |  ESC to Menu", True, settings.COLOR_TEXT)
            hint_rect = hint_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 + 30))
            
            self.screen.blit(title_text, title_rect)
            self.screen.blit(hint_text, hint_rect)
    
    def _spawn_obstacle(self):
        """Tạo obstacle mới."""
        new_obstacle = Obstacle(game_speed=self.game_speed)
        
        # Đảm bảo không spawn quá gần obstacle cuối
        if self.obstacles:
            last_obs = self.obstacles[-1]
            min_gap = 200  # Khoảng cách tối thiểu giữa 2 obstacles
            if new_obstacle.x - (last_obs.x + last_obs.width) < min_gap:
                new_obstacle.x = last_obs.x + last_obs.width + min_gap
        
        self.obstacles.append(new_obstacle)
    
    def _game_over(self):
        """Xử lý khi game over."""
        from states.gameover_state import GameOverState
        
        # Ép vẽ frame hiện tại (frame xảy ra va chạm) trước khi đóng màng hình
        self.draw()
        
        self.game_manager.change_state(
            GameOverState(self.game_manager, self.score, self.highscore)
        )
        
    def _spawn_powerup(self):
        """Tạo powerup mới."""
        from entities.powerup import PowerUp
        new_powerup = PowerUp(game_speed=self.game_speed)
        
        # Tránh spawn đè lên obstacle
        for obs in self.obstacles:
            if abs(new_powerup.x - obs.x) < 50:
                new_powerup.x += 100
                
        self.powerups.append(new_powerup)
