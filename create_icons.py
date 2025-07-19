#!/usr/bin/env python3
"""
PWA用アイコン生成スクリプト
dari.pngから各サイズのアイコンを生成する
"""
from PIL import Image
import os

# アイコンサイズの定義
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# パスの設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_IMAGE = os.path.join(BASE_DIR, 'static/images/dari.png')
OUTPUT_DIR = os.path.join(BASE_DIR, 'static/images')

def create_icons():
    """各サイズのアイコンを生成"""
    
    # 出力ディレクトリの確認
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # ソース画像を開く
    try:
        img = Image.open(SOURCE_IMAGE)
        print(f"✅ ソース画像を読み込みました: {SOURCE_IMAGE}")
        print(f"   元のサイズ: {img.size}")
    except FileNotFoundError:
        print(f"❌ エラー: ソース画像が見つかりません: {SOURCE_IMAGE}")
        return
    except Exception as e:
        print(f"❌ エラー: 画像の読み込みに失敗しました: {e}")
        return
    
    # RGBAモードに変換（透過情報を保持）
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # 各サイズのアイコンを生成
    for size in ICON_SIZES:
        output_path = os.path.join(OUTPUT_DIR, f'icon-{size}x{size}.png')
        
        # リサイズ（高品質な縮小）
        resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # 保存
        resized_img.save(output_path, 'PNG', optimize=True)
        print(f"✅ 生成完了: icon-{size}x{size}.png")
    
    print("\n🎉 すべてのアイコンの生成が完了しました！")
    print(f"📁 出力先: {OUTPUT_DIR}")

if __name__ == "__main__":
    print("🎨 PWA用アイコン生成スクリプト")
    print("=" * 40)
    create_icons()