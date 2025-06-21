import subprocess
import cv2
import numpy as np
import tempfile
import os
import time

class DeviceController:
    def __init__(self):
        self.current_device = None
        self.adb_path = "adb"  # ADBのパス
        
    def set_device(self, device):
        """使用するデバイスの設定"""
        self.current_device = device
        
    def get_devices(self):
        """接続されているデバイスのリストを取得"""
        try:
            result = subprocess.run([self.adb_path, "devices"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return []
                
            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # 最初の行はヘッダーなのでスキップ
            
            for line in lines:
                if line.strip() and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
                    
            return devices
            
        except Exception as e:
            print(f"デバイス取得エラー: {str(e)}")
            return []
            
    def get_screenshot(self):
        """スクリーンショットの取得"""
        if not self.current_device:
            raise Exception("デバイスが設定されていません")
            
        try:
            # 一時ファイルを作成
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                
            try:
                # ADBコマンドでスクリーンショットを取得
                cmd = [self.adb_path, "-s", self.current_device, "exec-out", "screencap", "-p"]
                result = subprocess.run(cmd, capture_output=True, timeout=15)
                
                if result.returncode != 0:
                    raise Exception(f"スクリーンショット取得失敗: {result.stderr.decode()}")
                    
                # 画像データを一時ファイルに保存
                with open(temp_path, 'wb') as f:
                    f.write(result.stdout)
                    
                # OpenCVで画像を読み込み
                screenshot = cv2.imread(temp_path)
                
                if screenshot is None:
                    raise Exception("スクリーンショットの読み込みに失敗しました")
                    
                return screenshot
                
            finally:
                # 一時ファイルを削除
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except subprocess.TimeoutExpired:
            raise Exception("スクリーンショット取得がタイムアウトしました")
        except Exception as e:
            raise Exception(f"スクリーンショット取得エラー: {str(e)}")
            
    def tap(self, x, y):
        """指定座標をタップ"""
        if not self.current_device:
            raise Exception("デバイスが設定されていません")
            
        try:
            cmd = [self.adb_path, "-s", self.current_device, "shell", "input", "tap", str(x), str(y)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                raise Exception(f"タップ失敗: {result.stderr}")
                
            return True
            
        except subprocess.TimeoutExpired:
            raise Exception("タップコマンドがタイムアウトしました")
        except Exception as e:
            raise Exception(f"タップエラー: {str(e)}")
            
    def swipe(self, x1, y1, x2, y2, duration=500):
        """スワイプ操作"""
        if not self.current_device:
            raise Exception("デバイスが設定されていません")
            
        try:
            cmd = [self.adb_path, "-s", self.current_device, "shell", "input", "swipe", 
                   str(x1), str(y1), str(x2), str(y2), str(duration)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                raise Exception(f"スワイプ失敗: {result.stderr}")
                
            return True
            
        except subprocess.TimeoutExpired:
            raise Exception("スワイプコマンドがタイムアウトしました")
        except Exception as e:
            raise Exception(f"スワイプエラー: {str(e)}")
            
    def get_screen_size(self):
        """画面サイズの取得"""
        if not self.current_device:
            raise Exception("デバイスが設定されていません")
            
        try:
            cmd = [self.adb_path, "-s", self.current_device, "shell", "wm", "size"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                raise Exception(f"画面サイズ取得失敗: {result.stderr}")
                
            # 出力例: "Physical size: 1080x1920"
            output = result.stdout.strip()
            size_part = output.split(": ")[1]
            width, height = map(int, size_part.split("x"))
            
            return width, height
            
        except Exception as e:
            raise Exception(f"画面サイズ取得エラー: {str(e)}")
            
    def is_device_connected(self, device_id):
        """デバイスが接続されているかチェック"""
        devices = self.get_devices()
        return device_id in devices
        
    def wait_for_device(self, timeout=30):
        """デバイスの接続を待機"""
        if not self.current_device:
            raise Exception("デバイスが設定されていません")
            
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_device_connected(self.current_device):
                return True
            time.sleep(1)
            
        return False
        
    def check_adb_connection(self):
        """ADB接続の確認"""
        try:
            result = subprocess.run([self.adb_path, "version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
            
    def restart_adb_server(self):
        """ADBサーバーの再起動"""
        try:
            # ADBサーバーを停止
            subprocess.run([self.adb_path, "kill-server"], 
                          capture_output=True, timeout=10)
            
            # ADBサーバーを開始
            result = subprocess.run([self.adb_path, "start-server"], 
                                  capture_output=True, timeout=10)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"ADBサーバー再起動エラー: {str(e)}")
            return False
