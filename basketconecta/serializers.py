from rest_framework import serializers
from .models import Jugador, Equipo, AnuncioJugador, AnuncioEquipo, Chat, Mensaje, Invitacion, EventoCalendario, Notificacion, geocodificar_direccion

class JugadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jugador
        fields = [
            'id', 'user', 'nombre', 'edad', 'altura', 'posicion',
            'direccion', 'nivel', 'descripcion', 'correo',
            'sexo', 'foto_jugador', 'latitud', 'longitud'
        ]
        read_only_fields = ['user', 'id', 'latitud', 'longitud']

    def update(self, instance, validated_data):
        direccion = validated_data.get('direccion', instance.direccion)
        if direccion != instance.direccion:
            from .models import geocodificar_direccion
            lat, lon = geocodificar_direccion(direccion)
            instance.latitud = lat
            instance.longitud = lon
        return super().update(instance, validated_data)
    
    def validate_direccion(self, value):
        lat, lon = geocodificar_direccion(value)
        if lat is None or lon is None:
            raise serializers.ValidationError("La dirección no es válida o no se pudo geolocalizar.")
        return value
    

class JugadorMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jugador
        fields = ['id', 'nombre', 'posicion']


class EquipoSerializer(serializers.ModelSerializer):
    jugadores = JugadorMiniSerializer(many=True, read_only=True)
    class Meta:
        model = Equipo
        fields = [
            'id', 'creador', 'nombre', 'categoria',
            'primera_camiseta', 'primera_pantalon',
            'segunda_camiseta', 'segunda_pantalon',
            'descripcion', 'sexo', 'jugadores'
        ]
        read_only_fields = ['creador', 'id']


class AnuncioJugadorSerializer(serializers.ModelSerializer):
    jugador = JugadorSerializer(read_only=True)
    jugador_id = serializers.PrimaryKeyRelatedField(
        queryset=Jugador.objects.all(), source='jugador', write_only=True
    )

    class Meta:
        model = AnuncioJugador
        fields = [
            'id', 'jugador', 'jugador_id',
            'disponibilidad_dia', 'disponibilidad_horaria',
            'descripcion', 'sexo', 'creado'
        ]
        read_only_fields = ['id', 'jugador', 'creado']


class AnuncioEquipoSerializer(serializers.ModelSerializer):
    equipo = EquipoSerializer(read_only=True)
    equipo_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipo.objects.all(), source='equipo', write_only=True
    )

    class Meta:
        model = AnuncioEquipo
        fields = [
            'id', 'equipo', 'equipo_id',
            'dia_partido', 'horario_partido', 'direccion_partido',
            'dia_entrenamiento', 'horario_entrenamiento', 'direccion_entrenamiento',
            'descripcion', 'creado'
        ]
        read_only_fields = ['id', 'equipo', 'creado']


    def validate_direccion_partido(self, value):
        lat, lon = geocodificar_direccion(value)
        if lat is None or lon is None:
            raise serializers.ValidationError("La dirección del partido no es válida o no se pudo geolocalizar.")
        return value

    def validate_direccion_entrenamiento(self, value):
        if value:  # solo validamos si se ha introducido
            lat, lon = geocodificar_direccion(value)
            if lat is None or lon is None:
                raise serializers.ValidationError("La dirección del entrenamiento no es válida.")
        return value


class MensajeSerializer(serializers.ModelSerializer):
    emisor_username = serializers.CharField(source='emisor.username', read_only=True)

    class Meta:
        model = Mensaje
        fields = ['id', 'chat', 'emisor', 'emisor_username', 'contenido', 'timestamp']
        read_only_fields = ['id', 'timestamp', 'emisor', 'emisor_username']


class ChatSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True)
    ultimo_mensaje = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            'id',
            'jugador', 'jugador_nombre',
            'equipo', 'equipo_nombre',
            'creado',
            'ultimo_mensaje'
        ]

    def get_ultimo_mensaje(self, obj):
        mensaje = obj.mensajes.order_by('-timestamp').first()
        if mensaje:
            return {
                'contenido': mensaje.contenido,
                'timestamp': mensaje.timestamp,
                'emisor': mensaje.emisor.username
            }
        return None
    

class InvitacionSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True)
    jugador_nombre = serializers.CharField(source='jugador.nombre', read_only=True)

    class Meta:
        model = Invitacion
        fields = [
            'id',
            'equipo', 'equipo_nombre',
            'jugador', 'jugador_nombre',
            'estado', 'mensaje', 'enviada'
        ]
        read_only_fields = ['id', 'equipo_nombre', 'jugador_nombre', 'enviada']


class EventoCalendarioSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True)

    class Meta:
        model = EventoCalendario
        fields = [
            'id',
            'equipo', 'equipo_nombre',
            'tipo', 'fecha', 'hora',
            'lugar', 'descripcion', 'creado'
        ]
        read_only_fields = ['id', 'equipo_nombre', 'creado']



class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['id', 'mensaje', 'leida', 'creada']
        read_only_fields = ['id', 'mensaje', 'creada']