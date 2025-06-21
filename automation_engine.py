import cv2
import numpy as np
import time
import threading
import os
from image_detector import ImageDetector
from device_controller import DeviceController

class AutomationEngine:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.image_detector = ImageDetector()
        self.device_controller = DeviceController()
        
        self.is_running = False
        self.log_callback = None
        
        # 最後のタップ時間
        self.last_tap_time = 0
        
        # 画像パスを初期化
        self.reload_images()
        
    def reload_images(self):
        """imageフォルダから画像を再読み込みし、分類する"""
        image_dir = "image"
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
            
        # デフォルトのタップする画像
        default_tap_images = ['play_1.png', 'play_2.png', 'next.png', 'close.png', 'close_mini.png', 'ok.png']
        
        # デフォルトのタップしない画像
        default_ignore_images = ['koukan.png', 'menu.png', 'ranking.png', 'yubin.png']
        
        # 画像ファイルのパスを再構築
        self.image_paths = {}
        self.ignore_images = {}
        
        # imageフォルダ内のすべての画像ファイルを確認
        for filename in os.listdir(image_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(image_dir, filename)
                
                # ファイル名から拡張子を除去
                name_without_ext = os.path.splitext(filename)[0]
                
                if filename in default_ignore_images:
                    # デフォルトのタップしない画像
                    self.ignore_images[name_without_ext] = file_path
                elif filename in default_tap_images:
                    # デフォルトのタップする画像
                    self.image_paths[name_without_ext] = file_path
                else:
                    # 新規追加された画像は初期状態でタップする画像として扱う
                    # ユーザーが明示的にタップしない画像として追加した場合の処理は将来拡張
                    self.image_paths[name_without_ext] = file_path
                    
        self.log(f"画像を再読み込みしました - タップ: {len(self.image_paths)}個, 無視: {len(self.ignore_images)}個")
        
    def set_log_callback(self, callback):
        """ログコールバックの設定"""
        self.log_callback = callback
        
    def log(self, message):
        """ログメッセージの送信"""
        if self.log_callback:
            self.log_callback(message)
            
    def get_available_devices(self):
        """利用可能なデバイスの取得"""
        return self.device_controller.get_devices()
        
    def start(self):
        """自動化の開始"""
        self.is_running = True
        
        # デバイスの設定
        config = self.config_manager.get_config()
        device = config.get('device')
        
        if not device:
            raise Exception("デバイスが選択されていません")
            
        # デバイスコントローラーの初期化
        self.device_controller.set_device(device)
        
        # 画像検出器の初期化
        threshold = config.get('detection_threshold', 0.8)
        self.image_detector.set_threshold(threshold)
        
        self.log(f"自動化開始: デバイス {device}")
        
    def stop(self):
        """自動化の停止"""
        self.is_running = False
        self.log("自動化停止")
        
    def process_frame(self):
        """フレームの処理"""
        if not self.is_running:
            return False
            
        try:
            # スクリーンショットの取得
            screenshot = self.device_controller.get_screenshot()
            if screenshot is None:
                return False
                  # タップしない画像が表示されているかチェック
            ignore_detected = False
            config = self.config_manager.get_config()
            
            for ignore_name, ignore_path in self.ignore_images.items():
                # 設定でその画像の誤タップ防止が有効かチェック
                prevent_key = f'prevent_{ignore_name}'
                if not config.get(prevent_key, True):
                    continue  # この画像の誤タップ防止が無効なのでスキップ
                    
                try:
                    positions = self.image_detector.detect_image(screenshot, ignore_path)
                    if positions:
                        ignore_detected = True
                        self.log(f"{ignore_name} を検出（タップしません）")
                        break
                except:
                    # 画像ファイルが存在しない場合は無視
                    pass
            
            # タップしない画像が検出された場合は何もしない
            if ignore_detected:
                return True
                
            # まずプレイボタンの検出を確認
            play_detected = False
            play_positions = []
            
            # プレイボタンの検出
            for play_image in ['play_1', 'play_2']:
                if play_image in self.image_paths:
                    positions = self.image_detector.detect_image(screenshot, self.image_paths[play_image])
                    if positions:
                        play_detected = True
                        play_positions.extend([(play_image, pos) for pos in positions])
            
            # 各画像の検出とタップ（優先順位付き）
            detected_any = False
            
            # プレイボタンが検出された場合は、プレイボタンのみタップ
            if play_detected:
                current_time = time.time()
                tap_interval = self.config_manager.get_config().get('tap_interval', 0.5)
                
                if current_time - self.last_tap_time >= tap_interval:
                    # 最初に見つかったプレイボタンをタップ
                    image_name, (x, y) = play_positions[0]
                    self.device_controller.tap(x, y)
                    self.last_tap_time = current_time
                    
                    self.log(f"{image_name} を検出してタップ: ({x}, {y})")
                    detected_any = True
                    
            else:
                # プレイボタンが検出されていない場合のみ、他のボタンを処理
                for image_name, image_path in self.image_paths.items():
                    # プレイボタンはすでに処理済みなのでスキップ
                    if image_name in ['play_1', 'play_2']:
                        continue
                        
                    positions = self.image_detector.detect_image(screenshot, image_path)
                    
                    if positions:
                        detected_any = True
                        
                        # タップ間隔の確認
                        current_time = time.time()
                        tap_interval = self.config_manager.get_config().get('tap_interval', 0.5)
                        
                        if current_time - self.last_tap_time >= tap_interval:
                            # 最初に見つかった位置をタップ
                            x, y = positions[0]
                            self.device_controller.tap(x, y)
                            self.last_tap_time = current_time
                            
                            self.log(f"{image_name} を検出してタップ: ({x}, {y})")
                            
                            # 一度にひとつの画像のみ処理
                            break
                        
            return detected_any
            
        except Exception as e:
            self.log(f"処理エラー: {str(e)}")
            return False
            
    def test_image_detection(self):
        """画像検出のテスト"""
        config = self.config_manager.get_config()
        device = config.get('device')
        
        if not device:
            raise Exception("デバイスが選択されていません")
            
        # デバイスコントローラーの初期化
        self.device_controller.set_device(device)
        
        # 画像検出器の初期化
        threshold = config.get('detection_threshold', 0.8)
        self.image_detector.set_threshold(threshold)
        
        # スクリーンショットの取得
        screenshot = self.device_controller.get_screenshot()
        if screenshot is None:
            raise Exception("スクリーンショットの取得に失敗しました")
            
        # 各画像の検出テスト
        results = {}
        
        # タップする画像の検出テスト
        for image_name, image_path in self.image_paths.items():
            try:
                positions = self.image_detector.detect_image(screenshot, image_path)
                results[image_name] = len(positions) > 0
                
                if positions:
                    self.log(f"{image_name}: 検出 ({len(positions)}箇所)")
                else:
                    self.log(f"{image_name}: 未検出")
                    
            except Exception as e:
                self.log(f"{image_name}: エラー - {str(e)}")
                results[image_name] = False
          # タップしない画像の検出テスト
        config = self.config_manager.get_config()
        for ignore_name, ignore_path in self.ignore_images.items():
            # 設定でその画像の誤タップ防止が有効かチェック
            prevent_key = f'prevent_{ignore_name}'
            if not config.get(prevent_key, True):
                results[f"{ignore_name}(無効)"] = False
                self.log(f"{ignore_name}(無効): 誤タップ防止が無効です")
                continue
                
            try:
                positions = self.image_detector.detect_image(screenshot, ignore_path)
                results[f"{ignore_name}(無視)"] = len(positions) > 0
                
                if positions:
                    self.log(f"{ignore_name}(無視): 検出 ({len(positions)}箇所)")
                else:
                    self.log(f"{ignore_name}(無視): 未検出")
                    
            except Exception as e:
                self.log(f"{ignore_name}(無視): エラー - {str(e)}")
                results[f"{ignore_name}(無視)"] = False
                
        return results
