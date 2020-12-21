from .base import *

DEBUG = False
# be careful on the order of middlewares
MIDDLEWARE.insert(2, 'django.middleware.cache.UpdateCacheMiddleware')
MIDDLEWARE.insert(4, 'django.middleware.cache.FetchFromCacheMiddleware')

# set website cache time and use redis default backend for caching
CACHE_MIDDLEWARE_SECONDS = 1200
CACHE_MIDDLEWARE_ALIAS = 'default'


CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_ACCESS_KEY_ID = os.getenv('AWS_SES_ACCESS_KEY_ID')
AWS_SES_SECRET_ACCESS_KEY = os.getenv('AWS_SES_SECRET_ACCESS_KEY')
AWS_SES_REGION_NAME = os.getenv('AWS_SES_REGION_NAME')
AWS_SES_REGION_ENDPOINT = os.getenv('AWS_SES_REGION_ENDPOINT')
AWS_SES_CONFIGURATION_SET = os.getenv('AWS_SES_CONFIGURATION_SET')
