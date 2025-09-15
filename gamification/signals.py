from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone

from .models import UserProfile, UserProgress, Level, Notification


@receiver(post_save, sender=UserProfile)
def update_user_progress(sender, instance, created, **kwargs):
    """Обновление прогресса при изменении профиля"""
    progress, created = UserProgress.objects.get_or_create(user=instance.user)
    
    # Обновляем общее количество звезд
    progress.stars_earned = instance.stars
    progress.save()
    
    # Проверяем, достиг ли пользователь нового уровня
    if instance.group:
        levels = Level.objects.filter(group=instance.group, stars_required__lte=instance.stars).order_by('-stars_required')
        if levels.exists():
            new_level = levels.first()
            if progress.current_level != new_level:
                progress.current_level = new_level
                progress.save()
                
                # Начисляем бонусные звезды
                instance.stars += new_level.bonus_stars
                instance.save()
                
                # Создаем уведомление
                Notification.objects.create(
                    title=f"🎉 Достижение уровня {new_level.name}!",
                    message=f"Поздравляем! Вы достигли уровня '{new_level.name}' и получили {new_level.bonus_stars} ⭐ бонуса!",
                    is_active=True
                )