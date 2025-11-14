#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from novels.models import Comment

# 小説ID 1951 のコメントで、author_id=468 のものを 496 に変更
comments = Comment.objects.filter(author_id=468, novel_id=1951)
count = comments.count()
print(f'変更対象コメント: {count}件')

for c in comments:
    print(f'コメントID {c.id}: {c.content[:50]}...')

comments.update(author_id=496)
print('完了！author_id を 468 → 496 に変更しました')
