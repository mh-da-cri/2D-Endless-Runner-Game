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
from ui.background import Background
from ui.hud import HUD
from utils.score_manager import load_highscore


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
                if event.key == pygame.K_SPACE:
                    self.player.jump()
                
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    self.player.dash()
                
                if event.key == pygame.K_ESCAPE:
                    # Về menu
                    from states.menu_state import MenuState
                    self.game_manager.change_state(MenuState(self.game_manager))
                    return
        
        # Kiểm tra phím đang giữ (cho duck - cần giữ liên tục)
        keys = pygame.key.get_pressed()
        self.player.duck(keys[pygame.K_DOWN])
    
    def update(self):
        """Cập nhật logic game mỗi frame."""
        if self.is_paused:
            return
        
        # --- Cập nhật game speed (tăng dần) ---
        if self.game_speed < settings.MAX_GAME_SPEED:
            self.game_speed += settings.SPEED_INCREMENT
        
        # --- Cập nhật player ---
        self.player.update()
        
        # --- Cập nhật obstacles ---
        for obstacle in self.obstacles:
            obstacle.update(self.game_speed)
        
        # Xóa obstacles đã ra khỏi màn hình
        self.obstacles = [obs for obs in self.obstacles if not obs.is_off_screen()]
        
        # --- Spawn obstacle mới ---
        self.spawn_timer += 1
        if self.spawn_timer >= self.next_spawn_delay:
            self._spawn_obstacle()
            self.spawn_timer = 0
            # Random delay tiếp theo (giảm dần khi tốc độ tăng)
            speed_factor = self.game_speed / settings.INITIAL_GAME_SPEED
            min_delay = max(30, int(settings.MIN_SPAWN_DELAY / speed_factor))
            max_delay = max(60, int(settings.MAX_SPAWN_DELAY / speed_factor))
            self.next_spawn_delay = random.randint(min_delay, max_delay)
        
        # --- Collision Detection ---
        player_rect = self.player.get_rect()
        for obstacle in self.obstacles:
            if player_rect.colliderect(obstacle.get_rect()):
                # Nếu đang dash → bất tử (dash xuyên qua)
                if self.player.is_dashing:
                    continue
                
                # GAME OVER
                self._game_over()
                return
        
        # --- Cập nhật score ---
        self.score += settings.SCORE_INCREMENT * (self.game_speed / settings.INITIAL_GAME_SPEED)
        
        # --- Cập nhật background & ground ---
        self.background.update(self.game_speed)
        self.ground.update(self.game_speed)
    
    def draw(self):
        """Vẽ mọi thứ lên màn hình (theo thứ tự lớp)."""
        # 1. Background (lớp xa nhất)
        self.background.draw(self.screen)
        
        # 2. Ground
        self.ground.draw(self.screen)
        
        # 3. Obstacles
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
        
        # 4. Player
        self.player.draw(self.screen)
        
        # 5. HUD (lớp trên cùng)
        self.hud.draw(self.screen, self.score, self.highscore, self.game_speed)
    
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
        self.game_manager.change_state(
            GameOverState(self.game_manager, self.score, self.highscore)
        )
