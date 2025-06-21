# 妖怪ウォッチぷにぷに 自動プレイ for MacOS

## 概要
MacOSで動作する妖怪ウォッチぷにぷに自動タップ補助ツールです。

- GUI: tkinter
- 画像検出: OpenCV2
- ADB経由でAndroid端末を制御
- 画像管理・誤タップ防止・設定永続化などWindows版と同等の機能

## 使い方
1. Python3, ADB, 必要なパッケージをインストール
2. MacOSフォルダ内で `python3 main.py` を実行
3. GUIからデバイス選択・設定・画像管理が可能

## 注意点
- MacOSではADBのパスや権限に注意してください
- 画像パスやファイル操作は基本的にWindows版と同じですが、パス区切りや権限で問題が出た場合は適宜修正してください

## 必要パッケージ
- opencv-python
- numpy
- Pillow
- tkinter (標準搭載)

## 既知の違い
- フォントやウィンドウサイズがMacで最適化されていない場合は適宜調整してください
- ADBのインストール方法やパス設定はMacOSの手順に従ってください

---

Windows版の `automation_engine.py` や `config_manager.py` などは共通で利用できます。

---

# MacOS版：配布用アプリ化について

本ツールはMacOSでもスタンドアロンアプリ（.app）として配布可能です。

## Mac用スタンドアロン化（.app化）手順
1. Python3と依存パッケージをインストール
2. `pip3 install pyinstaller`
3. MacOSフォルダで以下を実行：
   ```sh
   pyinstaller --noconfirm --onefile --windowed main.py
   ```
   - `dist/main` または `dist/main.app` が生成されます
   - `image/` フォルダや config.json も同梱してください
4. Gatekeeper対策で初回は右クリック→「開く」で起動

## 配布時の注意
- `image/` フォルダや設定ファイルも一緒に配布してください
- ADB（Android Debug Bridge）は各自でインストール・パス設定が必要です
- 詳細な手順やトラブルシュートは本READMEおよび親ディレクトリのREADME.mdも参照

---
