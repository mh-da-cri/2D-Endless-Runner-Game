"""
Settings - Cấu hình tập trung cho game Endless Runner
Chứa tất cả hằng số, thông số game có thể điều chỉnh.
"""

import pygame

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
# PLAYER / NHÂN VẬT
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
DASH_COOLDOWN = 180           # Cooldown dash: 3 giây (3 * 60 frames)

DUCK_SPEED_BONUS = 1          # Bonus tốc độ khi cúi (player hơi trượt nhanh hơn)

# ============================================================
# HP SYSTEM / HỆ THỐNG MÁU
# ============================================================
PLAYER_MAX_HP = 3             # Số máu tối đa
INVINCIBILITY_FRAMES = 120    # 2 giây bất tử sau khi bị đánh (60 FPS)

# ============================================================
# CHARACTER TYPES / LOẠI NHÂN VẬT
# ============================================================
CHARACTER_KNIGHT = "knight"
CHARACTER_SORCERER = "sorcerer"
CHARACTER_PRIEST = "priest"

# ============================================================
# SKILL SYSTEM / HỆ THỐNG KỸ NĂNG
# ============================================================
SKILL_KEY = pygame.K_1        # Phím 1 để dùng skill

# Knight - Khiên bảo vệ
SKILL_KNIGHT_DURATION = 600   # Thời lượng khiên: 10 giây (10 * 60 frames)
SKILL_KNIGHT_COOLDOWN = 1800  # Cooldown: 30 giây (30 * 60 frames) - tính SAU KHI khiên hết

# Sorcerer - Cầu lửa (bắn tuần tự)
SKILL_SORCERER_COOLDOWN = 300 # Cooldown: 5 giây (5 * 60 frames)
FIREBALL_SPEED = 10           # Tốc độ bay của fireball
FIREBALL_COUNT = 3            # Số quả cầu lửa mỗi lần bắn
FIREBALL_SIZE = 15            # Bán kính fireball
FIREBALL_FIRE_INTERVAL = 30   # 0.5 giây giữa mỗi viên đạn

# Priest - Hồi máu
SKILL_PRIEST_COOLDOWN = 1800  # Cooldown: 30 giây (30 * 60 frames)

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

# Thời gian spawn (giãn cách rộng hơn)
MIN_SPAWN_DELAY = 90          # Delay tối thiểu giữa các obstacle (frames)
MAX_SPAWN_DELAY = 200         # Delay tối đa giữa các obstacle (frames)

# ============================================================
# POWER-UPS / VẬT PHẨM TĂNG SỨC MẠNH
# ============================================================
POWERUP_SIZE = 30
POWERUP_DURATION = 300        # Hiệu lực 5 giây (ở 60 FPS)

MIN_POWERUP_SPAWN_DELAY = 600   # Khoảng 10s
MAX_POWERUP_SPAWN_DELAY = 1200  # Khoảng 20s

# ============================================================
# GAME SPEED / TỐC ĐỘ GAME
# ============================================================
INITIAL_GAME_SPEED = 6        # Tốc độ cuộn ban đầu
MAX_GAME_SPEED = 18           # Tốc độ tối đa
SPEED_INCREMENT = 0.001       # Tăng tốc mỗi frame (chậm hơn để dễ chơi)

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
# COLORS / MÀU SẮC
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
COLOR_POWERUP_SHIELD = (100, 200, 255) # Xanh dương nhạt (bất tử)
COLOR_POWERUP_SCORE = (255, 215, 0)    # Vàng gold (nhân đôi điểm)
COLOR_POWERUP_SLOW = (100, 255, 100)   # Xanh lá (giảm tốc)

# Nhân vật mới
COLOR_SORCERER = (120, 60, 180)        # Pháp sư - tím đậm (áo choàng)
COLOR_SORCERER_HAT = (80, 40, 140)     # Mũ phù thủy - tím tối
COLOR_SORCERER_ACCENT = (200, 150, 255) # Điểm nhấn sáng
COLOR_PRIEST = (240, 230, 210)         # Nữ tu - trắng kem (áo tu)
COLOR_PRIEST_HOOD = (200, 190, 170)    # Mũ hood - kem tối
COLOR_PRIEST_ACCENT = (255, 220, 120)  # Vàng nhạt (thánh giá)

# Skill colors
COLOR_FIREBALL = (255, 120, 30)        # Cam đỏ (lửa)
COLOR_FIREBALL_CORE = (255, 230, 80)   # Lõi vàng sáng
COLOR_SHIELD_SKILL = (80, 180, 255)    # Xanh dương (khiên skill)
COLOR_HEAL = (100, 255, 150)           # Xanh lá nhạt (hồi máu)
COLOR_HP_FULL = (220, 50, 50)          # Đỏ (trái tim đầy)
COLOR_HP_EMPTY = (60, 30, 30)          # Nền trái tim trống
COLOR_SKILL_READY = (100, 255, 200)    # Skill sẵn sàng
COLOR_SKILL_COOLDOWN = (100, 100, 100) # Skill đang hồi
COLOR_COMPANION_PICKUP = (255, 200, 80)     # Quả cầu vàng
COLOR_COMPANION_PICKUP_GLOW = (255, 230, 150) # Hào quang vàng

# ============================================================
# HỆ THỐNG ĐỒNG HÀNH
# ============================================================
COMPANION_SCORE_MILESTONES = [200, 500]  # Mốc điểm xuất hiện item đồng hành
COMPANION_SCALE = 0.8                    # Tỉ lệ kích thước đồng hành (80%)
COMPANION_OFFSET_X = -45                 # Khoảng cách X đồng hành sau lưng player
COMPANION_PICKUP_SIZE = 35               # Kích thước item đồng hành
SKILL_KEY_COMPANION_1 = pygame.K_2       # Phím 2 cho đồng hành thứ 1
SKILL_KEY_COMPANION_2 = pygame.K_3       # Phím 3 cho đồng hành thứ 2

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
