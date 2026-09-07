from rest_framework import serializers
from .models import UserProfile, IngestedDocument, AgentExecutionLog


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'name', 'email', 'section', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class IngestedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestedDocument
        fields = [
            'id', 'user', 'original_file_name', 'normalized_file_type',
            'stored_file_path', 'chroma_collection_name', 'total_chunks',
            'ingestion_status', 'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AgentExecutionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentExecutionLog
        fields = [
            'id', 'user', 'query', 'final_output', 'retry_iterations',
            'evaluation_passed', 'hallucination_report', 'execution_status',
            'execution_duration', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PipelineRunSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    section = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    query = serializers.CharField(required=True, min_length=3)
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        default=list
    )

    def validate_query(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Query cannot be empty or whitespace only.")
        return cleaned

    def validate_files(self, value):
        allowed_extensions = {'.pdf', '.docx', '.doc', '.csv', '.txt'}
        for f in value:
            ext = '.' + f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Unsupported file format '{ext}' for file '{f.name}'. Supported formats: PDF, DOCX, DOC, CSV, TXT."
                )
            if f.size > 25 * 1024 * 1024:
                raise serializers.ValidationError(f"File '{f.name}' exceeds maximum allowed size of 25MB.")
        return value
