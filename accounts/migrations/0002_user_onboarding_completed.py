# Generated migration file

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='onboarding_completed',
            field=models.BooleanField(default=False, help_text='Whether user has completed onboarding flow'),
        ),
    ]
