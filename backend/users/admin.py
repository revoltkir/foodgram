from django.contrib import admin
from django.utils.html import format_html
from users.models import FoodgramUser, Subscription


@admin.register(FoodgramUser)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email', 'username', 'first_name',
        'last_name', 'avatar_preview'
    )
    list_filter = ('email', 'first_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('avatar_preview',)

    @admin.display(description='Аватар')
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" '
                'style="object-fit:cover;border-radius:5px;" />',
                obj.avatar.url)
        return "No avatar"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'date_added')
    search_fields = ('user__username', 'author__username')
    list_filter = ('date_added',)
