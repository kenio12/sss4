# Generated by Django 4.2.16 on 2024-11-30 02:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('game_maturi', '0005_merge_20241125_2301'),
        ('novels', '0002_novel_scheduled_at_alter_novel_genre_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='is_maturi_comment',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='comment',
            name='maturi_game',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comments', to='game_maturi.maturigame'),
        ),
        migrations.AddField(
            model_name='comment',
            name='original_commenter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='original_comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comments', to=settings.AUTH_USER_MODEL),
        ),
    ]
