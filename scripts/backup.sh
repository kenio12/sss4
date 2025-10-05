#!/bin/bash

# プロジェクトのルートディレクトリを取得
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# バックアップ先ディレクトリ
BACKUP_DIR="ここに実際のバックアップ先のパスをいれる"

# 日付つきのファイル名
DATE=$(date +%Y%m%d_%H%M%S)

# バックアップディレクトリが存在しない場合は作成
mkdir -p "$BACKUP_DIR"

echo "バックアップを開始します..."

# envファイルのバックアップ
if [ -f "$PROJECT_ROOT/.env" ]; then
    cp "$PROJECT_ROOT/.env" "$BACKUP_DIR/.env.backup_$DATE"
    echo ".envファイルをバックアップしました"
fi

# データベースのバックアップ
echo "データベースのバックアップを作成中..."
docker-compose exec -T web python manage.py dumpdata | gzip > "$BACKUP_DIR/backup_$DATE.json.gz"
echo "データベースのバックアップが完了しました"

# 30日以上前のバックアップを削除
echo "古いバックアップを削除中..."
find "$BACKUP_DIR" -type f -mtime +30 -exec rm {} \;
echo "古いバックアップの削除が完了しました"

echo "バックアップが正常に完了しました！"

