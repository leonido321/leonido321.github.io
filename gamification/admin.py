from django.contrib import admin
from .models import (
    Task, Prize, UserProfile, Battle, BattleType, BattleResult,
    PerformanceData, Notification, Purchase, TaskCompletion,
    Group, Level, UserProgress
)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'stars', 'group')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('group',)


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'stars_required', 'bonus_stars')
    list_filter = ('group',)
    search_fields = ('name',)


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_level', 'stars_earned')
    search_fields = ('user__username',)
    list_filter = ('current_level__group',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'stars_reward', 'task_type')
    search_fields = ('title',)
    list_filter = ('task_type',)


@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost_in_stars', 'created_at')
    search_fields = ('name',)


@admin.register(BattleType)
class BattleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Battle)
class BattleAdmin(admin.ModelAdmin):
    list_display = ('name', 'battle_type', 'start_time', 'end_time', 'active')
    list_filter = ('active', 'battle_type')
    filter_horizontal = ('participants',)
    date_hierarchy = 'start_time'


@admin.register(BattleResult)
class BattleResultAdmin(admin.ModelAdmin):
    list_display = ('battle', 'user', 'score', 'position')
    list_filter = ('battle', 'position')
    search_fields = ('user__username',)


@admin.register(PerformanceData)
class PerformanceDataAdmin(admin.ModelAdmin):
    list_display = ('date_uploaded', 'processed')
    list_filter = ('processed',)
    date_hierarchy = 'date_uploaded'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active', 'battle')
    list_filter = ('is_active',)
    search_fields = ('title', 'message')
    raw_id_fields = ('battle',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'prize', 'purchased_at')
    search_fields = ('user__username', 'prize__name')
    date_hierarchy = 'purchased_at'


@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'completed_at', 'stars_awarded')
    search_fields = ('user__username', 'task__title')
    date_hierarchy = 'completed_at'