from django import forms
from ui.models import Commute

class CommuteForm(forms.ModelForm):
    class Meta:
        model = Commute
        fields = ['seats', 'start_location', 'end_location', 'start_time', 'repeat']
