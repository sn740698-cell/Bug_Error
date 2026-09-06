import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.documents.models import Document

User = get_user_model()

class Workflow(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('WAITING', 'Waiting'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='workflows')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='workflows')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    current_agent = models.CharField(max_length=100, default='document_decomposer')
    current_supervisor = models.CharField(max_length=100, default='master_orchestrator')
    selected_llm = models.CharField(max_length=100, null=True, blank=True)
    document_sections = models.JSONField(default=dict, blank=True)
    simplified_summary = models.TextField(null=True, blank=True)
    fallback_used = models.BooleanField(default=False)
    failure_reason = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Workflow {self.id} ({self.status})"


class FinancialInsight(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='insights')
    field_name = models.CharField(max_length=100)
    field_value = models.JSONField(null=True, blank=True)
    confidence = models.FloatField(default=0.0)
    source = models.CharField(max_length=100, default='DataAnalyzer')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.field_name}: {self.field_value} ({self.confidence})"


class RoutingDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='routing_decisions')
    supervisor = models.CharField(max_length=100)
    selected_target = models.CharField(max_length=100)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.supervisor} -> {self.selected_target}"


class GeneratedDraft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='drafts')
    draft_text = models.TextField()
    llm_model = models.CharField(max_length=100)
    generation_attempt = models.IntegerField(default=1)
    validation_status = models.CharField(max_length=20, default='PENDING')  # PASS | FAIL | PENDING
    validation_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Draft {self.id} ({self.validation_status})"
