"""Shop state."""

import math
import sys

import pygame

import settings
from utils.asset_loader import load_font, load_sound, play_sound
from utils.music_manager import play_music
from utils.score_manager import load_save_data, save_save_data


class ShopState:
    """Shop screen with an ornate fantasy menu style."""

    PANEL_DARK = (45, 37, 36)
    PANEL_MID = (78, 61, 52)
    PANEL_HOVER = (99, 75, 59)
    GOLD_DARK = (104, 70, 39)
    GOLD = (195, 133, 66)
    GOLD_LIGHT = (255, 214, 137)
    TEXT_GOLD = (255, 224, 163)
    TEXT_SHADOW = (78, 30, 34)

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.screen = game_manager.screen
        
        self.save_data = load_save_data()
        self.money = self.save_data.get('money', 0)
        self.inventory = self.save_data.get('inventory', {})
        
        # Max HP upgrades limit
        self.MAX_HP_UPGRADES = 3
        
        self.title_font = load_font(58, "georgia")
        self.name_font = load_font(30, "georgia")
        self.desc_font = load_font(14, "georgia")
        self.small_font = load_font(14)
        self.price_font = load_font(24)
        self.button_font = load_font(25, "georgia")

        self.card_width = 220
        self.card_height = 320
        self.card_gap = 30
        
        self.back_button = pygame.Rect(34, settings.SCREEN_HEIGHT - 76, 170, 54)
        self.hovered_card = -1
        self.back_hovered = False
        self.frame_count = 0

        self.click_sound = load_sound(settings.UI_CLICK_SOUND)
        play_music(settings.MENU_MUSIC, settings.BACKGROUND_MUSIC_VOLUME)
        
        self._setup_items()

    def _setup_items(self):
        hp_upgrades = self.inventory.get('max_hp_upgrades', 0)
        hp_price = 300 + hp_upgrades * 100 if hp_upgrades < self.MAX_HP_UPGRADES else "MAX"
        
        self.items = [
            {
                "id": "omni_buff",
                "name": "Omni Buff",
                "desc": "Gain all buffs for 10s (Press Q)",
                "price": 100,
                "owned": self.inventory.get('omni_buff', 0),
            },
            {
                "id": "boost",
                "name": "Boost",
                "desc": "Dash forward to 200 score",
                "price": 200,
                "owned": self.inventory.get('boost', 0),
            },
            {
                "id": "max_hp",
                "name": "Max HP +1",
                "desc": f"Increase Max HP (Max {self.MAX_HP_UPGRADES})",
                "price": hp_price,
                "owned": hp_upgrades,
            },
            {
                "id": "revive",
                "name": "Revive",
                "desc": "Revive once after dying",
                "price": 500,
                "owned": self.inventory.get('revive', 0),
            }
        ]
        
        total_width = self.card_width * 4 + self.card_gap * 3
        start_x = (settings.SCREEN_WIDTH - total_width) // 2
        card_y = 232
        self.card_rects = [
            pygame.Rect(start_x + i * (self.card_width + self.card_gap), card_y, self.card_width, self.card_height)
            for i in range(4)
        ]

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_card = -1
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_card = i
                break

        self.back_hovered = self.back_button.collidepoint(mouse_pos)

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hovered_card >= 0:
                    self._buy_item(self.hovered_card)
                elif self.back_hovered:
                    play_sound(self.click_sound, volume=0.5)
                    from states.character_select_state import CharacterSelectState
                    self.game_manager.change_state(CharacterSelectState(self.game_manager))

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    from states.character_select_state import CharacterSelectState
                    self.game_manager.change_state(CharacterSelectState(self.game_manager))

    def _buy_item(self, index):
        item = self.items[index]
        price = item["price"]
        
        if price == "MAX":
            return
            
        if self.money >= price:
            self.money -= price
            play_sound(self.click_sound, volume=0.8)
            
            if item["id"] == "max_hp":
                self.inventory['max_hp_upgrades'] = self.inventory.get('max_hp_upgrades', 0) + 1
            else:
                self.inventory[item["id"]] = self.inventory.get(item["id"], 0) + 1
                
            # Save data
            self.save_data['money'] = self.money
            self.save_data['inventory'] = self.inventory
            save_save_data(self.save_data)
            
            # Refresh items for price changes
            self._setup_items()

    def update(self):
        self.frame_count += 1

    def draw(self):
        self.screen.fill((20, 16, 15))
        self._draw_header()

        for i, item in enumerate(self.items):
            self._draw_item_card(i, item)
            
        self._draw_back_button()

        # Draw Money
        money_text = self.title_font.render(f"Money: {self.money}", True, (255, 215, 0))
        self.screen.blit(money_text, (settings.SCREEN_WIDTH - money_text.get_width() - 30, settings.SCREEN_HEIGHT - 80))

    def _draw_header(self):
        panel = pygame.Rect(0, 54, 700, 116)
        panel.centerx = settings.SCREEN_WIDTH // 2
        self._draw_ornate_panel(panel, self.PANEL_DARK, large=True)

        title = self.title_font.render("MERCHANT SHOP", True, self.TEXT_GOLD)
        title_rect = title.get_rect(center=(panel.centerx, panel.centery - 3))
        self._draw_text_surface(title, title_rect, shadow=self.TEXT_SHADOW, outline=(58, 28, 29))

        subtitle = self.small_font.render("Purchase items and upgrades for your journey", True, (220, 179, 126))
        subtitle_rect = subtitle.get_rect(center=(panel.centerx, panel.bottom + 27))
        self._draw_text_surface(subtitle, subtitle_rect, shadow=(39, 28, 23))

    def _draw_item_card(self, index, item):
        rect = self.card_rects[index]
        is_hovered = self.hovered_card == index
        can_afford = item["price"] != "MAX" and self.money >= item["price"]
        
        draw_rect = rect.move(0, -10 if is_hovered and can_afford else 0)

        if is_hovered and can_afford:
            glow = pygame.Surface((draw_rect.width + 34, draw_rect.height + 34), pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 215, 0, 42), glow.get_rect(), border_radius=16)
            self.screen.blit(glow, (draw_rect.x - 17, draw_rect.y - 17))

        fill = self.PANEL_HOVER if (is_hovered and can_afford) else self.PANEL_DARK
        self._draw_ornate_panel(draw_rect, fill)
        
        name_text = self.name_font.render(item["name"].upper(), True, self.TEXT_GOLD)
        name_rect = name_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 40))
        self._draw_text_surface(name_text, name_rect, shadow=self.TEXT_SHADOW)

        desc_text = self.desc_font.render(item["desc"], True, (235, 218, 190))
        desc_rect = desc_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 100))
        self._draw_text_surface(desc_text, desc_rect, shadow=(39, 27, 22))

        owned_text = self.small_font.render(f"Owned: {item['owned']}", True, (178, 146, 100))
        owned_rect = owned_text.get_rect(center=(draw_rect.centerx, draw_rect.y + 180))
        self._draw_text_surface(owned_text, owned_rect, shadow=(39, 27, 22))
        
        price_color = (255, 215, 0) if can_afford else (200, 50, 50)
        price_str = f"Price: {item['price']}" if item['price'] != "MAX" else "MAX LEVEL"
        price_text = self.price_font.render(price_str, True, price_color)
        price_rect = price_text.get_rect(center=(draw_rect.centerx, draw_rect.bottom - 40))
        self._draw_text_surface(price_text, price_rect, shadow=self.TEXT_SHADOW)

    def _draw_back_button(self):
        draw_rect = self.back_button.move(0, -3 if self.back_hovered else 0)
        if self.back_hovered:
            glow = pygame.Surface((draw_rect.width + 28, draw_rect.height + 24), pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 196, 96, 42), glow.get_rect(), border_radius=10)
            self.screen.blit(glow, (draw_rect.x - 14, draw_rect.y - 12))

        self._draw_ornate_panel(draw_rect, self.PANEL_HOVER if self.back_hovered else self.PANEL_MID)
        label = self.button_font.render("< BACK", True, self.TEXT_GOLD)
        self._draw_text_surface(
            label,
            label.get_rect(center=draw_rect.center),
            shadow=self.TEXT_SHADOW,
            outline=(58, 28, 29),
        )

    def _draw_ornate_panel(self, rect, fill, large=False):
        cut = 18 if large else 14
        outer = self._beveled_points(rect, cut)
        shadow = [(x + 6, y + 6) for x, y in outer]
        pygame.draw.polygon(self.screen, (16, 17, 18), shadow)
        pygame.draw.polygon(self.screen, (52, 43, 42), outer)
        pygame.draw.polygon(self.screen, self.GOLD_DARK, outer, 5)
        pygame.draw.polygon(self.screen, self.GOLD_LIGHT, outer, 2)

        mid = rect.inflate(-12, -12)
        pygame.draw.polygon(self.screen, self.GOLD, self._beveled_points(mid, max(6, cut - 5)), 3)

        inner = rect.inflate(-24, -24)
        inner_points = self._beveled_points(inner, max(4, cut - 8))
        pygame.draw.polygon(self.screen, fill, inner_points)
        pygame.draw.polygon(self.screen, (73, 36, 38), inner_points, 2)

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
