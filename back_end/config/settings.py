import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-financial-intelligence-local-dev-key')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
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

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Platform Data & AI Model Storage Paths
DATA_DIR = os.getenv('DATA_DIR', str(BASE_DIR / 'data'))
DOCUMENTS_DIR = Path(DATA_DIR) / 'documents'
CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', str(BASE_DIR / 'data' / 'chroma'))
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

# AI Model Configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_LLAMA_MODEL = os.getenv('OLLAMA_LLAMA_MODEL', 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0')
OLLAMA_QWEN_MODEL = os.getenv('OLLAMA_QWEN_MODEL', 'hf.co/nulledinstance/Qwen2.5-1B-Instruct-Q8_0-GGUF:Q8_0')
DEFAULT_LLM = os.getenv('DEFAULT_LLM', 'llama')

TOP_K = int(os.getenv('TOP_K', 5))
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.70))
MAX_WORKFLOW_ITERATIONS = int(os.getenv('MAX_WORKFLOW_ITERATIONS', 10))
MAX_DRAFT_RETRIES = int(os.getenv('MAX_DRAFT_RETRIES', 2))
MAX_RETRIEVAL_RETRIES = int(os.getenv('MAX_RETRIEVAL_RETRIES', 2))
