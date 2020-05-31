from django import forms
from django.utils.safestring import mark_safe

class NameForm(forms.Form):
    your_name = forms.CharField(label=mark_safe("<strong style='font-size:25px'>Login</strong>"), max_length=100,widget=forms.TextInput(attrs={'placeholder': 'user name',
                                                                                             'style': 'font-size: 25px;'}))


class RegionForm(forms.Form):
    region_name = forms.CharField(label='Region name', max_length=100, required=False)


class PlaceForm(forms.Form):
    place_name = forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder': 'Place Name'}), max_length=100, required=False)
    upper_region_name = forms.CharField(label='',widget=forms.TextInput(attrs={'placeholder': 'In Region'}), max_length=100, required=False)
    latitude = forms.FloatField(label='',widget=forms.NumberInput(attrs={'placeholder': 'Latitude'}), max_value=90, min_value=-90, required=False)
    longitude = forms.FloatField(label='',widget=forms.NumberInput(attrs={'placeholder': 'Longitude'}), max_value=180, min_value=-180, required=False)
    radius = forms.FloatField(label='',widget=forms.NumberInput(attrs={'placeholder': 'Radius'}), max_value=25, min_value=0, required=False)
    language = forms.ChoiceField(label='Language', choices=(('ar', 'ar'), ('en', 'en'), ('he', 'he'), ('fa', 'fa')), required=False)


class GetTweetsForm(forms.Form):
    from_region = forms.CharField(label='From Region', max_length=100, required=False)
    from_place = forms.CharField(label='From Place', max_length=100, required=False)
