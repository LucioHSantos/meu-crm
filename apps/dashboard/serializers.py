from rest_framework import serializers
from apps.contacts.models import Contact
from apps.deals.models import Deal
from apps.tasks.models import Task


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class DealSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    assigned_to_username = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = '__all__'

    def get_assigned_to_username(self, obj):
        return obj.assigned_to.username if obj.assigned_to else None


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_username = serializers.SerializerMethodField()
    contact_name = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'

    def get_assigned_to_username(self, obj):
        return obj.assigned_to.username if obj.assigned_to else None

    def get_contact_name(self, obj):
        return obj.contact.name if obj.contact else None
