#  Knight Runner - Endless Fantasy

Game chạy vô tận 2D phong cách **High Fantasy**, được xây dựng bằng **Python** và **Pygame**.

Chọn một trong ba nhân vật — **Knight**, **Sorcerer**, **Priest** — rồi lao vào vùng rừng đầy quái vật, thu thập power-up, chiến đấu với Boss, và chinh phục điểm số cao nhất!

---

##  Điều khiển

| Phím | Hành động |
|------|-----------|
| `SPACE` | Nhảy (nhấn 2 lần = Double Jump) |
| `↓ DOWN` / `S` | Cúi xuống (né quái bay) |
| `SHIFT` | Dash (lướt nhanh, tăng tốc 1.5×) |
| `1` | Dùng Skill nhân vật chính |
| `2` / `3` | Dùng Skill đồng hành thứ 1 / 2 |
| `Q` | Dùng Omni Buff (nếu có trong túi đồ) |
| `P` / `ESC` | Tạm dừng / Về menu |
| `Chuột` | Chọn nút trong giao diện |

---

##  Tính năng nổi bật

###  3 Nhân vật có kỹ năng riêng

| Nhân vật | Vai trò | Skill | Cooldown |
|----------|---------|-------|----------|
| **Knight** | Tank Warrior | **Shield** — Bất tử 10 giây | 30s |
| **Sorcerer** | Fire Mage | **Fireball** — Bắn 3 quả cầu lửa tiêu diệt quái/boss | 5s |
| **Priest** | Holy Healer | **Heal** — Hồi 1 HP | 30s |

Ngoài ra còn có lựa chọn **Random** để hệ thống chọn ngẫu nhiên.

###  Hệ thống quái vật (Sprite Animation)
- **Skeleton** — Quái mặt đất, 3 biến thể màu (cam, tím, xám).
- **Bat** — Quái bay ở nhiều độ cao khác nhau, cần cúi hoặc nhảy để né.
- **Spider** — Nhện đu tơ từ trên xuống, 3 biến thể: xám (trừ điểm), xanh (làm chậm), đỏ (x2 sát thương).

###  Boss Fight
- Boss xuất hiện tại mốc **500 điểm**.
- Boss bắn 4 kiểu đạn: hàng ngang thấp (cần nhảy), hàng ngang cao (cần cúi), tường đạn (cần dash), mưa đạn (cần dash).
- Nhặt **Counter Shield** để phản đạn boss gây sát thương ngược.
- Fireball của Sorcerer cũng gây sát thương lên Boss.
- Boss Phase 2 (HP < 50%): tăng tốc bắn.

###  Hệ thống đồng hành (Companion)
- Nhặt item đồng hành tại mốc **250 điểm** và sau khi hạ Boss.
- Đồng hành đi theo sau lưng nhân vật chính, sao chép chuyển động, và có skill riêng (phím `2`, `3`).
- Tối đa **2 đồng hành** cùng lúc — nhân vật được chọn ngẫu nhiên từ 3 class.
- Đồng hành Knight bật Shield → cả đội được bảo vệ bằng vòng khiên nhóm.

###  Power-ups
Thu thập ngẫu nhiên trên đường chạy:
- **Shield** — Bất tử tạm thời.
- **Double Score** — Nhân đôi điểm.
- **Slow Down** — Giảm tốc độ game.
- **Speed Up** — Tăng tốc + thêm điểm.
- **High Jump** — Nhảy cao hơn.

###  Shop (Cửa hàng)
Dùng tiền kiếm được sau mỗi ván để mua vật phẩm:

| Vật phẩm | Giá | Mô tả |
|----------|-----|-------|
| **Omni Buff** | 100 | Kích hoạt tất cả buff trong 10 giây (phím Q, tối đa 3 lần/ván) |
| **Boost** | 200 | Lướt nhanh lên 200 điểm ngay đầu ván |
| **Max HP +1** | 300+ | Tăng máu tối đa (tối đa 3 lần, giá tăng dần) |
| **Revive** | 500 | Hồi sinh 1 lần khi chết (mỗi ván chỉ dùng 1 lần) |

###  Hệ thống điểm & tiến trình
- **Combo**: Né liên tục quái/đạn boss tăng combo, combo cao tăng hệ số điểm (lên đến x2.0 ở 200 combo).
- **Highscore** và **Money** được lưu tự động vào `data/save.json`.
- Tiền nhận được sau mỗi ván = `Score ÷ 2` (làm tròn lên).

###  Âm thanh & Nhạc nền
- Nhạc nền khác nhau cho Menu và Chiến đấu.
- Hiệu ứng âm thanh cho nhảy, skill, nhặt item, quái chết, boss bị đánh, v.v.

###  Admin Mode
- Vào từ Menu chính → **ADMIN MODE**.
- Chỉnh realtime các thông số: Boss HP, Dash Cooldown, Shield Duration, Bullet Speed, v.v.
- Nút **+9999 Money** để test shop.
- Mọi thay đổi chỉ áp dụng trong phiên test, tự động reset khi về Menu.

---

##  Cài đặt & Chạy

> **Yêu cầu:** Python 3.11+ đã được cài đặt và thêm vào PATH.

```
# 1. Clone repository
git clone <repo-url>
cd 2D-Endless-Runner-Game

# 2. Cài đặt môi trường (chỉ cần chạy lần đầu)
Nhấp đúp vào file setup.bat

# 3. Chạy game
Nhấp đúp vào file run.bat
```

`setup.bat` sẽ tự động tạo virtual environment, cài đặt thư viện (pygame), và tạo các thư mục cần thiết.

---

##  Cấu trúc dự án

```
2D-Endless-Runner-Game/
├── assets/                         # Tài nguyên game
│   ├── images/                     # Sprite sheets, background, UI
│   ├── audio/                      # Nhạc nền, hiệu ứng âm thanh
│   ├── Priest.png                  # Sprite sheet Priest
│   └── Priest-skills.png           # Sprite sheet hiệu ứng Priest
├── data/                           # Dữ liệu lưu game (gitignored)
│   ├── highscore.json
│   └── save.json
├── entities/                       # Các đối tượng trong game
│   ├── player.py                   # Nhân vật chính (Knight/Sorcerer/Priest)
│   ├── companion.py                # Nhân vật đồng hành
│   ├── obstacle.py                 # Quái vật (Skeleton, Bat, Spider)
│   ├── boss.py                     # Boss (Shadow Boss)
│   ├── boss_bullet.py              # Đạn boss
│   ├── fireball.py                 # Cầu lửa (skill Sorcerer)
│   ├── powerup.py                  # Vật phẩm tăng sức mạnh
│   ├── companion_pickup.py         # Item triệu hồi đồng hành
│   ├── counter_shield_pickup.py    # Item khiên phản đạn
│   └── ground.py                   # Mặt đất cuộn
├── states/                         # State Machine (các màn hình)
│   ├── menu_state.py               # Menu chính
│   ├── character_select_state.py   # Chọn nhân vật
│   ├── play_state.py               # Gameplay chính
│   ├── gameover_state.py           # Game Over + Revive
│   ├── shop_state.py               # Cửa hàng
│   └── admin_config_state.py       # Admin Test Mode
├── ui/                             # Giao diện
│   ├── background.py               # Parallax scrolling background
│   └── hud.py                      # HUD (HP, Score, Skill, Combo, Buff)
├── utils/                          # Tiện ích
│   ├── asset_loader.py             # Load ảnh, font, âm thanh
│   ├── music_manager.py            # Quản lý nhạc nền
│   ├── score_manager.py            # Đọc/ghi save data
│   └── spritesheet.py              # Cắt frame từ sprite sheet
├── settings.py                     # Cấu hình tập trung (tất cả hằng số game)
├── game_manager.py                 # Điều phối State Machine
├── main.py                         # Entry point
├── setup.bat                       # Script cài đặt tự động
├── run.bat                         # Script chạy game
└── requirements.txt                # Dependencies (pygame==2.6.1)
```

---

##  Luồng game

```
Menu ──► Chọn nhân vật ──► Gameplay ──► Game Over ──► Chọn nhân vật
  │            │                                          │
  ├─ Tutorial  ├─ Shop                                    ├─ Revive (quay lại Gameplay)
  ├─ Admin Mode                                           └─ Menu
  └─ Exit
```
