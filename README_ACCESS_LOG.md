# 🔍 アクセスログ確認方法（超簡単版）

## けーにもーん用クイックガイド

### 📋 誰がアクセスしたか確認する

```bash
heroku run --app sss4 python manage.py show_access_logs
```

**これだけ！** ニックネーム、IP、アクセス時刻が全部表示される。

### 📅 過去48時間分見たい時

```bash
heroku run --app sss4 python manage.py show_access_logs --hours 48
```

### 📍 特定のページだけ見たい時

```bash
# 投稿・編集ページのみ
heroku run --app sss4 python manage.py show_access_logs --path /game_same_title/post_or_edit/

# タイトル提案ページのみ
heroku run --app sss4 python manage.py show_access_logs --path /game_same_title/propose_title/
```

### 👤 特定のユーザーだけ見たい時

```bash
heroku run --app sss4 python manage.py show_access_logs --user kenio
```

## 🎯 記録されるページ

1. `/game_same_title/post_or_edit/` - 同タイトルゲーム投稿・編集
2. `/game_same_title/novels/` - 同タイトルゲーム小説一覧
3. `/game_same_title/propose_title/` - タイトル提案

## 📊 表示される情報

- **ニックネーム（ユーザー名）** - 誰がアクセスしたか
- **IPアドレス** - どこからアクセスしたか
- **日時** - いつアクセスしたか（日本時間）
- **パス** - どのページにアクセスしたか

## 🔥 詳しい情報

`docs/ACCESS_LOG_GUIDE.md` を見てや。
