"""Weather observation model; database binding is configured by app.py."""
from datetime import datetime, timezone
from peewee import Model, CharField, DateTimeField, FloatField, TextField


class WeatherObservation(Model):
    city = CharField(max_length=120)
    provider = CharField(max_length=32)
    temperature = FloatField()
    feels_like = FloatField(null=True)
    humidity = FloatField(null=True)
    description = CharField(max_length=255, default="")
    raw_json = TextField(default="{}")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    class Meta:
        table_name = "weather_observations"
