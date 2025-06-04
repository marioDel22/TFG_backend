from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import JugadorViewSet, EquipoViewSet, AnuncioEquipoViewSet, AnuncioJugadorViewSet,  ChatViewSet, MensajeViewSet, ChatEquipoViewSet, MensajeChatEquipoViewSet, IniciarChatView, InvitacionViewSet, MisEquiposView, InvitacionesPendientesView, EventoCalendarioViewSet, CalendarioEquipoView,NotificacionViewSet, AnunciosCercanosView, MisEquiposCreadosView  

router = DefaultRouter()
router.register(r'jugadores', JugadorViewSet, basename='jugador')
router.register(r'equipos', EquipoViewSet, basename='equipo')
router.register(r'anuncios-equipo', AnuncioEquipoViewSet, basename='anuncio-equipo')
router.register(r'anuncios-jugador', AnuncioJugadorViewSet, basename='anuncio-jugador')
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'mensajes', MensajeViewSet, basename='mensaje')
router.register(r'chats-equipo', ChatEquipoViewSet, basename='chat-equipo')
router.register(r'mensajes-chat-equipo', MensajeChatEquipoViewSet, basename='mensaje-chat-equipo')
router.register(r'invitaciones', InvitacionViewSet, basename='invitacion')
router.register(r'eventos-calendario', EventoCalendarioViewSet, basename='evento-calendario')
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')

urlpatterns = router.urls

urlpatterns += [
    path('iniciar-chat/', IniciarChatView.as_view(), name='iniciar-chat'),
]

urlpatterns += [
    path('mis-equipos/', MisEquiposView.as_view(), name='mis-equipos'),
]

urlpatterns += [
    path('invitaciones-pendientes/', InvitacionesPendientesView.as_view(), name='invitaciones-pendientes'),
]

urlpatterns += [
    path('calendario-equipo/<int:equipo_id>/', CalendarioEquipoView.as_view(), name='calendario-equipo'),
]

urlpatterns += [
    path('anuncios-cercanos/', AnunciosCercanosView.as_view(), name='anuncios-cercanos'),
]

urlpatterns += [
    path('mis-equipos-creados/', MisEquiposCreadosView.as_view(), name='mis-equipos-creados'),
]