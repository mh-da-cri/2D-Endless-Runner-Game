import pygame
import sys
import settings
from utils.asset_loader import load_font

class AdminConfigState:
    """State cấu hình nhanh các thông số game phục vụ việc test."""
    
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.screen = game_manager.screen
        
        # Load fonts
        self.title_font = load_font(settings.TITLE_FONT_SIZE)
        self.label_font = load_font(24)
        self.val_font = load_font(24)
        self.btn_font = load_font(settings.BUTTON_FONT_SIZE)
        
        # Params data
        self.params = [
            {'id': 'BOSS_FIRST_SCORE', 'name': 'Boss Spawn Score', 'desc': 'Score needed to encounter the boss', 'val': 500.0, 'step': 50.0, 'min': 10.0, 'max': 5000.0},
            {'id': 'BOSS_HP', 'name': 'Boss Max HP', 'desc': 'Total health points of the boss', 'val': 100.0, 'step': 10.0, 'min': 10.0, 'max': 1000.0},
            {'id': 'COUNTER_DAMAGE', 'name': 'Shield Counter DMG', 'desc': 'Damage dealt when reflecting boss bullets', 'val': 1.0, 'step': 1.0, 'min': 1.0, 'max': 100.0},
            {'id': 'BOSS_INTERVAL', 'name': 'Boss Attack Interval', 'desc': 'Frames between boss bullet waves (lower = faster)', 'val': 190.0, 'step': 10.0, 'min': 30.0, 'max': 300.0},
            {'id': 'SHIELD_DURATION', 'name': 'Knight Shield Dur', 'desc': 'Frames the Knight\'s skill lasts (60 = 1s)', 'val': 600.0, 'step': 60.0, 'min': 60.0, 'max': 1200.0},
            {'id': 'COOLDOWN_MULTI', 'name': 'Cooldown Multiplier', 'desc': 'Skill cooldown speed (0.1 = extremely fast)', 'val': 1.0, 'step': 0.1, 'min': 0.1, 'max': 2.0},
        ]
        
        # UI Layout
        self.start_y = 160
        self.row_height = 65
        
        # Generate Rects for [-] and [+] and hitboxes
        self.buttons = []
        center_x = settings.SCREEN_WIDTH // 2
        
        for i, param in enumerate(self.params):
            y = self.start_y + i * self.row_height
            minus_rect = pygame.Rect(center_x + 50, y - 15, 30, 30)
            plus_rect = pygame.Rect(center_x + 180, y - 15, 30, 30)
            self.buttons.append({
                'minus': minus_rect,
                'plus': plus_rect,
                'hover_minus': False,
                'hover_plus': False
            })
            
        # Test Game Button
        self.test_btn = pygame.Rect(
            center_x - settings.BUTTON_WIDTH // 2,
            settings.SCREEN_HEIGHT - 120,
            settings.BUTTON_WIDTH,
            settings.BUTTON_HEIGHT
        )
        self.test_hovered = False
        
        # Back Menu Button
        self.back_btn = pygame.Rect(20, settings.SCREEN_HEIGHT - 70, 150, 45)
        self.back_hovered = False

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        
        self.test_hovered = self.test_btn.collidepoint(mouse_pos)
        self.back_hovered = self.back_btn.collidepoint(mouse_pos)
        
        for i, btns in enumerate(self.buttons):
            btns['hover_minus'] = btns['minus'].collidepoint(mouse_pos)
            btns['hover_plus'] = btns['plus'].collidepoint(mouse_pos)
            
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Tham số cộng/trừ
                for i, btns in enumerate(self.buttons):
                    p = self.params[i]
                    if btns['hover_minus']:
                        p['val'] = max(p['min'], p['val'] - p['step'])
                        p['val'] = round(p['val'], 1)
                    elif btns['hover_plus']:
                        p['val'] = min(p['max'], p['val'] + p['step'])
                        p['val'] = round(p['val'], 1)
                
                # Nút Start Test
                if self.test_hovered:
                    self._apply_settings_and_start()
                    
                # Nút Back
                elif self.back_hovered:
                    from states.menu_state import MenuState
                    self.game_manager.change_state(MenuState(self.game_manager))
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    from states.menu_state import MenuState
                    self.game_manager.change_state(MenuState(self.game_manager))

    def _apply_settings_and_start(self):
        """Áp dụng thông số vào module settings và chạy game."""
        import settings
        # Đọc dữ liệu từ self.params
        data = {p['id']: p['val'] for p in self.params}
        
        settings.BOSS_FIRST_SCORE = int(data['BOSS_FIRST_SCORE'])
        settings.BOSS_HP = int(data['BOSS_HP'])
        settings.COUNTER_DAMAGE_TO_BOSS = int(data['COUNTER_DAMAGE'])
        settings.BOSS_PATTERN_INTERVAL = int(data['BOSS_INTERVAL'])
        settings.SKILL_KNIGHT_DURATION = int(data['SHIELD_DURATION'])
        
        # Cooldown multi
        multi = data['COOLDOWN_MULTI']
        settings.SKILL_KNIGHT_COOLDOWN = max(1, int(settings.SKILL_KNIGHT_COOLDOWN * multi))
        settings.SKILL_SORCERER_COOLDOWN = max(1, int(settings.SKILL_SORCERER_COOLDOWN * multi))
        settings.SKILL_PRIEST_COOLDOWN = max(1, int(settings.SKILL_PRIEST_COOLDOWN * multi))
        
        # Chuyển sang màn hình chọn nhân vật (khi vào PlayState nó sẽ dùng settings đã bị sửa)
        from states.character_select_state import CharacterSelectState
        self.game_manager.change_state(CharacterSelectState(self.game_manager))

    def update(self):
        pass

    def draw(self):
        self.screen.fill((30, 25, 35))
        
        # Title
        title = self.title_font.render("ADMIN TEST MODE", True, (255, 100, 100))
        self.screen.blit(title, title.get_rect(center=(settings.SCREEN_WIDTH // 2, 70)))
        
        warning = self.label_font.render("Changes here will reset when you return to Menu.", True, (200, 200, 100))
        self.screen.blit(warning, warning.get_rect(center=(settings.SCREEN_WIDTH // 2, 115)))
        
        # Vẽ danh sách tham số
        center_x = settings.SCREEN_WIDTH // 2
        for i, param in enumerate(self.params):
            y = self.start_y + i * self.row_height
            
            # Label
            lbl = self.label_font.render(param['name'] + ":", True, settings.COLOR_WHITE)
            lbl_rect = lbl.get_rect(midright=(center_x + 20, y - 10))
            self.screen.blit(lbl, lbl_rect)
            
            # Desc
            try:
                desc_font = load_font(14)
            except Exception:
                desc_font = pygame.font.Font(None, 14)
            desc_lbl = desc_font.render(param.get('desc', ''), True, (150, 150, 150))
            desc_rect = desc_lbl.get_rect(midright=(center_x + 20, y + 12))
            self.screen.blit(desc_lbl, desc_rect)
            
            # Nút Minus
            btns = self.buttons[i]
            m_col = settings.COLOR_TITLE if btns['hover_minus'] else settings.COLOR_BUTTON
            pygame.draw.rect(self.screen, m_col, btns['minus'], border_radius=4)
            m_text = self.val_font.render("-", True, settings.COLOR_WHITE)
            self.screen.blit(m_text, m_text.get_rect(center=btns['minus'].center))
            
            # Value
            # Hiển thị số nguyên nếu không có phần thập phân
            val_str = str(int(param['val'])) if param['val'].is_integer() else str(param['val'])
            v_text = self.val_font.render(val_str, True, (150, 255, 150))
            self.screen.blit(v_text, v_text.get_rect(center=(center_x + 105, y)))
            
            # Nút Plus
            p_col = settings.COLOR_TITLE if btns['hover_plus'] else settings.COLOR_BUTTON
            pygame.draw.rect(self.screen, p_col, btns['plus'], border_radius=4)
            p_text = self.val_font.render("+", True, settings.COLOR_WHITE)
            self.screen.blit(p_text, p_text.get_rect(center=btns['plus'].center))

        # Test Button
        self._draw_btn(self.test_btn, "Start Test ->", self.test_hovered, is_main=True)
        
        # Back Button
        self._draw_btn(self.back_btn, "<- Exit Admin", self.back_hovered, is_main=False)

    def _draw_btn(self, rect, text, hovered, is_main=False):
        color = settings.COLOR_BUTTON_HOVER if hovered else settings.COLOR_BUTTON
        if is_main and hovered:
            color = (200, 50, 50)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        border_color = settings.COLOR_TITLE if hovered else (90, 70, 120)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=8)
        
        font = self.btn_font if is_main else load_font(22)
        txt = font.render(text, True, settings.COLOR_BUTTON_TEXT)
        self.screen.blit(txt, txt.get_rect(center=rect.center))
