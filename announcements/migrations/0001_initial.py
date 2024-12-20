# Generated by Django 4.2.16 on 2024-12-08 00:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='タイトル')),
                ('content', models.TextField(verbose_name='お知らせ内容')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('is_active', models.BooleanField(default=True, verbose_name='有効')),
                ('created_by', models.ForeignKey(limit_choices_to={'is_staff': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='作成者')),
            ],
            options={
                'verbose_name': 'お知らせ',
                'verbose_name_plural': 'お知らせ',
                'ordering': ['-created_at'],
            },
        ),
    ]
