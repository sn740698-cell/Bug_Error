from rest_framework import serializers
from .models import Document, DocumentChunk

class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ['id', 'chunk_id', 'page_number', 'chunk_text', 'created_at']

class DocumentSerializer(serializers.ModelSerializer):
    chunks = DocumentChunkSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'user', 'filename', 'file_path', 'file_type', 'file_size', 'status', 'created_at', 'updated_at', 'chunks']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']
