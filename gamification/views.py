import csv
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.utils import timezone
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from .models import Task, Prize, UserProfile, Battle, BattleType, BattleResult, PerformanceData, Notification, Purchase, TaskCompletion
from .forms import PerformanceDataForm
from django.contrib.auth import logout
from django.shortcuts import render, redirect




@login_required
def profile(request):
    """Личный кабинет"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    progress, created = UserProgress.objects.get_or_create(user=request.user)
    purchased_prizes = Purchase.objects.filter(user=request.user).order_by('-purchased_at')[:5]
    
    # Рассчитываем прогресс до следующего уровня
    next_level = None
    progress_percent = 0
    
    if progress.current_level:
        levels = Level.objects.filter(group=profile.group, stars_required__gt=progress.current_level.stars_required).order_by('stars_required')
        if levels.exists():
            next_level = levels.first()
    else:
        # Первый уровень
        first_level = Level.objects.filter(group=profile.group).order_by('stars_required').first()
        if first_level:
            next_level = first_level
    
    # Рассчитываем процент прогресса
    if next_level and next_level.stars_required > 0:
        progress_percent = (progress.stars_earned / next_level.stars_required) * 100
        progress_percent = min(progress_percent, 100)  # Не больше 100%
    
    return render(request, 'gamification/profile.html', {
        'profile': profile,
        'progress': progress,
        'next_level': next_level,
        'progress_percent': progress_percent,
        'purchased_prizes': purchased_prizes
    })

def home(request):
    """Главная страница — всегда отображается"""
    active_notifications = Notification.objects.filter(is_active=True)[:3]
    return render(request, 'gamification/home.html', {'notifications': active_notifications})


def index(request):
    """Страница с заданиями"""
    tasks = Task.objects.all()
    return render(request, 'gamification/tasks.html', {'tasks': tasks})


@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    profile = UserProfile.objects.get(user=request.user)
    
    # Проверяем, не выполнил ли пользователь это задание сегодня
    today = timezone.now().date()
    if TaskCompletion.objects.filter(
        task=task,
        user=request.user,
        completed_at__date=today
    ).exists() and task.task_type == 'daily':
        messages.error(request, 'Вы уже выполнили это задание сегодня')
    else:
        # Начисляем звезды
        profile.stars += task.stars_reward
        profile.save()
        
        # Создаем запись о выполнении
        TaskCompletion.objects.create(
            task=task,
            user=request.user,
            stars_awarded=task.stars_reward
        )
        
        # Уведомление
        Notification.objects.create(
            title=f"✅ Задание выполнено!",
            message=f"Вы получили {task.stars_reward} ⭐ за задание '{task.title}'",
            is_active=True
        )
        
        messages.success(request, f'Вы получили {task.stars_reward} ⭐ за задание!')
    
    return redirect('gamification:index')


@login_required
def profile(request):
    """Личный кабинет"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    purchased_prizes = Purchase.objects.filter(user=request.user).order_by('-purchased_at')[:5]
    return render(request, 'gamification/profile.html', {
        'profile': profile,
        'purchased_prizes': purchased_prizes
    })


@login_required
def shop(request):
    """Магазин призов"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    prizes = Prize.objects.all()
    return render(request, 'gamification/shop.html', {
        'prizes': prizes,
        'profile': profile
    })


@login_required
def purchase_prize(request, prize_id):
    """Покупка приза"""
    prize = get_object_or_404(Prize, id=prize_id)
    profile = UserProfile.objects.get(user=request.user)

    if profile.stars >= prize.cost_in_stars:
        # Списываем звёзды
        profile.stars -= prize.cost_in_stars
        profile.save()
        
        # Создаём запись о покупке
        Purchase.objects.create(user=request.user, prize=prize)
        
        messages.success(request, f'Вы успешно приобрели "{prize.name}"!')
    else:
        messages.error(request, 'Недостаточно звёзд для покупки!')

    return redirect('gamification:shop')


@login_required
def import_performance_data(request):
    """Импорт данных из CSV"""
    if not request.user.is_staff:
        return redirect('gamification:home')
    
    if request.method == 'POST':
        form = PerformanceDataForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            file_name = file.name
            file_path = default_storage.save(f'performance_data/{file_name}', file)
            
            # Проверяем, не обработан ли уже этот файл
            if PerformanceData.objects.filter(file=f'performance_data/{file_name}', processed=True).exists():
                messages.error(request, 'Этот файл уже был обработан ранее')
                return redirect('gamification:import_data')
            
            # Сохраняем запись о файле
            performance_data = PerformanceData.objects.create(
                file=f'performance_data/{file_name}',
                processed=False
            )
            
            # Обработка CSV
            with default_storage.open(file_path) as f:
                reader = csv.reader(f.read().decode('utf-8').splitlines())
                next(reader)  # Пропускаем заголовок
                
                summary = {
                    'processed': 0,
                    'total_stars': 0,
                    'skipped': 0
                }
                
                for row in reader:
                    if len(row) < 3:
                        continue
                        
                    username, tasks, quality = row[0], row[1], row[2]
                    
                    try:
                        user = User.objects.get(username=username)
                        profile = UserProfile.objects.get(user=user)
                        
                        # Начисляем звёзды
                        stars = int(tasks) + int(quality) // 2
                        profile.stars += stars
                        profile.save()
                        summary['total_stars'] += stars
                        summary['processed'] += 1
                        
                        # Уведомление
                        Notification.objects.create(
                            title="⭐ Звёзды начислены!",
                            message=f"{user.get_full_name() or user.username} получил {stars} ⭐ за эффективность!",
                            is_active=True
                        )
                    except User.DoesNotExist:
                        summary['skipped'] += 1
                        continue
            
            # Отмечаем файл как обработанный
            performance_data.processed = True
            performance_data.save()
            
            messages.success(request, f'Данные успешно обработаны! '
                                     f'Обработано: {summary["processed"]} пользователей, '
                                     f'начислено {summary["total_stars"]} звёзд. '
                                     f'Пропущено: {summary["skipped"]}')
            return redirect('gamification:profile')
    else:
        form = PerformanceDataForm()
    
    return render(request, 'gamification/import_data.html', {'form': form})


def battles(request):
    """Страница батлов"""
    active_battles = Battle.objects.filter(
        active=True, 
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    )
    upcoming_battles = Battle.objects.filter(
        active=True,
        start_time__gt=timezone.now()
    ).order_by('start_time')[:3]
    completed_battles = Battle.objects.filter(
        active=False,
        end_time__lt=timezone.now()
    ).order_by('-end_time')[:5]

    # Добавляем результаты для каждого батла
    if request.user.is_authenticated:
        for battle in active_battles:
            battle.user_result = battle.battleresult_set.filter(user=request.user).first()

    return render(request, 'gamification/battles.html', {
        'active_battles': active_battles,
        'upcoming_battles': upcoming_battles,
        'completed_battles': completed_battles
    })


@login_required
def join_battle(request, battle_id):
    """Присоединение к батлу"""
    battle = get_object_or_404(Battle, id=battle_id)
    battle.participants.add(request.user)
    
    # Создаем уведомление
    Notification.objects.create(
        title=f"Вы участвуете в батле {battle.name}",
        message=f"Батл начнётся {battle.start_time.strftime('%d.%m в %H:%M')}",
        battle=battle
    )
    
    messages.success(request, f'Вы присоединились к батлу "{battle.name}"!')
    return redirect('gamification:battles')


def leaderboard(request):
    """Таблица лидеров"""
    leaders = UserProfile.objects.order_by('-stars')[:10]
    return render(request, 'gamification/leaderboard.html', {'leaders': leaders})


def notifications(request):
    """Уведомления"""
    all_notifications = Notification.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'gamification/notifications.html', {'notifications': all_notifications})

def custom_logout(request):
    logout(request)
    return render(request, 'gamification/logout.html')