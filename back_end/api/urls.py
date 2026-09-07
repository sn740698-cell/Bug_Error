from django.urls import path
from . import views

urlpatterns = [
    path('pipeline/run/', views.pipeline_run_api, name='pipeline_run'),
    path('users/profile/', views.user_profile_api, name='user_profile'),
    path('documents/list/', views.user_documents_api, name='user_documents'),
    path('executions/list/', views.user_executions_api, name='user_executions'),
    path('health/', views.health_check, name='health_check'),
    path('chat/', views.chat_api, name='chat_api'),
]
