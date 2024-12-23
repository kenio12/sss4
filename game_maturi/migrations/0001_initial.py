# Generated by Django 4.2.16 on 2024-11-21 13:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('novels', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Phrase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=100, verbose_name='語句')),
            ],
        ),
        migrations.CreateModel(
            name='MaturiGame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, unique=True, verbose_name='タイトル')),
                ('description', models.TextField(verbose_name='説明')),
                ('start_date', models.DateField(verbose_name='開始日')),
                ('end_date', models.DateField(verbose_name='終了日')),
                ('prediction_start_date', models.DateField(verbose_name='作者予想の開始日')),
                ('prediction_end_date', models.DateField(verbose_name='作者予想の終了日')),
                ('entry_start_date', models.DateField(blank=True, null=True)),
                ('entry_end_date', models.DateField(blank=True, null=True)),
                ('maturi_start_date', models.DateField(blank=True, null=True, verbose_name='祭り開始日')),
                ('maturi_end_date', models.DateField(blank=True, null=True, verbose_name='祭り終了日')),
                ('year', models.CharField(choices=[('2024年〜2025年の祭り', '2024年〜2025年の祭り'), ('2025年〜2026年の祭り', '2025年〜2026年の祭り'), ('2026年〜2027年の祭り', '2026年〜2027年の祭り'), ('2027年〜2028年の祭り', '2027年〜2028年の祭り'), ('2028年〜2029年の祭り', '2028年〜2029年の祭り'), ('2029年〜2030年の祭り', '2029年〜2030年の祭り'), ('2030年〜2031年の祭り', '2030年〜2031年の祭り'), ('2031年〜2032年の祭り', '2031年〜2032年の祭り'), ('2032年〜2033年の祭り', '2032年〜2033年の祭り'), ('2033年〜2034年の祭り', '2033年〜2034年の祭り'), ('2034年〜2035年の祭り', '2034年〜2035年の祭り'), ('2035年〜2036年の祭り', '2035年〜2036年の祭り'), ('2036年〜2037年の祭り', '2036年〜2037年の祭り'), ('2037年〜2038年の祭り', '2037年〜2038年の祭り'), ('2038年〜2039年の祭り', '2038年〜2039年の祭り'), ('2039年〜2040年の祭り', '2039年〜2040年の祭り'), ('2040年〜2041年の祭り', '2040年〜2041年の祭り'), ('2041年〜2042年の祭り', '2041年〜2042年の祭り'), ('2042年〜2043年の祭り', '2042年〜2043年の祭り'), ('2043年〜2044年の祭り', '2043年〜2044年の祭り'), ('2044年〜2045年の祭り', '2044年〜2045年の祭り'), ('2045年〜2046年の祭り', '2045年〜2046年の祭り'), ('2046年〜2047年の祭り', '2046年〜2047年の祭り'), ('2047年〜2048年の祭り', '2047年〜2048年の祭り'), ('2048年〜2049年の祭り', '2048年〜2049年の祭り'), ('2049年〜2050年の祭り', '2049年〜2050年の祭り'), ('2050年〜2051年の祭り', '2050年〜2051年の祭り'), ('2051年〜2052年の祭り', '2051年〜2052年の祭り'), ('2052年〜2053年の祭り', '2052年〜2053年の祭り'), ('2053年〜2054年の祭り', '2053年〜2054年の祭り'), ('2054年〜2055年の祭り', '2054年〜2055年の祭り'), ('2055年〜2056年の祭り', '2055年〜2056年の祭り'), ('2056年〜2057年の祭り', '2056年〜2057年の祭り'), ('2057年〜2058年の祭り', '2057年〜2058年の祭り'), ('2058年〜2059年の祭り', '2058年〜2059年の祭り'), ('2059年〜2060年の祭り', '2059年〜2060年の祭り'), ('2060年〜2061年の祭り', '2060年〜2061年の祭り'), ('2061年〜2062年の祭り', '2061年〜2062年の祭り'), ('2062年〜2063年の祭り', '2062年〜2063年の祭り'), ('2063年〜2064年の祭り', '2063年〜2064年の祭り'), ('2064年〜2065年の祭り', '2064年〜2065年の祭り'), ('2065年〜2066年の祭り', '2065年〜2066年の祭り'), ('2066年〜2067年の祭り', '2066年〜2067年の祭り'), ('2067年〜2068年の祭り', '2067年〜2068年の祭り'), ('2068年〜2069年の祭り', '2068年〜2069年の祭り'), ('2069年〜2070年の祭り', '2069年〜2070年の祭り'), ('2070年〜2071年の祭り', '2070年〜2071年の祭り'), ('2071年〜2072年の祭り', '2071年〜2072年の祭り'), ('2072年〜2073年の祭り', '2072年〜2073年の祭り'), ('2073年〜2074年の祭り', '2073年〜2074年の祭り'), ('2074年〜2075年の祭り', '2074年〜2075年の祭り'), ('2075年〜2076年の祭り', '2075年〜2076年の祭り'), ('2076年〜2077年の祭り', '2076年〜2077年の祭り'), ('2077年〜2078年の祭り', '2077年〜2078年の祭り'), ('2078年〜2079年の祭り', '2078年〜2079年の祭り'), ('2079年〜2080年の祭り', '2079年〜2080年の祭り'), ('2080年〜2081年の祭り', '2080年〜2081年の祭り'), ('2081年〜2082年の祭り', '2081年〜2082年の祭り'), ('2082年〜2083年の祭り', '2082年〜2083年の祭り'), ('2083年〜2084年の祭り', '2083年〜2084年の祭り'), ('2084年〜2085年の祭り', '2084年〜2085年の祭り'), ('2085年〜2086年の祭り', '2085年〜2086年の祭り'), ('2086年〜2087年の祭り', '2086年〜2087年の祭り'), ('2087年〜2088年の祭り', '2087年〜2088年の祭り'), ('2088年〜2089年の祭り', '2088年〜2089年の祭り'), ('2089年〜2090年の祭り', '2089年〜2090年の祭り'), ('2090年〜2091年の祭り', '2090年〜2091年の祭り'), ('2091年〜2092年の祭り', '2091年〜2092年の祭り'), ('2092年〜2093年の祭り', '2092年〜2093年の祭り'), ('2093年〜2094年の祭り', '2093年〜2094年の祭り'), ('2094年〜2095年の祭り', '2094年〜2095年の祭り'), ('2095年〜2096年の祭り', '2095年〜2096年の祭り'), ('2096年〜2097年の祭り', '2096年〜2097年の祭り'), ('2097年〜2098年の祭り', '2097年〜2098年の祭り'), ('2098年〜2099年の祭り', '2098年〜2099年の祭り'), ('2099年〜2100年の祭り', '2099年〜2100年の祭り'), ('2100年〜2101年の祭り', '2100年〜2101年の祭り'), ('2101年〜2102年の祭り', '2101年〜2102年の祭り'), ('2102年〜2103年の祭り', '2102年〜2103年の祭り'), ('2103年〜2104年の祭り', '2103年〜2104年の祭り'), ('2104年〜2105年の祭り', '2104年〜2105年の祭り'), ('2105年〜2106年の祭り', '2105年〜2106年の祭り'), ('2106年〜2107年の祭り', '2106年〜2107年の祭り'), ('2107年〜2108年の祭り', '2107年〜2108年の祭り'), ('2108年〜2109年の祭り', '2108年〜2109年の祭り'), ('2109年〜2110年の祭り', '2109年〜2110年の祭り'), ('2110年〜2111年の祭り', '2110年〜2111年の祭り'), ('2111年〜2112年の祭り', '2111年〜2112年の祭り'), ('2112年〜2113年の祭り', '2112年〜2113年の祭り'), ('2113年〜2114年の祭り', '2113年〜2114年の祭り'), ('2114年〜2115年の祭り', '2114年〜2115年の祭り'), ('2115年〜2116年の祭り', '2115年〜2116年の祭り'), ('2116年〜2117年の祭り', '2116年〜2117年の祭り'), ('2117年〜2118年の祭り', '2117年〜2118年の祭り'), ('2118年〜2119年の祭り', '2118年〜2119年の祭り'), ('2119年〜2120年の祭り', '2119年〜2120年の祭り'), ('2120年〜2121年の祭り', '2120年〜2121年の祭り'), ('2121年〜2122年の祭り', '2121年〜2122年の祭り'), ('2122年〜2123年の祭り', '2122年〜2123年の祭り'), ('2123年〜2124年の祭り', '2123年〜2124年の祭り')], max_length=100, verbose_name='開催年度')),
                ('dummy_author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dummy_maturi_games', to=settings.AUTH_USER_MODEL)),
                ('entrants', models.ManyToManyField(blank=True, related_name='entered_games', to=settings.AUTH_USER_MODEL, verbose_name='エントリー参加者')),
                ('maturi_novels', models.ManyToManyField(blank=True, limit_choices_to={'genre': '祭り'}, related_name='maturi_games', to='novels.novel', verbose_name='祭りの小説')),
                ('phrases', models.ManyToManyField(blank=True, to='game_maturi.phrase', verbose_name='語句')),
            ],
        ),
        migrations.CreateModel(
            name='GamePrediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('novel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predictions', to='novels.novel')),
                ('predicted_author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_predictions', to=settings.AUTH_USER_MODEL)),
                ('predictor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='made_predictions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('novel', 'predictor')},
            },
        ),
    ]
