# Generated by Django 5.0.2 on 2025-04-05 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('reference_number', models.CharField(max_length=50, unique=True)),
                ('published_date', models.DateTimeField(auto_now_add=True)),
                ('closing_date', models.DateTimeField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('closed', 'Closed'), ('awarded', 'Awarded'), ('cancelled', 'Cancelled')], default='draft', max_length=20)),
                ('estimated_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('currency', models.CharField(default='USD', max_length=3)),
            ],
            options={
                'ordering': ['-published_date'],
            },
        ),
    ]
