from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('chat/', views.chat_api, name='chat_api'),
    path('chat/stream/', views.chat_stream_api, name='chat_stream_api'),
    path('vector/add/', views.vector_add_api, name='vector_add_api'),
    path('vector/search/', views.vector_search_api, name='vector_search_api'),
    path('vector/documents/', views.vector_documents_api, name='vector_documents_api'),
]
