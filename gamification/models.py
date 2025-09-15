from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Group(models.Model):
    """Группы сотрудников (отделы, роли)"""
    name = models.CharField("Название группы", max_length=100, unique=True)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активна", default=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"


class UserProfile(models.Model):
    """Профиль пользователя с группой"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    stars = models.PositiveIntegerField("Количество звёзд", default=0)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Группа")

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.stars} ⭐"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
        ordering = ['-stars']


class Level(models.Model):
    """Уровни для разных групп"""
    name = models.CharField("Название уровня", max_length=100)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")
    stars_required = models.PositiveIntegerField("Звезд для уровня", default=100)
    bonus_stars = models.PositiveIntegerField("Бонусные звезды", default=10)
    description = models.TextField("Описание", blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.group.name})"

    class Meta:
        verbose_name = "Уровень"
        verbose_name_plural = "Уровни"


class UserProgress(models.Model):
    """Прогресс пользователя по уровням"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True)
    stars_earned = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.user} - {self.current_level}"

    class Meta:
        verbose_name = "Прогресс пользователя"
        verbose_name_plural = "Прогресс пользователей"


class Task(models.Model):
    title = models.CharField("Название задания", max_length=200)
    description = models.TextField("Описание", blank=True)
    stars_reward = models.PositiveIntegerField("Награда (звёзд)", default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    task_type = models.CharField(
        "Тип задания",
        max_length=20,
        choices=[
            ('daily', 'Ежедневное'),
            ('weekly', 'Еженедельное'),
            ('one_time', 'Разовое')
        ],
        default='daily'
    )
    
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"


class TaskCompletion(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    stars_awarded = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.user} выполнил {self.task}"
    
    class Meta:
        verbose_name = "Выполнение задания"
        verbose_name_plural = "Выполненные задания"


class Prize(models.Model):
    name = models.CharField("Название приза", max_length=200)
    cost_in_stars = models.PositiveIntegerField("Стоимость (в звёздах)")
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.cost_in_stars} ⭐)"

    class Meta:
        verbose_name = "Приз"
        verbose_name_plural = "Призы"


class BattleType(models.Model):
    """Типы батлов (можно добавлять новые)"""
    name = models.CharField("Название батла", max_length=100)
    description = models.TextField("Описание", blank=True)
    stars_reward = models.JSONField(
        "Награды (JSON: {1: 10, 2: 5})", 
        default=dict,
        help_text='Формат: {"1": 10, "2": 5, "3": 2}'
    )
    
    def __str__(self):
        return self.name


class Battle(models.Model):
    """Активный батл"""
    name = models.CharField("Название", max_length=200)
    battle_type = models.ForeignKey(BattleType, on_delete=models.CASCADE)
    start_time = models.DateTimeField("Начало")
    end_time = models.DateTimeField("Конец")
    participants = models.ManyToManyField(User, blank=True)
    active = models.BooleanField("Активен", default=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class BattleResult(models.Model):
    """Результаты батла для пользователя"""
    battle = models.ForeignKey(Battle, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField("Счёт")
    position = models.PositiveIntegerField("Место", null=True, blank=True)
    
    class Meta:
        unique_together = [['battle', 'user']]
        ordering = ['-score']


class PerformanceData(models.Model):
    """Модель для загрузки данных по эффективности сотрудников"""
    date_uploaded = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='performance_data/')
    processed = models.BooleanField("Обработан", default=False)
    notes = models.TextField("Примечания", blank=True)

    def __str__(self):
        return f"Данные от {self.date_uploaded.strftime('%d.%m.%Y')} {'(обработано)' if self.processed else '(не обработано)'}"

    class Meta:
        verbose_name = "Данные эффективности"
        verbose_name_plural = "Данные эффективности"
        ordering = ['-date_uploaded']


class Notification(models.Model):
    """Уведомления для пользователей"""
    title = models.CharField("Заголовок", max_length=200)
    message = models.TextField("Сообщение")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField("Активно", default=True)
    battle = models.ForeignKey(Battle, on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']


class Purchase(models.Model):
    """История покупок призов"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} купил {self.prize}"