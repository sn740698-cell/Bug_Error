from django.urls import path
from .views import (
    WorkflowAnalyzeView,
    WorkflowStatusView,
    WorkflowInsightsView,
    WorkflowDraftView,
    WorkflowRegenerateView,
    WorkflowChatView
)

urlpatterns = [
    path('analyze/', WorkflowAnalyzeView.as_view(), name='workflow_analyze'),
    path('<uuid:workflow_id>/', WorkflowStatusView.as_view(), name='workflow_status'),
    path('<uuid:workflow_id>/insights/', WorkflowInsightsView.as_view(), name='workflow_insights'),
    path('<uuid:workflow_id>/draft/', WorkflowDraftView.as_view(), name='workflow_draft'),
    path('<uuid:workflow_id>/regenerate/', WorkflowRegenerateView.as_view(), name='workflow_regenerate'),
    path('<str:workflow_id>/chat/', WorkflowChatView.as_view(), name='workflow_chat'),
]
