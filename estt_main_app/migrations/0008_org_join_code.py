# Generated by Django 5.1.4 on 2025-02-11 01:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estt_main_app', '0007_organization_org_user_org_team'),
    ]

    operations = [
        migrations.CreateModel(
            name='Org_join_code',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20)),
                ('org', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='estt_main_app.organization')),
            ],
        ),
    ]
