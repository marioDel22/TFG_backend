from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('basketconecta', '0009_notificacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='anuncio_jugador',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chats_jugador', to='basketconecta.anunciojugador'),
        ),
        migrations.AddField(
            model_name='chat',
            name='anuncio_equipo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chats_equipo', to='basketconecta.anuncioequipo'),
        ),
    ] 