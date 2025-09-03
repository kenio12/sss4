# Novel Site マイグレーション修正手順書

## 🔍 判明した問題
- game_maturiで0004番マイグレーションが2つ存在
- 本番DBには両方とも適用済み
- これが原因でマイグレーション実行時にエラーが出る可能性

## ✅ ローカルテスト結果
1. 本番データをローカルにリストア → 成功
2. django_migrationsテーブル確認 → 両方の0004が記録済み
3. 重複レコード削除テスト → 成功

## 🚀 本番環境での修正手順

### 1. Heroku Shellにアクセス
```bash
heroku run bash --app sss4
```

### 2. Django shellでDBに接続
```bash
python manage.py dbshell
```

### 3. 現状確認
```sql
-- マイグレーション状況確認
SELECT app, name FROM django_migrations 
WHERE app='game_maturi' 
ORDER BY id;
```

### 4. 重複レコード削除
```sql
-- 0004_remove_maturi_novel_fixを削除
DELETE FROM django_migrations 
WHERE app='game_maturi' 
AND name='0004_remove_maturi_novel_fix';

-- 確認
SELECT app, name FROM django_migrations 
WHERE app='game_maturi' 
ORDER BY id;
```

### 5. exitでシェル終了
```sql
\q
exit
```

## ⚠️ 注意事項
- **データは一切削除されない**（django_migrationsテーブルのレコードのみ）
- **すでに適用されたマイグレーションの記録を整理するだけ**
- **失敗しても本番データには影響なし**

## 🔧 エラー時の対処
もし問題が起きたら：
1. 何もせずに終了
2. エラー内容を記録
3. 別の方法を検討

## 📅 実行タイミング
- ユーザーが少ない時間帯推奨
- バックアップ後に実行

## ✨ 期待される結果
- マイグレーションのエラーが解消
- 今後のマイグレーションがスムーズに実行可能
- データベースの整合性向上

---
作成日: 2025-09-03
作成者: そに〜🌸