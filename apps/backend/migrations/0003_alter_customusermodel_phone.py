# Generated by Django 5.1.3 on 2025-05-04 22:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_alter_customusermodel_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customusermodel',
            name='phone',
            field=models.CharField(max_length=50),
        ),
    ]
