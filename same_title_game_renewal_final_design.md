# 🎯 novel_site 同タイトルゲーム完全リニューアル設計書（確定版）

**作成日**: 2025-10-13（日）
**バージョン**: 1.0 FINAL
**改修方針**: 参加障壁を下げ、プロモーション強化で活性化する

---

## 📋 1. 改修の目的と背景

### 現状の問題点
1. **エントリー制が参加障壁**: 投稿前にエントリー必須 → 面倒で離脱者多数
2. **通知機能が不十分**: イベント開始・タイトル提案を知らせる仕組みがない → 参加者少ない
3. **タイトル提案者の名誉がない**: 提案しても何も得られない → 提案者が集まらない
4. **一番槍の二重取りが可能**: 自分で提案して自分で一番槍を取れる → 不公平感
5. **同タイトル崩れの扱いが不明**: 一番槍確定後、別タイトルで書いた人の記録がない → 参加意欲低下
6. **プロフィールにイベント実績がない**: 一番槍・一番盾を取っても記録が残らない → 達成感が薄い
7. **祭り設定が手間**: タイトルをゼロから手動入力 → 参考情報がなくて大変

### 改修後の期待効果
1. **参加者30%増加**: エントリー廃止 + メール通知で再訪問促進
2. **提案者増加**: 一番盾称号で名誉 → タイトル提案が活発化
3. **公平性向上**: 自分の提案タイトル除外 → 一番槍二重取り防止
4. **モチベーション向上**: プロフィールにイベント実績表示 → 参加意欲向上
5. **管理効率化**: 祭り設定画面に参考表示 → 管理者の作業時間50%削減

---

## 🎯 2. 全7項目の詳細仕様

### 📌 項目1：エントリー制完全廃止

#### 仕様
- **エントリーなしで誰でも同タイトル投稿可能**
- 既存のエントリー関連コード・テーブル削除
- UI簡素化（エントリーボタン削除）

#### 実装内容
1. **モデル削除**: `SameTitleEntry` テーブル削除（migrations作成）
2. **View削除**: `game_same_title/views.py` のエントリー関連View削除
3. **URL削除**: `game_same_title/urls.py` のエントリー関連URL削除
4. **テンプレート削除**: エントリーボタン・エントリーページのHTML削除
5. **投稿フォーム修正**: タイトル選択時にエントリー確認なしで投稿可能

#### UI変更
**変更前（エントリー必須）**:
```
同タイトルページ → [エントリーする] → 確認画面 → 投稿フォーム → 投稿
```

**変更後（エントリー不要）**:
```
同タイトルページ → [俺もこのタイトルで作る] → 投稿フォーム → 投稿
```

---

### 📌 項目2：同タイトル崩れ機能

#### 仕様
- **一番槍が決まった後、別タイトルで書いた人**を「同タイトル崩れ」として記録
- プロフィールに「同タイトル崩れ」バッジ表示
- 一覧画面で区別表示（背景色・アイコン）

#### データ構造
**Novel モデルに追加**:
```python
class Novel(models.Model):
    # 既存フィールド
    is_same_title_game = models.BooleanField(default=False)
    event = models.CharField(max_length=50, choices=[('同タイトル', '同タイトル'), ('祭り', '祭り')], blank=True, null=True)

    # 🆕 追加フィールド
    is_ichiban_yari = models.BooleanField(default=False, verbose_name='一番槍')
    is_same_title_failure = models.BooleanField(default=False, verbose_name='同タイトル崩れ')
    same_title_month = models.DateField(blank=True, null=True, verbose_name='同タイトル参加月')
```

#### ロジック
1. **一番槍判定**: 月の最初の同タイトル投稿 → `is_ichiban_yari=True` 設定
2. **崩れ判定**: 一番槍確定後、その月の同タイトル提案に選ばれなかったタイトルで投稿 → `is_same_title_failure=True` 設定
3. **イベント変更**: 崩れ作品は `event='同タイトル崩れ'` に自動変更
4. **ジャンル維持**: ジャンルはユーザーが選択したまま（変更なし）
5. **タイトル固定**: 一番槍確定後はタイトル編集不可

#### UI表示
**一覧画面**:
```
タイトル           | ジャンル   | イベント         | 作者 | 投稿日
------------------|-----------|-----------------|------|-------
恋の物語 🏆      | 恋愛      | 同タイトル       | 太郎 | 2025-10-11
夜の殺人 💔      | ミステリー | 同タイトル崩れ💔 | 花子 | 2025-10-10
```
- 🏆: 一番槍アイコン
- 💔: 同タイトル崩れアイコン
- ジャンルはユーザーが選択したまま（変更されない）
- イベントが「同タイトル崩れ」に自動変更される

**プロフィール**:
```
【同タイトル崩れ歴】
・2025年10月「夜の殺人」💔
・2025年09月「朝の光」💔
```

---

### 📌 項目3：一番盾称号システム

#### 仕様
- **タイトル提案者に名誉バッジ（🛡️）**
- MonthlySameTitleInfo.proposerフィールド活用
- AI提案は除外（人間のみ対象）
- プロフィールに「一番盾獲得歴」表示

#### データ構造
**MonthlySameTitleInfo モデル（既存）**:
```python
class MonthlySameTitleInfo(models.Model):
    year = models.IntegerField()
    month = models.IntegerField()
    selected_title = models.CharField(max_length=100)
    proposer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # ← これを活用
    selected_at = models.DateTimeField(null=True, blank=True)
```

#### ロジック
1. **一番槍投稿時**: `proposer`フィールドを確認
2. **AI提案除外**: `proposer=None` の場合は一番盾なし
3. **称号付与**: `proposer`が人間ユーザーの場合、一番盾バッジ表示

#### UI表示
**プロフィール**:
```
【一番盾獲得歴】
・2025年10月「恋の物語」🛡️
・2025年09月「夜の殺人」🛡️
```

**一覧画面**:
```
タイトル          | ジャンル | イベント   | 作者 | 提案者
-----------------|---------|-----------|------|-------
恋の物語 🏆     | 恋愛    | 同タイトル | 太郎 | 花子 🛡️
```

---

### 📌 項目4：自分の提案タイトル除外

#### 仕様
- **先月自分が提案したタイトルは選択肢に表示しない**
- 一番槍＋一番盾の二重取り禁止
- 他人が一番槍取った場合は執筆可能

#### ロジック
**投稿フォームのタイトル選択肢生成**:
```python
def get_same_title_choices(user):
    """
    ログインユーザーが選択できる同タイトル一覧を返す
    自分が提案したタイトルは除外
    """
    current_month = timezone.now()

    # 今月の同タイトル候補
    proposals = TitleProposal.objects.filter(
        proposal_month__year=current_month.year,
        proposal_month__month=current_month.month,
        status='active'
    ).exclude(proposer=user)  # ← 自分の提案を除外

    return [(p.title, p.title) for p in proposals]
```

#### UI変更
**変更前（全タイトル表示）**:
```
【同タイトル候補】
- 恋の物語（自分が提案）
- 夜の殺人
- 朝の光
```

**変更後（自分の提案を除外）**:
```
【同タイトル候補】
- 夜の殺人
- 朝の光
```

---

### 📌 項目5：プロフィールページにイベントセクション

#### 仕様
- **「イベント」セクション新設**
- 一番槍獲得歴（年月・タイトル・🏆）
- 一番盾獲得歴（年月・タイトル・🛡️）
- 同タイトル崩れ歴（年月・タイトル・💔）
- 祭り参加歴も表示

#### UI設計
**プロフィールページ（accounts/profile.html）**:
```html
<!-- 既存の「作品一覧」セクションの下に追加 -->
<section class="event-section">
  <h3>🎯 イベント実績</h3>

  <!-- 一番槍 -->
  <div class="ichiban-yari">
    <h4>🏆 一番槍獲得歴</h4>
    {% for record in ichiban_yari_records %}
    <div class="record-item">
      <span class="date">{{ record.year }}年{{ record.month }}月</span>
      <span class="title">「{{ record.title }}」</span>
      <span class="badge">🏆</span>
    </div>
    {% empty %}
    <p>まだ一番槍を取っていません</p>
    {% endfor %}
  </div>

  <!-- 一番盾 -->
  <div class="ichiban-tate">
    <h4>🛡️ 一番盾獲得歴</h4>
    {% for record in ichiban_tate_records %}
    <div class="record-item">
      <span class="date">{{ record.year }}年{{ record.month }}月</span>
      <span class="title">「{{ record.title }}」</span>
      <span class="badge">🛡️</span>
    </div>
    {% empty %}
    <p>まだ一番盾を取っていません</p>
    {% endfor %}
  </div>

  <!-- 同タイトル崩れ -->
  <div class="same-title-failure">
    <h4>💔 同タイトル崩れ歴</h4>
    {% for record in failure_records %}
    <div class="record-item">
      <span class="date">{{ record.year }}年{{ record.month }}月</span>
      <span class="title">「{{ record.title }}」</span>
      <span class="badge">💔</span>
    </div>
    {% empty %}
    <p>同タイトル崩れ歴はありません</p>
    {% endfor %}
  </div>

  <!-- 祭り参加歴 -->
  <div class="maturi-history">
    <h4>🎪 祭り参加歴</h4>
    {% for record in maturi_records %}
    <div class="record-item">
      <span class="date">{{ record.year }}年{{ record.month }}月</span>
      <span class="title">「{{ record.title }}」</span>
      <span class="badge">🎪</span>
    </div>
    {% empty %}
    <p>祭りに参加していません</p>
    {% endfor %}
  </div>
</section>
```

#### View実装
```python
def profile_view(request, username):
    user = get_object_or_404(User, username=username)

    # 一番槍獲得歴
    ichiban_yari_records = Novel.objects.filter(
        author=user,
        is_ichiban_yari=True
    ).order_by('-same_title_month')

    # 一番盾獲得歴
    ichiban_tate_records = MonthlySameTitleInfo.objects.filter(
        proposer=user
    ).order_by('-year', '-month')

    # 同タイトル崩れ歴
    failure_records = Novel.objects.filter(
        author=user,
        is_same_title_failure=True
    ).order_by('-same_title_month')

    # 祭り参加歴
    maturi_records = Novel.objects.filter(
        author=user,
        event='祭り'
    ).order_by('-created_at')

    context = {
        'profile_user': user,
        'ichiban_yari_records': ichiban_yari_records,
        'ichiban_tate_records': ichiban_tate_records,
        'failure_records': failure_records,
        'maturi_records': maturi_records,
    }
    return render(request, 'accounts/profile.html', context)
```

---

### 📌 項目6：祭り設定画面に参考表示

#### 仕様
- **adminpanel/maturi_game_setup.htmlに機能追加**
- 当年（1月〜12月）の全提案タイトル表示
- 一番槍タイトルは🏆マークで強調
- 管理者が手動で名詞抽出して5つの語句を決定
- 自動追加はしない（参考表示のみ）

#### UI設計
**祭り設定画面（adminpanel/maturi_game_setup.html）**:
```html
<section class="reference-section">
  <h3>📊 参考：今年の同タイトル提案一覧</h3>
  <p>今年（{{ current_year }}年）に提案された同タイトル候補です。一番槍タイトルは🏆マークで表示されます。</p>

  <table>
    <thead>
      <tr>
        <th>年月</th>
        <th>タイトル</th>
        <th>提案者</th>
        <th>状態</th>
      </tr>
    </thead>
    <tbody>
      {% for proposal in yearly_proposals %}
      <tr class="{% if proposal.is_ichiban_yari %}ichiban-yari{% endif %}">
        <td>{{ proposal.year }}年{{ proposal.month }}月</td>
        <td>
          {{ proposal.title }}
          {% if proposal.is_ichiban_yari %}🏆{% endif %}
        </td>
        <td>{{ proposal.proposer.nickname }}</td>
        <td>{{ proposal.status }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="usage-note">
    <p><strong>使い方</strong>:</p>
    <ol>
      <li>上記のタイトルから名詞を手動で抽出</li>
      <li>5つの語句を下記フォームに入力</li>
      <li>祭り設定を保存</li>
    </ol>
  </div>
</section>

<!-- 既存の祭り設定フォーム -->
<section class="maturi-form">
  <h3>🎪 祭り設定</h3>
  <form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">保存</button>
  </form>
</section>
```

#### View実装
```python
def maturi_game_setup(request):
    current_year = timezone.now().year

    # 今年の全提案タイトル
    yearly_proposals = TitleProposal.objects.filter(
        proposal_month__year=current_year
    ).order_by('-proposal_month')

    # 一番槍かどうかを判定
    for proposal in yearly_proposals:
        monthly_info = MonthlySameTitleInfo.objects.filter(
            year=proposal.proposal_month.year,
            month=proposal.proposal_month.month,
            selected_title=proposal.title
        ).first()
        proposal.is_ichiban_yari = monthly_info is not None if monthly_info else False

    context = {
        'current_year': current_year,
        'yearly_proposals': yearly_proposals,
        'form': MaturiGameForm(),  # 既存のフォーム
    }
    return render(request, 'adminpanel/maturi_game_setup.html', context)
```

---

### 📌 項目7：プロモーション・通知システム（NEW!）

#### 仕様
**3種類のメール通知**:

1. **同タイトル募集通知（月初・1日）**:
   - 全会員に同タイトルイベント募集開始を通知
   - Heroku Schedulerで自動送信
   - コマンド: `python manage.py send_monthly_recruitment`

2. **同タイトル提案通知（提案投稿時）**:
   - タイトル提案時に全会員へリアルタイム通知
   - 提案者自身を除く全会員に送信

3. **同タイトル決定通知（一番槍投稿時）**:
   - 月の最初の投稿（一番槍）時に全会員へ通知
   - 投稿者自身を除く全会員に送信
   - 「俺もこのタイトルで作る」リンク付き

#### データ構造
**EmailNotificationSettings モデル（新規作成）**:
```python
class EmailNotificationSettings(models.Model):
    """
    ユーザーごとのメール通知設定
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )

    # 同タイトル関連通知
    same_title_recruitment = models.BooleanField(
        default=True,
        verbose_name='同タイトル募集通知'
    )
    same_title_proposal = models.BooleanField(
        default=True,
        verbose_name='同タイトル提案通知'
    )
    same_title_decision = models.BooleanField(
        default=True,
        verbose_name='同タイトル決定通知'
    )

    # その他通知（将来追加用）
    maturi_notification = models.BooleanField(
        default=True,
        verbose_name='祭り通知'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'メール通知設定'
        verbose_name_plural = 'メール通知設定'
```

#### 配信停止機能
**仕組み**:
- メール本文に署名付きトークンの配信停止URL
- トークンは24時間有効（Django signing使用）
- 配信停止ページでワンクリック停止

**URL例**:
```
https://www.sss4.life/accounts/unsubscribe/{token}/
```

**View実装**:
```python
from django.core import signing
from django.shortcuts import render, redirect

def unsubscribe_email(request, token):
    """
    メール配信停止処理
    """
    try:
        # トークン検証（24時間有効）
        user_id = signing.loads(token, salt='email_unsubscribe', max_age=86400)
        user = User.objects.get(id=user_id)

        if request.method == 'POST':
            # 全通知を停止
            settings, created = EmailNotificationSettings.objects.get_or_create(user=user)
            settings.same_title_recruitment = False
            settings.same_title_proposal = False
            settings.same_title_decision = False
            settings.save()

            return render(request, 'accounts/unsubscribe_complete.html')

        return render(request, 'accounts/unsubscribe_confirm.html', {'user': user})

    except (signing.BadSignature, User.DoesNotExist):
        return render(request, 'accounts/unsubscribe_error.html')
```

#### Heroku Scheduler設定
**コマンド**: `python manage.py send_monthly_recruitment`
**実行タイミング**: 毎月1日 10:00 (JST)

**設定手順**:
1. Heroku Dashboardで Scheduler アドオン追加
2. 新しいJobを作成
3. コマンド: `python manage.py send_monthly_recruitment`
4. 実行頻度: Monthly（毎月1日）
5. 時刻: 10:00 AM JST

#### 期待効果
1. **参加者増加**: 募集通知で再訪問促進 → 月間参加者30%増
2. **提案者増加**: 提案通知で新タイトルの認知度向上 → 提案数50%増
3. **一番槍競争激化**: 決定通知で「俺もこのタイトルで作る」クリック増 → 同タイトル投稿数2倍
4. **リテンション向上**: 定期的なメール通知でサイト離脱率50%減

---

## 🗂️ 3. データベース設計（追加・変更フィールド）

### 3.1 Novel モデル変更

**追加フィールド**:
```python
class Novel(models.Model):
    # 既存フィールド（変更なし）
    is_same_title_game = models.BooleanField(default=False)
    event = models.CharField(max_length=50, choices=[('同タイトル', '同タイトル'), ('祭り', '祭り')], blank=True, null=True)

    # 🆕 追加フィールド
    is_ichiban_yari = models.BooleanField(
        default=False,
        verbose_name='一番槍',
        help_text='月の最初の同タイトル投稿'
    )
    is_same_title_failure = models.BooleanField(
        default=False,
        verbose_name='同タイトル崩れ',
        help_text='一番槍確定後、別タイトルで投稿した作品'
    )
    same_title_month = models.DateField(
        blank=True,
        null=True,
        verbose_name='同タイトル参加月',
        help_text='同タイトルイベント参加年月'
    )
```

**migration作成**:
```bash
python manage.py makemigrations novels
python manage.py migrate novels
```

---

### 3.2 EmailNotificationSettings モデル新規作成

**モデル定義**（上記「項目7」参照）

**migration作成**:
```bash
python manage.py makemigrations accounts
python manage.py migrate accounts
```

---

### 3.3 既存データの変換（データ移行）

**migration内で既存データを変換**:
```python
# novels/migrations/0XXX_add_same_title_fields.py

from django.db import migrations
from django.utils import timezone

def migrate_existing_data(apps, schema_editor):
    """
    既存の同タイトル作品にフラグを設定
    """
    Novel = apps.get_model('novels', 'Novel')
    MonthlySameTitleInfo = apps.get_model('game_same_title', 'MonthlySameTitleInfo')

    # 全ての同タイトル作品
    same_title_novels = Novel.objects.filter(is_same_title_game=True)

    for novel in same_title_novels:
        # 同タイトル参加月を設定
        novel.same_title_month = novel.created_at.date()

        # 一番槍判定
        monthly_info = MonthlySameTitleInfo.objects.filter(
            year=novel.created_at.year,
            month=novel.created_at.month,
            selected_title=novel.title
        ).first()

        if monthly_info and monthly_info.selected_at:
            # この作品が月の最初の投稿か確認
            first_novel = Novel.objects.filter(
                title=novel.title,
                is_same_title_game=True,
                created_at__year=novel.created_at.year,
                created_at__month=novel.created_at.month
            ).order_by('created_at').first()

            if first_novel and first_novel.id == novel.id:
                novel.is_ichiban_yari = True

        novel.save()

class Migration(migrations.Migration):
    dependencies = [
        ('novels', '0XXX_previous_migration'),
        ('game_same_title', '0XXX_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='novel',
            name='is_ichiban_yari',
            field=models.BooleanField(default=False, verbose_name='一番槍'),
        ),
        migrations.AddField(
            model_name='novel',
            name='is_same_title_failure',
            field=models.BooleanField(default=False, verbose_name='同タイトル崩れ'),
        ),
        migrations.AddField(
            model_name='novel',
            name='same_title_month',
            field=models.DateField(blank=True, null=True, verbose_name='同タイトル参加月'),
        ),
        migrations.RunPython(migrate_existing_data),
    ]
```

---

## 📝 4. 実装ステップ（5段階）

### ステップ1：データベース準備（1日）

**作業内容**:
1. Novel モデルに3フィールド追加（migrations作成・実行）
2. EmailNotificationSettings モデル作成（migrations作成・実行）
3. 既存データ変換migration作成・実行
4. データ確認（一番槍フラグが正しく設定されているか）

**完了条件**:
- [ ] migrations全て実行完了
- [ ] 既存の同タイトル作品に `same_title_month` 設定済み
- [ ] 一番槍作品に `is_ichiban_yari=True` 設定済み

---

### ステップ2：エントリー制廃止＋同タイトル崩れ（2日）

**作業内容**:
1. エントリー関連削除:
   - `SameTitleEntry` モデル削除
   - エントリーView・URL削除
   - エントリーボタン削除
2. 同タイトル崩れ実装:
   - 一番槍投稿時に `is_ichiban_yari=True` 設定
   - 崩れ判定ロジック実装（別タイトル投稿時に `is_same_title_failure=True` 設定）
   - UI表示（一覧・プロフィール）

**完了条件**:
- [ ] エントリーなしで同タイトル投稿可能
- [ ] 一番槍が正しく判定される
- [ ] 同タイトル崩れが正しく記録される
- [ ] 一覧画面で🏆・💔アイコン表示

---

### ステップ3：一番盾＋自分の提案除外（1日）

**作業内容**:
1. 一番盾称号:
   - MonthlySameTitleInfo.proposer活用
   - プロフィールに一番盾獲得歴表示
2. 自分の提案除外:
   - 投稿フォームのタイトル選択肢生成時に除外ロジック追加
   - UI確認（自分の提案が選択肢に出ないこと）

**完了条件**:
- [ ] 一番盾バッジがプロフィールに表示
- [ ] 自分の提案タイトルが選択肢に出ない
- [ ] 他人が一番槍取った場合は執筆可能

---

### ステップ4：プロフィール＋祭り設定画面（1日）

**作業内容**:
1. プロフィールに「イベント」セクション追加:
   - 一番槍獲得歴表示
   - 一番盾獲得歴表示
   - 同タイトル崩れ歴表示
   - 祭り参加歴表示
2. 祭り設定画面に参考表示:
   - 今年の全提案タイトル表示
   - 一番槍タイトルに🏆マーク

**完了条件**:
- [ ] プロフィールにイベント実績セクション表示
- [ ] 祭り設定画面に参考一覧表示
- [ ] UI確認（見やすく整理されているか）

---

### ステップ5：プロモーション・通知システム（2日）

**作業内容**:
1. 通知機能実装（既存コード活用）:
   - `game_same_title/notifications.py` 確認
   - 3種類のメール通知テスト
2. 配信停止機能:
   - 配信停止URL生成
   - 配信停止ページ作成
   - ワンクリック停止機能
3. Heroku Scheduler設定:
   - `send_monthly_recruitment` コマンド確認
   - Heroku Schedulerに登録

**完了条件**:
- [ ] 月初募集通知が送信される
- [ ] タイトル提案時に通知送信
- [ ] 一番槍投稿時に通知送信
- [ ] 配信停止リンクが機能する
- [ ] Heroku Schedulerで月初自動送信

---

## 🧪 5. テストシナリオ（3パターン）

### テストパターン1：エントリー廃止テスト

**手順**:
1. ログインする
2. 同タイトルページにアクセス
3. [俺もこのタイトルで作る] ボタンをクリック
4. 投稿フォームに遷移
5. タイトル・本文を入力して投稿

**期待結果**:
- [ ] エントリーボタンが表示されない
- [ ] エントリー確認画面が表示されない
- [ ] 直接投稿フォームに遷移する
- [ ] 投稿が成功する

---

### テストパターン2：一番槍＋一番盾テスト

**手順**:
1. **ユーザーA**: タイトル「テスト物語」を提案（1日）
2. **ユーザーB**: 「テスト物語」で投稿（5日）← 一番槍
3. **ユーザーC**: 「テスト物語」で投稿（10日）
4. プロフィール確認

**期待結果**:
- [ ] ユーザーBのプロフィールに一番槍🏆表示
- [ ] ユーザーAのプロフィールに一番盾🛡️表示
- [ ] ユーザーCは一番槍なし（通常の同タイトル参加者）

---

### テストパターン3：同タイトル崩れテスト

**手順**:
1. **ユーザーA**: タイトル「テスト物語A」を提案（1日）
2. **ユーザーB**: タイトル「テスト物語B」を提案（2日）
3. **ユーザーC**: 「テスト物語A」で投稿（5日）← 一番槍確定
4. **ユーザーD**: 「テスト物語B」で投稿（10日）← 同タイトル崩れ
5. 一覧・プロフィール確認

**期待結果**:
- [ ] ユーザーCの作品に一番槍🏆表示
- [ ] ユーザーDの作品に同タイトル崩れ💔表示
- [ ] ユーザーDのプロフィールに「同タイトル崩れ歴」表示
- [ ] ユーザーDの作品が `genre='旧同タイトル'` に変更

---

## 🎯 6. 期待効果とリスク対策

### 期待効果

| 項目 | 現状 | 改修後 | 効果 |
|-----|------|--------|------|
| 月間参加者数 | 30人 | 40人 | +33% |
| タイトル提案数 | 10件 | 15件 | +50% |
| 同タイトル投稿数 | 20件 | 40件 | +100% |
| リテンション率 | 40% | 60% | +50% |
| 管理作業時間 | 2時間 | 1時間 | -50% |

### リスク対策

| リスク | 対策 |
|--------|------|
| データ移行失敗 | バックアップ取得、開発環境で十分テスト |
| 既存ユーザーの混乱 | お知らせページで改修内容説明、1週間ヘルプページ目立たせる |
| メール通知の苦情 | 配信停止ボタン必須、通知頻度は適切に設定 |
| 一番槍判定の誤作動 | テストケース30パターン実施、ログ監視 |
| 通知メール送信エラー | 送信失敗時のリトライ機能、ログ監視 |

---

## ✅ 7. 完了条件

### データベース
- [ ] Novel に3フィールド追加完了
- [ ] EmailNotificationSettings モデル作成完了
- [ ] 既存データ変換migration実行完了
- [ ] データ確認完了（一番槍フラグ正常）

### 機能実装
- [ ] エントリー制完全廃止
- [ ] 同タイトル崩れ機能動作確認
- [ ] 一番盾称号システム動作確認
- [ ] 自分の提案タイトル除外動作確認
- [ ] プロフィールにイベントセクション表示
- [ ] 祭り設定画面に参考表示
- [ ] メール通知3種類送信確認
- [ ] 配信停止機能動作確認
- [ ] Heroku Scheduler設定完了

### テスト
- [ ] テストパターン1（エントリー廃止）通過
- [ ] テストパターン2（一番槍＋一番盾）通過
- [ ] テストパターン3（同タイトル崩れ）通過

### UI確認
- [ ] 一覧画面に🏆・💔・🛡️アイコン表示
- [ ] プロフィールに全イベント実績表示
- [ ] 祭り設定画面に参考一覧表示
- [ ] レスポンシブ対応（スマホ表示OK）

### 本番環境
- [ ] Herokuへデプロイ完了
- [ ] 本番環境で全機能動作確認
- [ ] エラーログ確認（エラーなし）
- [ ] ユーザーテスト実施（3人以上）

---

## 📚 8. 参考資料

### 既存実装ファイル
- `/Users/keikeikun2/ai-try-programing/novel_site/game_same_title/notifications.py` - 通知関数実装済み
- `/Users/keikeikun2/ai-try-programing/novel_site/game_same_title/management/commands/send_monthly_recruitment.py` - 月初自動メール
- `/Users/keikeikun2/ai-try-programing/novel_site/game_same_title/models.py` - TitleProposal, MonthlySameTitleInfo
- `/Users/keikeikun2/ai-try-programing/novel_site/novels/models.py` - Novel（3フィールド追加必要）
- `/Users/keikeikun2/ai-try-programing/novel_site/adminpanel/views.py` - maturi_game_setup
- `/Users/keikeikun2/ai-try-programing/novel_site/adminpanel/templates/adminpanel/maturi_game_setup.html`

### 統合元ファイル（削除予定）
- `/Users/keikeikun2/ai-try-programing/novel_site/same_title_event_reform_plan_v2.md` - 旧計画書（この設計書に統合済み、削除してOK）

---

## 🚀 9. 次のステップ

**承認いただけましたら、ステップ1から実装開始します！**

1. **ステップ1**: データベース準備（1日）
2. **ステップ2**: エントリー制廃止＋同タイトル崩れ（2日）
3. **ステップ3**: 一番盾＋自分の提案除外（1日）
4. **ステップ4**: プロフィール＋祭り設定画面（1日）
5. **ステップ5**: プロモーション・通知システム（2日）

**合計実装期間**: 7日間（約1週間）

---

## 🔥🔥🔥 11. 一番槍判定ロジック（2025-10-14追記・超重要）

### 背景
- けーにもーんの指示により、一番槍判定ロジックを完全確定

### 一番槍判定の絶対ルール

#### ルール1：same_title_event_monthで判定
- **投稿日の月ではなく、same_title_event_month（提案月の翌月）で判定**
- 例：2025年4月に提案されたタイトル → 2025年5月が対象月（same_title_event_month='2025-05'）

#### ルール2：過去の提案も執筆可能
- **2025年10月に2025年5月のタイトルを書いても、2025年5月の一番槍候補になる**
- 投稿日に関係なく、same_title_event_monthで一番槍を決定

#### ルール3：最も早いpublished_dateが一番槍
- 同じsame_title_event_month・同じタイトルで複数投稿がある場合
- 最も早いpublished_dateの投稿が一番槍

#### ルール4：一番槍がいる月はタイトル固定
- **すでに一番槍がいる月は、その一番槍のタイトルでしか書けない**
- 例：2025年5月に「恋の物語」で一番槍が決定
  - ✅ 2025年10月に「恋の物語」で執筆 → 2025年5月の同タイトル参加者
  - ❌ 2025年10月に「夜の殺人」で執筆 → 2025年5月のタイトルではないため不可

### 実装ロジック

#### all_same_title_novels view（一番槍表示）
```python
# タイトル・イベント月ごとにグループ化
novels_by_title_event_month = defaultdict(list)
for novel in novels:
    # same_title_event_month（提案月の翌月）でグループ化
    event_month = novel.same_title_event_month
    if event_month:
        title_month_key = (novel.title, event_month)
        novels_by_title_event_month[title_month_key].append(novel)

# 各グループで最古のpublished_dateの投稿を特定
for (title, event_month), group_novels in novels_by_title_event_month.items():
    earliest_novel = min(group_novels, key=lambda n: n.published_date)
    ichiban_yari_ids.add(earliest_novel.id)
```

#### post_or_edit_same_title view（タイトル選択制限）
```python
# 過去の全提案を取得
all_proposals = TitleProposal.objects.all().select_related('proposer')

# 一番槍が既にいる月を特定
months_with_ichiban_yari = MonthlySameTitleInfo.objects.values_list('month', 'title')

# タイトル選択肢を生成
title_choices = []
for proposal in all_proposals:
    proposal_month = proposal.proposal_month.strftime('%Y-%m')

    # この月に一番槍がいるか確認
    ichiban_yari_info = next(
        (info for info in months_with_ichiban_yari if info[0] == proposal_month),
        None
    )

    if ichiban_yari_info:
        # 一番槍がいる月 → 一番槍のタイトルのみ選択可能
        if proposal.title == ichiban_yari_info[1]:
            title_choices.append((proposal.title, proposal.title))
    else:
        # 一番槍がいない月 → 全ての提案から選択可能
        title_choices.append((proposal.title, proposal.title))
```

### 具体例

#### ケース1：過去のタイトルを今から書く
- 2017年4月に「夢老い人」が提案される（same_title_event_month='2017-04'）
- 2017年4月15日にユーザーAが投稿 → 一番槍
- 2025年10月14日にユーザーBが「夢老い人」で投稿 → 2017年4月の同タイトル参加者（一番槍ではない）

#### ケース2：一番槍がいない月のタイトルを選ぶ
- 2025年5月に「恋の物語」「夜の殺人」「朝の光」が提案される
- まだ誰も投稿していない
- ユーザーAは3つのタイトルから自由に選べる
- ユーザーAが「恋の物語」で投稿 → 一番槍確定

#### ケース3：一番槍がいる月のタイトルを選ぶ
- 2025年5月に「恋の物語」で一番槍が決定済み
- ユーザーBは「恋の物語」のみ選択可能
- 「夜の殺人」「朝の光」は選択不可（一番槍がいない別タイトル）

---

## 📝 10. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|----------|---------|
| 2025-10-13 | 1.0 FINAL | 初版作成（全7項目統合版） |
| 2025-10-14 | 1.1 | 一番槍判定ロジック追記（same_title_event_month基準、タイトル選択制限） |
| 2025-10-14 | 1.2 | 「俺もこのタイトルで作る」ボタン表示条件修正、募集タイトル除外 |
| 2025-10-15 | 1.3 | **🔥 URL日本語パラメータ完全削除（けーにもーん指示）** - ボタンURLから`?title={{ novel.title\|urlencode }}`削除、MonthlySameTitleInfoから今月の一番槍タイトルを自動取得する仕様に変更 |

---

## 🔥🔥🔥 12. 「俺もこのタイトルで作る」ボタン表示条件（2025-10-14追記・超重要）

### 背景
- けーにもーんの指摘により、ボタン表示条件を修正
- 未公開（draft）の編集画面にボタンが表示されてた問題を解決
- **🔥 2025-10-15追記**: けーにもーんの「日本語URL絶対ダメ！」指示により、URLパラメータを完全削除

### ボタン表示の絶対ルール

#### 表示条件
「俺もこのタイトルで作る」ボタンは以下の条件を**全て満たす場合のみ**表示:

1. **公開済み（status='published'）の小説であること**
2. **同タイトルゲーム（event='同タイトル'）であること**
3. **ログインしていること（user.is_authenticated）**

#### 表示場所
- **小説詳細画面のみ**（novel_detail.html / novel_detail_section.html）
- 編集画面（post_or_edit_novel.html）には表示しない

#### 自分の小説でもOK
- **自分が公開した同タイトル小説でもボタンを表示**
- 理由：創作意欲が高まり、同じタイトルでもう一度書きたくなることがある

#### 具体例：山田さんのケース
1. 山田さんが今月の同タイトルで一番槍「恋の物語」を公開投稿
2. 山田さん自身が自分の公開した小説の詳細画面を見る
3. 「俺もこのタイトルで作る」ボタンが表示される
4. ボタンをクリックすると、新規作成ページに遷移（**URLパラメータなし**）
5. view関数がMonthlySameTitleInfoから今月の一番槍タイトル「恋の物語」を自動取得
6. テンプレートで固定青枠表示（編集不可）

### 実装コード

**テンプレート**: `templates/novels/novel_detail_section.html`

```django
<!-- 「俺もこのタイトルで作る」ボタン（公開済みの同タイトル小説の詳細画面のみ表示） -->
{% if novel.event == '同タイトル' and novel.status == 'published' and user.is_authenticated %}
    <div class="same-title-button-container" style="margin-top: 15px; margin-bottom: 15px; margin-left: 0.5rem;">
        <a href="{% url 'novels:post_novel' %}" class="btn same-title-button" style="display: inline-flex; align-items: center; height: 38px; line-height: 26px; padding: 5px 15px; font-size: 20px; border-radius: 20px; background-color: #ff6b6b; color: white; text-decoration: none; transition: background-color 0.3s;">
            <span>俺もこのタイトルで作る</span>
        </a>
    </div>
{% endif %}
```

### 修正前の問題点
1. **未公開（draft）の編集画面にもボタンが表示**
   - 保存しただけの下書き状態でボタンが出てた
   - 自分の編集画面に「俺もこのタイトルで作る」ボタンはおかしい

2. **status チェックなし**
   - `novel.event == '同タイトル'` だけで判定してた
   - `novel.status == 'published'` 条件が欠けてた

### 修正後の仕様
1. **公開済み（published）の詳細画面のみ表示**
2. **自分の小説でも他人の小説でも、公開されてればOK**
3. **未公開（draft）の編集画面には表示しない**
4. **🔥 URL日本語パラメータなし（2025-10-15追記）**: ボタンURLから`?title={{ novel.title|urlencode }}`を完全削除、代わりにview関数でMonthlySameTitleInfoから今月の一番槍タイトルを自動取得

---

## 🔥🔥🔥 13. 過去の同タイトル一覧から募集タイトル除外（2025-10-14追記・超重要）

### 背景
- けーにもーんの指摘により、「募集します」を含むタイトルを除外
- これは小説ではなく募集告知なので、同タイトル一覧から除外すべき

### 除外ルール

#### 除外対象
- **タイトルに「募集します」を含む投稿**
- これらは同タイトルゲームの募集告知であり、小説ではない

#### 実装コード

**View**: `game_same_title/views.py` の `all_same_title_novels` 関数

```python
def all_same_title_novels(request):
    """
    過去の同タイトル小説を全て表示
    「募集します」を含むタイトルは除外
    """
    novels = Novel.objects.filter(
        is_same_title_game=True,
        status='published'
    ).exclude(
        title__contains='募集します'  # 🆕 募集告知を除外
    ).order_by('-published_date').select_related('author')

    # ... （以降のコードは省略）
```

### 効果
- **過去の同タイトル一覧が整理される**
- **募集告知（小説ではない）が表示されなくなる**
- **ユーザーが本当の小説だけを見れる**

---

**この設計書は、けーにもーんが「これだけ見れば全部わかる」状態にした確定版です。**
**旧計画書（same_title_event_reform_plan_v2.md）の内容を完全統合しました。**
**統合後は旧計画書を削除してOKです。**
