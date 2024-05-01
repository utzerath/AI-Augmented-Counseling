from django.db import models
from db_connection import db
# Create your models here.
from django.db import models

class MyModel(models.Model):
    image = models.ImageField(upload_to='uploads/')

logIn_collection = db['logIn']
adminLogIn_collection = db['adminLogIn']
text_entries_collection = db['text_entries']
video_entries_collection = db['video_entries']
audio_entries_collection = db['audio_entries']
otherFiles_entries_collection = db['otherFiles_entries']
screening_collection = db['screening']
