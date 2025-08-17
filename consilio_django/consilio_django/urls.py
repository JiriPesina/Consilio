from django.contrib import admin
from django.urls import path, include

# Nejvyšší úroveň URL vzorů. Každý path předává část URL do dalších souborů nebo aplikací.
urlpatterns = [
    # Administrace Django – standardní rozhraní na /admin/
    path('admin/', admin.site.urls),
    # Autentizační endpoints poskytované balíkem djoser
    path('api/v1/auth/', include('djoser.urls')),
     # Token-based autentizace djoseru – login vrací token a umožňuje jeho obnovení
    path('api/v1/auth/', include('djoser.urls.authtoken')),
    # Všechny ostatní API v1 endpointy aplikace Redmine
    path('api/v1/', include('Redmine.urls')),
]
