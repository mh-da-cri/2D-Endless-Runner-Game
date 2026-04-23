"""Heads-up display for score, HP, skills, buffs, and boss HP."""

import math

import pygame

import settings
from utils.asset_loader import load_font


class HUD:
    """Draws gameplay HUD elements."""

    def __init__(self):
        self.font = load_font(settings.HUD_FONT_SIZE)
        self.small_font = load_font(settings.HUD_FONT_SIZE - 6)
        self.hp_font = load_font(22)
        self.skill_font = load_font(19)
        self.score_font = load_font(27)
        self.best_font = load_font(23)
        self.frame_count = 0

    def draw(self, screen, score, highscore, game_speed=None, player=None, companions=None, active_buffs=None, combo=0, inventory=None, omni_uses=0):
        self.frame_count += 1
        self._draw_score(screen, int(score), int(highscore))
        
        if combo > 0:
            self._draw_combo(screen, combo)
            
        if inventory and inventory.get('omni_buff', 0) > 0 and omni_uses < 3:
            self._draw_omni_buff(screen, inventory.get('omni_buff', 0), omni_uses)

        if player:
            self._draw_hp_bar(screen, player)
            self._draw_skill_indicator(screen, player, "[1]", 58)

            if companions:
                for i, comp in enumerate(companions):
                    key_label = f"[{comp.companion_index + 2}]"
                    self._draw_companion_skill(screen, comp, key_label, 118 + i * 42)

        if active_buffs:
            num_companions = len(companions) if companions else 0
            self._draw_active_buffs(screen, active_buffs, num_companions)

    def _draw_score(self, screen, score, highscore):
        panel = pygame.Rect(settings.SCREEN_WIDTH - 238, 8, 220, 76)
        self._draw_score_panel(screen, panel)

        text_color = (246, 228, 188)
        value_color = (241, 218, 167)

        score_label = self.score_font.render("Score:", True, text_color)
        score_value = self.score_font.render(str(score), True, value_color)
        best_label = self.best_font.render("Best:", True, text_color)
        best_value = self.best_font.render(str(highscore), True, value_color)

        score_width = score_label.get_width() + 8 + score_value.get_width() + 30
        score_x = panel.centerx - score_width // 2
        score_y = panel.y + 17
        self._draw_text_with_shadow(screen, score_label, (score_x, score_y))
        self._draw_text_with_shadow(screen, score_value, (score_x + score_label.get_width() + 8, score_y))
        coin_x = score_x + score_label.get_width() + 8 + score_value.get_width() + 19
        self._draw_coin_icon(screen, coin_x, score_y + score_label.get_height() // 2)

        best_width = best_label.get_width() + 8 + best_value.get_width()
        best_x = panel.centerx - best_width // 2
        best_y = panel.y + 45
        self._draw_text_with_shadow(screen, best_label, (best_x, best_y))
        self._draw_text_with_shadow(screen, best_value, (best_x + best_label.get_width() + 8, best_y))

    def _draw_combo(self, screen, combo):
        combo_text = f"Combo: {combo}"
        multiplier = "1.0x"
        if combo >= 200: multiplier = "2.0x"
        elif combo >= 100: multiplier = "1.5x"
        elif combo >= 70: multiplier = "1.3x"
        elif combo >= 50: multiplier = "1.2x"
        elif combo >= 20: multiplier = "1.1x"
        
        if multiplier != "1.0x":
            combo_text += f" ({multiplier})"
            
        color = (255, 215, 0) if combo >= 100 else (255, 255, 255)
        text_surf = self.score_font.render(combo_text, True, color)
        # Draw below score panel
        panel = pygame.Rect(settings.SCREEN_WIDTH - 238, 8, 220, 76)
        x = panel.centerx - text_surf.get_width() // 2
        y = panel.bottom + 10
        self._draw_text_with_shadow(screen, text_surf, (x, y))

    def _draw_omni_buff(self, screen, count, uses):
        text = f"[Q] Omni Buff: {count} (Used: {uses}/3)"
        text_surf = self.small_font.render(text, True, (200, 200, 255))
        screen.blit(text_surf, (15, settings.SCREEN_HEIGHT - 35))

    def _draw_hp_bar(self, screen, player):
        heart_size = 27
        heart_gap = 14
        
        panel_width = max(242, 76 + player.max_hp * (heart_size + heart_gap) - heart_gap + 20)
        panel = pygame.Rect(8, 8, panel_width, 44)
        self._draw_pixel_panel(screen, panel)

        hp_label = self.hp_font.render("HP", True, (72, 38, 24))
        screen.blit(hp_label, (panel.x + 16, panel.y + 13))

        heart_start_x = panel.x + 76

        for i in range(player.max_hp):
            hx = heart_start_x + i * (heart_size + heart_gap)
            hy = panel.y + 8

            if i < player.hp:
                if player.hp == 1:
                    pulse = 1 + 0.1 * math.sin(self.frame_count * 0.15)
                    self._draw_heart(screen, hx, hy, int(heart_size * pulse), settings.COLOR_HP_FULL)
                else:
                    self._draw_heart(screen, hx, hy, heart_size, settings.COLOR_HP_FULL)
            else:
                self._draw_heart(screen, hx, hy, heart_size, settings.COLOR_HP_EMPTY)

    def _draw_skill_indicator(self, screen, player, key_label, y_pos):
        icon_rect = pygame.Rect(8, y_pos, 50, 44)
        text_rect = pygame.Rect(61, y_pos, 189, 44)
        self._draw_pixel_panel(screen, icon_rect, fill=(41, 34, 29))
        self._draw_pixel_panel(screen, text_rect)

        skill_names = {
            settings.CHARACTER_KNIGHT: "Shield",
            settings.CHARACTER_SORCERER: "Fireball",
            settings.CHARACTER_PRIEST: "Heal",
        }
        skill_name = skill_names.get(player.character_type, "Skill")
        status_text, name_color, status_color = self._skill_status(player)

        self._draw_skill_icon(screen, player.character_type, icon_rect)

        name_text = self.skill_font.render(f"{skill_name}:", True, (238, 226, 205))
        screen.blit(name_text, (text_rect.x + 10, text_rect.y + 12))

        status = self.skill_font.render(status_text, True, status_color)
        screen.blit(status, (text_rect.x + 88, text_rect.y + 12))

        key_text = self.skill_font.render(key_label, True, (125, 110, 96))
        screen.blit(key_text, (text_rect.right - key_text.get_width() - 8, text_rect.y + 12))

        if not player.can_use_skill and not player.skill_active and player.skill_cooldown_max > 0:
            ratio = 1 - (player.skill_cooldown_timer / player.skill_cooldown_max)
            bar_width = int((text_rect.width - 14) * max(0, min(1, ratio)))
            bar_rect = pygame.Rect(text_rect.x + 7, text_rect.bottom - 8, bar_width, 3)
            pygame.draw.rect(screen, settings.COLOR_SKILL_READY, bar_rect)

    def _skill_status(self, actor):
        if actor.can_use_skill:
            return "READY!", settings.COLOR_SKILL_READY, settings.COLOR_SKILL_READY

        if actor.skill_active and actor.character_type == settings.CHARACTER_KNIGHT:
            remaining = actor.skill_duration_timer / settings.FPS
            return f"ACTIVE {remaining:.0f}s", settings.COLOR_SHIELD_SKILL, settings.COLOR_SHIELD_SKILL

        remaining = actor.skill_cooldown_timer / settings.FPS
        return f"{remaining:.1f}s", settings.COLOR_SKILL_COOLDOWN, settings.COLOR_SKILL_COOLDOWN

    def _draw_companion_skill(self, screen, companion, key_label, y_pos):
        panel = pygame.Rect(8, y_pos, 214, 36)
        self._draw_pixel_panel(screen, panel, fill=(58, 49, 39))

        skill_names = {
            settings.CHARACTER_KNIGHT: "Shield",
            settings.CHARACTER_SORCERER: "Fireball",
            settings.CHARACTER_PRIEST: "Heal",
        }
        skill_name = f"Ally {skill_names.get(companion.character_type, 'Skill')}"
        status_text, _, status_color = self._skill_status(companion)

        key_text = self.skill_font.render(key_label, True, (125, 110, 96))
        screen.blit(key_text, (panel.x + 8, panel.y + 8))

        name_text = self.skill_font.render(skill_name, True, (238, 226, 205))
        screen.blit(name_text, (panel.x + 40, panel.y + 8))

        status = self.skill_font.render(status_text, True, status_color)
        screen.blit(status, (panel.right - status.get_width() - 8, panel.y + 8))

        if not companion.can_use_skill and not companion.skill_active and companion.skill_cooldown_max > 0:
            ratio = 1 - (companion.skill_cooldown_timer / companion.skill_cooldown_max)
            bar_width = int((panel.width - 12) * max(0, min(1, ratio)))
            pygame.draw.rect(screen, settings.COLOR_SKILL_READY, (panel.x + 6, panel.bottom - 6, bar_width, 3))

    def _draw_active_buffs(self, screen, active_buffs, num_companions=0):
        start_x = 15
        y = 138 + num_companions * 42

        labels = {
            "shield": "Shield",
            "double_score": "2x Score",
            "slow_down": "Slow Motion",
            "speed_up": "Speed Boost",
            "high_jump": "High Jump",
            "counter_shield": "Counter Shield",
        }
        colors = {
            "shield": settings.COLOR_POWERUP_SHIELD,
            "double_score": settings.COLOR_POWERUP_SCORE,
            "slow_down": settings.COLOR_POWERUP_SLOW,
            "speed_up": settings.COLOR_POWERUP_SPEED,
            "high_jump": settings.COLOR_POWERUP_JUMP,
            "counter_shield": settings.COLOR_COUNTER_SHIELD,
        }

        for buff in active_buffs:
            b_id = buff["id"]
            timer = buff["timer"]
            max_timer = buff["max_timer"]
            color = colors.get(b_id, settings.COLOR_WHITE)

            label_text = self.small_font.render(labels.get(b_id, b_id), True, color)
            screen.blit(label_text, (start_x, y))

            bar_width = 180
            bg_rect = pygame.Rect(start_x, y + 25, bar_width, 8)
            pygame.draw.rect(screen, (40, 40, 40, 180), bg_rect, border_radius=4)

            ratio = max(0, timer / max_timer)
            fill_rect = pygame.Rect(start_x, y + 25, int(bar_width * ratio), 8)
            pygame.draw.rect(screen, color, fill_rect, border_radius=4)
            y += 45

    def _draw_pixel_panel(self, screen, rect, fill=(94, 76, 55)):
        shadow = rect.move(3, 3)
        pygame.draw.rect(screen, (21, 23, 24), shadow, border_radius=3)
        pygame.draw.rect(screen, (45, 47, 48), rect, border_radius=3)

        inner = rect.inflate(-8, -8)
        pygame.draw.rect(screen, fill, inner, border_radius=2)
        pygame.draw.rect(screen, (116, 96, 70), inner, 2, border_radius=2)

        pygame.draw.line(screen, (154, 133, 96), (inner.left + 3, inner.top + 3), (inner.right - 4, inner.top + 3), 1)
        pygame.draw.line(screen, (44, 38, 32), (inner.left + 3, inner.bottom - 4), (inner.right - 4, inner.bottom - 4), 1)

        bolt_color = (88, 91, 91)
        for bx, by in (
            (rect.left + 4, rect.top + 4),
            (rect.right - 8, rect.top + 4),
            (rect.left + 4, rect.bottom - 8),
            (rect.right - 8, rect.bottom - 8),
        ):
            pygame.draw.rect(screen, bolt_color, (bx, by, 4, 4))

    def _draw_score_panel(self, screen, rect):
        shadow = rect.move(4, 4)
        pygame.draw.rect(screen, (14, 18, 18), shadow, border_radius=3)
        pygame.draw.rect(screen, (43, 49, 48), rect, border_radius=3)

        inner = rect.inflate(-10, -10)
        pygame.draw.rect(screen, (82, 65, 47), inner, border_radius=2)
        pygame.draw.rect(screen, (49, 40, 34), inner, 3, border_radius=2)
        pygame.draw.rect(screen, (169, 122, 61), inner, 2, border_radius=2)

        pygame.draw.line(screen, (210, 163, 84), (inner.left + 5, inner.top + 4), (inner.right - 6, inner.top + 4), 2)
        pygame.draw.line(screen, (48, 35, 28), (inner.left + 5, inner.bottom - 5), (inner.right - 6, inner.bottom - 5), 2)

        trim = (226, 170, 84)
        trim_shadow = (77, 55, 37)
        corner = 13
        for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            cx = inner.left if sx == 1 else inner.right
            cy = inner.top if sy == 1 else inner.bottom
            pygame.draw.line(screen, trim_shadow, (cx, cy + sy * corner), (cx, cy), 2)
            pygame.draw.line(screen, trim_shadow, (cx, cy), (cx + sx * corner, cy), 2)
            pygame.draw.line(screen, trim, (cx + sx * 2, cy + sy * (corner - 2)), (cx + sx * 2, cy + sy * 2), 2)
            pygame.draw.line(screen, trim, (cx + sx * 2, cy + sy * 2), (cx + sx * (corner - 2), cy + sy * 2), 2)

    def _draw_text_with_shadow(self, screen, text_surface, pos):
        x, y = pos
        shadow = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
        shadow.blit(text_surface, (0, 0))
        shadow.fill((45, 31, 24, 190), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(shadow, (x + 2, y + 2))
        screen.blit(text_surface, (x, y))

    def _draw_coin_icon(self, screen, cx, cy):
        pygame.draw.circle(screen, (94, 61, 23), (cx + 2, cy + 2), 11)
        pygame.draw.circle(screen, (226, 158, 38), (cx, cy), 11)
        pygame.draw.circle(screen, (255, 213, 77), (cx, cy), 8)
        pygame.draw.circle(screen, (245, 184, 42), (cx, cy), 5)
        pygame.draw.rect(screen, (255, 232, 125), (cx - 3, cy - 8, 4, 3))

    def _draw_heart(self, screen, x, y, size, color):
        self._draw_heart_shape(screen, x + 2, y + 2, size, (35, 18, 18))
        self._draw_heart_shape(screen, x, y, size, color)

    def _draw_heart_shape(self, screen, x, y, size, color):
        half = size // 2
        quarter = size // 4
        cx1 = x + quarter
        cx2 = x + quarter * 3
        cy = y + quarter
        r = quarter + 1

        pygame.draw.circle(screen, color, (cx1, cy), r)
        pygame.draw.circle(screen, color, (cx2, cy), r)
        pygame.draw.polygon(screen, color, [
            (x - 1, cy),
            (x + half, y + size - 2),
            (x + size + 1, cy),
        ])

    def _draw_skill_icon(self, screen, character_type, rect):
        cx, cy = rect.center
        if character_type == settings.CHARACTER_SORCERER:
            self._draw_fireball_icon(screen, cx, cy)
        elif character_type == settings.CHARACTER_KNIGHT:
            self._draw_shield_icon(screen, cx, cy)
        elif character_type == settings.CHARACTER_PRIEST:
            self._draw_heal_icon(screen, cx, cy)

    def _draw_fireball_icon(self, screen, cx, cy):
        pygame.draw.circle(screen, (91, 23, 10), (cx, cy), 16)
        pygame.draw.polygon(screen, (180, 45, 13), [(cx - 16, cy + 4), (cx - 4, cy - 18), (cx + 12, cy + 4)])
        pygame.draw.circle(screen, settings.COLOR_FIREBALL, (cx, cy + 2), 11)
        pygame.draw.circle(screen, settings.COLOR_FIREBALL_CORE, (cx - 2, cy), 6)

    def _draw_shield_icon(self, screen, cx, cy):
        points = [(cx, cy - 17), (cx + 15, cy - 9), (cx + 11, cy + 12), (cx, cy + 18), (cx - 11, cy + 12), (cx - 15, cy - 9)]
        pygame.draw.polygon(screen, (26, 67, 96), points)
        pygame.draw.polygon(screen, settings.COLOR_SHIELD_SKILL, points, 3)
        pygame.draw.line(screen, (190, 235, 255), (cx, cy - 12), (cx, cy + 12), 2)

    def _draw_heal_icon(self, screen, cx, cy):
        pygame.draw.circle(screen, (22, 72, 46), (cx, cy), 16)
        pygame.draw.rect(screen, settings.COLOR_HEAL, (cx - 4, cy - 14, 8, 28))
        pygame.draw.rect(screen, settings.COLOR_HEAL, (cx - 14, cy - 4, 28, 8))

    def draw_boss_hp_bar(self, screen, boss):
        if boss.hp <= 0:
            return

        bar_width = 400
        bar_height = 20
        x = (settings.SCREEN_WIDTH - bar_width) // 2
        y = 30

        title = self.font.render("DEMON LORD", True, settings.COLOR_BOSS_ACCENT)
        title_rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, y - 15))
        screen.blit(title, title_rect)

        bg_rect = pygame.Rect(x - 2, y - 2, bar_width + 4, bar_height + 4)
        pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect, border_radius=4)

        empty_rect = pygame.Rect(x, y, bar_width, bar_height)
        pygame.draw.rect(screen, settings.COLOR_BOSS_HP_BG, empty_rect, border_radius=3)

        hp_ratio = max(0, float(boss.hp) / boss.max_hp)
        current_bar_width = int(bar_width * hp_ratio)

        if current_bar_width > 0:
            hp_rect = pygame.Rect(x, y, current_bar_width, bar_height)
            pygame.draw.rect(screen, settings.COLOR_BOSS_HP_BAR, hp_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 100, 100), pygame.Rect(x, y, current_bar_width, 2), border_radius=2)

        if boss.hp < boss.max_hp // 3:
            flash_alpha = int(30 + 30 * math.sin(self.frame_count * 0.2))
            flash_surf = pygame.Surface((bar_width + 10, bar_height + 10), pygame.SRCALPHA)
            pygame.draw.rect(flash_surf, (*settings.COLOR_BOSS_HP_BAR, flash_alpha), flash_surf.get_rect(), border_radius=6)
            screen.blit(flash_surf, (x - 5, y - 5))
