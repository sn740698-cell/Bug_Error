import os
import uuid
from pathlib import Path
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document
from .serializers import DocumentSerializer
from .services import document_processing_service

class DocumentUploadView(APIView):
    """
    POST /api/documents/upload/
    Uploads document file, stores locally on SSD, extracts text, chunks, and indexes into ChromaDB.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        filename = file_obj.name
        file_ext = filename.split('.')[-1].lower()
        if file_ext not in ['pdf', 'docx', 'txt']:
            return Response({'error': 'Unsupported file type. Only PDF, DOCX, and TXT are supported.'}, status=status.HTTP_400_BAD_REQUEST)

        # Save file to local SSD storage directory
        dest_dir = Path(settings.DOCUMENTS_DIR)
        dest_dir.mkdir(parents=True, exist_ok=True)
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        saved_file_path = dest_dir / unique_filename

        with open(saved_file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        # Create Document DB Record
        document = Document.objects.create(
            user=request.user if request.user.is_authenticated else None,
            filename=filename,
            file_path=str(saved_file_path),
            file_type=file_ext,
            file_size=file_obj.size,
            status='PENDING'
        )

        try:
            full_text, chunk_count = document_processing_service.process_and_index_document(document)
            serializer = DocumentSerializer(document)
            return Response({
                'message': 'Document uploaded and indexed successfully into ChromaDB',
                'document': serializer.data,
                'chunk_count': chunk_count
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'error': f'Failed to process and index document: {str(e)}',
                'document_id': str(document.id)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
