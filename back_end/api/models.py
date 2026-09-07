import uuid
from django.db import models


class UserProfile(models.Model):
    """Multi-tenant User Profile entity."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    section = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} <{self.email}>"


class IngestedDocument(models.Model):
    """Relational record for documents uploaded and indexed into ChromaDB."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('INDEXED', 'Indexed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='ingested_documents')
    original_file_name = models.CharField(max_length=255)
    normalized_file_type = models.CharField(max_length=50)  # PDF, DOCX, DOC, CSV, TXT
    stored_file_path = models.CharField(max_length=512)
    chroma_collection_name = models.CharField(max_length=255, default='user_knowledge_base')
    total_chunks = models.IntegerField(default=0)
    ingestion_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_file_name} [{self.normalized_file_type}] ({self.ingestion_status})"


class AgentExecutionLog(models.Model):
    """Execution audit trail for multi-agent LangGraph workflow runs."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='execution_logs')
    query = models.TextField()
    final_output = models.TextField(blank=True, default='')
    retry_iterations = models.IntegerField(default=0)
    evaluation_passed = models.BooleanField(default=False)
    hallucination_report = models.JSONField(default=dict, blank=True)
    execution_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    execution_duration = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Execution {self.id} - User {self.user.email} ({self.execution_status})"
