"""
Settings - Cấu hình tập trung cho game Endless Runner
Chứa tất cả hằng số, thông số game có thể điều chỉnh.
"""

# ============================================================
# SCREEN / MÀN HÌNH
# ============================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Knight Runner - Endless Fantasy"

# ============================================================
# PHYSICS / VẬT LÝ
# ============================================================
GRAVITY = 0.8                # Gia tốc trọng trường (pixels/frame²)
GROUND_Y = 620               # Tọa độ Y của mặt đất (tính từ trên xuống)
GROUND_HEIGHT = 100           # Chiều cao phần mặt đất vẽ bên dưới

# ============================================================
# PLAYER / NHÂN VẬT (Knight)
# ============================================================
PLAYER_START_X = 150          # Vị trí X cố định của player
PLAYER_WIDTH = 50             # Chiều rộng hitbox bình thường
PLAYER_HEIGHT = 80            # Chiều cao hitbox bình thường
PLAYER_DUCK_HEIGHT = 40       # Chiều cao hitbox khi cúi

JUMP_FORCE = -15              # Lực nhảy lần 1 (âm = đi lên)
DOUBLE_JUMP_FORCE = -13       # Lực nhảy lần 2 (yếu hơn một chút)
MAX_JUMPS = 2                 # Số lần nhảy tối đa (double jump)

DASH_SPEED = 1.5              # Hệ số tăng tốc độ khi lướt
DASH_DURATION = 60            # Thời gian lướt (frames)
DASH_COOLDOWN = 60            # Thời gian chờ (cooldown) để lướt lần tiếp theo (frames)

DUCK_SPEED_BONUS = 1          # Bonus tốc độ khi cúi (player hơi trượt nhanh hơn)

# ============================================================
# OBSTACLES / CHƯỚNG NGẠI VẬT
# ============================================================
OBSTACLE_MIN_WIDTH = 40       # Kích thước tối thiểu
OBSTACLE_MAX_WIDTH = 70       # Kích thước tối đa
OBSTACLE_MIN_HEIGHT = 50
OBSTACLE_MAX_HEIGHT = 80

# Chướng ngại vật bay (cần cúi để né)
FLYING_OBSTACLE_Y_MIN = 480   # Vị trí Y tối thiểu (cao nhất) của obstacle bay
FLYING_OBSTACLE_Y_MAX = 560   # Vị trí Y tối đa (thấp nhất) của obstacle bay
FLYING_OBSTACLE_WIDTH = 50
FLYING_OBSTACLE_HEIGHT = 40

# Spawn timing
MIN_SPAWN_DELAY = 60          # Delay tối thiểu giữa các obstacle (frames)
MAX_SPAWN_DELAY = 150         # Delay tối đa giữa các obstacle (frames)

# ============================================================
# GAME SPEED / TỐC ĐỘ GAME
# ============================================================
INITIAL_GAME_SPEED = 6        # Tốc độ cuộn ban đầu
MAX_GAME_SPEED = 18           # Tốc độ tối đa
SPEED_INCREMENT = 0.002       # Tăng tốc mỗi frame

# ============================================================
# SCORING / ĐIỂM SỐ
# ============================================================
SCORE_INCREMENT = 0.02        # Điểm tăng mỗi frame
HIGHSCORE_FILE = "data/highscore.json"

# ============================================================
# PARALLAX BACKGROUND / NỀN CUỘN
# ============================================================
# Tỷ lệ tốc độ cuộn cho mỗi lớp nền (so với game speed)
BG_LAYER_SPEEDS = [0.1, 0.3, 0.5, 0.8]

# ============================================================
# COLORS / MÀU SẮC (Placeholder - sẽ thay bằng sprite)
# ============================================================
# Theme: High Fantasy
COLOR_SKY = (40, 45, 80)              # Bầu trời tối (dark fantasy)
COLOR_SKY_GRADIENT = (70, 80, 130)    # Gradient bầu trời
COLOR_GROUND = (55, 40, 30)           # Đất nâu tối
COLOR_GROUND_TOP = (75, 60, 45)       # Viền trên mặt đất (sáng hơn)
COLOR_GRASS = (45, 80, 45)            # Cỏ xanh tối
COLOR_PLAYER = (180, 180, 210)        # Knight - màu bạc (giáp)
COLOR_PLAYER_VISOR = (100, 150, 220)  # Phần mũ giáp - xanh
COLOR_OBSTACLE_GROUND = (100, 60, 50) # Quái mặt đất - nâu đỏ (goblin/orc)
COLOR_OBSTACLE_FLYING = (80, 50, 90)  # Quái bay - tím tối
COLOR_MENU_BG = (25, 25, 45)          # Nền menu
COLOR_BUTTON = (70, 50, 100)          # Nút bấm - tím
COLOR_BUTTON_HOVER = (100, 70, 140)   # Nút bấm hover
COLOR_BUTTON_TEXT = (230, 220, 200)   # Text nút bấm
COLOR_TITLE = (220, 190, 100)         # Tiêu đề - vàng gold
COLOR_TEXT = (220, 215, 200)          # Text chung - trắng ấm
COLOR_SCORE = (255, 215, 0)           # Điểm số - vàng
COLOR_GAMEOVER = (200, 50, 50)        # Game Over - đỏ
COLOR_HUD_BG = (0, 0, 0, 120)        # Nền HUD bán trong suốt
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# ============================================================
# UI / GIAO DIỆN
# ============================================================
BUTTON_WIDTH = 250
BUTTON_HEIGHT = 60
BUTTON_BORDER_RADIUS = 12
BUTTON_FONT_SIZE = 32
TITLE_FONT_SIZE = 72
HUD_FONT_SIZE = 28
GAMEOVER_TITLE_SIZE = 64
GAMEOVER_SCORE_SIZE = 36
GAMEOVER_HINT_SIZE = 24
