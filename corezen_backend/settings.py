from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-corezen-secret-key-change-me'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'simpleui',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # --- 第三方库 ---
    'rest_framework',
    'corsheaders',
    # --- 我们的核心应用 ---
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # 跨域支持
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'corezen_backend.urls'

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

WSGI_APPLICATION = 'corezen_backend.wsgi.application'

# --- 核心：连接 PostgreSQL 数据库 ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'corezen',
        'USER': 'zen_admin',
        'PASSWORD': 'zen_secure_password',
        'HOST': 'db',  # Docker 内部域名
        'PORT': 5432,
    }
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'zh-hans' # 中文界面
TIME_ZONE = 'Asia/Shanghai' # 中国时间
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- 自定义用户模型 ---
AUTH_USER_MODEL = 'core.CustomUser'

# --- 图片存储路径 (映射到腾讯云硬盘) ---
MEDIA_URL = '/uploads/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
# --- SimpleUI 个性化配置 (加在文件最后) ---
SIMPLEUI_HOME_INFO = False  # 关闭首页广告
SIMPLEUI_ANALYSIS = False   # 关闭分析
SIMPLEUI_LOGO = 'https://i.ibb.co/5xbz0qj/logo.png' # 这里以后可以换成你的 Corezen Logo
SIMPLEUI_DEFAULT_THEME = 'admin.lte.css' # 默认深色主题
# SimpleUI 优化配置
SIMPLEUI_HOME_INFO = False 
SIMPLEUI_ANALYSIS = False
SIMPLEUI_DEFAULT_ICON = False
# 关键：在左侧菜单增加一个“返回工作台”的按钮
SIMPLEUI_CONFIG = {
    'system_keep': True,
    'dynamic_menus': [{
        'name': '🔙 返回工作台',
        'url': '/',
        'icon': 'fa fa-home'
    }]
}