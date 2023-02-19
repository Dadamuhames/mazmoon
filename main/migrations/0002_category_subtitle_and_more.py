# Generated by Django 4.1 on 2023-02-19 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='subtitle',
            field=models.JSONField(blank=True, null=True, verbose_name='Subtitle'),
        ),
        migrations.AlterField(
            model_name='shortapplication',
            name='know_about_you',
            field=models.TextField(blank=True, null=True, verbose_name='About you'),
        ),
    ]