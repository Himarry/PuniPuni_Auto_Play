import cv2
import numpy as np
import os

class ImageDetector:
    def __init__(self):
        self.threshold = 0.8
        self.template_cache = {}
        
    def set_threshold(self, threshold):
        """検出閾値の設定"""
        self.threshold = threshold
        
    def load_template(self, image_path):
        """テンプレート画像の読み込み（キャッシュ付き）"""
        if image_path not in self.template_cache:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")
                
            template = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if template is None:
                raise ValueError(f"画像の読み込みに失敗しました: {image_path}")
                
            self.template_cache[image_path] = template
            
        return self.template_cache[image_path]
        
    def detect_image(self, screenshot, template_path):
        """
        スクリーンショット内でテンプレート画像を検出
        
        Args:
            screenshot: スクリーンショット画像（numpy array）
            template_path: テンプレート画像のパス
            
        Returns:
            list: 検出された位置のリスト [(x, y), ...]
        """
        try:
            # テンプレート画像の読み込み
            template = self.load_template(template_path)
            
            # スクリーンショットがNoneの場合
            if screenshot is None:
                return []
                
            # グレースケール変換
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # テンプレートマッチング
            result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            
            # 閾値以上の位置を検出
            locations = np.where(result >= self.threshold)
            
            # 検出された位置をリストに変換
            positions = []
            template_h, template_w = template_gray.shape
            
            for pt in zip(*locations[::-1]):  # locationは(y, x)の順なので反転
                # テンプレートの中心座標を計算
                center_x = pt[0] + template_w // 2
                center_y = pt[1] + template_h // 2
                positions.append((center_x, center_y))
                
            # 重複する検出結果を除去
            positions = self.remove_duplicate_detections(positions, template_w, template_h)
            
            return positions
            
        except Exception as e:
            print(f"画像検出エラー: {str(e)}")
            return []
            
    def remove_duplicate_detections(self, positions, template_w, template_h):
        """
        重複する検出結果を除去
        
        Args:
            positions: 検出された位置のリスト
            template_w: テンプレートの幅
            template_h: テンプレートの高さ
            
        Returns:
            list: 重複を除去した位置のリスト
        """
        if not positions:
            return []
            
        # 距離の閾値（テンプレートサイズの半分）
        distance_threshold = max(template_w, template_h) // 2
        
        filtered_positions = []
        
        for pos in positions:
            # 既存の位置と比較
            is_duplicate = False
            for existing_pos in filtered_positions:
                distance = np.sqrt((pos[0] - existing_pos[0])**2 + (pos[1] - existing_pos[1])**2)
                if distance < distance_threshold:
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                filtered_positions.append(pos)
                
        return filtered_positions
        
    def save_debug_image(self, screenshot, positions, template_path, output_path):
        """
        デバッグ用：検出結果をマークした画像を保存
        
        Args:
            screenshot: スクリーンショット画像
            positions: 検出された位置のリスト
            template_path: テンプレート画像のパス
            output_path: 出力画像のパス
        """
        try:
            # テンプレートサイズの取得
            template = self.load_template(template_path)
            template_h, template_w = template.shape[:2]
            
            # スクリーンショットのコピー
            debug_image = screenshot.copy()
            
            # 検出された位置に矩形を描画
            for x, y in positions:
                # 矩形の座標計算
                top_left = (x - template_w // 2, y - template_h // 2)
                bottom_right = (x + template_w // 2, y + template_h // 2)
                
                # 矩形を描画
                cv2.rectangle(debug_image, top_left, bottom_right, (0, 255, 0), 2)
                
                # 中心点を描画
                cv2.circle(debug_image, (x, y), 5, (0, 0, 255), -1)
                
            # 画像を保存
            cv2.imwrite(output_path, debug_image)
            
        except Exception as e:
            print(f"デバッグ画像保存エラー: {str(e)}")
            
    def clear_cache(self):
        """テンプレートキャッシュのクリア"""
        self.template_cache.clear()
