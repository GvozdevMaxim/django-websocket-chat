import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack
from api.routing import websocket_urlpatterns
from . import middleware



class TokenAuthMiddlewareWrapper:
    """
    Обертка, которая пытается аутентифицировать через токен,
    иначе использует стандартный сессионный middleware.
    """
    def __init__(self, inner):
        self.token_middleware = middleware.TokenAuthMiddleware(inner)
        self.session_stack = SessionMiddlewareStack(AuthMiddlewareStack(inner))

    async def __call__(self, scope, receive, send):
        # Проверяем, есть ли токен в query string
        query_string = scope.get('query_string', b'').decode()
        if 'token=' in query_string:
            # Если есть токен — используем TokenAuthMiddleware
            return await self.token_middleware(scope, receive, send)
        else:
            # Иначе — используем сессионный middleware (AuthMiddlewareStack)
            return await self.session_stack(scope, receive, send)


application = ProtocolTypeRouter({
    "http": get_asgi_application(),

    "websocket": TokenAuthMiddlewareWrapper(
        URLRouter(websocket_urlpatterns)
    ),
})
