# Generated by Django 4.2.16 on 2024-11-30 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game_maturi', '0006_gameprediction_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='maturigame',
            name='is_author_revealed',
            field=models.BooleanField(default=False, help_text='作者が公開済みの場合はTrue', verbose_name='作者公開済み'),
        ),
    ]
