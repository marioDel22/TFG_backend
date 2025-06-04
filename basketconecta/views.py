from django.shortcuts import render
from haversine import haversine, Unit
from django.db import models
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status,filters   
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import Jugador
from .models import AnuncioEquipo
from .models import AnuncioJugador
from .models import Equipo, Chat, Mensaje, Invitacion, EventoCalendario, Notificacion, ChatEquipo, MensajeChatEquipo
from .serializers import JugadorSerializer
from .serializers import EquipoSerializer, AnuncioEquipoSerializer, AnuncioJugadorSerializer, ChatSerializer, MensajeSerializer, InvitacionSerializer, EventoCalendarioSerializer, NotificacionSerializer, ChatEquipoSerializer, MensajeChatEquipoSerializer   



class EsDueñoDelAnuncioJugador(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Permitir lectura (GET, HEAD, OPTIONS) a todos los autenticados
        if request.method in permissions.SAFE_METHODS:
            return True
        # Solo permitir edición/eliminación al dueño
        return obj.jugador.user == request.user

class AnuncioJugadorViewSet(viewsets.ModelViewSet):
    serializer_class = AnuncioJugadorSerializer
    permission_classes = [permissions.IsAuthenticated, EsDueñoDelAnuncioJugador]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'sexo': ['exact'],
        'disponibilidad_dia': ['exact'],
        'disponibilidad_horaria': ['exact'],
        'jugador__posicion': ['exact'],
        'jugador__altura': ['gte', 'lte'],
        'jugador__nivel': ['exact'],
    }

    def get_queryset(self):
        return AnuncioJugador.objects.all()

    def perform_create(self, serializer):
        jugador = serializer.validated_data['jugador']
        if jugador.user != self.request.user:
            raise serializers.ValidationError("Solo puedes crear un anuncio con tu propio jugador.")
        if AnuncioJugador.objects.filter(jugador=jugador).exists():
            raise serializers.ValidationError("Este jugador ya tiene un anuncio publicado.")
        serializer.save()

class EsCreadorDelEquipo(permissions.BasePermission):
    """
    Permite lectura a todos los equipos pero solo modificación/eliminación a equipos creados por el usuario.
    """
    def has_object_permission(self, request, view, obj):
        # Permitir lectura (GET, HEAD, OPTIONS) a todos
        if request.method in permissions.SAFE_METHODS:
            return True
        # Solo permitir escritura al creador
        return obj.creador == request.user

class EquipoViewSet(viewsets.ModelViewSet):
    serializer_class = EquipoSerializer
    permission_classes = [permissions.IsAuthenticated, EsCreadorDelEquipo]

    def get_queryset(self):
        return Equipo.objects.all()

    def perform_create(self, serializer):
        serializer.save(creador=self.request.user)

class EsDueñoDelJugador(permissions.BasePermission):
    """
    Permite acceso solo al propietario del perfil de jugador.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class JugadorViewSet(viewsets.ModelViewSet):
    serializer_class = JugadorSerializer
    permission_classes = [permissions.IsAuthenticated, EsDueñoDelJugador]

    def get_queryset(self):
        # Solo el jugador del usuario autenticado
        return Jugador.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Verificar que el usuario no tenga ya un jugador
        if Jugador.objects.filter(user=request.user).exists():
            return Response({"detail": "Ya tienes un perfil de jugador."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class EsCreadorDelAnuncioEquipo(permissions.BasePermission):
    """
    Solo el creador del equipo puede crear/modificar su anuncio.
    """

    def has_object_permission(self, request, view, obj):
        return obj.equipo.creador == request.user

class AnuncioEquipoViewSet(viewsets.ModelViewSet):
    serializer_class = AnuncioEquipoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'dia_partido': ['exact'],
        'horario_partido': ['exact'],
        'dia_entrenamiento': ['exact'],
        'horario_entrenamiento': ['exact'],
        'equipo__sexo': ['exact'],
        'equipo__categoria': ['exact'],
    }

    def get_queryset(self):
        queryset = AnuncioEquipo.objects.all()
        lat = self.request.query_params.get('latitud')
        lon = self.request.query_params.get('longitud')
        distancia = self.request.query_params.get('distancia')
        print(f"Parámetros recibidos: lat={lat}, lon={lon}, distancia={distancia}")
        if lat and lon and distancia:
            from math import radians, cos, sin, asin, sqrt
            lat = float(lat)
            lon = float(lon)
            distancia = float(distancia)

            def haversine(lat1, lon1, lat2, lon2):
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                r = 6371
                return c * r

            ids = [
                anuncio.id for anuncio in queryset
                if anuncio.latitud_partido and anuncio.longitud_partido and
                haversine(lat, lon, anuncio.latitud_partido, anuncio.longitud_partido) <= distancia
            ]
            queryset = queryset.filter(id__in=ids)
        return queryset

    def perform_create(self, serializer):
        equipo = serializer.validated_data['equipo']
        if equipo.creador != self.request.user:
            raise serializers.ValidationError("Solo puedes publicar anuncios de tus propios equipos.")
        if AnuncioEquipo.objects.filter(equipo=equipo).exists():
            raise serializers.ValidationError("Este equipo ya tiene un anuncio publicado.")
        serializer.save()

class ChatViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Chat.objects.filter(
            models.Q(jugador__user=user) |
            models.Q(equipo__creador=user)
        )
        anuncio_equipo_id = self.request.query_params.get('anuncio_equipo')
        if anuncio_equipo_id:
            queryset = queryset.filter(anuncio_equipo_id=anuncio_equipo_id)
        return queryset


class MensajeViewSet(viewsets.ModelViewSet):
    serializer_class = MensajeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        chat_id = self.request.query_params.get('chat')
        if chat_id:
            # Solo permitir si el usuario es participante del chat
            from .models import Chat
            try:
                chat = Chat.objects.get(id=chat_id)
            except Chat.DoesNotExist:
                return Mensaje.objects.none()
            if chat.jugador.user != user and chat.equipo.creador != user:
                return Mensaje.objects.none()
            return Mensaje.objects.filter(chat=chat).order_by('timestamp')
        return Mensaje.objects.filter(emisor=user).order_by('timestamp')

    def perform_create(self, serializer):
        chat = serializer.validated_data['chat']
        user = self.request.user
        print(f"[DEBUG] Usuario autenticado: {user.username} (ID: {user.id})")
        print(f"[DEBUG] Creador del equipo del chat: {chat.equipo.creador.username} (ID: {chat.equipo.creador.id})")
        print(f"[DEBUG] Jugador del chat: {chat.jugador.user.username} (ID: {chat.jugador.user.id})")
        if chat.jugador.user != user and chat.equipo.creador != user:
            print(f"[DEBUG] Permiso denegado para usuario {user.username}")
            raise PermissionDenied("No puedes escribir en este chat.")
        serializer.save(emisor=user)

class IniciarChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        jugador_id = request.data.get("jugador_id")
        equipo_id = request.data.get("equipo_id")

        if not jugador_id or not equipo_id:
            return Response({"error": "Faltan jugador_id o equipo_id."}, status=status.HTTP_400_BAD_REQUEST)

        jugador = get_object_or_404(Jugador, id=jugador_id)
        equipo = get_object_or_404(Equipo, id=equipo_id)

        print(f"[DEBUG] Usuario autenticado: {request.user} (ID: {request.user.id})")
        print(f"[DEBUG] Equipo recibido: {equipo.id}, creador: {equipo.creador} (ID: {equipo.creador.id})")

        # Buscar si ya existe
        chat, created = Chat.objects.get_or_create(jugador=jugador, equipo=equipo)

        # Vincular anuncios si existen y no están ya asignados
        anuncio_jugador = getattr(jugador, 'anuncio', None)
        anuncio_equipo = getattr(equipo, 'anuncio', None)
        changed = False
        if anuncio_jugador and chat.anuncio_jugador != anuncio_jugador:
            chat.anuncio_jugador = anuncio_jugador
            changed = True
        if anuncio_equipo and chat.anuncio_equipo != anuncio_equipo:
            chat.anuncio_equipo = anuncio_equipo
            changed = True
        if changed:
            chat.save()

        return Response({
            "chat_id": chat.id,
            "creado": created
        }, status=status.HTTP_200_OK)


class InvitacionViewSet(viewsets.ModelViewSet):
    serializer_class = InvitacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Invitacion.objects.filter(
            models.Q(equipo__creador=user) | models.Q(jugador__user=user)
        )
        equipo_id = self.request.query_params.get('equipo')
        jugador_id = self.request.query_params.get('jugador')
        if equipo_id:
            queryset = queryset.filter(equipo_id=equipo_id)
        if jugador_id:
            queryset = queryset.filter(jugador_id=jugador_id)
        return queryset

    def perform_create(self, serializer):
        equipo = serializer.validated_data['equipo']
        jugador = serializer.validated_data['jugador']

        if equipo.creador != self.request.user:
            raise serializers.ValidationError("No puedes enviar invitaciones con equipos que no te pertenecen.")

        # Solo permitir crear si NO existe una invitación pendiente o aceptada
        if Invitacion.objects.filter(equipo=equipo, jugador=jugador, estado__in=['pendiente', 'aceptada']).exists():
            raise serializers.ValidationError("Ya existe una invitación pendiente o aceptada para este jugador y equipo.")

        invitacion = serializer.save()

        # Crear notificación para el jugador
        Notificacion.objects.create(
            usuario=jugador.user,
            mensaje=f"Has recibido una invitación del equipo {equipo.nombre}"
        )

    def perform_update(self, serializer):
        invitacion = self.get_object()
        user = self.request.user

        if invitacion.jugador.user != user:
            raise serializers.ValidationError("Solo el jugador invitado puede aceptar o rechazar esta invitación.")

        nueva_estado = self.request.data.get('estado')

        if nueva_estado == 'aceptada':
            equipo = invitacion.equipo
            jugador = invitacion.jugador

            if jugador in equipo.jugadores.all():
                raise serializers.ValidationError("El jugador ya pertenece al equipo.")

            equipo.jugadores.add(jugador)

        # Crear notificación para el creador del equipo
            Notificacion.objects.create(
                usuario=equipo.creador,
                mensaje=f"El jugador {jugador.nombre} ha aceptado tu invitación para unirse al equipo {equipo.nombre}"
            )

        serializer.save()

class MisEquiposView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jugador = get_object_or_404(Jugador, user=request.user)
        equipos = jugador.equipos.all()  # relación M:N
        serializer = EquipoSerializer(equipos, many=True)
        return Response(serializer.data)
    
class InvitacionesPendientesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jugador = get_object_or_404(Jugador, user=request.user)
        invitaciones = Invitacion.objects.filter(jugador=jugador, estado='pendiente')
        serializer = InvitacionSerializer(invitaciones, many=True)
        return Response(serializer.data)
    
class EventoCalendarioViewSet(viewsets.ModelViewSet):
    serializer_class = EventoCalendarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return EventoCalendario.objects.filter(equipo__creador=user)

    def perform_create(self, serializer):
        equipo = serializer.validated_data['equipo']
        if equipo.creador != self.request.user:
            raise serializers.ValidationError("No puedes crear eventos para un equipo que no te pertenece.")
        serializer.save()

class CalendarioEquipoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, equipo_id):
        equipo = get_object_or_404(Equipo, id=equipo_id)

        # Validar que el usuario sea miembro del equipo (jugador) o su creador
        if request.user != equipo.creador and not equipo.jugadores.filter(user=request.user).exists():
            return Response({"detail": "No tienes acceso a este calendario."}, status=status.HTTP_403_FORBIDDEN)

        eventos = equipo.eventos.all().order_by('fecha', 'hora')
        serializer = EventoCalendarioSerializer(eventos, many=True)
        return Response(serializer.data)
    
class NotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user).order_by('-creada')

    def perform_update(self, serializer):
        # Solo permite marcar como leída
        serializer.save()

class AnunciosCercanosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            distancia_max_km = float(request.query_params.get('distancia', 5))  # valor por defecto: 5 km
            jugador = get_object_or_404(Jugador, user=request.user)

            # Información de depuración del jugador
            debug_info = {
                "jugador_id": jugador.id,
                "jugador_nombre": jugador.nombre,
                "coordenadas_jugador": {
                    "latitud": jugador.latitud,
                    "longitud": jugador.longitud
                }
            }

            if not jugador.latitud or not jugador.longitud:
                return Response({
                    "error": "Tu perfil de jugador no tiene coordenadas registradas.",
                    "debug_info": debug_info
                }, status=400)

            anuncios_cercanos = []
            todos_los_anuncios = []
            posicion_jugador = (jugador.latitud, jugador.longitud)
            total_anuncios = AnuncioEquipo.objects.count()
            anuncios_con_coordenadas = 0

            for anuncio in AnuncioEquipo.objects.all():
                if anuncio.latitud_partido and anuncio.longitud_partido:
                    anuncios_con_coordenadas += 1
                    posicion_anuncio = (anuncio.latitud_partido, anuncio.longitud_partido)
                    
                    # Calcular distancia usando haversine
                    distancia = haversine(
                        (float(jugador.latitud), float(jugador.longitud)),
                        (float(anuncio.latitud_partido), float(anuncio.longitud_partido)),
                        unit=Unit.KILOMETERS
                    )
                    
                    anuncio_data = AnuncioEquipoSerializer(anuncio).data
                    anuncio_data['distancia'] = round(distancia, 2)
                    anuncio_data['posicion_jugador'] = posicion_jugador
                    anuncio_data['posicion_anuncio'] = posicion_anuncio
                    todos_los_anuncios.append(anuncio_data)

                    # Solo añadir si está dentro del radio
                    if distancia <= distancia_max_km:
                        anuncios_cercanos.append(anuncio_data)

            # Añadir información de depuración
            debug_info.update({
                "total_anuncios": total_anuncios,
                "anuncios_con_coordenadas": anuncios_con_coordenadas,
                "distancia_maxima_km": distancia_max_km,
                "anuncios_cercanos_encontrados": len(anuncios_cercanos)
            })

            return Response({
                "anuncios_cercanos": anuncios_cercanos,
                "todos_los_anuncios": todos_los_anuncios,
                "debug_info": debug_info
            })

        except Exception as e:
            return Response({
                "error": str(e),
                "debug_info": debug_info if 'debug_info' in locals() else None
            }, status=500)

class MisEquiposCreadosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        equipos = Equipo.objects.filter(creador=request.user)
        serializer = EquipoSerializer(equipos, many=True)
        return Response(serializer.data)

class ChatEquipoViewSet(viewsets.ModelViewSet):
    serializer_class = ChatEquipoSerializer
    permission_classes = [IsAuthenticated]
    queryset = ChatEquipo.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        equipo_id = self.request.query_params.get('equipo')
        if equipo_id:
            queryset = queryset.filter(equipo_id=equipo_id)
        return queryset

    def perform_create(self, serializer):
        # Solo crear si no existe ya un chat grupal para el equipo
        equipo = serializer.validated_data['equipo']
        if ChatEquipo.objects.filter(equipo=equipo).exists():
            raise serializers.ValidationError('Ya existe un chat grupal para este equipo.')
        serializer.save()

class MensajeChatEquipoViewSet(viewsets.ModelViewSet):
    serializer_class = MensajeChatEquipoSerializer
    permission_classes = [IsAuthenticated]
    queryset = MensajeChatEquipo.objects.all().order_by('timestamp')

    def get_queryset(self):
        queryset = super().get_queryset()
        chat_id = self.request.query_params.get('chat')
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(emisor=user)