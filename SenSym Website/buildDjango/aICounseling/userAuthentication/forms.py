from django import forms
from .models import VideoEntry

class VideoEntryForm(forms.ModelForm):
    class Meta:
        model = VideoEntry
        fields = ['title', 'video']