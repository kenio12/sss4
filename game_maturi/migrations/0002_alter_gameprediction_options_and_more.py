# Generated by Django 4.2.16 on 2024-11-23 02:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('novels', '0001_initial'),
        ('game_maturi', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gameprediction',
            options={'verbose_name': '祭り予想', 'verbose_name_plural': '祭り予想一覧'},
        ),
        migrations.AlterUniqueTogether(
            name='gameprediction',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='gameprediction',
            name='maturi_game',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='predictions', to='game_maturi.maturigame', verbose_name='祭りゲーム'),
        ),
        migrations.AlterField(
            model_name='gameprediction',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='作成日時'),
        ),
        migrations.AlterField(
            model_name='gameprediction',
            name='novel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predictions', to='novels.novel', verbose_name='小説'),
        ),
        migrations.AlterField(
            model_name='gameprediction',
            name='predicted_author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_predictions', to=settings.AUTH_USER_MODEL, verbose_name='予想された作者'),
        ),
        migrations.AlterField(
            model_name='gameprediction',
            name='predictor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='made_predictions', to=settings.AUTH_USER_MODEL, verbose_name='予想者'),
        ),
        migrations.AlterField(
            model_name='gameprediction',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='更新日時'),
        ),
        migrations.AlterUniqueTogether(
            name='gameprediction',
            unique_together={('maturi_game', 'novel', 'predictor')},
        ),
    ]
