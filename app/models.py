from django.db import models
from django.contrib.auth.models import User

class Melodie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='melodii')
    titlu = models.CharField(max_length=255)
    fisier_original = models.FileField(upload_to='originale/')
    data_incarcare = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titlu} - {self.user.username}"

class Stem(models.Model):
    TIPURI_STEM = [
        ('vocals', 'Vocals'),
        ('drums', 'Drums'),
        ('bass', 'Bass'),
        ('other', 'Other'),
    ]
    melodie = models.ForeignKey(Melodie, on_delete=models.CASCADE, related_name='stemuri')
    tip = models.CharField(max_length=10, choices=TIPURI_STEM)
    fisier_stem = models.FileField(upload_to='separated/')

    def __str__(self):
        return f"{self.tip} pentru {self.melodie.titlu}"