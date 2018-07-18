from config.common_settings import *

DEBUG = True

DATABASES['default'].update({
    'NAME': 'mymdb',
    'USER': 'mymdb',
    'PASSWORD': 'development',
    'HOST': '127.0.0.1',
    'PORT': '5432',
})

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'default-locmemcache',
        'TIMEOUT': 5,
    }
}

# file uploads
MEDIA_ROOT = os.path.join(BASE_DIR, '../media_root')

# Django Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]
