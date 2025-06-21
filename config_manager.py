import json
import os

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """設定ファイルの読み込み"""
        default_config = {
            'device': '',
            'tap_interval': 0.5,
            'detection_threshold': 0.8,
            'window_size': '600x500',
            'auto_refresh_devices': True,
            'log_level': 'INFO',
            'save_debug_images': False,
            'debug_images_path': 'debug_images',
            'prevent_goukan': True,
            'prevent_yuubin': True,
            'prevent_ranking': True,
            'prevent_menu': True
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # デフォルト設定と統合
                default_config.update(loaded_config)
                return default_config
                
            except Exception as e:
                print(f"設定ファイル読み込みエラー: {str(e)}")
                return default_config
        else:
            return default_config
            
    def save_config(self):
        """設定ファイルの保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"設定ファイル保存エラー: {str(e)}")
            return False
            
    def get_config(self):
        """設定の取得"""
        return self.config.copy()
        
    def set_config(self, new_config):
        """設定の更新"""
        self.config.update(new_config)
        self.save_config()
        
    def get_value(self, key, default=None):
        """特定の設定値を取得"""
        return self.config.get(key, default)
        
    def set_value(self, key, value):
        """特定の設定値を設定"""
        self.config[key] = value
        self.save_config()
        
    def reset_to_default(self):
        """設定をデフォルトに戻す"""
        default_config = {
            'device': '',
            'tap_interval': 0.5,
            'detection_threshold': 0.8,
            'window_size': '600x500',
            'auto_refresh_devices': True,
            'log_level': 'INFO',
            'save_debug_images': False,
            'debug_images_path': 'debug_images'
        }
        
        self.config = default_config
        self.save_config()
        
    def validate_config(self):
        """設定の検証"""
        errors = []
        
        # タップ間隔の検証
        tap_interval = self.config.get('tap_interval', 0.5)
        if not isinstance(tap_interval, (int, float)) or tap_interval < 0.1 or tap_interval > 10:
            errors.append("タップ間隔は0.1秒から10秒の間で設定してください")
            
        # 検出精度の検証
        threshold = self.config.get('detection_threshold', 0.8)
        if not isinstance(threshold, (int, float)) or threshold < 0.1 or threshold > 1.0:
            errors.append("検出精度は0.1から1.0の間で設定してください")
            
        return errors
        
    def export_config(self, export_path):
        """設定のエクスポート"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"設定エクスポートエラー: {str(e)}")
            return False
            
    def import_config(self, import_path):
        """設定のインポート"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                
            # 現在の設定と統合
            self.config.update(imported_config)
            
            # 設定の検証
            errors = self.validate_config()
            if errors:
                print("設定の警告:")
                for error in errors:
                    print(f"  - {error}")
                    
            self.save_config()
            return True
            
        except Exception as e:
            print(f"設定インポートエラー: {str(e)}")
            return False
            
    def backup_config(self, backup_path=None):
        """設定のバックアップ"""
        if backup_path is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"config_backup_{timestamp}.json"
            
        return self.export_config(backup_path)
        
    def __str__(self):
        """設定の文字列表現"""
        return json.dumps(self.config, indent=2, ensure_ascii=False)
