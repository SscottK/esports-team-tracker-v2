# Generated by Django 5.2 on 2025-04-16 23:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estt_main_app', '0010_gamesuggestion'),
    ]

    operations = [
        migrations.CreateModel(
            name='Diamond_times',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('diamond_target', models.CharField(max_length=9)),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='estt_main_app.level')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='estt_main_app.team')),
            ],
            options={
                'unique_together': {('level', 'team')},
            },
        ),
    ]
