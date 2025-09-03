#!/usr/bin/env python
"""
マイグレーションファイルを確認するスクリプト
DB接続なしで動作
"""
import os
import glob

def check_migrations():
    print("=" * 60)
    print("Novel Site マイグレーション確認")
    print("=" * 60)
    
    apps = [
        'accounts', 'announcements', 'contacts', 
        'game_maturi', 'game_same_title', 'novels'
    ]
    
    total_migrations = 0
    
    for app in apps:
        migrations_dir = f'{app}/migrations'
        migration_files = glob.glob(f'{migrations_dir}/[0-9]*.py')
        migration_files.sort()
        
        if migration_files:
            print(f"\n📁 {app}:")
            for mig_file in migration_files:
                filename = os.path.basename(mig_file)
                print(f"  - {filename}")
            print(f"  合計: {len(migration_files)}個")
            total_migrations += len(migration_files)
    
    print(f"\n📊 総マイグレーション数: {total_migrations}個")
    
    # 重複チェック
    print("\n⚠️ 潜在的な問題:")
    
    # game_maturiの重複
    maturi_0004 = glob.glob('game_maturi/migrations/0004_*.py')
    if len(maturi_0004) > 1:
        print(f"  - game_maturiに0004番の重複あり！")
        for f in maturi_0004:
            print(f"    {os.path.basename(f)}")
    
    # バックアップフォルダ
    if os.path.exists('game_maturi/migrations/backup'):
        backup_files = glob.glob('game_maturi/migrations/backup/*.py')
        if backup_files:
            print(f"  - game_maturi/migrations/backupに{len(backup_files)}個のファイルあり")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_migrations()