from django.contrib import admin

from users.models import FoodgramUser, Subscription


@admin.register(FoodgramUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('email', 'first_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'date_added')
    search_fields = ('user__username', 'author__username')
    list_filter = ('date_added',)
