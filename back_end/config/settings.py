import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-master-rag-backend-secret-key')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't', 'yes')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '*').split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api',
    'apps.documents',
    'apps.workflows_api',
    'apps.health',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database Configuration with DATABASE_URL or SQLite fallback
DATABASE_URL = os.getenv('DATABASE_URL', '')
if DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://'):
    import urllib.parse
    url = urllib.parse.urlparse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port or 5432,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media Storage Configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',') if origin.strip()
]

# Platform Data & ChromaDB Vector Store Paths
DATA_DIR = os.getenv('DATA_DIR', str(BASE_DIR / 'data'))
DOCUMENTS_DIR = Path(DATA_DIR) / 'documents'
CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', str(BASE_DIR / 'data' / 'chroma'))
CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'user_knowledge_base')
HF_HOME = os.getenv('HF_HOME', str(BASE_DIR / 'data' / 'models' / 'huggingface'))

# Ensure directories exist
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
Path(HF_HOME).mkdir(parents=True, exist_ok=True)

# Celery & Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# Multi-LLM Provider & Model Configurations
EMBEDDING_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'ollama')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

LLM_A_PROVIDER = os.getenv('LLM_A_PROVIDER', 'ollama')
LLM_A_MODEL = os.getenv('LLM_A_MODEL', 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0')

LLM_B_PROVIDER = os.getenv('LLM_B_PROVIDER', 'ollama')
LLM_B_MODEL = os.getenv('LLM_B_MODEL', 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0')

EVALUATOR_PROVIDER = os.getenv('EVALUATOR_PROVIDER', 'ollama')
EVALUATOR_MODEL = os.getenv('EVALUATOR_MODEL', 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0')

# Ollama local settings
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_LLAMA_MODEL = os.getenv('OLLAMA_LLAMA_MODEL', 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0')
OLLAMA_QWEN_MODEL = os.getenv('OLLAMA_QWEN_MODEL', 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0')
DEFAULT_LLM = os.getenv('DEFAULT_LLM', 'llama')

# RAG & Graph Retries thresholds
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 150))
TOP_K = int(os.getenv('TOP_K', 5))
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.70))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 2))
MAX_WORKFLOW_ITERATIONS = int(os.getenv('MAX_WORKFLOW_ITERATIONS', 10))
MAX_DRAFT_RETRIES = int(os.getenv('MAX_DRAFT_RETRIES', 2))
MAX_RETRIEVAL_RETRIES = int(os.getenv('MAX_RETRIEVAL_RETRIES', 2))

