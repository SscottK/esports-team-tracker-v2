# Generated by Django 5.1.4 on 2025-04-12 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estt_main_app', '0008_org_join_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='target_times',
            name='high_target',
            field=models.CharField(max_length=9),
        ),
        migrations.AlterField(
            model_name='target_times',
            name='low_target',
            field=models.CharField(max_length=9),
        ),
        migrations.AlterField(
            model_name='time',
            name='time',
            field=models.CharField(max_length=9),
        ),
    ]
