import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import cv2
import numpy as np
import subprocess
import threading
import time
import os
from datetime import datetime
import json
import struct
import socket

class PuniPuniAutoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("妖怪ウォッチぷにぷに自動周回ソフト")
        self.root.geometry("800x600")
        
        # 変数の初期化
        self.devices = []
        self.selected_devices = []
        self.running = False
        self.threads = {}
        self.device_status = {}
        
        # 画像ファイルパス
        self.image_paths = {
            'boss': 'image/boss.jpg',
            'play': 'image/play.png',
            'puzzle': 'image/puzzle.png',
            'waza_ok': 'image/waza_ok.png',
            'next': 'image/next.png',
            'close': 'image/close.png',
            'close_mini': 'image/close_mini.png',
            'stage_45': 'image/stage_45.png'
        }
          # 設定
        self.settings = {
            'similarity_threshold': 0.8,
            'tap_delay': 0.3,  # 実際のタップに近い遅延
            'puzzle_tap_count': 2,
            'check_interval': 0.1,  # 高速チェック間隔
            'screenshot_cache_time': 0.05,  # スクリーンショットキャッシュ時間
            'human_like_delay_min': 0.15,  # 人間らしい遅延の最小値
            'human_like_delay_max': 0.4   # 人間らしい遅延の最大値
        }
        
        # スクリーンショットキャッシュ
        self.screenshot_cache = {}
        self.last_screenshot_time = {}          # メモリ直接アクセス用の設定
        self.use_memory_capture = True  # メモリ直接取得を有効化
        self.minicap_connections = {}  # デバイスごとのminicap接続
        self.raw_capture_enabled = False  # RAWキャプチャフラグ
        self.device_compatibility = {}  # デバイス互換性情報
        self.fallback_count = {}  # フォールバック回数の記録
        
        # リアルタイム監視用
        self.realtime_monitoring = False
        self.realtime_monitor_thread = None
        
        self.create_widgets()
        self.refresh_devices()
        
    def create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # デバイス選択フレーム
        device_frame = ttk.LabelFrame(main_frame, text="デバイス選択", padding="5")
        device_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(device_frame, text="デバイス更新", command=self.refresh_devices).grid(row=0, column=0, padx=(0, 10))
        
        self.device_listbox = tk.Listbox(device_frame, height=4, selectmode=tk.MULTIPLE)
        self.device_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 設定フレーム
        settings_frame = ttk.LabelFrame(main_frame, text="設定", padding="5")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))
        
        ttk.Label(settings_frame, text="類似度閾値:").grid(row=0, column=0, sticky=tk.W)
        self.similarity_var = tk.DoubleVar(value=self.settings['similarity_threshold'])
        ttk.Scale(settings_frame, from_=0.5, to=1.0, variable=self.similarity_var, 
                 orient=tk.HORIZONTAL, length=150).grid(row=0, column=1, padx=(5, 0))
        ttk.Label(settings_frame, textvariable=self.similarity_var).grid(row=0, column=2, padx=(5, 0))
        
        ttk.Label(settings_frame, text="タップ間隔(秒):").grid(row=1, column=0, sticky=tk.W)
        self.delay_var = tk.DoubleVar(value=self.settings['tap_delay'])
        ttk.Scale(settings_frame, from_=0.1, to=2.0, variable=self.delay_var, 
                 orient=tk.HORIZONTAL, length=150).grid(row=1, column=1, padx=(5, 0))
        ttk.Label(settings_frame, textvariable=self.delay_var).grid(row=1, column=2, padx=(5, 0))
        
        ttk.Label(settings_frame, text="パズルタップ回数:").grid(row=2, column=0, sticky=tk.W)
        self.puzzle_count_var = tk.IntVar(value=self.settings['puzzle_tap_count'])
        ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.puzzle_count_var, 
                   width=10).grid(row=2, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(settings_frame, text="検知間隔(秒):").grid(row=3, column=0, sticky=tk.W)
        self.check_interval_var = tk.DoubleVar(value=self.settings['check_interval'])
        ttk.Scale(settings_frame, from_=0.05, to=1.0, variable=self.check_interval_var, 
                 orient=tk.HORIZONTAL, length=150).grid(row=3, column=1, padx=(5, 0))
        ttk.Label(settings_frame, textvariable=self.check_interval_var).grid(row=3, column=2, padx=(5, 0))
        
        # メモリ直接取得設定
        self.memory_capture_var = tk.BooleanVar(value=self.settings.get('use_memory_capture', True))
        ttk.Checkbutton(settings_frame, text="メモリ直接取得", variable=self.memory_capture_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        # コントロールフレーム
        control_frame = ttk.LabelFrame(main_frame, text="制御", padding="5")
        control_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N))
        
        self.start_button = ttk.Button(control_frame, text="開始", command=self.start_automation)
        self.start_button.grid(row=0, column=0, padx=(0, 5), pady=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="停止", command=self.stop_automation, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, pady=(0, 5))
        
        ttk.Button(control_frame, text="スクリーンショット", command=self.take_screenshot).grid(row=1, column=0, columnspan=2, pady=(0, 5))
        
        ttk.Button(control_frame, text="メモリ診断", command=self.run_memory_diagnostic).grid(row=2, column=0, columnspan=2, pady=(0, 5))
        
        ttk.Button(control_frame, text="画像検出テスト", command=self.test_image_detection).grid(row=3, column=0, columnspan=2, pady=(0, 5))
        
        ttk.Button(control_frame, text="puzzle専用テスト", command=self.test_puzzle_detection_specifically).grid(row=4, column=0, columnspan=2, pady=(0, 5))
        
        self.realtime_monitor_button = ttk.Button(control_frame, text="リアルタイム監視", command=self.toggle_realtime_monitor)
        self.realtime_monitor_button.grid(row=5, column=0, columnspan=2, pady=(0, 5))
        
        ttk.Button(control_frame, text="設定保存", command=self.save_settings).grid(row=6, column=0, padx=(0, 5))
        ttk.Button(control_frame, text="設定読込", command=self.load_settings).grid(row=6, column=1)
        
        # ログフレーム
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="5")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        device_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def log(self, message, device_id=None):
        """ログメッセージを表示"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if device_id:
            log_message = f"[{timestamp}] [{device_id}] {message}\n"
        else:
            log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        print(log_message.strip())
        
    def refresh_devices(self):
        """ADBデバイスを更新"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')[1:]  # ヘッダーを除く
            
            self.devices = []
            for line in lines:
                if line.strip() and 'device' in line:
                    device_id = line.split('\t')[0]
                    self.devices.append(device_id)
            
            # リストボックスを更新
            self.device_listbox.delete(0, tk.END)
            for device in self.devices:
                self.device_listbox.insert(tk.END, device)
            
            self.log(f"デバイス検出: {len(self.devices)}台")
            
        except Exception as e:
            self.log(f"デバイス検出エラー: {str(e)}")
            
    def get_selected_devices(self):
        """選択されたデバイスを取得"""
        selected_indices = self.device_listbox.curselection()
        return [self.devices[i] for i in selected_indices]
        
    def take_screenshot(self, device_id=None, force_new=False):
        """スクリーンショットを取得（キャッシュ機能付き）"""
        if not device_id:
            devices = self.get_selected_devices()
            if not devices:
                messagebox.showwarning("警告", "デバイスを選択してください")
                return
            device_id = devices[0]
        
        current_time = time.time()
        
        # キャッシュチェック（強制更新でない場合）
        if not force_new and device_id in self.last_screenshot_time:
            if current_time - self.last_screenshot_time[device_id] < self.settings['screenshot_cache_time']:
                if device_id in self.screenshot_cache:
                    return self.screenshot_cache[device_id]
        
        try:
            # スクリーンショットを取得
            screenshot_path = f'screenshot_{device_id}.png'
            subprocess.run(['adb', '-s', device_id, 'shell', 'screencap', '/sdcard/screenshot.png'], 
                         check=True, capture_output=True)
            subprocess.run(['adb', '-s', device_id, 'pull', '/sdcard/screenshot.png', screenshot_path], 
                         check=True, capture_output=True)
            
            # キャッシュに保存
            self.screenshot_cache[device_id] = screenshot_path
            self.last_screenshot_time[device_id] = current_time
            
            return screenshot_path
        except Exception as e:
            self.log(f"スクリーンショットエラー: {str(e)}", device_id)
            return None
            
    def find_image_on_screen_optimized(self, template_path, device_id, threshold=None):
        """最適化された画像検索（メモリ直接対応）"""
        if threshold is None:
            threshold = self.similarity_var.get()
            
        # メモリから直接スクリーンショットを取得
        screenshot = self.fast_screenshot_to_memory(device_id)
        if screenshot is None:
            return None
            
        try:
            template = cv2.imread(template_path)
            if template is None:
                self.log(f"テンプレート読み込みエラー: {template_path}", device_id)
                return None
            
            # テンプレートマッチング（高速化）
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                return (center_x, center_y)
            else:
                return None
                
        except Exception as e:
            self.log(f"最適化画像検索エラー: {str(e)}", device_id)
            return None
            
    def find_multiple_images_on_screen_optimized(self, template_paths, device_id, threshold=None):
        """最適化された複数画像同時検索（メモリ直接対応）"""
        if threshold is None:
            threshold = self.similarity_var.get()
            
        # メモリから直接スクリーンショットを取得
        screenshot = self.fast_screenshot_to_memory(device_id)
        if screenshot is None:
            return {}
            
        try:
            results = {}
            for name, template_path in template_paths.items():
                template = cv2.imread(template_path)
                if template is None:
                    continue
                
                # テンプレートマッチング（高速化）
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= threshold:
                    h, w = template.shape[:2]
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    
                    results[name] = {
                        'pos': (center_x, center_y),
                        'confidence': max_val
                    }
                    
                    # ログは最高精度のもののみ表示（ログ量削減）
                    if max_val > 0.9:
                        self.log(f"高精度検出: {name} ({max_val:.3f})", device_id)
            
            return results
                
        except Exception as e:
            self.log(f"最適化複数画像検索エラー: {str(e)}", device_id)
            return {}
        """画面にタップ"""
        try:
            subprocess.run(['adb', '-s', device_id, 'shell', 'input', 'tap', str(x), str(y)], check=True)
            self.log(f"タップ: ({x}, {y})", device_id)
            time.sleep(self.delay_var.get())
            return True
        except Exception as e:
            self.log(f"タップエラー: {str(e)}", device_id)
            return False
            
    def human_like_delay(self):
        """人間らしいランダムな遅延"""
        import random
        delay = random.uniform(
            self.settings['human_like_delay_min'], 
            self.settings['human_like_delay_max']
        )
        time.sleep(delay)
        
    def smart_tap_screen(self, x, y, device_id, tap_type="normal"):
        """スマートタップ機能（タップ種類に応じて遅延を調整）"""
        try:
            subprocess.run(['adb', '-s', device_id, 'shell', 'input', 'tap', str(x), str(y)], 
                         check=True, capture_output=True)
            self.log(f"タップ: ({x}, {y}) [{tap_type}]", device_id)
            
            # タップ種類に応じた遅延
            if tap_type == "boss":
                time.sleep(self.delay_var.get() * 1.5)  # ボス選択は少し長め
            elif tap_type == "play":
                time.sleep(self.delay_var.get() * 2.0)  # プレイボタンは読み込み時間考慮
            elif tap_type == "puzzle":
                time.sleep(self.delay_var.get() * 0.8)  # パズルは短め
            elif tap_type == "close":
                time.sleep(self.delay_var.get() * 0.5)  # 閉じるボタンは最短
            else:
                time.sleep(self.delay_var.get())
            
            # 人間らしい微小な遅延を追加
            self.human_like_delay()
            return True
        except Exception as e:
            self.log(f"タップエラー: {str(e)}", device_id)
            return False
            
    def automation_loop(self, device_id):
        """最適化されたメインの自動化ループ"""
        self.device_status[device_id] = "実行中"
        puzzle_tap_count = 0
        stage_45_detected = False
        
        while self.running and device_id in self.threads:
            try:                # 優先度の高い画像を同時検索
                priority_images = {}
                
                # stage_45.pngを最初にチェック
                stage_45_pos = self.find_image_on_screen_optimized(self.image_paths['stage_45'], device_id)
                if stage_45_pos and not stage_45_detected:
                    stage_45_detected = True
                    self.log("ステージ45検出 - close系ボタンの監視を停止", device_id)
                elif not stage_45_pos and stage_45_detected:
                    stage_45_detected = False
                    self.log("ステージ45終了 - close系ボタンの監視を再開", device_id)
                
                # close系の監視（stage_45検出時は除く）
                if not stage_45_detected:
                    priority_images['close'] = self.image_paths['close']
                    priority_images['close_mini'] = self.image_paths['close_mini']
                
                # 現在の状態に応じた画像を追加
                priority_images['boss'] = self.image_paths['boss']
                priority_images['play'] = self.image_paths['play']
                priority_images['next'] = self.image_paths['next']                # 複数画像を同時検索（最適化版）
                detected_images = self.find_multiple_images_on_screen_optimized(priority_images, device_id)
                
                # playボタンを直接検出した場合の処理を追加
                if 'play' in detected_images:
                    self.log("playボタンを直接検出しました", device_id)
                    pos = detected_images['play']['pos']
                    
                    # play.pngをタップ前に再度stage_45.pngをチェック
                    stage_45_pos = self.find_image_on_screen_optimized(self.image_paths['stage_45'], device_id)
                    if stage_45_pos:
                        stage_45_detected = True
                        self.log("プレイ前ステージ45検出 - close系ボタンの監視を停止", device_id)
                    
                    self.smart_tap_screen(pos[0], pos[1], device_id, "play")
                    
                    # プレイ後も再度チェック
                    time.sleep(self.delay_var.get() * 0.5)
                    stage_45_pos_after = self.find_image_on_screen_optimized(self.image_paths['stage_45'], device_id)
                    if stage_45_pos_after and not stage_45_detected:
                        stage_45_detected = True
                        self.log("プレイ後ステージ45検出 - close系ボタンの監視を停止", device_id)
                    
                    # バトルループ（③④の処理）
                    self.battle_loop(device_id, puzzle_tap_count)
                    puzzle_tap_count = 0
                    continue
                
                # 優先順位に従って処理
                if 'close' in detected_images and not stage_45_detected:
                    pos = detected_images['close']['pos']
                    self.smart_tap_screen(pos[0], pos[1], device_id, "close")
                    continue
                    
                if 'close_mini' in detected_images and not stage_45_detected:
                    pos = detected_images['close_mini']['pos']
                    self.smart_tap_screen(pos[0], pos[1], device_id, "close")
                    continue
                
                # next.pngが検出された場合（最優先）
                if 'next' in detected_images:
                    pos = detected_images['next']['pos']
                    self.smart_tap_screen(pos[0], pos[1], device_id, "next")
                    stage_45_detected = False  # リセット
                    puzzle_tap_count = 0
                    continue
                  # boss.pngが検出された場合
                if 'boss' in detected_images:
                    pos = detected_images['boss']['pos']
                    self.smart_tap_screen(pos[0], pos[1], device_id, "boss")
                    
                    # play.pngを待機して検索（最適化版・強化）
                    self.log("boss検出後、playボタンを検索中...", device_id)
                    play_found = False
                    max_attempts = 10  # 最大試行回数
                    
                    for attempt in range(max_attempts):
                        time.sleep(0.5)  # 画面遷移を待つ
                        # 段階的閾値検索を使用
                        play_pos = self.find_image_with_multiple_thresholds(self.image_paths['play'], device_id)
                        
                        if play_pos:
                            self.log(f"playボタン検出成功 (試行{attempt + 1}回目): {play_pos}", device_id)
                            play_found = True
                            
                            # play.pngをタップ前に再度stage_45.pngをチェック
                            stage_45_pos = self.find_image_on_screen_optimized(self.image_paths['stage_45'], device_id)
                            if stage_45_pos:
                                stage_45_detected = True
                                self.log("プレイ前ステージ45検出 - close系ボタンの監視を停止", device_id)
                            
                            self.smart_tap_screen(play_pos[0], play_pos[1], device_id, "play")
                            
                            # プレイ後も再度チェック
                            time.sleep(self.delay_var.get() * 0.5)
                            stage_45_pos_after = self.find_image_on_screen_optimized(self.image_paths['stage_45'], device_id)
                            if stage_45_pos_after and not stage_45_detected:
                                stage_45_detected = True
                                self.log("プレイ後ステージ45検出 - close系ボタンの監視を停止", device_id)
                            
                            # バトルループ（③④の処理）
                            self.battle_loop(device_id, puzzle_tap_count)
                            puzzle_tap_count = 0
                            break
                        else:
                            self.log(f"playボタン未検出 (試行{attempt + 1}回目)", device_id)
                            
                            # close系ボタンがあればタップして再試行
                            close_images = {
                                'close': self.image_paths['close'],
                                'close_mini': self.image_paths['close_mini']
                            }
                            close_detected = self.find_multiple_images_on_screen_optimized(close_images, device_id)
                            
                            if 'close' in close_detected:
                                self.log("playボタン待機中にcloseボタンを検出、タップします", device_id)
                                close_pos = close_detected['close']['pos']
                                self.smart_tap_screen(close_pos[0], close_pos[1], device_id, "close")
                            elif 'close_mini' in close_detected:
                                self.log("playボタン待機中にclose_miniボタンを検出、タップします", device_id)
                                close_pos = close_detected['close_mini']['pos']
                                self.smart_tap_screen(close_pos[0], close_pos[1], device_id, "close")
                    
                    if not play_found:
                        self.log(f"playボタンが見つかりませんでした（{max_attempts}回試行）", device_id)
                
                # 短い間隔で次のチェック
                time.sleep(self.check_interval_var.get())
                
            except Exception as e:
                self.log(f"自動化エラー: {str(e)}", device_id)
                time.sleep(0.5)        
        self.device_status[device_id] = "停止"
        self.log("自動化停止", device_id)
        
    def battle_loop(self, device_id, initial_puzzle_count=0):
        """バトル中のループ処理（③④の最適化・puzzle検知強化）"""
        puzzle_tap_count = initial_puzzle_count
        battle_start_time = time.time()
        max_battle_time = 60  # 最大バトル時間（秒）
        stage_45_in_battle = False
        puzzle_search_attempts = 0  # puzzle検索試行回数
        
        self.log(f"バトル開始 (初期puzzle回数: {puzzle_tap_count})", device_id)
        
        while self.running and device_id in self.threads:
            # 最大時間チェック
            if time.time() - battle_start_time > max_battle_time:
                self.log("バトル時間超過 - 次のサイクルに移行", device_id)
                break
            
            # バトル開始時にstage_45をチェック
            if not stage_45_in_battle:
                stage_45_pos = self.find_image_on_screen_optimized(self.image_paths['stage_45'], device_id)
                if stage_45_pos:
                    stage_45_in_battle = True
                    self.log("バトル中ステージ45検出 - close系監視停止", device_id)
              # バトル関連の画像を同時検索（puzzle優先順序）
            battle_images = {
                'puzzle': self.image_paths['puzzle'],  # puzzleを最初に配置
                'next': self.image_paths['next'],
                'waza_ok': self.image_paths['waza_ok']
            }
            
            # stage_45が検出されていない場合のみclose系を追加
            if not stage_45_in_battle:
                battle_images['close'] = self.image_paths['close']
                battle_images['close_mini'] = self.image_paths['close_mini']
            
            detected = self.find_multiple_images_on_screen_optimized(battle_images, device_id)
            
            # 最優先: puzzle.pngをタップ（回数制限あり・超積極的検知）# puzzle.pngをタップ（回数制限あり・超積極的検知）
            if puzzle_tap_count < self.puzzle_count_var.get():
                puzzle_detected = False
                
                # 方法1: 通常の検知を試行
                if 'puzzle' in detected:
                    pos = detected['puzzle']['pos']
                    confidence = detected['puzzle']['confidence']
                    self.log(f"puzzle通常検出 (回数: {puzzle_tap_count + 1}/{self.puzzle_count_var.get()}, 信頼度: {confidence:.3f})", device_id)
                    self.smart_tap_screen(pos[0], pos[1], device_id, "puzzle")
                    puzzle_tap_count += 1
                    puzzle_detected = True
                
                # 方法2: 通常検知で失敗した場合、すぐに強化検知を試行
                if not puzzle_detected:
                    puzzle_pos = self.find_puzzle_with_enhanced_detection(device_id)
                    if puzzle_pos:
                        self.log(f"puzzle強化検出 (回数: {puzzle_tap_count + 1}/{self.puzzle_count_var.get()})", device_id)
                        self.smart_tap_screen(puzzle_pos[0], puzzle_pos[1], device_id, "puzzle")
                        puzzle_tap_count += 1
                        puzzle_detected = True
                
                # 方法3: それでも失敗した場合、低閾値で最後の試行
                if not puzzle_detected and puzzle_search_attempts % 3 == 0:  # 3回に1回だけ
                    low_threshold_pos = self.find_image_on_screen_optimized(
                        self.image_paths['puzzle'], device_id, threshold=0.5
                    )
                    if low_threshold_pos:
                        self.log(f"puzzle低閾値検出 (回数: {puzzle_tap_count + 1}/{self.puzzle_count_var.get()})", device_id)
                        self.smart_tap_screen(low_threshold_pos[0], low_threshold_pos[1], device_id, "puzzle")
                        puzzle_tap_count += 1
                        puzzle_detected = True
                
                # puzzle検出成功時は短いスリープで次のループへ
                if puzzle_detected:
                    time.sleep(0.2)  # さらに短いディレイでpuzzleを連続検索
                    continue
                else:
                    # puzzle検出失敗時の処理（ログ頻度を制御）
                    puzzle_search_attempts += 1
                    if puzzle_search_attempts % 3 == 1:  # 3回に1回ログ（頻度を上げる）
                        self.log(f"puzzle全検出失敗 ({puzzle_search_attempts}回目) - waza_okを待機中", device_id)
                        # 失敗時はリアルタイム状況をログ
                        if puzzle_search_attempts % 9 == 1:  # 9回に1回は詳細ログ
                            current_images = self.find_multiple_images_on_screen_optimized(
                                {'waza_ok': self.image_paths['waza_ok'], 'next': self.image_paths['next']}, device_id
                            )
                            detected_names = list(current_images.keys())
                            self.log(f"現在検出中の画像: {detected_names if detected_names else 'なし'}", device_id)
            
            # waza_ok.pngをタップ
            if 'waza_ok' in detected:
                pos = detected['waza_ok']['pos']
                self.smart_tap_screen(pos[0], pos[1], device_id, "waza_ok")
                puzzle_tap_count = 0  # パズルカウンターリセット
                puzzle_search_attempts = 0  # 検索試行回数もリセット
                continue
            
            # close系の処理（stage_45が検出されていない場合のみ）
            if not stage_45_in_battle:
                if 'close' in detected:
                    pos = detected['close']['pos']
                    self.smart_tap_screen(pos[0], pos[1], device_id, "close")
                    continue
                    
                if 'close_mini' in detected:
                    pos = detected['close_mini']['pos']
                    self.smart_tap_screen(pos[0], pos[1], device_id, "close")
                    continue
              # 最後: next.pngが検出されたらバトル終了
            if 'next' in detected:
                pos = detected['next']['pos']
                self.smart_tap_screen(pos[0], pos[1], device_id, "next")
                break
            
            # puzzleが必要な場合は短い間隔、そうでなければ通常間隔
            if puzzle_tap_count < self.puzzle_count_var.get():
                time.sleep(max(0.15, self.check_interval_var.get() * 0.3))  # puzzle検索時は超高速
            else:
                time.sleep(self.check_interval_var.get())
        
    def start_automation(self):
        """自動化開始"""
        selected_devices = self.get_selected_devices()
        if not selected_devices:
            messagebox.showwarning("警告", "デバイスを選択してください")
            return
        
        # 画像ファイルの確認
        missing_files = []
        for name, path in self.image_paths.items():
            if not os.path.exists(path):
                missing_files.append(path)
        
        if missing_files:
            messagebox.showerror("エラー", f"画像ファイルが見つかりません:\n" + "\n".join(missing_files))
            return
        
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 設定を更新
        self.settings['similarity_threshold'] = self.similarity_var.get()
        self.settings['tap_delay'] = self.delay_var.get()
        self.settings['puzzle_tap_count'] = self.puzzle_count_var.get()
        self.settings['check_interval'] = self.check_interval_var.get()
        self.settings['use_memory_capture'] = self.memory_capture_var.get()
          # デバイス互換性チェック
        for device_id in selected_devices:
            self.log_device_compatibility(device_id)
            
        # メモリ直接取得の警告
        if self.memory_capture_var.get():
            memory_supported_devices = [
                device_id for device_id in selected_devices 
                if self.device_compatibility.get(device_id, {}).get('memory_capture_supported', False)
            ]
            if not memory_supported_devices:
                self.log("警告: メモリ直接取得をサポートするデバイスがありません")
                self.log("すべてのデバイスでファイル方式を使用します")
        
        # 各デバイスでスレッドを開始
        for device_id in selected_devices:
            thread = threading.Thread(target=self.automation_loop, args=(device_id,))
            thread.daemon = True
            self.threads[device_id] = thread
            thread.start()
            self.log("自動化開始", device_id)
            
    def stop_automation(self):
        """自動化停止"""
        self.running = False
        self.threads.clear()
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        self.log("全デバイスの自動化を停止")
        
    def save_settings(self):
        """設定保存"""
        settings = {
            'similarity_threshold': self.similarity_var.get(),
            'tap_delay': self.delay_var.get(),
            'puzzle_tap_count': self.puzzle_count_var.get(),
            'check_interval': self.check_interval_var.get(),
            'use_memory_capture': self.memory_capture_var.get()
        }
        
        try:
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            self.log("設定を保存しました")
        except Exception as e:
            self.log(f"設定保存エラー: {str(e)}")
            
    def load_settings(self):
        """設定読込"""
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            self.similarity_var.set(settings.get('similarity_threshold', 0.8))
            self.delay_var.set(settings.get('tap_delay', 0.3))
            self.puzzle_count_var.set(settings.get('puzzle_tap_count', 2))
            self.check_interval_var.set(settings.get('check_interval', 0.1))
            self.memory_capture_var.set(settings.get('use_memory_capture', True))
            
            self.log("設定を読み込みました")
        except FileNotFoundError:
            self.log("設定ファイルが見つかりません")
        except Exception as e:
            self.log(f"設定読込エラー: {str(e)}")

    def setup_memory_capture(self, device_id):
        """メモリ直接キャプチャのセットアップ"""
        try:
            # scrcpyのRAWモードを使用してメモリから直接取得
            cmd = [
                'adb', '-s', device_id, 'exec-out', 
                'screencap'
            ]
            
            # プロセスを開始（継続的にデータを取得）
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.minicap_connections[device_id] = process
            
            self.log(f"メモリ直接キャプチャセットアップ完了", device_id)
            return True
            
        except Exception as e:
            self.log(f"メモリキャプチャセットアップエラー: {str(e)}", device_id)
            return False
    def get_memory_screenshot(self, device_id):
        """メモリから直接スクリーンショットを取得（改良版）"""
        try:
            # 方法1: ADB exec-outを使用してRAWデータを直接取得
            result = subprocess.run([
                'adb', '-s', device_id, 'exec-out', 'screencap'
            ], capture_output=True, timeout=3)
            
            if result.returncode == 0 and len(result.stdout) > 0:
                raw_data = result.stdout
                
                # PNGヘッダーをチェック
                if raw_data[:8] == b'\x89PNG\r\n\x1a\n':
                    # PNG形式の場合
                    nparr = np.frombuffer(raw_data, np.uint8)
                    screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if screenshot is not None:
                        return screenshot
                
                # RAW形式の場合のパース（Android 4.4以降）
                if len(raw_data) >= 12:
                    # ヘッダー情報を解析
                    width = struct.unpack('<I', raw_data[0:4])[0]
                    height = struct.unpack('<I', raw_data[4:8])[0]
                    pixel_format = struct.unpack('<I', raw_data[8:12])[0]
                    
                    # 妥当性チェック
                    if 100 <= width <= 4096 and 100 <= height <= 4096:
                        if pixel_format == 1:  # RGBA_8888
                            expected_size = width * height * 4 + 12
                            if len(raw_data) >= expected_size:
                                # RGBA データを抽出
                                image_data = raw_data[12:12 + width * height * 4]
                                # numpy配列に変換
                                img_array = np.frombuffer(image_data, dtype=np.uint8)
                                img_array = img_array.reshape((height, width, 4))
                                # BGRAからBGRに変換（Alphaチャンネル削除）
                                screenshot = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
                                return screenshot
            
            # 方法2: shellコマンドでscreencapを実行してファイル取得を避ける
            result2 = subprocess.run([
                'adb', '-s', device_id, 'shell', 'screencap', '-p'
            ], capture_output=True, timeout=3)
            
            if result2.returncode == 0 and len(result2.stdout) > 0:
                # base64形式でない場合の処理
                raw_data = result2.stdout
                if raw_data[:8] == b'\x89PNG\r\n\x1a\n':
                    nparr = np.frombuffer(raw_data, np.uint8)
                    screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if screenshot is not None:
                        return screenshot
                        
            return None
            
        except subprocess.TimeoutExpired:
            self.log(f"メモリキャプチャタイムアウト", device_id)
            return None
        except Exception as e:
            self.log(f"メモリキャプチャエラー: {str(e)}", device_id)
            return None
    
    def fast_screenshot_to_memory(self, device_id):
        """高速スクリーンショット（メモリ直接 or ファイル）改良版"""
        # 互換性チェック
        if device_id not in self.device_compatibility:
            self.log_device_compatibility(device_id)
        
        # メモリ直接取得を試行（サポートされている場合のみ）
        if (self.memory_capture_var.get() and 
            self.device_compatibility.get(device_id, {}).get('memory_capture_supported', False)):
            
            screenshot = self.get_memory_screenshot(device_id)
            if screenshot is not None:
                # メモリ取得成功のログ（初回のみ）
                if not hasattr(self, '_memory_success_logged'):
                    self.log(f"メモリ直接取得成功", device_id)
                    self._memory_success_logged = True
                return screenshot
            else:
                # フォールバック回数を記録
                self.fallback_count[device_id] = self.fallback_count.get(device_id, 0) + 1
                
                # 連続失敗時は一時的にメモリ取得を無効化
                if self.fallback_count[device_id] >= 5:
                    self.device_compatibility[device_id]['memory_capture_supported'] = False
                    self.log("メモリ取得を一時無効化（連続失敗）", device_id)
        
        # 従来のファイル方式（高速化版）
        screenshot_path = self.take_screenshot_fast(device_id)
        if screenshot_path:
            return cv2.imread(screenshot_path)
        
        return None
    
    def take_screenshot_fast(self, device_id):
        """高速ファイルベーススクリーンショット"""
        try:
            # テンポラリファイル名を使用
            temp_name = f'/sdcard/temp_screenshot_{int(time.time() * 1000) % 10000}.png'
            local_path = f'temp_screenshot_{device_id}.png'
            
            # 高速スクリーンショット取得
            subprocess.run(['adb', '-s', device_id, 'shell', 'screencap', temp_name], 
                         check=True, capture_output=True, timeout=3)
            subprocess.run(['adb', '-s', device_id, 'pull', temp_name, local_path], 
                         check=True, capture_output=True, timeout=3)
            
            # デバイス上のテンポラリファイルを削除
            subprocess.run(['adb', '-s', device_id, 'shell', 'rm', temp_name], 
                         capture_output=True, timeout=1)
            
            return local_path
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            self.log(f"高速スクリーンショットエラー: {str(e)}", device_id)
            return None
    def check_device_memory_support(self, device_id):
        """デバイスのメモリ直接取得サポートをチェック"""
        try:
            # Androidバージョンを取得
            result = subprocess.run([
                'adb', '-s', device_id, 'shell', 'getprop', 'ro.build.version.release'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                android_version = result.stdout.strip()
                self.log(f"Androidバージョン: {android_version}", device_id)
                
                # Android 4.4以降でexec-outをサポート
                try:
                    version_num = float(android_version.split('.')[0])
                    if version_num >= 4:
                        return True
                except:
                    pass
            
            # exec-outコマンドが使用可能かテスト
            test_result = subprocess.run([
                'adb', '-s', device_id, 'exec-out', 'echo', 'test'
            ], capture_output=True, timeout=3)
            
            if test_result.returncode == 0 and b'test' in test_result.stdout:
                self.log(f"exec-outコマンド利用可能", device_id)
                return True
            else:
                self.log(f"exec-outコマンド利用不可 - ファイル方式を使用", device_id)
                return False
                
        except Exception as e:
            self.log(f"デバイス互換性チェックエラー: {str(e)}", device_id)
            return False
    def check_device_compatibility(self, device_id):
        """デバイスの互換性チェック"""
        if device_id in self.device_compatibility:
            return self.device_compatibility[device_id]
        
        compatibility = {
            'exec_out_supported': False,
            'android_version': 'unknown',
            'memory_capture_supported': False,
            'reason': ''
        }
        
        try:
            # Androidバージョンを取得
            result = subprocess.run(['adb', '-s', device_id, 'shell', 'getprop', 'ro.build.version.release'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                compatibility['android_version'] = result.stdout.strip()
            
            # exec-out screencapコマンドの動作テスト
            result = subprocess.run(['adb', '-s', device_id, 'exec-out', 'screencap', '-p'],
                                  capture_output=True, timeout=15)
            
            if result.returncode == 0 and len(result.stdout) > 1000:  # 最小限の画像データサイズ
                compatibility['exec_out_supported'] = True
                compatibility['memory_capture_supported'] = True
                compatibility['reason'] = 'Memory capture fully supported'
            else:
                compatibility['reason'] = f'exec-out failed (returncode: {result.returncode})'
                
        except subprocess.TimeoutExpired:
            compatibility['reason'] = 'Command timeout'
        except Exception as e:
            compatibility['reason'] = f'Error: {str(e)}'
        
        self.device_compatibility[device_id] = compatibility
        return compatibility

    def log_device_compatibility(self, device_id):
        """デバイス互換性情報をログ出力"""
        compat = self.check_device_compatibility(device_id)
        self.log(f"デバイス互換性チェック: Android {compat['android_version']}", device_id)
        if compat['memory_capture_supported']:
            self.log("メモリ直接取得: サポート", device_id)
        else:
            self.log(f"メモリ直接取得: 非サポート - {compat['reason']}", device_id)
            self.log("通常のファイル方式を使用します", device_id)
    def diagnostic_memory_capture(self, device_id):
        """メモリ直接取得の診断情報を表示"""
        self.log("=== メモリ直接取得診断 ===", device_id)
        
        try:
            # 1. デバイス情報取得
            info_cmd = ['adb', '-s', device_id, 'shell', 'getprop']
            result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'ro.build.version.release' in line or 'ro.build.version.sdk' in line:
                        self.log(f"デバイス情報: {line.strip()}", device_id)
            
            # 2. exec-outコマンドのサポート確認
            test_cmd = ['adb', '-s', device_id, 'exec-out', 'echo', 'test']
            result = subprocess.run(test_cmd, capture_output=True, timeout=3)
            if result.returncode == 0:
                self.log("exec-out コマンド: サポート", device_id)
            else:
                self.log(f"exec-out コマンド: 非サポート (code: {result.returncode})", device_id)
            
            # 3. screencapコマンドの直接実行
            screencap_cmd = ['adb', '-s', device_id, 'shell', 'screencap', '-h']
            result = subprocess.run(screencap_cmd, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                self.log("screencap コマンド: 利用可能", device_id)
            else:
                self.log(f"screencap コマンド: エラー (code: {result.returncode})", device_id)
            
            # 4. 実際のメモリ取得を試行
            memory_cmd = ['adb', '-s', device_id, 'exec-out', 'screencap']
            result = subprocess.run(memory_cmd, capture_output=True, timeout=5)
            
            if result.returncode == 0:
                data_size = len(result.stdout)
                self.log(f"メモリ取得: 成功 (データサイズ: {data_size} bytes)", device_id)
                
                if data_size > 0:
                    # データ形式を確認
                    header = result.stdout[:16]
                    self.log(f"データヘッダー: {header}", device_id)
                    
                    if header[:8] == b'\x89PNG\r\n\x1a\n':
                        self.log("データ形式: PNG", device_id)
                    else:
                        self.log("データ形式: RAW (もしくは不明)", device_id)
                else:
                    self.log("メモリ取得: データが空", device_id)
            else:
                self.log(f"メモリ取得: 失敗 (code: {result.returncode})", device_id)
                if result.stderr:
                    error_msg = result.stderr.decode('utf-8', errors='ignore')
                    self.log(f"エラー詳細: {error_msg}", device_id)
            
        except Exception as e:
            self.log(f"診断エラー: {str(e)}", device_id)
        
        self.log("=== 診断終了 ===", device_id)
    
    def run_memory_diagnostic(self):
        """メモリ診断を実行"""
        selected_devices = self.get_selected_devices()
        if not selected_devices:
            messagebox.showwarning("警告", "デバイスを選択してください")
            return
        
        self.log("メモリ直接取得の診断を開始します")
        for device_id in selected_devices:
            self.diagnostic_memory_capture(device_id)
    
    def find_image_with_multiple_thresholds(self, template_path, device_id, initial_threshold=None):
        """複数の閾値でplayボタンを検索（段階的に閾値を下げる）"""
        if initial_threshold is None:
            initial_threshold = self.similarity_var.get()
        
        # 段階的に閾値を下げて検索
        thresholds = [initial_threshold, initial_threshold - 0.1, initial_threshold - 0.2, 0.6]
        
        for threshold in thresholds:
            if threshold < 0.5:  # 最低限の閾値
                break
                
            result = self.find_image_on_screen_optimized(template_path, device_id, threshold)
            if result:
                self.log(f"画像検出成功 (閾値: {threshold:.2f}): {template_path}", device_id)
                return result
            else:
                self.log(f"画像未検出 (閾値: {threshold:.2f}): {template_path}", device_id)
        
        return None

    def test_image_detection(self):
        """画像検出のテスト機能"""
        selected_devices = self.get_selected_devices()
        if not selected_devices:
            messagebox.showwarning("警告", "デバイスを選択してください")
            return
        
        device_id = selected_devices[0]
        
        self.log("=== 画像検出テスト ===", device_id)
        
        # すべての画像ファイルをテスト
        for name, path in self.image_paths.items():
            self.log(f"テスト対象: {name} ({path})", device_id)
            
            # 画像ファイルの存在確認
            if not os.path.exists(path):
                self.log(f"❌ ファイルが存在しません: {path}", device_id)
                continue
            
            # 画像の読み込みテスト
            template = cv2.imread(path)
            if template is None:
                self.log(f"❌ 画像読み込み失敗: {path}", device_id)
                continue
            
            height, width = template.shape[:2]
            self.log(f"✅ 画像読み込み成功: {width}x{height}", device_id)
            
            # 現在の画面で検索テスト
            result = self.find_image_with_multiple_thresholds(path, device_id)
            if result:
                self.log(f"✅ 検出成功: {name} at {result}", device_id)
            else:
                self.log(f"❌ 検出失敗: {name}", device_id)        
        self.log("=== テスト終了 ===", device_id)
    
    def test_puzzle_detection_specifically(self):
        """puzzle.png超詳細テスト（全検出方法）"""
        selected_devices = self.get_selected_devices()
        if not selected_devices:
            messagebox.showwarning("警告", "デバイスを選択してください")
            return
        
        device_id = selected_devices[0]
        self.enhanced_puzzle_detection_test(device_id)
    
    def find_puzzle_with_enhanced_detection(self, device_id):
        """puzzle.png専用の超強化検知機能"""
        screenshot = self.fast_screenshot_to_memory(device_id)
        if screenshot is None:
            return None
        
        template = cv2.imread(self.image_paths['puzzle'])
        if template is None:
            self.log("puzzle画像ファイルが読み込めません", device_id)
            return None
        
        # 検出方法1: 段階的閾値検索
        thresholds = [self.similarity_var.get(), 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
        for i, threshold in enumerate(thresholds):
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                self.log(f"puzzle検出成功-方法1 (閾値: {threshold:.2f}, 信頼度: {max_val:.3f}): ({center_x}, {center_y})", device_id)
                return (center_x, center_y)
        
        # 検出方法2: 複数マッチング手法
        matching_methods = [
            cv2.TM_CCOEFF_NORMED,
            cv2.TM_CCORR_NORMED,
            cv2.TM_SQDIFF_NORMED
        ]
        
        for method_idx, method in enumerate(matching_methods):
            try:
                result = cv2.matchTemplate(screenshot, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # TM_SQDIFF_NORMEDの場合は最小値を使用
                if method == cv2.TM_SQDIFF_NORMED:
                    if min_val <= 0.4:  # 低い値が良いマッチ
                        h, w = template.shape[:2]
                        center_x = min_loc[0] + w // 2
                        center_y = min_loc[1] + h // 2
                        self.log(f"puzzle検出成功-方法2-{method_idx+1} (信頼度: {1-min_val:.3f}): ({center_x}, {center_y})", device_id)
                        return (center_x, center_y)
                else:
                    if max_val >= 0.3:
                        h, w = template.shape[:2]
                        center_x = max_loc[0] + w // 2
                        center_y = max_loc[1] + h // 2
                        self.log(f"puzzle検出成功-方法2-{method_idx+1} (信頼度: {max_val:.3f}): ({center_x}, {center_y})", device_id)
                        return (center_x, center_y)
            except Exception as e:
                continue
        
        # 検出方法3: スケール変換対応
        scales = [1.0, 0.9, 1.1, 0.8, 1.2, 0.7, 1.3]
        for scale in scales:
            try:
                if scale != 1.0:
                    h, w = template.shape[:2]
                    new_h, new_w = int(h * scale), int(w * scale)
                    scaled_template = cv2.resize(template, (new_w, new_h))
                else:
                    scaled_template = template
                
                result = cv2.matchTemplate(screenshot, scaled_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= 0.3:
                    h, w = scaled_template.shape[:2]
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    self.log(f"puzzle検出成功-方法3 (スケール: {scale:.1f}, 信頼度: {max_val:.3f}): ({center_x}, {center_y})", device_id)
                    return (center_x, center_y)
            except Exception as e:
                continue
        
        # 検出方法4: グレースケール＋エッジ検出
        try:
            gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # エッジ検出
            screenshot_edges = cv2.Canny(gray_screenshot, 50, 150)
            template_edges = cv2.Canny(gray_template, 50, 150)
            
            result = cv2.matchTemplate(screenshot_edges, template_edges, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= 0.2:  # エッジ検出は閾値を下げる
                h, w = template_edges.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                self.log(f"puzzle検出成功-方法4 (エッジ検出, 信頼度: {max_val:.3f}): ({center_x}, {center_y})", device_id)
                return (center_x, center_y)
        except Exception as e:
            pass
        
        # 検出方法5: HSV色空間での検索
        try:
            hsv_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            hsv_template = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
            
            result = cv2.matchTemplate(hsv_screenshot, hsv_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= 0.25:
                h, w = hsv_template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                self.log(f"puzzle検出成功-方法5 (HSV, 信頼度: {max_val:.3f}): ({center_x}, {center_y})", device_id)
                return (center_x, center_y)
        except Exception as e:
            pass
        
        # 検出方法6: 画像の明度調整
        try:
            # 明度を調整したバージョンで試行
            brightness_adjustments = [1.2, 0.8, 1.5, 0.6]
            for brightness in brightness_adjustments:
                adjusted_screenshot = cv2.convertScaleAbs(screenshot, alpha=brightness, beta=0)
                result = cv2.matchTemplate(adjusted_screenshot, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= 0.3:
                    h, w = template.shape[:2]
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    self.log(f"puzzle検出成功-方法6 (明度調整: {brightness:.1f}, 信頼度: {max_val:.3f}): ({center_x}, {center_y})", device_id)
                    return (center_x, center_y)
        except Exception as e:
            pass
        
        self.log("❌ puzzle検出失敗 - 全ての検出方法で未検出", device_id)
        return None

    def toggle_realtime_monitor(self):
        """リアルタイム監視の開始/停止"""
        if not self.realtime_monitoring:
            selected_devices = self.get_selected_devices()
            if not selected_devices:
                messagebox.showwarning("警告", "デバイスを選択してください")
                return
            
            self.realtime_monitoring = True
            self.realtime_monitor_button.config(text="監視停止")
            
            # 監視スレッドを開始
            self.realtime_monitor_thread = threading.Thread(
                target=self.realtime_monitor_loop, 
                args=(selected_devices[0],)
            )
            self.realtime_monitor_thread.daemon = True
            self.realtime_monitor_thread.start()
            
            self.log("リアルタイム監視開始")
        else:
            self.realtime_monitoring = False
            self.realtime_monitor_button.config(text="リアルタイム監視")
            self.log("リアルタイム監視停止")
    
    def realtime_monitor_loop(self, device_id):
        """リアルタイム監視のメインループ"""
        last_detection_status = {}
        
        while self.realtime_monitoring:
            try:
                # 全画像を同時検索
                all_images = self.image_paths.copy()
                detected = self.find_multiple_images_on_screen_optimized(all_images, device_id)
                
                # 検出状況の変化をログ
                current_status = {}
                for name in all_images.keys():
                    current_status[name] = name in detected
                    
                    # 状態が変化した場合のみログ
                    if name not in last_detection_status or last_detection_status[name] != current_status[name]:
                        if current_status[name]:
                            confidence = detected[name]['confidence']
                            pos = detected[name]['pos']
                            self.log(f"🔍 検出: {name} (信頼度: {confidence:.3f}, 位置: {pos})", device_id)
                        else:
                            self.log(f"❌ 消失: {name}", device_id)
                
                # puzzle.pngが検出されていない場合は強化検知を試行
                if not current_status.get('puzzle', False):
                    puzzle_pos = self.find_puzzle_with_enhanced_detection(device_id)
                    if puzzle_pos:
                        self.log(f"🔍 強化検出: puzzle (位置: {puzzle_pos})", device_id)
                        current_status['puzzle'] = True
                
                last_detection_status = current_status.copy()
                
                # 1秒間隔で監視
                time.sleep(1.0)
                
            except Exception as e:
                self.log(f"監視エラー: {str(e)}", device_id)
                time.sleep(1.0)
    
    def enhanced_puzzle_detection_test(self, device_id):
        """puzzle.png検出テストの全バリエーション"""
        self.log("=== puzzle.png 超詳細テスト ===", device_id)
        
        # 画像ファイルの確認
        if not os.path.exists(self.image_paths['puzzle']):
            self.log("❌ puzzle.pngファイルが存在しません", device_id)
            return
        
        template = cv2.imread(self.image_paths['puzzle'])
        if template is None:
            self.log("❌ puzzle.png読み込み失敗", device_id)
            return
        
        template_h, template_w = template.shape[:2]
        self.log(f"✅ puzzle.pngサイズ: {template_w}x{template_h}", device_id)
        
        # スクリーンショット取得
        screenshot = self.fast_screenshot_to_memory(device_id)
        if screenshot is None:
            self.log("❌ スクリーンショット取得失敗", device_id)
            return
        
        screenshot_h, screenshot_w = screenshot.shape[:2]
        self.log(f"✅ スクリーンショットサイズ: {screenshot_w}x{screenshot_h}", device_id)
        
        # 各検出方法をテスト
        methods = [
            ("方法1: 通常マッチング", self.test_normal_matching),
            ("方法2: 複数アルゴリズム", self.test_multiple_algorithms),
            ("方法3: スケール変換", self.test_scale_matching),
            ("方法4: エッジ検出", self.test_edge_matching),
            ("方法5: HSV色空間", self.test_hsv_matching),
            ("方法6: 明度調整", self.test_brightness_matching)
        ]
        
        for method_name, test_func in methods:
            self.log(f"--- {method_name} ---", device_id)
            result = test_func(screenshot, template, device_id)
            if result:
                self.log(f"✅ {method_name}: 成功 {result}", device_id)
            else:
                self.log(f"❌ {method_name}: 失敗", device_id)
        
        self.log("=== puzzle.png 超詳細テスト 終了 ===", device_id)
    
    def test_normal_matching(self, screenshot, template, device_id):
        """通常マッチングテスト"""
        thresholds = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
        for threshold in thresholds:
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x, center_y = max_loc[0] + w // 2, max_loc[1] + h // 2
                return f"(閾値: {threshold:.1f}, 信頼度: {max_val:.3f}, 位置: ({center_x}, {center_y}))"
        return None
    
    def test_multiple_algorithms(self, screenshot, template, device_id):
        """複数アルゴリズムテスト"""
        algorithms = [
            (cv2.TM_CCOEFF_NORMED, "CCOEFF_NORMED"),
            (cv2.TM_CCORR_NORMED, "CCORR_NORMED"),
            (cv2.TM_SQDIFF_NORMED, "SQDIFF_NORMED")
        ]
        
        for method, name in algorithms:
            try:
                result = cv2.matchTemplate(screenshot, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if method == cv2.TM_SQDIFF_NORMED:
                    if min_val <= 0.4:
                        h, w = template.shape[:2]
                        center_x, center_y = min_loc[0] + w // 2, min_loc[1] + h // 2
                        return f"({name}, 信頼度: {1-min_val:.3f}, 位置: ({center_x}, {center_y}))"
                else:
                    if max_val >= 0.3:
                        h, w = template.shape[:2]
                        center_x, center_y = max_loc[0] + w // 2, max_loc[1] + h // 2
                        return f"({name}, 信頼度: {max_val:.3f}, 位置: ({center_x}, {center_y}))"
            except:
                continue
        return None
    
    def test_scale_matching(self, screenshot, template, device_id):
        """スケールマッチングテスト"""
        scales = [1.0, 0.9, 1.1, 0.8, 1.2, 0.7, 1.3]
        for scale in scales:
            try:
                h, w = template.shape[:2]
                new_h, new_w = int(h * scale), int(w * scale)
                if new_w > 0 and new_h > 0:
                    scaled_template = cv2.resize(template, (new_w, new_h))
                    result = cv2.matchTemplate(screenshot, scaled_template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    if max_val >= 0.3:
                        sh, sw = scaled_template.shape[:2]
                        center_x, center_y = max_loc[0] + sw // 2, max_loc[1] + sh // 2
                        return f"(スケール: {scale:.1f}, 信頼度: {max_val:.3f}, 位置: ({center_x}, {center_y}))"
            except:
                continue
        return None
    
    def test_edge_matching(self, screenshot, template, device_id):
        """エッジマッチングテスト"""
        try:
            gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            screenshot_edges = cv2.Canny(gray_screenshot, 50, 150)
            template_edges = cv2.Canny(gray_template, 50, 150)
            
            result = cv2.matchTemplate(screenshot_edges, template_edges, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= 0.2:
                h, w = template_edges.shape[:2]
                center_x, center_y = max_loc[0] + w // 2, max_loc[1] + h // 2
                return f"(エッジ検出, 信頼度: {max_val:.3f}, 位置: ({center_x}, {center_y}))"
        except:
            pass
        return None
    
    def test_hsv_matching(self, screenshot, template, device_id):
        """HSVマッチングテスト"""
        try:
            hsv_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            hsv_template = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
            
            result = cv2.matchTemplate(hsv_screenshot, hsv_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= 0.25:
                h, w = hsv_template.shape[:2]
                center_x, center_y = max_loc[0] + w // 2, max_loc[1] + h // 2
                return f"(HSV色空間, 信頼度: {max_val:.3f}, 位置: ({center_x}, {center_y}))"
        except:
            pass
        return None
    
    def test_brightness_matching(self, screenshot, template, device_id):
        """明度調整マッチングテスト"""
        brightness_values = [1.2, 0.8, 1.5, 0.6, 1.8, 0.4]
        for brightness in brightness_values:
            try:
                adjusted_screenshot = cv2.convertScaleAbs(screenshot, alpha=brightness, beta=0)
                result = cv2.matchTemplate(adjusted_screenshot, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= 0.3:
                    h, w = template.shape[:2]
                    center_x, center_y = max_loc[0] + w // 2, max_loc[1] + h // 2
                    return f"(明度: {brightness:.1f}, 信頼度: {max_val:.3f}, 位置: ({center_x}, {center_y}))"
            except:
                continue
        return None

def main():
    root = tk.Tk()
    app = PuniPuniAutoPlayer(root)
    
    def on_closing():
        if app.running:
            app.stop_automation()
        if app.realtime_monitoring:
            app.realtime_monitoring = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
