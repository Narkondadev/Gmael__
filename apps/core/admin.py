from django.contrib import admin
from apps.core.models import SharedInbox

@admin.register(SharedInbox)
class SharedInboxAdmin(admin.ModelAdmin):
    list_display = ('email_address', 'pin', 'expiry', 'created_at')
    readonly_fields = ('email_address', 'app_password', 'pin', 'expiry', 'created_at')
    
    def has_add_permission(self, request):
        # We disable manual creation! Must use the dedicated App Password flow.
        return False
        
    def has_change_permission(self, request, obj=None):
        return True # Can view the records but fields are readonly
