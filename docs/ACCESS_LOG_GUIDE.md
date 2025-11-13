# AccessLog（アクセスログ）確認ガイド

## 📋 概要

**誰が・いつ・どこにアクセスしたか**をニックネームで確認できるシステムです。

## 🎯 目的

- ユーザーのアクセス履歴を永久保存
- Herokuログが消えても大丈夫
- エラー発生時に誰がアクセスしたか即座に確認
- ニックネームで表示されるから分かりやすい

## 📊 記録される情報

- **ユーザー名（ニックネーム）** - 誰がアクセスしたか
- **アクセス日時** - いつアクセスしたか（日本時間）
- **IPアドレス** - どこからアクセスしたか
- **アクセスパス** - どのページにアクセスしたか
- **HTTPメソッド** - GET/POST等

## 🔍 記録対象ページ

以下のページへのアクセスが自動記録されます：

1. `/game_same_title/post_or_edit/` - 同タイトルゲーム投稿・編集
2. `/game_same_title/novels/` - 同タイトルゲーム小説一覧
3. `/game_same_title/propose_title/` - タイトル提案

## 🚀 使い方（Heroku）

### 基本的な使い方

```bash
# 過去24時間のアクセスログを確認
heroku run --app sss4 python manage.py show_access_logs
```

### オプション付き

```bash
# 過去48時間のアクセスログを確認
heroku run --app sss4 python manage.py show_access_logs --hours 48

# 特定のページのみ確認
heroku run --app sss4 python manage.py show_access_logs --path /game_same_title/post_or_edit/

# 特定のユーザーのみ確認
heroku run --app sss4 python manage.py show_access_logs --user kenio

# 組み合わせ
heroku run --app sss4 python manage.py show_access_logs --hours 72 --path /game_same_title/
```

## 📝 出力例

```
======================================================================
📊 過去24時間のアクセスログ: 3件
======================================================================

🕒 2025-11-13 19:36:41
   👤 ユーザー: けにを (kenio)
   🌐 IP: 14.13.0.129
   📍 パス: /game_same_title/post_or_edit/
   📝 メソッド: GET

🕒 2025-11-13 19:35:35
   👤 ユーザー: けにを (kenio)
   🌐 IP: 14.13.0.129
   📍 パス: /game_same_title/post_or_edit/
   📝 メソッド: GET

🕒 2025-11-13 19:22:22
   👤 ユーザー: 匿名ユーザー
   🌐 IP: 14.13.0.129
   📍 パス: /game_same_title/post_or_edit/
   📝 メソッド: GET

======================================================================
✅ 合計 3件のアクセスログを表示しました
======================================================================
```

## 🛠️ 技術詳細

### データベースモデル

- **モデル名**: `game_same_title.models.AccessLog`
- **テーブル名**: `game_same_title_accesslog`

### フィールド

| フィールド | 型 | 説明 |
|----------|-----|------|
| user | ForeignKey | ユーザー（NULL可） |
| path | CharField | アクセスパス |
| method | CharField | HTTPメソッド |
| ip_address | GenericIPAddressField | IPアドレス |
| user_agent | CharField | User Agent |
| accessed_at | DateTimeField | アクセス日時（インデックス付き） |

### ミドルウェア

- **ファイル**: `game_same_title/middleware.py`
- **クラス**: `SameTitleAccessLogMiddleware`
- **設定**: `config/settings.py` の `MIDDLEWARE` に追加済み

### 管理コマンド

- **ファイル**: `game_same_title/management/commands/show_access_logs.py`
- **コマンド名**: `show_access_logs`

## 🔥 重要な注意事項

### エラー時の挙動

- **ミドルウェアエラー時**: AccessLogが記録されない
- **例**: `request.METHOD`（存在しない属性）でエラー → ログ記録失敗
- **修正**: `request.method`（正しい属性）に修正済み

### 匿名ユーザー

- ログインしていないユーザーは「匿名ユーザー」と表示
- IPアドレスで識別可能

### データ保持期間

- **永久保存** - Herokuログと違って消えない
- 必要に応じて古いログを削除する仕組みを追加予定

## 📞 トラブルシューティング

### ログが記録されない

1. ミドルウェアが正しく動作しているか確認
2. `config/settings.py` の `MIDDLEWARE` に `game_same_title.middleware.SameTitleAccessLogMiddleware` が含まれているか確認
3. データベースマイグレーションが実行されているか確認

### ニックネームが表示されない

1. ユーザーにプロフィールが存在するか確認
2. `user.profile.nickname` が設定されているか確認
3. デフォルトでusernameが表示される

## 🎯 次のステップ

- [ ] 古いログ自動削除機能（90日以上前のログを削除）
- [ ] アクセス統計機能（日別・ユーザー別）
- [ ] CSV/Excel出力機能
- [ ] 管理画面でのログ閲覧機能

## 📅 更新履歴

- **2025-11-13**: AccessLog管理コマンド追加
- **2025-11-13**: middleware.py の request.METHOD → request.method 修正
- **2025-11-13**: ドキュメント作成
