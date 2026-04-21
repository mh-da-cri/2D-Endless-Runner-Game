"""
Play State - Trạng thái đang chơi game
Logic chính: điều khiển player, spawn obstacles, collision, scoring.
Hỗ trợ HP system, skill, fireball tuần tự, đồng hành, powerups, pause.
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
    
    def __init__(self, game_manager, character_type=settings.CHARACTER_KNIGHT):
        """
        Khởi tạo play state.
        
        Args:
            game_manager: Reference đến GameManager
            character_type: Loại nhân vật đã chọn
        """
        self.game_manager = game_manager
        self.screen = game_manager.screen
        self.character_type = character_type
        
        # Game objects
        self.player = Player(character_type)
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
        
        # Fireballs & queue bắn tuần tự
        self.fireballs = []
        self.fireball_queue = []  # [{source, count, timer}, ...]
        
        # Đồng hành
        self.companions = []
        self.companion_pickups = []
        self.companion_milestones_spawned = [False] * len(settings.COMPANION_SCORE_MILESTONES)
        
        # Game state
        self.score = 0
        self.highscore = load_highscore()
        self.game_speed = settings.INITIAL_GAME_SPEED
        
        # Flags
        self.is_paused = False
        self.hit_stop_timer = 0
        self.death_snapshot = None    # Snapshot màn hình lúc xác chết
        self.pending_game_over = False  # Flag chờ chuyển sang GameOver
    
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
                # Toggle pause
                if event.key == pygame.K_p:
                    self.is_paused = not self.is_paused
                
                if self.is_paused:
                    if event.key == pygame.K_SPACE:
                        self.is_paused = False
                    elif event.key == pygame.K_ESCAPE:
                        from states.menu_state import MenuState
                        self.game_manager.change_state(MenuState(self.game_manager))
                        return
                    continue  # Bỏ qua input game khi đang pause
                
                # Input khi đang chơi
                if event.key == pygame.K_SPACE:
                    if not self.player.is_dead:
                        self.player.jump()
                
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    if not self.player.is_dead:
                        self.player.dash()
                
                # Skill nhân vật chính - Phím 1
                if event.key == settings.SKILL_KEY and not self.player.is_dead:
                    self._handle_skill(self.player)
                
                # Skill đồng hành - Phím 2, 3
                for comp in self.companions:
                    if event.key == comp.skill_key:
                        self._handle_companion_skill(comp)
                
                if event.key == pygame.K_ESCAPE:
                    self.is_paused = True
        
        if not self.is_paused and not self.player.is_dead:
            # Kiểm tra phím đang giữ (cho duck)
            keys = pygame.key.get_pressed()
            is_duck_pressed = keys[pygame.K_DOWN] or keys[pygame.K_s]
            self.player.duck(is_duck_pressed)
    
    def _handle_skill(self, player):
        """Xử lý khi player dùng skill."""
        result = player.use_skill()
        
        if result == "fireball":
            self._queue_fireballs(player)
    
    def _handle_companion_skill(self, companion):
        """Xử lý khi đồng hành dùng skill."""
        result = companion.use_skill()
        
        if result == "fireball":
            self._queue_fireballs(companion)
    
    def _queue_fireballs(self, source):
        """Thêm lượt bắn vào hàng đợi, delay viên đầu để khớp frame vung gậy."""
        first_shot_delay = (
            settings.SORCERER_FIREBALL_RELEASE_DELAY
            if getattr(source, 'character_type', None) == settings.CHARACTER_SORCERER
            else 0
        )
        self.fireball_queue.append({
            'source': source,
            'count': settings.FIREBALL_COUNT,
            'timer': first_shot_delay
        })
    
    def _get_fireball_spawn_position(self, source):
        """Tính vị trí sinh fireball ngay đầu gậy thay vì giữa hitbox."""
        if getattr(source, 'character_type', None) == settings.CHARACTER_SORCERER:
            if hasattr(source, 'companion_index'):
                return (
                    int(source.x + source.width + 18),
                    int(source.y + source.height * 0.35)
                )
            return (
                int(source.x + settings.SORCERER_FIREBALL_SPAWN_X_OFFSET),
                int(source.y + settings.SORCERER_FIREBALL_SPAWN_Y_OFFSET)
            )
        
        return (
            int(source.x + source.width),
            int(source.y + source.height // 2)
        )
    
    def _is_team_shielded(self):
        """Kiểm tra có thành viên nào đang bật khiên hoặc có power-up shield không."""
        # Kiểm tra power-up của player chính
        if self.player.has_powerup('shield'):
            return True
        # Kiểm tra skill Knight của player chính
        if self.player.skill_active and self.player.character_type == settings.CHARACTER_KNIGHT:
            return True
        # Kiểm tra skill Knight của đồng hành
        for comp in self.companions:
            if hasattr(comp, 'has_active_shield') and comp.has_active_shield():
                return True
        return False
    
    def update(self):
        """Cập nhật logic game mỗi frame."""
        if self.is_paused:
            return
            
        # --- Hit-stop Freeze Logic ---
        if self.player.is_dead:
            # Nếu đang chờ chuyển game over (draw() đã vẽ và chụp xong) → chuyển state
            if self.pending_game_over:
                self._game_over()
                return
            
            self.hit_stop_timer -= 1
            if self.hit_stop_timer <= 0:
                # Đặt flag → draw() frame này sẽ vẽ xác chết rồi chụp snapshot
                self.pending_game_over = True
            return  # Đóng băng - không cập nhật physics/cuộn cảnh
        
        # --- Cập nhật game speed ---
        if self.game_speed < settings.MAX_GAME_SPEED:
            self.game_speed += settings.SPEED_INCREMENT
        
        # Tốc độ thực tế (có tính dash speed cho obstacles & powerups)
        active_speed = self.game_speed * 1.5 if self.player.is_dashing else self.game_speed
        
        # Áp dụng hiệu ứng giảm tốc từ powerup slow_down
        if self.player.has_powerup('slow_down'):
            active_speed *= 0.7
            
        # Áp dụng hiệu ứng tăng tốc từ powerup speed_up
        if self.player.has_powerup('speed_up'):
            active_speed *= settings.POWERUP_SPEED_MULTIPLIER
        
        # --- Cập nhật player ---
        self.player.update()
        
        # --- Cập nhật đồng hành ---
        for comp in self.companions:
            comp.update()
        
        # --- Cập nhật obstacles ---
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
        
        # --- Cập nhật fireballs ---
        for fb in self.fireballs:
            fb.update()
        self.fireballs = [fb for fb in self.fireballs if getattr(fb, 'alive', True) and not fb.is_off_screen()]
        
        # --- Xử lý hàng đợi bắn fireball tuần tự ---
        for fq in self.fireball_queue[:]:
            fq['timer'] -= 1
            if fq['timer'] <= 0 and fq['count'] > 0:
                # Tạo fireball mới từ source
                try:
                    from entities.fireball import Fireball
                    source = fq['source']
                    spawn_x, spawn_y = self._get_fireball_spawn_position(source)
                    fb = Fireball(spawn_x, spawn_y)
                    self.fireballs.append(fb)
                except ImportError:
                    pass
                fq['count'] -= 1
                fq['timer'] = settings.FIREBALL_FIRE_INTERVAL
            
            if fq['count'] <= 0:
                self.fireball_queue.remove(fq)
        
        # --- Spawn obstacles ---
        self.spawn_timer += 1
        if self.player.is_dashing:
            self.spawn_timer += 0.5  # Bù thêm 0.5 tương ứng với hệ số dash 1.5x
            
        if self.spawn_timer >= self.next_spawn_delay:
            self._spawn_obstacle()
            self.spawn_timer = 0
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
                if len(self.companions) < 2:
                    self._spawn_companion_pickup()
        
        # --- Collision Detection ---
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
        
        # Fireball tiêu diệt obstacle
        for fireball in self.fireballs[:]:
            if not getattr(fireball, 'alive', True):
                continue
            fb_rect = fireball.get_rect()
            for obstacle in self.obstacles[:]:
                if fb_rect.colliderect(obstacle.get_rect()):
                    fireball.alive = False
                    self.obstacles.remove(obstacle)
                    break
        
        # Va chạm player với obstacle
        team_shielded = self._is_team_shielded()
        for obstacle in self.obstacles[:]:
            if player_rect.colliderect(obstacle.get_rect()):
                # Nếu có khiên → phá hủy obstacle
                if team_shielded:
                    self.obstacles.remove(obstacle)
                    continue
                
                # Bất tử (sau khi trúng đòn) → bỏ qua
                if self.player.is_invincible():
                    continue
                
                # Nhận sát thương
                is_dead = self.player.take_damage()
                if is_dead:
                    # Bắt đầu hit-stop
                    self.player.is_dead = True
                    self.hit_stop_timer = settings.HIT_STOP_FRAMES
                    return
                break  # Chỉ nhận 1 hit mỗi frame
        
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
        
        # 3. Obstacles, Powerups, Companion pickups
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
        for powerup in self.powerups:
            powerup.draw(self.screen)
        for pickup in self.companion_pickups:
            pickup.draw(self.screen)
        
        # 4. Fireballs
        for fireball in self.fireballs:
            fireball.draw(self.screen)
        
        # 5. Đồng hành (phía sau player)
        for comp in self.companions:
            comp.draw(self.screen)
        
        # 6. Player
        self.player.draw(self.screen)
        
        # 7. HUD (lớp trên cùng) - tryfall nếu HUD chưa nhận được player arg
        try:
            self.hud.draw(self.screen, self.score, self.highscore, self.game_speed,
                          self.player, self.companions)
        except TypeError:
            self.hud.draw(self.screen, self.score, self.highscore, self.game_speed)
        
        # 8. Giao diện Pause
        if self.is_paused:
            overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            
            try:
                from utils.asset_loader import load_font
                font_title = load_font(72)
                font_hint  = load_font(28)
            except Exception:
                font_title = pygame.font.Font(None, 72)
                font_hint  = pygame.font.Font(None, 28)
            
            title_text = font_title.render("PAUSED", True, settings.COLOR_TITLE)
            title_rect = title_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 40))
            
            hint_text = font_hint.render("SPACE / P to Resume  |  ESC to Menu", True, settings.COLOR_TEXT)
            hint_rect = hint_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 + 30))
            
            self.screen.blit(title_text, title_rect)
            self.screen.blit(hint_text, hint_rect)
            
        # 9. Chụp snapshot lúc chết (nếu đang chờ chuyển state)
        # Chụp ở đây để đảm bảo đã vẽ xong xác chết (ở bước 6) lên screen
        if self.pending_game_over and self.death_snapshot is None:
            self.death_snapshot = self.screen.copy()
    
    def _spawn_companion_pickup(self):
        """Tạo item đồng hành."""
        try:
            from entities.companion_pickup import CompanionPickup
            pickup = CompanionPickup(self.game_speed)
            self.companion_pickups.append(pickup)
        except ImportError:
            pass
    
    def _spawn_companion(self):
        """Tạo đồng hành ngẫu nhiên (khác loại nhân vật chính)."""
        try:
            from entities.companion import Companion
            all_types = [settings.CHARACTER_KNIGHT, settings.CHARACTER_SORCERER, settings.CHARACTER_PRIEST]
            
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
        except (ImportError, Exception):
            pass
    
    def _spawn_obstacle(self):
        """Tạo obstacle mới."""
        new_obstacle = Obstacle(game_speed=self.game_speed)
        
        # Đảm bảo không spawn quá gần obstacle cuối
        if self.obstacles:
            last_obs = self.obstacles[-1]
            min_gap = 200
            if new_obstacle.x - (last_obs.x + last_obs.width) < min_gap:
                new_obstacle.x = last_obs.x + last_obs.width + min_gap
        
        self.obstacles.append(new_obstacle)
    
    def _spawn_powerup(self):
        """Tạo powerup mới."""
        try:
            from entities.powerup import PowerUp
            new_powerup = PowerUp(game_speed=self.game_speed)
            
            # Tránh spawn đè lên hoặc quá sát obstacle (kiểm tra lặp lại cho đến khi sạch)
            safe_distance = 100
            for _ in range(10):  # Thử tối đa 10 lần dịch chuyển
                overlapping = False
                for obs in self.obstacles:
                    if abs(new_powerup.x - obs.x) < safe_distance:
                        overlapping = True
                        break
                
                if overlapping:
                    new_powerup.x += 150  # Dịch chuyển xa hơn một chút
                    new_powerup.rect.x = new_powerup.x
                else:
                    break
                    
            self.powerups.append(new_powerup)
        except ImportError:
            pass
    
    def _game_over(self):
        """Xử lý khi game over."""
        from states.gameover_state import GameOverState
        # Dùng snapshot đã chụp lúc đóng băng, fallback sang screen hiện tại
        bg_snapshot = self.death_snapshot if self.death_snapshot else self.screen.copy()
        
        self.game_manager.change_state(
            GameOverState(self.game_manager, self.score, self.highscore, bg_snapshot)
        )
