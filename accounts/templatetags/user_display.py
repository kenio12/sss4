from django import template
from django.utils.html import format_html
from django.urls import reverse
import hashlib

register = template.Library()

@register.filter
def display_name(user):
    """ユーザーの表示名（ニックネーム）を返す"""
    if not user:
        return ''
    
    # UserProfileのdisplay_nameを確認
    try:
        if hasattr(user, 'userprofile') and user.userprofile.display_name:
            return user.userprofile.display_name
    except:
        pass
    
    # first_nameにニックネームが入ってる（旧実装）
    if user.first_name:
        return user.first_name
    
    # ニックネームが設定されていない場合はデフォルト名を返す
    return '名無しさん'

@register.filter
def display_initial(user):
    """ユーザーの頭文字を返す（日本語対応）"""
    if not user:
        return ''
    
    # display_nameを使って表示名を取得
    name = display_name(user)
    if not name:
        return ''
    
    # 最初の1文字を返す（日本語でも英語でも対応）
    return name[0] if name else ''

@register.filter
def user_color(user):
    """ユーザーごとに固定の色を生成する"""
    if not user:
        return '#667eea'  # デフォルト色
    
    # ユーザーIDをハッシュ化して色を生成
    hash_value = hashlib.md5(str(user.id).encode()).hexdigest()
    
    # 美しい色のパレット（紫系を含む）
    colors = [
        'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',  # 紫グラデーション
        'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',  # ピンク系
        'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',  # 青系
        'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',  # 緑系
        'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',  # 暖色系
        'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',  # 深い青紫
        'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',  # パステル系
        'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',  # ピンクパステル
        'linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%)',  # 薄紫系
        'linear-gradient(135deg, #fddb92 0%, #d1fdff 100%)',  # イエロー系
        'linear-gradient(135deg, #9890e3 0%, #b1f4cf 100%)',  # 紫緑系
        'linear-gradient(135deg, #ebc0fd 0%, #d9ded8 100%)',  # 薄紫グレー
    ]
    
    # ハッシュ値から色を選択
    index = int(hash_value[:2], 16) % len(colors)
    return colors[index]

@register.filter
def user_solid_color(user):
    """ユーザーごとに固定の単色を生成する（アバター用）"""
    if not user:
        return '#667eea'  # デフォルト色

    # ユーザーIDをハッシュ化して色を生成
    hash_value = hashlib.md5(str(user.id).encode()).hexdigest()

    # カスタムアイコンを設定してるか判定
    has_custom_avatar = False
    try:
        if hasattr(user, 'userprofile') and user.userprofile.avatar:
            has_custom_avatar = True
    except:
        pass

    if has_custom_avatar:
        # カスタムアイコンユーザー用の特別な40色パレット
        custom_avatar_colors = [
            '#E74C3C',  # 鮮やかな赤
            '#C0392B',  # 深い赤
            '#E67E22',  # オレンジ
            '#D35400',  # 濃いオレンジ
            '#F39C12',  # 琥珀色
            '#F1C40F',  # 黄色
            '#2ECC71',  # エメラルドグリーン
            '#27AE60',  # 深い緑
            '#1ABC9C',  # ターコイズ
            '#16A085',  # 深いターコイズ
            '#3498DB',  # 明るい青
            '#2980B9',  # 濃い青
            '#9B59B6',  # 紫
            '#8E44AD',  # 深い紫
            '#34495E',  # 濃いグレー
            '#2C3E50',  # ダークブルーグレー
            '#95A5A6',  # シルバー
            '#7F8C8D',  # 濃いシルバー
            '#EC87C0',  # ピンク
            '#BE60A6',  # 濃いピンク
            '#6DD5FA',  # スカイブルー
            '#2980B9',  # ロイヤルブルー
            '#A569BD',  # ラベンダー
            '#7D3C98',  # 濃いラベンダー
            '#48C9B0',  # ミントグリーン
            '#1ABC9C',  # シーグリーン
            '#F8B500',  # ゴールド
            '#E08E0B',  # 濃いゴールド
            '#FF6B6B',  # コーラルレッド
            '#EE5A6F',  # 濃いコーラル
            '#4ECDC4',  # シアン
            '#45B7AF',  # 濃いシアン
            '#A8E6CF',  # ライトグリーン
            '#81C784',  # 濃いライトグリーン
            '#FFD93D',  # レモンイエロー
            '#F4CA16',  # 濃いレモン
            '#6C5CE7',  # インディゴ
            '#5F27CD',  # 濃いインディゴ
            '#FD79A8',  # ローズ
            '#E84393',  # 濃いローズ
        ]
        # ハッシュ値から色を選択
        index = int(hash_value[:2], 16) % len(custom_avatar_colors)
        return custom_avatar_colors[index]
    else:
        # デフォルトアイコンユーザー用の12色パレット
        solid_colors = [
            '#667eea',  # 紫
            '#764ba2',  # 濃い紫
            '#f093fb',  # ピンク
            '#4facfe',  # 青
            '#43e97b',  # 緑
            '#fa709a',  # ローズ
            '#30cfd0',  # シアン
            '#ff9a9e',  # サーモンピンク
            '#fbc2eb',  # 薄ピンク
            '#fddb92',  # イエロー
            '#9890e3',  # 薄紫
            '#330867',  # 深い紫
        ]
        # ハッシュ値から色を選択
        index = int(hash_value[:2], 16) % len(solid_colors)
        return solid_colors[index]

@register.filter
def company_name(user):
    """ユーザーの法人名を返す（安全）"""
    if not user:
        return ''

    try:
        if hasattr(user, 'userprofile') and user.userprofile.company_name:
            return user.userprofile.company_name
    except:
        pass

    return ''

@register.simple_tag
def display_nickname_link(user, show_icon=False):
    """
    ニックネームをリンク・色付きで表示（開発者バッジ付き）

    使い方:
        {% load user_display %}
        {% display_nickname_link user %}  # 開発者バッジ付き
        {% display_nickname_link user show_icon=True %}  # 👤アイコン付き（旧互換性）
    """
    if not user:
        return ''

    # ニックネーム取得
    name = display_name(user)

    # 色取得
    color = user_solid_color(user)

    # プロフィールURL生成
    try:
        profile_url = reverse('gallery:user_profile', kwargs={'username': user.username})
    except:
        profile_url = f'/user/{user.username}/'

    # 開発者バッジを常に表示
    badge = '👨‍💻 '

    # HTMLを安全に生成（バッジ + ニックネーム）
    return format_html(
        '<a href="{}" style="color: {}; text-decoration: none; font-weight: 600; transition: opacity 0.2s;" '
        'onmouseover="this.style.opacity=\'0.7\'" onmouseout="this.style.opacity=\'1\'">'
        '{}<span style="color: {};">{}</span></a>',
        profile_url, '#666', badge, color, name
    )

@register.filter
def get_item(dictionary, key):
    """辞書から値を取得する"""
    if not dictionary:
        return None
    return dictionary.get(key)