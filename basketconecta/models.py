from django.db import models
from django.contrib.auth.models import User
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable


def geocodificar_direccion(direccion):
    try:
        geolocator = Nominatim(user_agent="basketconecta")
        location = geolocator.geocode(direccion)
        return (location.latitude, location.longitude) if location else (None, None)
    except GeocoderUnavailable:
        return (None, None)

class Jugador(models.Model):
    POSICIONES = [
        ('base', 'Base'),
        ('escolta', 'Escolta'),
        ('alero', 'Alero'),
        ('ala_pivot', 'Ala-Pívot'),
        ('pivot', 'Pívot'),
    ]

    NIVELES = [
        ('relajado', 'Relajado'),
        ('intermedio', 'Intermedio'),
        ('alto', 'Alto'),
    ]

    SEXOS = [
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='jugador')
    nombre = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    altura = models.DecimalField(max_digits=4, decimal_places=2)
    posicion = models.CharField(max_length=20, choices=POSICIONES)
    direccion = models.CharField(max_length=255)
    nivel = models.CharField(max_length=20, choices=NIVELES)
    descripcion = models.TextField(blank=True)
    correo = models.EmailField()
    sexo = models.CharField(max_length=10, choices=SEXOS)
    foto_jugador = models.ImageField(upload_to='jugadores/', blank=True, null=True)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.direccion and (not self.latitud or not self.longitud):
            self.latitud, self.longitud = geocodificar_direccion(self.direccion)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
    


class AnuncioJugador(models.Model):
    DISPONIBILIDAD_DIAS = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
        ('indiferente', 'Indiferente'),
    ]

    DISPONIBILIDAD_HORAS = [
        ('manana', 'Mañana'),
        ('tarde', 'Tarde'),
        ('todo_dia', 'Todo el día'),
        ('indiferente', 'Indiferente'),
    ]

    SEXOS = [
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('mixto', 'Mixto'),
        ('indiferente', 'Indiferente'),
    ]

    jugador = models.OneToOneField(Jugador, on_delete=models.CASCADE, related_name='anuncio')
    disponibilidad_dia = models.CharField(max_length=20, choices=DISPONIBILIDAD_DIAS)
    disponibilidad_horaria = models.CharField(max_length=20, choices=DISPONIBILIDAD_HORAS)
    descripcion = models.TextField(blank=True)
    sexo = models.CharField(max_length=15, choices=SEXOS)

    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Anuncio de {self.jugador.nombre}"
    
class Equipo(models.Model):
    CATEGORIAS = [
        ('infantil', 'Infantil'),
        ('cadete', 'Cadete'),
        ('juvenil', 'Juvenil'),
        ('senior', 'Senior'),
        ('veteranos', 'Veteranos'),
    ]

    SEXOS = [
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('mixto', 'Mixto'),
    ]

    creador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipos')
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    primera_camiseta = models.CharField(max_length=100)
    primera_pantalon = models.CharField(max_length=100)
    segunda_camiseta = models.CharField(max_length=100, blank=True, null=True)
    segunda_pantalon = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.TextField(blank=True)
    sexo = models.CharField(max_length=10, choices=SEXOS)


    jugadores = models.ManyToManyField(Jugador, blank=True, related_name='equipos')

    def __str__(self):
        return self.nombre
    
class AnuncioEquipo(models.Model):
    DIAS_SEMANA = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
        ('indiferente', 'Indiferente'),
    ]

    HORARIOS = [
        ('manana', 'Mañana'),
        ('tarde', 'Tarde'),
        ('todo_dia', 'Todo el día'),
        ('indiferente', 'Indiferente'),
    ]

    equipo = models.OneToOneField(Equipo, on_delete=models.CASCADE, related_name='anuncio')
    dia_partido = models.CharField(max_length=15, choices=DIAS_SEMANA)
    horario_partido = models.CharField(max_length=15, choices=HORARIOS)
    direccion_partido = models.CharField(max_length=255)
    latitud_partido = models.FloatField(null=True, blank=True)
    longitud_partido = models.FloatField(null=True, blank=True)

    # Entrenamientos (opcionales)
    dia_entrenamiento = models.CharField(max_length=15, choices=DIAS_SEMANA, blank=True, null=True)
    horario_entrenamiento = models.CharField(max_length=15, choices=HORARIOS, blank=True, null=True)
    direccion_entrenamiento = models.CharField(max_length=255, blank=True, null=True)
    latitud_entrenamiento = models.FloatField(null=True, blank=True)
    longitud_entrenamiento = models.FloatField(null=True, blank=True)

    descripcion = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        # Geolocalizar dirección de partido
        if self.direccion_partido and (not self.latitud_partido or not self.longitud_partido):
            self.latitud_partido, self.longitud_partido = geocodificar_direccion(self.direccion_partido)
        # Geolocalizar dirección de entrenamiento (si existe)
        if self.direccion_entrenamiento and (not self.latitud_entrenamiento or not self.longitud_entrenamiento):
            self.latitud_entrenamiento, self.longitud_entrenamiento = geocodificar_direccion(self.direccion_entrenamiento)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Anuncio del equipo {self.equipo.nombre}"
    
class Chat(models.Model):
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='chats')
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='chats')
    anuncio_jugador = models.ForeignKey('AnuncioJugador', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats_jugador')
    anuncio_equipo = models.ForeignKey('AnuncioEquipo', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats_equipo')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('jugador', 'equipo', 'anuncio_jugador', 'anuncio_equipo')

    def __str__(self):
        return f"Chat entre {self.equipo.nombre} y {self.jugador.nombre}"


class Mensaje(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='mensajes')
    emisor = models.ForeignKey(User, on_delete=models.CASCADE)  # Puede ser jugador o equipo (ambos son users)
    contenido = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensaje de {self.emisor.username} en {self.chat}"
    

class Invitacion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='invitaciones_enviadas')
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='invitaciones_recibidas')
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')
    mensaje = models.TextField(blank=True)
    enviada = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('equipo', 'jugador')  # no se puede invitar dos veces al mismo jugador

    def __str__(self):
        return f"{self.equipo.nombre} invita a {self.jugador.nombre} ({self.estado})"
    


class EventoCalendario(models.Model):
    TIPOS = [
        ('partido', 'Partido'),
        ('entrenamiento', 'Entrenamiento'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='eventos')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    fecha = models.DateField()
    hora = models.TimeField()
    lugar = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'hora']

    def __str__(self):
        return f"{self.tipo.capitalize()} - {self.fecha} {self.hora} - {self.equipo.nombre}"
        


class Notificacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.mensaje[:50]}"