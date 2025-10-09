import os
import json
import jwt
import time
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.utils import timezone
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.contrib.auth.models import User
from .models import Task, Prize, UserProfile, Battle, BattleType, BattleResult, PerformanceData, Notification, Purchase, Group, Level, UserProgress

def get_iam_token():
    """
    Получение IAM-токена с использованием JSON-ключа из переменной окружения
    """
    # Получаем JSON-строку из переменной окружения
    key_json = os.getenv('YANDEX_CLOUD_SERVICE_ACCOUNT_KEY')
    
    if not key_json:
        raise Exception("YANDEX_CLOUD_SERVICE_ACCOUNT_KEY должна быть настроена в переменных окружения")
    
    try:
        key_data = json.loads(key_json)
    except json.JSONDecodeError:
        raise Exception("Неверный формат ключа в переменной окружения")
    
    # Создание JWT-токена с указанием kid в заголовке
    now = int(time.time())
    payload = {
        'iss': key_data['service_account_id'],  # ID сервисного аккаунта
        'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        'iat': now,
        'exp': now + 3600  # Токен действителен 1 час
    }
    
    # Указываем kid в заголовке JWT
    headers = {
        'kid': key_data['id']  # Используем id ключа из JSON
    }
    
    # Кодирование JWT с использованием закрытого ключа и заголовка
    token = jwt.encode(payload, key_data['private_key'], algorithm='PS256', headers=headers)
    
    # Обмен JWT на IAM-токен
    response = requests.post(
        'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        json={'jwt': token}
    )
    
    if response.status_code == 200:
        return response.json()['iamToken']
    else:
        raise Exception(f'Ошибка получения IAM-токена: {response.status_code} - {response.text}')

@login_required
def import_performance_data(request):
    if not request.user.is_staff:
        return redirect('gamification:home')
    
    try:
        # Получаем IAM-токен
        iam_token = get_iam_token()
        
        # Получаем ID дашборда из переменной окружения
        dashboard_id = os.getenv('DATALENS_DASHBOARD_ID')
        if not dashboard_id:
            raise Exception("DATALENS_DASHBOARD_ID не установлена в переменных окружения")
        
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        
        url = f'https://datalens.yandexcloud.net/api/datalens/v1/dashboards/{dashboard_id}/export?format=csv'
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f'Ошибка при получении данных: {response.status_code} - {response.text}')
        
        # Обработка CSV данных
        csv_data = response.text
        from io import StringIO
        import csv
        
        f = StringIO(csv_data)
        reader = csv.reader(f)
        next(reader)  # пропускаем заголовок
        
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
                stars = int(tasks) + int(quality) // 2
                profile.stars += stars
                profile.save()
                summary['total_stars'] += stars
                summary['processed'] += 1
                Notification.objects.create(
                    title="⭐ Звёзды начислены!",
                    message=f"{user.get_full_name() or user.username} получил {stars} ⭐ за эффективность!",
                    is_active=True
                )
            except User.DoesNotExist:
                summary['skipped'] += 1
                continue
        
        messages.success(request, f'Данные успешно обработаны! '
                                 f'Обработано: {summary["processed"]} пользователей, '
                                 f'начислено {summary["total_stars"]} звёзд. '
                                 f'Пропущено: {summary["skipped"]}')
        
    except Exception as e:
        messages.error(request, f'Ошибка при импорте данных: {str(e)}')
    
    return redirect('gamification:profile')