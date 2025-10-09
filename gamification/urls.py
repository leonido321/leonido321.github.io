from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('', views.home, name='home'),
    path('tasks/', views.index, name='index'),
    path('profile/', views.profile, name='profile'), 
    path('tasks/complete/<int:task_id>/', views.complete_task, name='complete_task'),
    path('shop/', views.shop, name='shop'),
    path('shop/purchase/<int:prize_id>/', views.purchase_prize, name='purchase_prize'),
    path('import-data/', views.import_performance_data, name='import_data'),
    path('battles/', views.battles, name='battles'),
    path('battle/join/<int:battle_id>/', views.join_battle, name='join_battle'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('notifications/', views.notifications, name='notifications'),
    path('logout/', views.custom_logout, name='logout'),
    path('test-datalens/', views.test_datalens_connection, name='test_datalens'),
]