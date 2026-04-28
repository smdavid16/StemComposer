from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from app.views import incarca_melodie, interfata_simpla, verifica_status 
from app.views import signup_view, login_view, istoric_melodii, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/upload/', incarca_melodie, name='upload'),
    
    path('api/status/<str:task_id>/', verifica_status, name='status'),
    
    path('api/signup/', signup_view, name='signup'),
    path('api/login/', login_view, name='login'),
    path('api/istoric/', istoric_melodii, name='istoric'),
    path('api/logout/', logout_view, name='logout'),

    path('', interfata_simpla, name='home'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)