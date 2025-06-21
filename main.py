import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import os
import shutil
from automation_engine import AutomationEngine
from config_manager import ConfigManager

class PuniPuniAutoPlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("妖怪ウォッチぷにぷに オトクリ補助ツール V1.0alpha")
        self.root.geometry("500x900")
        self.root.resizable(True, True)
        
        # 設定管理とオートメーションエンジンの初期化
        self.config_manager = ConfigManager()
        self.automation_engine = AutomationEngine(self.config_manager)
        
        # GUI要素の初期化
        self.is_running = False
        self.automation_thread = None
        
        self.setup_ui()
        self.setup_callbacks()
        
    def setup_ui(self):
        """UIの設定"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="オトクリ補助ツール for Windows", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # デバイス設定フレーム
        device_frame = ttk.LabelFrame(main_frame, text="デバイス設定", padding="10")
        device_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # デバイス選択
        ttk.Label(device_frame, text="デバイス:").grid(row=0, column=0, sticky=tk.W)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(device_frame, textvariable=self.device_var, 
                                        width=30, state="readonly")
        self.device_combo.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        
        # デバイス更新ボタン
        self.refresh_btn = ttk.Button(device_frame, text="デバイス更新", 
                                     command=self.refresh_devices)
        self.refresh_btn.grid(row=0, column=2, padx=(10, 0))
        
        # 自動化設定フレーム
        automation_frame = ttk.LabelFrame(main_frame, text="自動化設定", padding="10")
        automation_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # タップ間隔設定
        ttk.Label(automation_frame, text="タップ間隔 (秒):").grid(row=0, column=0, sticky=tk.W)
        self.tap_interval_var = tk.DoubleVar(value=0.5)
        tap_interval_spin = ttk.Spinbox(automation_frame, from_=0.1, to=5.0, 
                                       increment=0.1, textvariable=self.tap_interval_var,
                                       width=10)
        tap_interval_spin.grid(row=0, column=1, padx=(10, 0), sticky=tk.W)
        
        # 検出精度設定
        ttk.Label(automation_frame, text="検出精度:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.detection_threshold_var = tk.DoubleVar(value=0.8)
        threshold_scale = ttk.Scale(automation_frame, from_=0.5, to=1.0, 
                                   variable=self.detection_threshold_var, 
                                   orient=tk.HORIZONTAL, length=200)
        threshold_scale.grid(row=1, column=1, padx=(10, 0), sticky=(tk.W, tk.E), pady=(10, 0))
          # 精度値表示
        self.threshold_label = ttk.Label(automation_frame, text="0.80")
        self.threshold_label.grid(row=1, column=2, padx=(10, 0), pady=(10, 0))
        
        # 誤タップ防止設定フレーム
        prevent_frame = ttk.LabelFrame(main_frame, text="誤タップ防止", padding="10")
        prevent_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 誤タップ防止の各チェックボックス
        self.prevent_goukan_var = tk.BooleanVar(value=True)
        self.prevent_yuubin_var = tk.BooleanVar(value=True)
        self.prevent_ranking_var = tk.BooleanVar(value=True)
        self.prevent_menu_var = tk.BooleanVar(value=True)        
        ttk.Checkbutton(prevent_frame, text="ごうかんボタンをタップしない", 
                       variable=self.prevent_goukan_var).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(prevent_frame, text="ゆうびんボタンをタップしない", 
                       variable=self.prevent_yuubin_var).grid(row=0, column=1, sticky=tk.W, pady=2, padx=(20, 0))
        ttk.Checkbutton(prevent_frame, text="ランキングボタンをタップしない", 
                       variable=self.prevent_ranking_var).grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(prevent_frame, text="メニューボタンをタップしない", 
                       variable=self.prevent_menu_var).grid(row=1, column=1, sticky=tk.W, pady=2, padx=(20, 0))
        
        # 画像管理フレーム
        image_frame = ttk.LabelFrame(main_frame, text="画像管理", padding="10")
        image_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 画像追加セクション
        ttk.Label(image_frame, text="新しい画像を追加:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # タップする画像追加
        tap_frame = ttk.Frame(image_frame)
        tap_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(tap_frame, text="タップする画像:").pack(side=tk.LEFT)
        self.add_tap_btn = ttk.Button(tap_frame, text="画像選択", 
                                     command=self.add_tap_image)
        self.add_tap_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # タップしない画像追加
        ignore_frame = ttk.Frame(image_frame)
        ignore_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(ignore_frame, text="タップしない画像:").pack(side=tk.LEFT)
        self.add_ignore_btn = ttk.Button(ignore_frame, text="画像選択", 
                                        command=self.add_ignore_image)
        self.add_ignore_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 画像リスト表示
        ttk.Label(image_frame, text="現在の画像一覧:").grid(row=3, column=0, sticky=tk.W, pady=(15, 5))
        
        # 画像リストフレーム
        list_frame = ttk.Frame(image_frame)
        list_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 画像リストボックス
        self.image_listbox = tk.Listbox(list_frame, height=6, width=50)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.image_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_listbox.config(yscrollcommand=scrollbar.set)
        
        # 画像削除ボタン
        self.remove_image_btn = ttk.Button(image_frame, text="選択した画像を削除", 
                                          command=self.remove_image)
        self.remove_image_btn.grid(row=5, column=0, columnspan=2, pady=(10, 0))
          # 制御ボタンフレーム
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=5, column=0, columnspan=2, pady=(0, 10))
        
        # 開始/停止ボタン
        self.start_stop_btn = ttk.Button(control_frame, text="自動化開始", 
                                        command=self.toggle_automation)
        self.start_stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # テストボタン
        self.test_btn = ttk.Button(control_frame, text="画像検出テスト", 
                                  command=self.test_detection)
        self.test_btn.pack(side=tk.LEFT)
        
        # ログフレーム
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # ログテキストエリア
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ステータスバー
        self.status_var = tk.StringVar(value="準備完了")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))        # グリッドの重み設定
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)  # ログフレームの行を拡張可能に
        device_frame.columnconfigure(1, weight=1)
        automation_frame.columnconfigure(1, weight=1)
        
        # 設定値の初期化
        self.load_ui_settings()
        
    def load_ui_settings(self):
        """UI設定値の読み込み"""
        config = self.config_manager.get_config()
        
        # 誤タップ防止設定の読み込み
        self.prevent_goukan_var.set(config.get('prevent_goukan', True))
        self.prevent_yuubin_var.set(config.get('prevent_yuubin', True))
        self.prevent_ranking_var.set(config.get('prevent_ranking', True))
        self.prevent_menu_var.set(config.get('prevent_menu', True))
        
        # 自動化設定の読み込み
        self.tap_interval_var.set(config.get('tap_interval', 0.5))
        self.detection_threshold_var.set(config.get('detection_threshold', 0.8))
        
    def setup_callbacks(self):
        """コールバックの設定"""
        # スケール値の更新
        self.detection_threshold_var.trace('w', self.update_threshold_label)
        
        # 自動化エンジンのログコールバック
        self.automation_engine.set_log_callback(self.log_message)
        
        # 画像リストの初期化
        self.update_image_list()
        
    def update_threshold_label(self, *args):
        """検出精度ラベルの更新"""
        value = self.detection_threshold_var.get()
        self.threshold_label.config(text=f"{value:.2f}")
        
    def refresh_devices(self):
        """接続されているデバイスの更新"""
        self.log_message("デバイスを検索中...")
        self.status_var.set("デバイス検索中...")
        
        # 別スレッドでデバイス検索
        def search_devices():
            devices = self.automation_engine.get_available_devices()
            
            # UIスレッドで結果を更新
            self.root.after(0, self.update_device_list, devices)
            
        threading.Thread(target=search_devices, daemon=True).start()
        
    def update_device_list(self, devices):
        """デバイスリストの更新"""
        self.device_combo['values'] = devices
        if devices:
            self.device_combo.current(0)
            self.log_message(f"デバイスが見つかりました: {len(devices)}台")
            self.status_var.set("デバイス検出完了")
        else:
            self.log_message("デバイスが見つかりませんでした")
            self.status_var.set("デバイスが見つかりません")
            
    def toggle_automation(self):
        """自動化の開始/停止"""
        if not self.is_running:
            self.start_automation()
        else:
            self.stop_automation()
            
    def start_automation(self):
        """自動化開始"""
        device = self.device_var.get()
        if not device:
            messagebox.showerror("エラー", "デバイスを選択してください")
            return
              # 設定の更新
        self.config_manager.set_config({
            'device': device,
            'tap_interval': self.tap_interval_var.get(),
            'detection_threshold': self.detection_threshold_var.get(),
            'prevent_goukan': self.prevent_goukan_var.get(),
            'prevent_yuubin': self.prevent_yuubin_var.get(),
            'prevent_ranking': self.prevent_ranking_var.get(),
            'prevent_menu': self.prevent_menu_var.get()
        })
        
        self.is_running = True
        self.start_stop_btn.config(text="自動化停止", style="Accent.TButton")
        self.status_var.set("自動化実行中...")
        
        # 自動化スレッドの開始
        self.automation_thread = threading.Thread(target=self.run_automation, daemon=True)
        self.automation_thread.start()
        
        self.log_message("自動化を開始しました")
        
    def stop_automation(self):
        """自動化停止"""
        self.is_running = False
        self.automation_engine.stop()
        
        self.start_stop_btn.config(text="自動化開始", style="")
        self.status_var.set("自動化停止")
        
        self.log_message("自動化を停止しました")
        
    def run_automation(self):
        """自動化の実行"""
        try:
            self.automation_engine.start()
            while self.is_running:
                if not self.automation_engine.process_frame():
                    time.sleep(0.1)
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"エラー: {str(e)}"))
            self.root.after(0, self.stop_automation)
            
    def test_detection(self):
        """画像検出のテスト"""
        device = self.device_var.get()
        if not device:
            messagebox.showerror("エラー", "デバイスを選択してください")
            return
            
        self.log_message("画像検出テストを実行しています...")
        
        def run_test():
            try:                # 設定の更新
                self.config_manager.set_config({
                    'device': device,
                    'detection_threshold': self.detection_threshold_var.get(),
                    'prevent_goukan': self.prevent_goukan_var.get(),
                    'prevent_yuubin': self.prevent_yuubin_var.get(),
                    'prevent_ranking': self.prevent_ranking_var.get(),
                    'prevent_menu': self.prevent_menu_var.get()
                })
                
                results = self.automation_engine.test_image_detection()
                  # UIスレッドで結果を表示
                self.root.after(0, lambda: self.show_test_results(results))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"テストエラー: {str(e)}"))
                
        threading.Thread(target=run_test, daemon=True).start()
        
    def show_test_results(self, results):
        """テスト結果の表示"""
        message = "画像検出テスト結果:\n\n"
        for image_name, detected in results.items():
            status = "検出" if detected else "未検出"
            message += f"{image_name}: {status}\n"
            
        messagebox.showinfo("テスト結果", message)
        self.log_message("画像検出テストが完了しました")
        
    def log_message(self, message):
        """ログメッセージの追加"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def update_image_list(self):
        """画像リストを更新"""
        self.image_listbox.delete(0, tk.END)
        
        image_dir = "image"
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
            return
            
        # タップする画像とタップしない画像を分類
        tap_images = []
        ignore_images = []
        
        # 設定から誤タップ防止画像を取得
        config = self.config_manager.get_config()
        prevent_images = []
        if config.get('prevent_goukan', True):
            prevent_images.append('koukan.png')
        if config.get('prevent_yuubin', True):
            prevent_images.append('yubin.png')
        if config.get('prevent_ranking', True):
            prevent_images.append('ranking.png')
        if config.get('prevent_menu', True):
            prevent_images.append('menu.png')
        
        # imageフォルダ内の画像ファイルを確認
        for filename in os.listdir(image_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                if filename in prevent_images:
                    ignore_images.append(filename)
                else:
                    tap_images.append(filename)
        
        # リストボックスに表示
        for img in sorted(tap_images):
            self.image_listbox.insert(tk.END, f"[タップする] {img}")
        
        for img in sorted(ignore_images):
            self.image_listbox.insert(tk.END, f"[タップしない] {img}")
    
    def add_tap_image(self):
        """タップする画像を追加"""
        file_path = filedialog.askopenfilename(
            title="タップする画像を選択",
            filetypes=[
                ("画像ファイル", "*.png *.jpg *.jpeg"),
                ("PNGファイル", "*.png"),
                ("JPEGファイル", "*.jpg *.jpeg"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            self._add_image_file(file_path, is_tap_image=True)
    
    def add_ignore_image(self):
        """タップしない画像を追加"""
        file_path = filedialog.askopenfilename(
            title="タップしない画像を選択",
            filetypes=[
                ("画像ファイル", "*.png *.jpg *.jpeg"),
                ("PNGファイル", "*.png"),
                ("JPEGファイル", "*.jpg *.jpeg"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            self._add_image_file(file_path, is_tap_image=False)
    
    def _add_image_file(self, file_path, is_tap_image=True):
        """画像ファイルをimageフォルダに追加"""
        try:
            # ファイル名を取得
            filename = os.path.basename(file_path)
            
            # 画像フォルダのパス
            image_dir = "image"
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            
            destination = os.path.join(image_dir, filename)
            
            # 既に同じ名前のファイルが存在する場合は確認
            if os.path.exists(destination):
                result = messagebox.askyesno(
                    "ファイル上書き確認",
                    f"'{filename}' は既に存在します。上書きしますか？"
                )
                if not result:
                    return
            
            # ファイルをコピー
            shutil.copy2(file_path, destination)
            
            # タップしない画像の場合、設定に追加
            if not is_tap_image:
                # 新規追加の場合はファイル名のみで管理
                self.log_message(f"タップしない画像として '{filename}' を追加しました")
            else:
                self.log_message(f"タップする画像として '{filename}' を追加しました")
            
            # 画像リストを更新
            self.update_image_list()
            
            # オートメーションエンジンに変更を通知
            self.automation_engine.reload_images()
            
        except Exception as e:
            messagebox.showerror("エラー", f"画像の追加に失敗しました:\n{str(e)}")
            self.log_message(f"画像追加エラー: {str(e)}")
    
    def remove_image(self):
        """選択した画像を削除"""
        selection = self.image_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除する画像を選択してください")
            return
        
        # 選択された項目のテキストを取得
        selected_text = self.image_listbox.get(selection[0])
        
        # ファイル名を抽出（[タイプ] filename形式から）
        if "] " in selected_text:
            filename = selected_text.split("] ", 1)[1]
        else:
            filename = selected_text
        
        # 削除確認
        result = messagebox.askyesno(
            "削除確認",
            f"'{filename}' を削除しますか？\nこの操作は元に戻せません。"
        )
        
        if result:
            try:
                # ファイルを削除
                file_path = os.path.join("image", filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.log_message(f"画像 '{filename}' を削除しました")
                    
                    # 画像リストを更新
                    self.update_image_list()
                    
                    # オートメーションエンジンに変更を通知
                    self.automation_engine.reload_images()
                else:
                    messagebox.showerror("エラー", f"ファイルが見つかりません: {filename}")
                    
            except Exception as e:
                messagebox.showerror("エラー", f"画像の削除に失敗しました:\n{str(e)}")
                self.log_message(f"画像削除エラー: {str(e)}")
    
    def run(self):
        """アプリケーションの実行"""
        # 初期化時にデバイスを検索
        self.root.after(100, self.refresh_devices)
        
        self.root.mainloop()

if __name__ == "__main__":
    app = PuniPuniAutoPlay()
    app.run()
