"""
Play State - Trạng thái đang chơi game
Logic chính: điều khiển player, spawn obstacles, collision, scoring.
Hỗ trợ hệ thống HP, skill, fireball tuần tự, đồng hành, và multi-character.
"""

import random
import pygame
import sys
import settings
from entities.player import Player
from entities.obstacle import Obstacle
from entities.ground import Ground
from entities.powerup import PowerUp
from entities.fireball import Fireball
from entities.companion import Companion
from entities.companion_pickup import CompanionPickup
from ui.background import Background
from ui.hud import HUD
from utils.score_manager import load_highscore
from utils.asset_loader import load_font


class PlayState:
    """Trạng thái game chính - đang chơi."""
    
    def __init__(self, game_manager, character_type=settings.CHARACTER_KNIGHT):
        """
        Khởi tạo play state.
        
        Args:
            game_manager: Tham chiếu đến GameManager
            character_type: Loại nhân vật đã chọn
        """
        self.game_manager = game_manager
        self.screen = game_manager.screen
        self.character_type = character_type
        
        # Đối tượng game
        self.player = Player(character_type)
        self.ground = Ground()
        self.background = Background()
        self.hud = HUD()
        
        # Chướng ngại vật
        self.obstacles = []
        self.spawn_timer = 0
        self.next_spawn_delay = random.randint(
            settings.MIN_SPAWN_DELAY, settings.MAX_SPAWN_DELAY
        )
        
        # Vật phẩm tăng sức mạnh
        self.powerups = []
        self.powerup_spawn_timer = 0
        self.next_powerup_spawn_delay = random.randint(
            settings.MIN_POWERUP_SPAWN_DELAY, settings.MAX_POWERUP_SPAWN_DELAY
        )
        
        # Cầu lửa
        self.fireballs = []
        
        # Hàng đợi bắn fireball tuần tự: (nguồn, số viên còn lại, đếm ngược)
        self.fireball_queue = []
        
        # Hệ thống đồng hành
        self.companions = []
        self.companion_pickups = []
        self.companion_milestones_spawned = [False] * len(settings.COMPANION_SCORE_MILESTONES)
        
        # Trạng thái game
        self.score = 0
        self.highscore = load_highscore()
        self.game_speed = settings.INITIAL_GAME_SPEED
        
        # Cờ trạng thái
        self.is_paused = False
    
    def handle_events(self, events):
        """
        Xử lý input từ người chơi.
        
        Args:
            events: Danh sách các pygame event
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
                        self.is_paused = False  # Tiếp tục chơi
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
                
                # Skill nhân vật chính - Phím 1
                if event.key == settings.SKILL_KEY:
                    self._handle_skill(self.player)
                
                # Skill đồng hành - Phím 2, 3
                for comp in self.companions:
                    if event.key == comp.skill_key:
                        self._handle_companion_skill(comp)
                
                if event.key == pygame.K_ESCAPE:
                    self.is_paused = True
        
        if not self.is_paused:
            # Kiểm tra phím đang giữ (cho duck - cần giữ liên tục)
            keys = pygame.key.get_pressed()
            is_duck_pressed = keys[pygame.K_DOWN] or keys[pygame.K_s]
            self.player.duck(is_duck_pressed)
    
    def _handle_skill(self, player):
        """Xử lý khi player dùng skill."""
        result = player.use_skill()
        
        if result == "fireball":
            # Thêm vào hàng đợi bắn tuần tự
            self.fireball_queue.append({
                'source': player,
                'count': settings.FIREBALL_COUNT,
                'timer': 0  # Bắn viên đầu tiên ngay lập tức
            })
    
    def _handle_companion_skill(self, companion):
        """Xử lý khi đồng hành dùng skill."""
        result = companion.use_skill()
        
        if result == "fireball":
            self.fireball_queue.append({
                'source': companion,
                'count': settings.FIREBALL_COUNT,
                'timer': 0
            })
    
    def _is_team_shielded(self):
        """Kiểm tra có thành viên nào trong team đang bật khiên không."""
        if self.player.skill_active and self.player.character_type == settings.CHARACTER_KNIGHT:
            return True
        for comp in self.companions:
            if comp.has_active_shield():
                return True
        return False
    
    def update(self):
        """Cập nhật logic game mỗi frame."""
        if self.is_paused:
            return
        
        # --- Tăng tốc game dần dần ---
        if self.game_speed < settings.MAX_GAME_SPEED:
            self.game_speed += settings.SPEED_INCREMENT
        
        # --- Cập nhật player ---
        self.player.update()
        
        # --- Cập nhật đồng hành ---
        for comp in self.companions:
            comp.update()
        
        # Tính tốc độ thực tế (nhân hệ số DASH_SPEED khi đang lướt)
        active_speed = self.game_speed * settings.DASH_SPEED if self.player.is_dashing else self.game_speed
        
        # Áp dụng hiệu ứng giảm tốc từ powerup
        if self.player.has_powerup('slow_down'):
            active_speed *= 0.7
        
        # --- Cập nhật chướng ngại vật ---
        for obstacle in self.obstacles:
            obstacle.update(active_speed)
        self.obstacles = [obs for obs in self.obstacles if not obs.is_off_screen()]
        
        # --- Cập nhật powerups ---
        for powerup in self.powerups:
            powerup.update(active_speed)
        self.powerups = [p for p in self.powerups if not p.is_off_screen()]
        
        # --- Cập nhật item đồng hành ---
        for pickup in self.companion_pickups:
            pickup.update(active_speed)
        self.companion_pickups = [p for p in self.companion_pickups if not p.is_off_screen()]
        
        # --- Xử lý hàng đợi bắn fireball tuần tự ---
        for fq in self.fireball_queue[:]:
            fq['timer'] -= 1
            if fq['timer'] <= 0:
                # Bắn 1 viên từ vị trí hiện tại của nguồn
                source = fq['source']
                fb = Fireball(source.x, source.y, 0)
                self.fireballs.append(fb)
                fq['count'] -= 1
                if fq['count'] <= 0:
                    self.fireball_queue.remove(fq)
                else:
                    fq['timer'] = settings.FIREBALL_FIRE_INTERVAL
        
        # --- Cập nhật cầu lửa ---
        for fireball in self.fireballs:
            fireball.update()
        self.fireballs = [fb for fb in self.fireballs if fb.alive and not fb.is_off_screen()]
        
        # --- Spawn chướng ngại vật mới ---
        self.spawn_timer += 1
        # Khi đang lướt, timer đếm nhanh hơn để duy trì mật độ quái
        if self.player.is_dashing:
            self.spawn_timer += (settings.DASH_SPEED - 1.0)
            
        if self.spawn_timer >= self.next_spawn_delay:
            self._spawn_obstacle()
            self.spawn_timer = 0
            # Random delay tiếp theo (giảm dần khi tốc độ tăng)
            speed_factor = active_speed / settings.INITIAL_GAME_SPEED
            min_delay = max(45, int(settings.MIN_SPAWN_DELAY / speed_factor))
            max_delay = max(90, int(settings.MAX_SPAWN_DELAY / speed_factor))
            self.next_spawn_delay = random.randint(min_delay, max_delay)
            
        # --- Spawn powerups ---
        self.powerup_spawn_timer += 1
        if self.powerup_spawn_timer >= self.next_powerup_spawn_delay:
            self._spawn_powerup()
            self.powerup_spawn_timer = 0
            self.next_powerup_spawn_delay = random.randint(
                settings.MIN_POWERUP_SPAWN_DELAY, settings.MAX_POWERUP_SPAWN_DELAY
            )
        
        # --- Spawn item đồng hành tại các mốc điểm ---
        for i, milestone in enumerate(settings.COMPANION_SCORE_MILESTONES):
            if not self.companion_milestones_spawned[i] and self.score >= milestone:
                self.companion_milestones_spawned[i] = True
                if len(self.companions) < 2:  # Tối đa 2 đồng hành
                    pickup = CompanionPickup(self.game_speed)
                    self.companion_pickups.append(pickup)
        
        # --- Phát hiện va chạm ---
        player_rect = self.player.get_rect()
        
        # Thu thập powerups
        for powerup in self.powerups[:]:
            if player_rect.colliderect(powerup.get_rect()):
                self.player.activate_powerup(powerup.type)
                self.powerups.remove(powerup)
        
        # Thu thập item đồng hành
        for pickup in self.companion_pickups[:]:
            if player_rect.colliderect(pickup.get_rect()):
                self._spawn_companion()
                self.companion_pickups.remove(pickup)
        
        # Va chạm cầu lửa với chướng ngại vật
        for fireball in self.fireballs[:]:
            if not fireball.alive:
                continue
            fb_rect = fireball.get_rect()
            for obstacle in self.obstacles[:]:
                if fb_rect.colliderect(obstacle.get_rect()):
                    fireball.destroy()
                    self.obstacles.remove(obstacle)
                    break
                
        # Va chạm player với chướng ngại vật
        team_shielded = self._is_team_shielded()
        for obstacle in self.obstacles:
            if player_rect.colliderect(obstacle.get_rect()):
                # Nếu đang bất tử hoặc team có khiên → bỏ qua
                if self.player.is_invincible() or team_shielded:
                    continue
                
                # Nhận sát thương
                is_dead = self.player.take_damage()
                if is_dead:
                    self._game_over()
                    return
                break  # Chỉ nhận 1 hit mỗi frame
        
        # --- Cập nhật điểm số ---
        score_multiplier = 2 if self.player.has_powerup('double_score') else 1
        self.score += settings.SCORE_INCREMENT * (active_speed / settings.INITIAL_GAME_SPEED) * score_multiplier
        if self.score > self.highscore:
            self.highscore = self.score
        
        # --- Cập nhật nền & mặt đất ---
        self.background.update(active_speed)
        self.ground.update(active_speed)
    
    def draw(self):
        """Vẽ mọi thứ lên màn hình (theo thứ tự lớp)."""
        # 1. Nền (lớp xa nhất)
        self.background.draw(self.screen)
        
        # 2. Mặt đất
        self.ground.draw(self.screen)
        
        # 3. Chướng ngại vật, Powerups, Item đồng hành
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
        for powerup in self.powerups:
            powerup.draw(self.screen)
        for pickup in self.companion_pickups:
            pickup.draw(self.screen)
        
        # 4. Cầu lửa
        for fireball in self.fireballs:
            fireball.draw(self.screen)
        
        # 5. Đồng hành (phía sau player)
        for comp in self.companions:
            comp.draw(self.screen)
        
        # 6. Player
        self.player.draw(self.screen)
        
        # 7. HUD (lớp trên cùng)
        self.hud.draw(self.screen, self.score, self.highscore, self.game_speed, 
                      self.player, self.companions)
        
        # 8. Giao diện Pause
        if self.is_paused:
            # Lớp phủ tối làm mờ game
            overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            
            font_title = load_font(72)
            font_hint  = load_font(28)
            
            title_text = font_title.render("PAUSED", True, settings.COLOR_TITLE)
            title_rect = title_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 40))
            
            hint_text = font_hint.render("SPACE / P to Resume  |  ESC to Menu", True, settings.COLOR_TEXT)
            hint_rect = hint_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 + 30))
            
            self.screen.blit(title_text, title_rect)
            self.screen.blit(hint_text, hint_rect)
    
    def _spawn_companion(self):
        """Tạo đồng hành ngẫu nhiên (khác loại với player chính và đồng hành hiện có)."""
        all_types = [settings.CHARACTER_KNIGHT, settings.CHARACTER_SORCERER, settings.CHARACTER_PRIEST]
        
        # Loại trừ loại nhân vật chính và đồng hành đã có
        used_types = [self.character_type]
        for comp in self.companions:
            used_types.append(comp.character_type)
        
        available = [t for t in all_types if t not in used_types]
        if not available:
            available = [t for t in all_types if t != self.character_type]
        
        if available:
            char_type = random.choice(available)
            comp_index = len(self.companions)
            companion = Companion(char_type, comp_index, self.player)
            self.companions.append(companion)
    
    def _spawn_obstacle(self):
        """Tạo chướng ngại vật mới."""
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
        # Ép vẽ frame hiện tại trước khi chuyển màn hình
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
