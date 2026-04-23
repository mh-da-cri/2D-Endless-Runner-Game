"""
Play State - Trạng thái đang chơi game
Logic chính: điều khiển player, spawn obstacles, collision, scoring.
Hỗ trợ HP system, skill, fireball tuần tự, đồng hành, powerups, pause.
"""

import random
import math
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
        self.bullet_explosions = [] # [{'x', 'y', 'radius', 'life', 'color'}]
        
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
        
        # Boss system
        self.boss = None
        self.boss_fight_active = False
        self.boss_defeated_count = 0
        self.boss_bullets = []
        self.counter_shield_pickups = []
        self.counter_shield_spawn_timer = 0
        self.next_counter_shield_delay = 0
        self.player_has_counter = False
        self.counter_shield_timer = 0
    
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
        if not self.boss_fight_active and self.game_speed < settings.MAX_GAME_SPEED:
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
        
        # --- Cập nhật hiệu ứng nổ đạn ---
        for exp in self.bullet_explosions[:]:
            exp['life'] -= 1
            exp['radius'] += 1.5
            if exp['life'] <= 0:
                self.bullet_explosions.remove(exp)
        
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
        
        # --- Cập nhật Counter Shield cho Player ---
        if self.player_has_counter:
            self.counter_shield_timer -= 1
            if self.counter_shield_timer <= 0:
                self.player_has_counter = False

        # --- Boss Logic ---
        # Kiểm tra spawn boss
        if not self.boss_fight_active and self.boss_defeated_count == 0 and self.score >= settings.BOSS_FIRST_SCORE:
            self.boss_fight_active = True
            self.obstacles.clear()  # Xoá quái cũ để nhường chỗ cho boss
            self.game_speed = settings.INITIAL_GAME_SPEED  # Trả tốc độ về ban đầu để không bị chóng mặt
            try:
                from entities.boss import Boss
                self.boss = Boss()
            except ImportError:
                pass
        
        if self.boss_fight_active and self.boss:
            self.boss.update()
            
            # Spawn bullet patterns
            self.boss.pattern_timer -= 1
            if self.boss.pattern_timer <= 0:
                new_bullets = self.boss.get_next_pattern()
                self.boss_bullets.extend(new_bullets)
                self.boss.pattern_timer = settings.BOSS_PATTERN_INTERVAL
                
            # Cập nhật đạn boss
            for bullet in self.boss_bullets:
                bullet.update()
            self.boss_bullets = [b for b in self.boss_bullets if not b.is_off_screen()]
            
            # Spawn Counter Shield item
            self.counter_shield_spawn_timer += 1
            if self.counter_shield_spawn_timer >= self.next_counter_shield_delay:
                self.counter_shield_spawn_timer = 0
                self.next_counter_shield_delay = random.randint(settings.COUNTER_SHIELD_SPAWN_MIN, settings.COUNTER_SHIELD_SPAWN_MAX)
                try:
                    from entities.counter_shield_pickup import CounterShieldPickup
                    self.counter_shield_pickups.append(CounterShieldPickup(self.game_speed))
                except ImportError:
                    pass
                    
            # Cập nhật Counter Shield item
            for shield in self.counter_shield_pickups:
                shield.update(self.game_speed)
            self.counter_shield_pickups = [s for s in self.counter_shield_pickups if not s.is_off_screen()]

        # --- Spawn obstacles ---
        if not self.boss_fight_active:
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
        priest_burrowed = self.player.is_priest_burrowed()
        
        # Thu thập powerups
        if not priest_burrowed:
            for powerup in self.powerups[:]:
                if player_rect.colliderect(powerup.get_rect()):
                    self.player.activate_powerup(powerup.type)
                    self.powerups.remove(powerup)
        
        # Thu thập item đồng hành
        for pickup in self.companion_pickups[:]:
            if player_rect.colliderect(pickup.get_rect()):
                self._spawn_companion()
                self.companion_pickups.remove(pickup)
                
        # Thu thập Counter Shield
        for shield in self.counter_shield_pickups[:]:
            if player_rect.colliderect(shield.get_rect()):
                self.player_has_counter = True
                self.counter_shield_timer = settings.COUNTER_SHIELD_DURATION
                self.player.activate_powerup('counter_shield')
                self.counter_shield_pickups.remove(shield)
        
        # Fireball tiêu diệt obstacle và đánh Boss
        for fireball in self.fireballs[:]:
            fb_rect = fireball.get_rect()
            
            # Xử lý Fireball va chạm với Boss
            if self.boss and self.boss.state == self.boss.STATE_FIGHTING:
                if fb_rect.colliderect(self.boss.get_rect()):
                    is_dead = self.boss.take_damage(5) # Fireball gây 5 sát thương lên Boss
                    fireball.alive = False
                    if fireball in self.fireballs:
                        self.fireballs.remove(fireball)
                    if is_dead:
                        self.boss_fight_active = False
                        self.boss_defeated_count += 1
                        self.boss = None
                        self.boss_bullets.clear()
                        # Spawn companion ngay sau khi hạ boss
                        if len(self.companions) < 2:
                            self._spawn_companion_pickup()
                    continue
            
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
        
        # --- Va chạm đồng hành với obstacle (Chia sẻ sát thương cả đội) ---
        for obstacle in self.obstacles[:]:
            obs_rect = obstacle.get_rect()
            for comp in self.companions:
                if comp.rect.colliderect(obs_rect):
                    # Nếu có khiên → phá hủy obstacle
                    if team_shielded:
                        if obstacle in self.obstacles:
                            self.obstacles.remove(obstacle)
                        break
                    
                    # Bất tử → bỏ qua
                    if self.player.is_invincible():
                        continue
                    
                    # Nhận sát thương cho cả đội
                    is_dead = self.player.take_damage()
                    if obstacle in self.obstacles:
                        self.obstacles.remove(obstacle)
                    
                    if is_dead:
                        self.player.is_dead = True
                        self.hit_stop_timer = settings.HIT_STOP_FRAMES
                        return
                    break # Chỉ nhận tối đa 1 hit từ obstacle này
        
        # --- Boss Bullet Collisions ---
        for bullet in self.boss_bullets[:]:
            b_rect = bullet.get_rect()
            
            # Đạn đã bị phản thì xét va chạm với boss
            if bullet.is_countered:
                if self.boss and self.boss.state == self.boss.STATE_FIGHTING and b_rect.colliderect(self.boss.get_rect()):
                    is_dead = self.boss.take_damage(settings.COUNTER_DAMAGE_TO_BOSS)
                    if bullet in self.boss_bullets:
                        self.boss_bullets.remove(bullet)
                    if is_dead:
                        self.boss_fight_active = False
                        self.boss_defeated_count += 1
                        self.boss = None
                        self.boss_bullets.clear()
                        # Spawn companion ngay sau khi hạ boss
                        if len(self.companions) < 2:
                            self._spawn_companion_pickup()
                continue
                
            # Đạn chưa bị phản xét va chạm với player
            if player_rect.colliderect(b_rect):
                # Ưu tiên Counter
                if self.player_has_counter:
                    bullet.counter()
                    continue
                
                # Nếu vượt qua được counter mà có frame bất tử hoặc đang dash thì né được
                if self.player.is_invincible():
                    continue
                    
                # Nếu có khiên team -> block toàn bộ đạn boss (triệt tiêu đạn)
                if team_shielded:
                    if bullet in self.boss_bullets:
                        # Thêm hiệu ứng nổ
                        color = settings.COLOR_BOSS_BULLET_DASH if bullet.requires_dash else settings.COLOR_BOSS_BULLET
                        self.bullet_explosions.append({
                            'x': bullet.x,
                            'y': bullet.y,
                            'radius': bullet.radius,
                            'life': 15,
                            'color': color
                        })
                        self.boss_bullets.remove(bullet)
                    continue
                    
                # Nhận dmg
                is_dead = self.player.take_damage(settings.BOSS_BULLET_DAMAGE)
                if bullet in self.boss_bullets:
                    self.boss_bullets.remove(bullet)
                if is_dead:
                    self.player.is_dead = True
                    self.hit_stop_timer = settings.HIT_STOP_FRAMES
                    return
        
        # --- Cập nhật score ---
        score_multiplier = 2 if self.player.has_powerup('double_score') else 1
        self.score += settings.SCORE_INCREMENT * (active_speed / settings.INITIAL_GAME_SPEED) * score_multiplier
        if self.score > self.highscore:
            self.highscore = self.score
        
        # --- Cập nhật background & ground ---
        self.background.update(active_speed)
        self.ground.update(active_speed)
    
    def _draw_team_shield(self):
        """Vẽ lá chắn lớn bao quanh toàn bộ đội nếu có đồng hành."""
        if not self._is_team_shielded() or not self.companions:
            return
            
        # Hiệu ứng nhấp nháy khi player bất tử (sau khi trúng đòn)
        if self.player.invincible_timer > 0 and (self.player.invincible_timer // 6) % 2 == 0:
            return
            
        # Xác định màu khiên (ưu tiên màu xanh skill Knight)
        color = settings.COLOR_POWERUP_SHIELD
        is_skill_shield = False
        if (self.player.skill_active and self.player.character_type == settings.CHARACTER_KNIGHT):
            color = settings.COLOR_SHIELD_SKILL
            is_skill_shield = True
        else:
            for comp in self.companions:
                if hasattr(comp, 'has_active_shield') and comp.has_active_shield():
                    color = settings.COLOR_SHIELD_SKILL
                    is_skill_shield = True
                    break

        # Tính toán bounding box của toàn đội
        rects = [self.player.rect]
        for comp in self.companions:
            rects.append(comp.rect)
            
        min_x = min(r.left for r in rects)
        max_x = max(r.right for r in rects)
        min_y = min(r.top for r in rects)
        max_y = max(r.bottom for r in rects)
        
        # Thêm padding rộng để bao quát
        pad_x, pad_y = 35, 30
        w = (max_x - min_x) + pad_x * 2
        h = (max_y - min_y) + pad_y * 2
        
        # Nếu cả đội cúi xuống, thu nhỏ vòng tròn thay vì làm dẹt sprite
        if self.player.is_ducking:
            # Thu nhỏ chiều rộng và giữ chiều cao không bị giảm quá sâu để tránh dẹt
            w = int(w * 0.82)
            h = int(h * 1.15) # Bù lại chiều cao để giữ hình dáng tròn trịa hơn
            shield_rect = pygame.Rect(0, 0, w, h)
            # Căn giữa theo vị trí cúi của đội
            shield_rect.center = (min_x + (max_x - min_x) // 2, min_y + (max_y - min_y) // 2 + 5)
        else:
            shield_rect = pygame.Rect(min_x - pad_x, min_y - pad_y, w, h)
        
        # Hiệu ứng nhấp nháy/pulse
        pulse = int(math.sin(pygame.time.get_ticks() * 0.005) * 6)
        shield_rect.inflate_ip(pulse, pulse)
        
        # Vẽ Sprite Khiên (Sử dụng sprite có sẵn từ player)
        shield_sprite = getattr(self.player, 'shield_sprite', None)
        if shield_sprite:
            # Scale sprite theo kích thước của team_rect
            scaled_shield = pygame.transform.smoothscale(shield_sprite, (shield_rect.width, shield_rect.height))
            scaled_shield = scaled_shield.copy()
            
            # Phủ màu (tint) theo loại khiên
            tint = pygame.Surface((shield_rect.width, shield_rect.height), pygame.SRCALPHA)
            tint.fill((*color, 80))
            scaled_shield.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            
            scaled_shield.set_alpha(200)
            self.screen.blit(scaled_shield, shield_rect.topleft)
        else:
            # Fallback nếu không có sprite
            pygame.draw.ellipse(self.screen, color, shield_rect, 3)
            inner_surf = pygame.Surface((shield_rect.width, shield_rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(inner_surf, (*color, 45), (0, 0, shield_rect.width, shield_rect.height))
            self.screen.blit(inner_surf, shield_rect.topleft)

    def draw(self):
        """Vẽ mọi thứ lên màn hình (theo thứ tự lớp)."""
        # 1. Background (lớp xa nhất)
        self.background.draw(self.screen)
        
        # 2. Ground
        self.ground.draw(self.screen)
        
        # 3. Obstacles, Powerups, Companion pickups
        # Vẽ hiệu ứng nổ đạn boss
        for exp in self.bullet_explosions:
            alpha = int(255 * (exp['life'] / 15))
            r = int(exp['radius'])
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*exp['color'][:3], alpha), (r, r), r, max(1, r // 4))
            self.screen.blit(surf, (exp['x'] - r, exp['y'] - r))
            
        # Chỉ vẽ obstacle nếu ko có boss
        if not self.boss_fight_active:
            for obstacle in self.obstacles:
                obstacle.draw(self.screen)
        for powerup in self.powerups:
            powerup.draw(self.screen)
        for pickup in self.companion_pickups:
            pickup.draw(self.screen)
        for shield in self.counter_shield_pickups:
            shield.draw(self.screen)
            
        # 3.5 Boss & Boss Bullets
        if self.boss:
            self.boss.draw(self.screen)
        for bullet in self.boss_bullets:
            bullet.draw(self.screen)
        
        # 4. Fireballs
        for fireball in self.fireballs:
            fireball.draw(self.screen)
        
        # 5. Đồng hành (phía sau player)
        use_group_shield = self._is_team_shielded() and len(self.companions) > 0
        for comp in self.companions:
            comp.draw(self.screen, draw_individual_shield=not use_group_shield)
        
        # 6. Player
        self.player.draw(self.screen, draw_individual_shield=not use_group_shield)
        
        # 6.5 Khiên nhóm (bao quanh tất cả)
        if use_group_shield:
            self._draw_team_shield()
        # Chỉ báo counter player
        if self.player_has_counter and not self.player.is_dead:
            px, py = self.player.rect.centerx, self.player.rect.centery
            r = max(self.player.width, self.player.height) // 2 + 10
            pygame.draw.circle(self.screen, settings.COLOR_COUNTER_SHIELD_GLOW, (px, py), r, 3)
            # Pulse nhỏ
            pulse = int(math.sin(pygame.time.get_ticks() * 0.01) * 3)
            pygame.draw.circle(self.screen, settings.COLOR_COUNTER_SHIELD, (px, py), r + pulse, 1)
        
        # 7. HUD (lớp trên cùng) - tryfall nếu HUD chưa nhận được player arg
        # Collect active buffs
        active_buffs = []
        for p_type, timer in self.player.active_powerups.items():
            if timer > 0:
                active_buffs.append({
                    'id': p_type,
                    'timer': timer,
                    'max_timer': settings.POWERUP_DURATION
                })
        if self.player_has_counter:
            active_buffs.append({
                'id': 'counter_shield',
                'timer': self.counter_shield_timer,
                'max_timer': settings.COUNTER_SHIELD_DURATION
            })

        try:
            self.hud.draw(self.screen, self.score, self.highscore, self.game_speed,
                          self.player, self.companions, active_buffs=active_buffs)
            if self.boss and self.boss.state != self.boss.STATE_DYING:
                self.hud.draw_boss_hp_bar(self.screen, self.boss)
        except TypeError:
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
            min_gap = 250
            if new_obstacle.x - (last_obs.x + last_obs.width) < min_gap:
                new_obstacle.x = last_obs.x + last_obs.width + min_gap
                
        # Ngăn obstacle đè lên item đang có trên màn hình (đặc biệt là powerups)
        safe_distance = 150
        for _ in range(10):
            overlapping = False
            items = self.powerups + self.companion_pickups + getattr(self, 'counter_shield_pickups', [])
            for item in items:
                if abs(new_obstacle.x - item.x) < safe_distance:
                    overlapping = True
                    break
            if overlapping:
                new_obstacle.x += safe_distance
            else:
                break
        
        new_obstacle.rect.x = int(new_obstacle.x)
        
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
                for obs in self.obstacles + getattr(self, 'companion_pickups', []):
                    if abs(new_powerup.x - obs.x) < safe_distance:
                        overlapping = True
                        break
                
                if overlapping:
                    new_powerup.x += 150  # Dịch chuyển xa hơn một chút
                    new_powerup.rect.x = int(new_powerup.x)
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
