from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Atom1Feed
from .models import Novel

class LatestNovelsFeed(Feed):
    """最新小説のRSSフィード（Zapier自動投稿用）"""
    title = "超短編小説会 - 最新小説"
    link = "/novels/"
    description = "400文字の超短編小説投稿サイト。誰でも気軽に小説が書ける、読める、感想が書ける。"

    def items(self):
        """最新20件の公開済み小説を取得"""
        return Novel.objects.filter(status='published').order_by('-published_date')[:20]

    def item_title(self, item):
        """タイトル: 「作品名」by 作者名"""
        return f'「{item.title}」by {item.author.username}'

    def item_description(self, item):
        """本文（400文字）+ ジャンル + URL"""
        genre_text = f"ジャンル: {item.genre}"
        url = f"https://www.sss4.life/novels/{item.id}/"
        return f"{item.content}\n\n{genre_text}\n\n続きはこちら: {url}"

    def item_link(self, item):
        """各小説へのリンク"""
        return f"/novels/{item.id}/"

    def item_pubdate(self, item):
        """公開日時"""
        return item.published_date


class LatestNovelsAtomFeed(LatestNovelsFeed):
    """Atom形式のフィード（Twitter/X用）"""
    feed_type = Atom1Feed
    subtitle = LatestNovelsFeed.description
