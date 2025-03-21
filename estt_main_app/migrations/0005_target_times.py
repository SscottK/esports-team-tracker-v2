# Generated by Django 5.1.4 on 2025-01-02 02:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estt_main_app', '0004_game_level_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='Target_times',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('high_target', models.CharField(max_length=8)),
                ('low_target', models.CharField(max_length=8)),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='estt_main_app.level')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='estt_main_app.team')),
            ],
        ),
    ]
