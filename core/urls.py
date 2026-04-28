from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from app.views import incarca_melodie, interfata_simpla, verifica_status 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/upload/', incarca_melodie, name='upload'),
    
    path('api/status/<str:task_id>/', verifica_status, name='status'),
    
    path('', interfata_simpla, name='home'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)