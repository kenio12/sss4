# このファイルは本番環境との互換性のため残しています
# 実際の処理は0004_remove_maturi_novel.pyで行われます

from django.db import migrations

class Migration(migrations.Migration):
    
    dependencies = [
        ('game_maturi', '0003_gameprediction_status_and_more'),
    ]
    
    operations = [
        # 何もしない（0004_remove_maturi_novel.pyで処理済み）
    ]