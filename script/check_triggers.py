import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from automations.models import AutomationTrigger, Contact

def check_triggers():
    triggers = AutomationTrigger.objects.all().order_by('-created_at')[:10]
    print(f"Total triggers: {AutomationTrigger.objects.count()}")
    for t in triggers:
        print(f"ID: {t.id} | Status: {t.status} | User: {t.instagram_username} | Created: {t.created_at}")
        
    contacts = Contact.objects.all().order_by('-last_interaction')[:10]
    print(f"\nTotal contacts: {Contact.objects.count()}")
    for c in contacts:
        print(f"ID: {c.id} | User: {c.instagram_username} | Last Interaction: {c.last_interaction}")

if __name__ == "__main__":
    check_triggers()
