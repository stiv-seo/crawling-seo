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

    CRAWL_SCOPE_CHOICES = [
        ('single_url', 'Analyse only the provided URL'),
        ('multiple_pages', 'Analyse multiple pages'),
    ]
    crawl_scope = forms.ChoiceField(
        choices=CRAWL_SCOPE_CHOICES,
        label='Scope of Analysis',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select whether to analyse a single URL or multiple pages.'
    )

    num_pages = forms.IntegerField(
        label='Number of Pages to Analyse',
        min_value=1,
        initial=10,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='Enter the number of pages to analyse if "Analyse multiple pages" is selected. Defaults to 10.'
    )

    WEBSITE_TECHNOLOGY_CHOICES = [
        ('generic', 'Generic / Unknown'),
        ('wordpress', 'WordPress'),
        ('shopify', 'Shopify'),
        ('joomla', 'Joomla'),
        ('drupal', 'Drupal'),
        ('wix', 'Wix'),
        ('squarespace', 'Squarespace'),
        ('django', 'Django'),
        ('ruby_on_rails', 'Ruby on Rails'),
        ('react', 'React (SPA)'),
        ('angular', 'Angular (SPA)'),
        ('vuejs', 'Vue.js (SPA)'),
    ]
    website_technology = forms.ChoiceField(
        choices=WEBSITE_TECHNOLOGY_CHOICES,
        label='Website Technology (Optional)',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select the technology used by the website, if known. This can help improve the analysis.'
    )

    def clean(self):
        cleaned_data = super().clean()
        crawl_scope = cleaned_data.get("crawl_scope")
        num_pages = cleaned_data.g<ctrl61>et("num_pages")

        if crawl_scope == "multiple_pages":
            if not num_pages:
                self.add_error('num_pages', "This field is required when analysing multiple pages.")
            elif num_pages < 1:
                self.add_error('num_pages', "The number of pages must be at least 1.")
        elif crawl_scope == "single_url":
            # If single URL, we can clear num_pages or set it to 1
            cleaned_data['num_pages'] = None # Or 1, depending on desired behavior
        return cleaned_data