from rest_framework import serializers
from .models import Automation, AutomationTrigger, Contact, InstagramAccount

class InstagramAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramAccount
        fields = ['id', 'username', 'instagram_user_id', 'profile_picture_url', 
                  'followers_count', 'is_active', 'last_synced', 'created_at']
        read_only_fields = ['id', 'last_synced', 'created_at']


class AutomationSerializer(serializers.ModelSerializer):
    instagram_account_username = serializers.CharField(source='instagram_account.username', read_only=True)
    
    class Meta:
        model = Automation
        fields = '__all__'
        read_only_fields = ['id', 'total_triggers', 'total_dms_sent', 'created_at', 'updated_at']

    def validate_dm_buttons(self, value):
        """Validate button format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Buttons must be a list")
        
        for button in value:
            if not isinstance(button, dict):
                raise serializers.ValidationError("Each button must be an object")
            if 'text' not in button or 'url' not in button:
                raise serializers.ValidationError("Each button must have 'text' and 'url'")
        
        return value


class AutomationTriggerSerializer(serializers.ModelSerializer):
    automation_name = serializers.CharField(source='automation.name', read_only=True)
    
    class Meta:
        model = AutomationTrigger
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ['id', 'first_interaction', 'last_interaction']


