# Generated by Django 4.2.17 on 2024-12-27 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game_maturi', '0007_maturigame_is_author_revealed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maturigame',
            name='year',
            field=models.CharField(editable=False, max_length=100, verbose_name='開催年度'),
        ),
    ]
