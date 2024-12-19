# Generated by Django 4.2.16 on 2024-12-08 01:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('announcements', '0002_alter_announcement_options_announcement_order_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='announcement',
            options={'ordering': ['-is_pinned', '-created_at'], 'verbose_name': 'お知らせ', 'verbose_name_plural': 'お知らせ'},
        ),
        migrations.RemoveField(
            model_name='announcement',
            name='order',
        ),
        migrations.AddField(
            model_name='announcement',
            name='is_pinned',
            field=models.BooleanField(default=False, verbose_name='固定表示'),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='作成者'),
        ),
    ]
