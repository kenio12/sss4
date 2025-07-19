# novel_site プロジェクト設定・トラブルシューティング

このファイルは`novel_site`プロジェクト固有の設定、解決した問題、重要な注意事項をまとめています。

## 📊 プロジェクト概要
- **プロジェクト名**: novel_site (超短編小説会)
- **フレームワーク**: Django 3.2.24
- **データベース**: PostgreSQL 16
- **環境**: Docker Compose
- **開発サーバー**: https://localhost:8000 (SSL証明書付き)

## 🔧 重要な設定

### Docker Compose構成
- **Web**: Django + runserver_plus (SSL)
- **DB**: PostgreSQL 16 (ポート5432)
- **Old DB**: PostgreSQL 13 (ポート5433) - 旧データ用
- **Redis**: メッセージブローカー (ポート6379)
- **Celery**: バックグラウンドタスク
- **Celery Beat**: 定期タスク

### SSL証明書
- `cert.pem` / `key.pem` でHTTPS対応
- 開発環境でもHTTPS必須の設定

## 🚨 重要なトラブルシューティング

### 2025-07-06 解決：Novelモデルのデータ作成エラー

**問題**: `django.db.utils.DataError: value too long for type character varying(1)`

**原因**: `initial`フィールドの理解ミス
- ❌ 誤解：「初回文」（文章の最初の部分）だと思っていた  
- ✅ 正解：「頭文字」（最初の1文字のみ）を保存するフィールド

**正しいフィールド定義**:
```python
# novels/models.py line 69
initial = models.CharField(max_length=1, blank=True, null=True)  # 頭文字を保存
```

**データベース構造**:
```sql
initial | character varying(1) | 1文字のみ保存可能
```

**正しいサンプルデータ作成方法**:
```python
Novel.objects.create(
    title='雨の日の思い出',
    initial='小',  # ← 1文字のみ！
    content='小さな喫茶店の窓際の席で...',  # ← 本文はここ
    # ... 他のフィールド
)
```

### マイグレーション状況
**2025-07-06時点で適用済み**:
- `novels.0002_novel_scheduled_at_alter_novel_genre_and_more` ✅
- `novels.0003_comment_is_maturi_comment_comment_maturi_game_and_more` ✅
- `novels.0004_alter_novel_genre` ✅

### Announcementモデル 正しいフィールド名
```python
# announcements/models.py
class Announcement(models.Model):
    title = models.CharField('タイトル', max_length=200)
    content = models.TextField('内容')
    created_by = models.ForeignKey('accounts.User', ...)  # ← authorではない
    is_pinned = models.BooleanField('固定表示', default=False)  # ← is_importantではない
    is_active = models.BooleanField('公開状態', default=True)
    created_at = models.DateTimeField('作成日時', default=timezone.now)
```

## 🎯 実装完了機能

### 2025-07-06: ホームページレイアウト変更
**要求**: 小説一覧を上部、お知らせ一覧を下部に配置

**実装**: `/home/templates/home/home.html`
- ✅ 小説一覧セクション（lines 224-274）を上部に移動
- ✅ お知らせ一覧セクション（lines 276-309）を下部に配置

### サンプルデータ作成完了
**小説**: 3件
- 「雨の日の思い出」（恋愛、頭文字：小）
- 「最後の授業」（日常、頭文字：老）
- 「星空カフェ」（ファンタジー、頭文字：夜）

**お知らせ**: 3件
- 新機能リリース（固定表示）
- 夏のキャンペーン（通常）
- メンテナンス告知（固定表示）

## 🔍 デバッグ・開発Tips

### Djangoシェルでのデータ確認
```bash
# コンテナ内でシェル起動
docker-compose exec web python manage.py shell

# モデルフィールド確認
from novels.models import Novel
for field in Novel._meta.fields:
    print(f'{field.name}: {field.__class__.__name__}')
```

### PostgreSQL直接確認
```bash
# DBコンテナ内でPostgreSQL接続
docker-compose exec db psql -U postgres -d novel_site_db

# テーブル構造確認
\d novels_novel
```

### マイグレーション管理
```bash
# マイグレーション状況確認
docker-compose exec web python manage.py showmigrations

# 新しいマイグレーション作成
docker-compose exec web python manage.py makemigrations

# マイグレーション適用
docker-compose exec web python manage.py migrate
```

## ⚠️ 注意事項

### 本番環境との差分管理
- **ユーザー懸念**: 「本番とで差が発生していて、それが怖いねん」
- **対策**: マイグレーションファイルの慎重な管理
- **方針**: 本番ではコードの反映はするが、マイグレーションは慎重に実施

### 開発環境での作業原則
1. マイグレーション前に必ずバックアップ
2. 本番影響のあるマイグレーションは事前相談
3. scheduled_atフィールド等の新機能は開発環境で十分テスト

### 2025-07-06 解決：ログイン前アクセス時のProgrammingError

**問題**: ログインせずにホームページにアクセスするとエラー
```
django.db.utils.ProgrammingError: relation "game_same_title_titleproposal" does not exist
```

**原因**: `game_same_title`アプリの初期マイグレーションが未適用
- TitleProposalテーブルが存在しないため、game_same_title/views.py:67でエラー

**解決方法**:
```bash
docker-compose exec web python manage.py migrate game_same_title
```

**マイグレーション詳細**:
- `game_same_title.0001_initial` を適用
- 作成されたテーブル:
  - `game_same_title_titleproposal`
  - `game_same_title_monthlysametitleinfo`  
  - `game_same_title_sametitleentry`

**結果**: HTTP 200 OK でエラー解決 ✅

## 📝 履歴

### 2025-07-06
- ホームページレイアウト変更（小説一覧を上部に）
- Novelモデルのinitialフィールド仕様理解・修正
- scheduled_atフィールド用マイグレーション適用
- サンプルデータ作成（小説3件、お知らせ3件）
- game_same_titleアプリのマイグレーション不備解決
- PROJECT_SETTINGS.md作成

---

**最終更新**: 2025-07-06 by Claude (そに〜🌸)