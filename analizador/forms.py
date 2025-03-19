from django import forms

class AnalisisForm(forms.Form):
    """Formulario para analizar una URL."""
    url = forms.URLField(
        label='URL del sitio web',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://ejemplo.com'
        }),
        help_text='Ingrese la URL completa del sitio web que desea analizar.'
    )

    def clean_url(self):
        """Validar y limpiar la URL."""
        url = self.cleaned_data['url']
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url 