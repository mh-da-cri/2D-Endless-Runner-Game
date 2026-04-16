#  Knight Runner - Endless Fantasy

A 2D Endless Runner game built with **Python** and **Pygame**.

**Theme:** High Fantasy - Bạn là một Knight phiêu lưu, chạy xuyên qua vùng đất fantasy đầy quái vật!

##  Điều khiển

| Phím | Hành động |
|------|-----------|
| `SPACE` | Nhảy (nhấn 2 lần = Double Jump) |
| `DOWN (↓)` | Cúi xuống (né quái bay) |
| `SHIFT` | Dash (lao nhanh, bất tử trong lúc dash) |
| `ESC` | Tạm dừng / Về menu |
| `Mouse Click` | Chọn nút trong menu |

##  Yêu cầu

- Python 3.11+
- pygame 2.6.1

##  Cài đặt & Chạy

```bash
# 1. Clone repository
git clone <repo-url>
cd 2D-Endless-Runner-Game

# 2. Tạo virtual environment
python -m venv venv

# 3. Kích hoạt venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat

# 4. Cài đặt thư viện
pip install -r requirements.txt

# 5. Chạy game
python main.py
```

##  Cấu trúc dự án

```
2D-Endless-Runner-Game/
├── assets/                     # Tài nguyên (sprite, âm thanh)
│   ├── images/
│   └── audio/
├── entities/                   # Các đối tượng game
│   ├── player.py               # Knight (nhảy, cúi, dash)
│   ├── obstacle.py             # Quái vật (ground + flying)
│   └── ground.py               # Mặt đất cuộn
├── states/                     # State Machine
│   ├── menu_state.py           # Menu chính
│   ├── play_state.py           # Đang chơi
│   └── gameover_state.py       # Game Over
├── ui/                         # Giao diện
│   ├── background.py           # Parallax scrolling
│   └── hud.py                  # Score display
├── utils/                      # Tiện ích
│   ├── asset_loader.py         # Load ảnh/âm thanh
│   └── score_manager.py        # Lưu/đọc highscore
├── data/
│   └── highscore.json          # Điểm cao nhất
├── settings.py                 # Cấu hình game
├── game_manager.py             # Điều phối states
├── main.py                     # Entry point
└── requirements.txt            # Dependencies
```

##  Phát triển tiếp

- [ ] Thay placeholder bằng pixel art sprites
- [ ] Thêm sprite animation (chạy, nhảy, cúi)
- [ ] Thêm nhiều loại quái vật (goblin, orc, skeleton, ...)
- [ ] Thêm âm thanh và nhạc nền
- [ ] Thêm hệ thống power-ups
- [ ] Thêm Pause state
- [ ] Thêm hiệu ứng particles
