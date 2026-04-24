"""
Score Manager - Quản lý đọc/ghi save data
Lưu trữ highscore, money, inventory vào file JSON trong thư mục data/.
"""

import os
import json
import copy
import settings

SAVE_FILE = "data/save.json"
_test_save_data = None

def get_default_save_data():
    return {
        "highscore": 0,
        "money": 0,
        "inventory": {
            "max_hp_upgrades": 0,
            "revive": 0,
            "boost": 0,
            "omni_buff": 0
        }
    }

def _real_load():
    default_data = get_default_save_data()
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                return _merge_dicts(default_data, data)
        elif os.path.exists(settings.HIGHSCORE_FILE):
            with open(settings.HIGHSCORE_FILE, "r") as f:
                old_data = json.load(f)
                default_data["highscore"] = old_data.get("highscore", 0)
                return default_data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return default_data

def load_save_data():
    """Đọc dữ liệu save từ file JSON."""
    if getattr(settings, 'IS_ADMIN_TEST_MODE', False):
        global _test_save_data
        if _test_save_data is not None:
            return copy.deepcopy(_test_save_data)
        else:
            _test_save_data = _real_load()
            return copy.deepcopy(_test_save_data)
    return _real_load()

def save_save_data(data):
    """Lưu dữ liệu save vào file JSON."""
    if getattr(settings, 'IS_ADMIN_TEST_MODE', False):
        global _test_save_data
        _test_save_data = copy.deepcopy(data)
        return
        
    os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def reset_test_save():
    global _test_save_data
    _test_save_data = None

def _merge_dicts(default_dict, user_dict):
    """Đệ quy merge 2 dict, giữ lại cấu trúc của default_dict."""
    merged = default_dict.copy()
    for key, value in user_dict.items():
        if key in merged:
            if isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = _merge_dicts(merged[key], value)
            else:
                merged[key] = value
    return merged
