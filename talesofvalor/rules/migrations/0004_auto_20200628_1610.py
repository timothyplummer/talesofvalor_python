# Generated by Django 2.2.12 on 2020-06-28 20:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rules', '0003_prerequisite'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prerequisite',
            name='header',
            field=models.ForeignKey(blank=True, help_text='What header the skills must be in.', null=True, on_delete=django.db.models.deletion.CASCADE, to='skills.Header'),
        ),
        migrations.AlterField(
            model_name='prerequisite',
            name='number_of_different_skills',
            field=models.PositiveIntegerField(blank=True, help_text='how many different skills must be purchased', null=True),
        ),
        migrations.AlterField(
            model_name='prerequisite',
            name='number_of_purchases',
            field=models.PositiveIntegerField(blank=True, help_text='How many you much purchase to me the requirement', null=True),
        ),
        migrations.AlterField(
            model_name='prerequisite',
            name='points',
            field=models.PositiveIntegerField(blank=True, help_text='how many character points', null=True),
        ),
        migrations.AlterField(
            model_name='prerequisite',
            name='skill',
            field=models.ForeignKey(blank=True, help_text='What skill must be purchased', null=True, on_delete=django.db.models.deletion.CASCADE, to='skills.Skill'),
        ),
    ]
