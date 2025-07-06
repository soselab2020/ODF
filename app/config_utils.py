# config_utils.py
import os

DEFAULT_CONFIG = {
    "OUTPUT_DIR": "D:\\temp"
}

def load_config(config_path="config.txt") -> dict:
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    print("設定：", config)                
    return config
