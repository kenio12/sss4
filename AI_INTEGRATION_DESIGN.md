# AI機能統合設計書（novel_site）

**作成日**: 2025-11-15
**対象プロジェクト**: novel_site (https://www.sss4.life/)
**使用AI**: Claude Sonnet 4.5 (Anthropic API)
**推定月額コスト**: 約$0.25（¥38）

---

## 📋 実装する5つの機能

### 1. AI自動小説投稿機能（月2回、流行ネタ）

**概要**: AI作家そに〜🌸が流行のネタで小説を自動投稿

**実装詳細**:
- **スケジュール**: 毎月1日と15日の午前9時に自動実行（Celery Beat）
- **処理フロー**:
  1. Google Trendsで日本の流行キーワード取得
  2. Claude Sonnet 4.5に「流行キーワード」で小説生成依頼
  3. 生成された小説をNovelモデルに保存（author=AI作家そに〜🌸）
  4. 公開ステータスで自動投稿

**技術スタック**:
```python
# novels/tasks.py
from celery import shared_task
import anthropic
from pytrends.request import TrendReq

@shared_task
def auto_post_novel():
    # 1. Google Trends取得
    pytrends = TrendReq(hl='ja-JP', tz=540)
    trending = pytrends.trending_searches(pn='japan')
    keyword = trending[0][0]  # 1位のキーワード

    # 2. Claude Sonnet 4.5で小説生成
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"「{keyword}」をテーマに2000文字の短編小説を書いてください"
        }]
    )

    # 3. 小説保存・公開
    Novel.objects.create(
        title=f"【AI創作】{keyword}",
        content=message.content[0].text,
        author=User.objects.get(username='ai_sonny'),
        status='published'
    )
```

**Celery Beat設定**:
```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    'auto-post-novel': {
        'task': 'novels.tasks.auto_post_novel',
        'schedule': crontab(day_of_month='1,15', hour=9, minute=0),
    },
}
```

---

### 2. AIコメント自動返信機能（通知検知→即座返信）

**概要**: AI作家そに〜🌸の小説にコメントが付いたら即座に返信

**実装詳細**:
- **トリガー**: Commentモデルのpost_saveシグナル
- **処理フロー**:
  1. コメント保存時にシグナル発火
  2. コメント対象がAI作家そに〜🌸の小説か確認
  3. Claude Sonnet 4.5にコメント内容を渡して返信文生成
  4. 自動で返信コメント投稿

**技術スタック**:
```python
# novels/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment, Novel
import anthropic

@receiver(post_save, sender=Comment)
def auto_reply_to_comment(sender, instance, created, **kwargs):
    if not created:
        return

    # AI作家そに〜🌸の小説へのコメントか確認
    ai_user = User.objects.get(username='ai_sonny')
    if instance.novel.author != ai_user:
        return

    # Claude Sonnet 4.5で返信文生成
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"小説「{instance.novel.title}」へのコメント「{instance.content}」に対して、AI作家そに〜🌸として温かく返信してください（200文字以内）"
        }]
    )

    # 返信コメント投稿
    Comment.objects.create(
        novel=instance.novel,
        user=ai_user,
        content=message.content[0].text,
        parent=instance  # 親コメント設定
    )
```

**AppConfig設定**:
```python
# novels/apps.py
class NovelsConfig(AppConfig):
    def ready(self):
        import novels.signals  # シグナル登録
```

---

### 3. AI他ユーザー小説自動読み取り・コメント機能

**概要**: AI作家そに〜🌸が他ユーザーの新着小説を読んでコメント

**実装詳細**:
- **スケジュール**: 毎日午前10時に自動実行（Celery Beat）
- **処理フロー**:
  1. 過去24時間以内に投稿された小説取得（AI作家そに〜🌸以外）
  2. ランダムに3作品選択
  3. Claude Sonnet 4.5に小説全文を渡して感想生成
  4. コメント投稿

**技術スタック**:
```python
# novels/tasks.py
from datetime import timedelta
from django.utils import timezone
import random

@shared_task
def auto_comment_on_novels():
    # 過去24時間の新着小説取得
    ai_user = User.objects.get(username='ai_sonny')
    yesterday = timezone.now() - timedelta(days=1)
    recent_novels = Novel.objects.filter(
        created_at__gte=yesterday,
        status='published'
    ).exclude(author=ai_user)

    # ランダムに3作品選択
    selected_novels = random.sample(list(recent_novels), min(3, len(recent_novels)))

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    for novel in selected_novels:
        # Claude Sonnet 4.5で感想生成
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": f"以下の小説を読んで、温かい感想を200文字以内で書いてください。\n\nタイトル: {novel.title}\n\n本文:\n{novel.content}"
            }]
        )

        # コメント投稿
        Comment.objects.create(
            novel=novel,
            user=ai_user,
            content=message.content[0].text
        )
```

**Celery Beat設定**:
```python
CELERY_BEAT_SCHEDULE = {
    'auto-comment-on-novels': {
        'task': 'novels.tasks.auto_comment_on_novels',
        'schedule': crontab(hour=10, minute=0),
    },
}
```

---

### 4. AI同タイトル提案機能（月初め自動実行）

**概要**: AI作家そに〜🌸が毎月初めに「同タイトル」のお題を提案

**実装詳細**:
- **スケジュール**: 毎月1日午前8時に自動実行（Celery Beat）
- **処理フロー**:
  1. Claude Sonnet 4.5に「今月のお題」生成依頼
  2. SameTitleモデルに保存（月初めのお題として）
  3. 全ユーザーに通知（メール・サイト内通知）

**技術スタック**:
```python
# novels/tasks.py
@shared_task
def suggest_same_title():
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Claude Sonnet 4.5でお題生成
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": "小説投稿サイトの「同タイトル企画」のお題を1つ提案してください。多くの人が参加しやすい、面白いタイトルをお願いします。タイトルのみ出力してください。"
        }]
    )

    # SameTitleモデルに保存
    ai_user = User.objects.get(username='ai_sonny')
    same_title = SameTitle.objects.create(
        title=message.content[0].text,
        proposed_by=ai_user,
        month=timezone.now().month,
        year=timezone.now().year
    )

    # 全ユーザーに通知
    from django.core.mail import send_mass_mail
    users = User.objects.filter(is_active=True)
    emails = [(
        f'【AI提案】今月の同タイトル企画: {same_title.title}',
        f'AI作家そに〜🌸が今月のお題を提案しました！\n\nお題: {same_title.title}\n\nぜひ参加してくださいね！',
        'noreply@sss4.life',
        [user.email]
    ) for user in users if user.email]

    send_mass_mail(emails, fail_silently=True)
```

**Celery Beat設定**:
```python
CELERY_BEAT_SCHEDULE = {
    'suggest-same-title': {
        'task': 'novels.tasks.suggest_same_title',
        'schedule': crontab(day_of_month=1, hour=8, minute=0),
    },
}
```

---

### 5. Anthropic新モデルリリース自動通知システム

**概要**: Anthropic APIの新モデルをチェックして、けーにもーんに通知

**実装詳細**:
- **スケジュール**: 毎日午前9時に自動実行（Celery Beat）
- **処理フロー**:
  1. Anthropic Models List APIで現在のモデル一覧取得
  2. 前回のキャッシュと比較して新モデル検出
  3. 新モデルがあれば、けーにもーんにメール・Slack通知
  4. 管理画面に警告バナー表示

**技術スタック**:
```python
# novels/tasks.py
import json
from pathlib import Path

MODELS_CACHE_FILE = Path(__file__).parent / 'anthropic_models.json'

@shared_task
def check_anthropic_new_models():
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # 現在のモデルリスト取得
    response = client.models.list()
    current_models = {m.id: m.display_name for m in response.data}

    # 前回のモデルリスト読み込み
    if MODELS_CACHE_FILE.exists():
        with open(MODELS_CACHE_FILE, 'r') as f:
            previous_models = json.load(f)
    else:
        previous_models = {}

    # 新しいモデルを検出
    new_models = {
        model_id: name
        for model_id, name in current_models.items()
        if model_id not in previous_models
    }

    if new_models:
        # けーにもーんに通知
        from django.core.mail import send_mail
        message = "🔥 Anthropic 新モデルリリース！🔥\n\n"
        for model_id, name in new_models.items():
            message += f"- {name} ({model_id})\n"
        message += "\nnovel_site の AI機能をアップグレードしますか？"

        send_mail(
            subject='🔥 Anthropic 新モデルリリース通知',
            message=message,
            from_email='noreply@sss4.life',
            recipient_list=[settings.ADMIN_EMAIL],
        )

    # 現在のモデルリストをキャッシュ保存
    with open(MODELS_CACHE_FILE, 'w') as f:
        json.dump(current_models, f)

    return f"チェック完了: 新モデル {len(new_models)}件"
```

**Celery Beat設定**:
```python
CELERY_BEAT_SCHEDULE = {
    'check-anthropic-new-models': {
        'task': 'novels.tasks.check_anthropic_new_models',
        'schedule': crontab(hour=9, minute=0),
    },
}
```

---

## 🔧 必要な環境設定

### 1. Anthropic API設定

**.env に追加**:
```bash
# Anthropic API設定
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-sonnet-4-5  # 使用モデル（設定ファイルで管理）
```

**settings.py に追加**:
```python
# Anthropic API設定
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY')
ANTHROPIC_MODEL = env('ANTHROPIC_MODEL', default='claude-sonnet-4-5')
```

### 2. Python パッケージ追加

**requirements.txt に追加**:
```txt
anthropic==0.39.0  # Anthropic公式SDK
pytrends==4.9.2     # Google Trends取得
```

**インストール**:
```bash
pip install anthropic pytrends
```

### 3. Celery Beat 設定確認

**settings.py**:
```python
# Celery設定
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_TIMEZONE = 'Asia/Tokyo'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30分タイムアウト

# Celery Beat スケジュール
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'auto-post-novel': {
        'task': 'novels.tasks.auto_post_novel',
        'schedule': crontab(day_of_month='1,15', hour=9, minute=0),  # 毎月1日・15日 午前9時
    },
    'auto-comment-on-novels': {
        'task': 'novels.tasks.auto_comment_on_novels',
        'schedule': crontab(hour=10, minute=0),  # 毎日午前10時
    },
    'suggest-same-title': {
        'task': 'novels.tasks.suggest_same_title',
        'schedule': crontab(day_of_month=1, hour=8, minute=0),  # 毎月1日 午前8時
    },
    'check-anthropic-new-models': {
        'task': 'novels.tasks.check_anthropic_new_models',
        'schedule': crontab(hour=9, minute=0),  # 毎日午前9時
    },
}
```

### 4. AI作家そに〜🌸 ユーザーアカウント作成

**管理画面で作成**:
```python
# Django shell で作成
from django.contrib.auth import get_user_model
User = get_user_model()

ai_user, created = User.objects.get_or_create(
    username='ai_sonny',
    defaults={
        'email': 'ai_sonny@sss4.life',
        'nickname': 'AI作家そに〜🌸',
        'is_active': True,
    }
)
```

---

## 💰 コスト試算

### Claude Sonnet 4.5 料金
- **Input**: $3 / 1M tokens
- **Output**: $15 / 1M tokens

### 月間使用量推定

| 機能 | 実行回数/月 | Input tokens | Output tokens | 月額コスト |
|------|------------|--------------|---------------|-----------|
| 自動小説投稿 | 2回 | 200 × 2 = 400 | 2,000 × 2 = 4,000 | $0.06 |
| コメント自動返信 | 10回 | 500 × 10 = 5,000 | 200 × 10 = 2,000 | $0.045 |
| 他ユーザー小説コメント | 30回 | 1,000 × 30 = 30,000 | 200 × 30 = 6,000 | $0.18 |
| 同タイトル提案 | 1回 | 100 | 50 | $0.001 |
| 新モデルチェック | 30回 | 10 × 30 = 300 | 0 | $0.001 |
| **合計** | - | **35,800** | **12,050** | **$0.287 (¥44)** |

**推定月額**: 約$0.29（¥44）

---

## 🚀 実装優先順位

1. **優先度1（即座実装）**: Anthropic新モデルリリース自動通知システム
   - 理由: 古いバージョン使い続けるリスク回避

2. **優先度2**: AI自動小説投稿機能
   - 理由: サイトの活性化・ユーザー増加に直結

3. **優先度3**: AIコメント自動返信機能
   - 理由: ユーザー体験向上・エンゲージメント強化

4. **優先度4**: AI他ユーザー小説自動読み取り・コメント機能
   - 理由: コミュニティ活性化

5. **優先度5**: AI同タイトル提案機能
   - 理由: 月1回の企画、ユーザー参加促進

---

## 📝 注意事項

### 1. モデルバージョン管理
- 新モデルリリース時は自動通知システムでけーにもーんに即座報告
- テスト環境で新モデルを試してから本番適用
- `.env` の `ANTHROPIC_MODEL` を変更するだけでモデル切り替え可能

### 2. エラーハンドリング
- API呼び出し失敗時は自動リトライ（Celery retry機能）
- エラーログをSentryに送信
- けーにもーんにエラー通知（重大エラーのみ）

### 3. セキュリティ
- `ANTHROPIC_API_KEY` は絶対に公開しない（.gitignoreに.env追加済み）
- Heroku Config Varsで環境変数管理
- APIキーは定期的にローテーション

### 4. テスト
- 本番実装前に必ずテスト環境で動作確認
- AI生成コンテンツの品質チェック
- コスト監視（Anthropic Consoleで月次使用量確認）

---

## 🔗 参考リンク

- **Anthropic API ドキュメント**: https://docs.anthropic.com/
- **Claude Models List API**: https://docs.claude.com/en/api/models-list
- **Anthropic Console**: https://console.anthropic.com/
- **料金ページ**: https://www.anthropic.com/pricing
- **リリースノート**: https://docs.claude.com/en/release-notes/api

---

**最終更新**: 2025-11-15
**作成者**: そに〜🌸（Claude Sonnet 4.5）
