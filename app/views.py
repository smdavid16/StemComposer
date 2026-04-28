import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from .tasks import proceseaza_melodia_task
from celery.result import AsyncResult
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Melodie, Stem


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def incarca_melodie(request):
    if 'file' not in request.FILES:
        return Response({"eroare": "Nu a fost trimis niciun fisier!"}, status=400)

    fisier = request.FILES['file']
    
    melodie_db = Melodie.objects.create(
        user=request.user,
        titlu=fisier.name,
        fisier_original=fisier
    )
    
    cale_fisier_original = melodie_db.fisier_original.path
    nume_fisier_salvat = os.path.basename(cale_fisier_original)
    folder_salvare = os.path.dirname(cale_fisier_original)
    
    task = proceseaza_melodia_task.delay(melodie_db.id, nume_fisier_salvat, folder_salvare)
    
    return Response({
        "task_id": task.id,
        "melodie_id": melodie_db.id
    })

@api_view(['GET'])
def verifica_status(request, task_id):
    res = AsyncResult(task_id)
    nume_fisier = request.GET.get('nume', '')
    
    nume_folder_piesa = nume_fisier.split('.')[0] if nume_fisier else ''
    
    cale_rezultate = os.path.join(os.getcwd(), 'melodii_de_procesat', 'separated', 'htdemucs', nume_folder_piesa)
    gata = os.path.exists(cale_rezultate)

    log_text = ""
    if res.state == 'PROGRESS' or res.state == 'SUCCESS':
        
        info = res.info
        if isinstance(info, dict):
            log_text = info.get('log', '')

    return JsonResponse({
        "state": res.state,
        "log": log_text,
        "gata": gata,
        "fisiere": ["vocals.wav", "drums.wav", "bass.wav", "other.wav"] if gata else []
    })

from django.http import HttpResponse

def interfata_simpla(request):
    html = """
    <!DOCTYPE html>
    <html lang="ro">
    <head>
        <title>StemComposer Pro</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: white; padding: 20px; }
            .card { background: #1e1e1e; padding: 20px; border-radius: 8px; max-width: 600px; margin: 20px auto; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
            input { width: 90%; padding: 10px; margin: 10px 0; background: #333; color: white; border: 1px solid #555; border-radius: 4px; }
            .btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; border-radius: 4px; font-weight: bold; width: 100%; margin-top: 10px;}
            .btn-blue { background: #2196F3; }
            .console-box { background: #000; color: #0f0; height: 200px; overflow-y: scroll; padding: 10px; border: 1px solid #333; font-family: monospace; display: none; margin-top: 15px;}
            .download-link { display: inline-block; background: #9c27b0; color: white; padding: 5px 10px; margin: 3px; text-decoration: none; border-radius: 3px; font-size: 12px; }
            .istoric-item { background: #2d2d2d; padding: 10px; margin-top: 10px; border-radius: 5px; text-align: left; }
            #sectiune-app, #sectiune-istoric { display: none; }
        </style>
    </head>
    <body>

        <div class="card" id="sectiune-auth">
            <h2>🔑 Autentificare</h2>
            <input type="text" id="user" placeholder="Nume utilizator">
            <input type="password" id="pass" placeholder="Parolă">
            <button class="btn" onclick="auth('/api/login/')">Login</button>
            <button class="btn btn-blue" onclick="auth('/api/signup/')">Creare Cont (Signup)</button>
            <p id="auth-msg" style="color: yellow;"></p>
        </div>

        <div class="card" id="sectiune-app">
            <button onclick="delogare()" style="background: #f44336; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; float: right;">🚪 Ieși din cont</button>
            <h2 style="margin-top: 0;">🎵 Studio StemComposer</h2>
            <input type="file" id="fileInput" accept=".mp3,.wav">
            <button class="btn" onclick="startProcesare()">Procesează Melodie Nouă</button>
            <div id="console" class="console-box"></div>
            <div id="rezultate" style="margin-top: 15px;"></div>
        </div>

        <div class="card" id="sectiune-istoric">
            <h2>📚 Istoricul Meu</h2>
            <button class="btn btn-blue" onclick="incarcaIstoric()">Refresh Istoric</button>
            <div id="lista-istoric"></div>
        </div>

        <script>
            async function auth(url) {
                const u = document.getElementById('user').value;
                const p = document.getElementById('pass').value;
                let csrfToken = getCookie('csrftoken');

                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify({username: u, password: p})
                });
                
                const data = await res.json();
                
                if(res.ok) {
                    document.getElementById('sectiune-auth').style.display = 'none';
                    document.getElementById('sectiune-app').style.display = 'block';
                    document.getElementById('sectiune-istoric').style.display = 'block';
                    incarcaIstoric();
                } else {
                    document.getElementById('auth-msg').innerText = data.eroare || "Eroare!";
                }
            }

            async function delogare() {
                let csrfToken = getCookie('csrftoken');
                
                await fetch('/api/logout/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken }
                });
                
                document.getElementById('sectiune-app').style.display = 'none';
                document.getElementById('sectiune-istoric').style.display = 'none';
                document.getElementById('sectiune-auth').style.display = 'block';
                
                document.getElementById('user').value = '';
                document.getElementById('pass').value = '';
                document.getElementById('auth-msg').style.color = '#4CAF50';
                document.getElementById('auth-msg').innerText = "Te-ai delogat cu succes!";
                document.getElementById('lista-istoric').innerHTML = "";
            }

            async function incarcaIstoric() {
                const res = await fetch('/api/istoric/');
                if(!res.ok) return;
                const date = await res.json();
                
                const div = document.getElementById('lista-istoric');
                div.innerHTML = "";
                
                date.forEach(m => {
                    let htmlStemuri = m.stemuri.map(s => `<a class="download-link" href="${s.url}" download>${s.tip}</a>`).join('');
                    div.innerHTML += `
                        <div class="istoric-item">
                            <strong>${m.titlu}</strong> <br>
                            <small style="color: gray;">Procesat la: ${m.data}</small><br>
                            ${htmlStemuri || '<small style="color: orange;">Inca se proceseaza...</small>'}
                        </div>
                    `;
                });
            }

            function startProcesare() {
                const file = document.getElementById('fileInput').files[0];
                if(!file) return alert("Alege fisier!");

                let fd = new FormData();
                fd.append('file', file);

                document.getElementById('console').style.display = 'block';
                document.getElementById('console').innerText = "Se trimite catre server...";
                
                let csrfToken = getCookie('csrftoken');

                fetch('/api/upload/', { 
                    method: 'POST', 
                    body: fd,
                    headers: { 'X-CSRFToken': csrfToken }
                })
                .then(async r => {
                    if (!r.ok) {
                        let text = await r.text();
                        throw new Error(`Eroare Server (Status ${r.status}): ${text.substring(0, 100)}...`);
                    }
                    return r.json();
                })
                .then(data => {
                    if(data.eroare) throw new Error(data.eroare);
                    document.getElementById('console').innerText = "Fisier salvat. Asteptam procesarea Celery...";
                    pollStatus(data.task_id, data.melodie_id);
                })
                .catch(err => {
                    document.getElementById('console').style.color = "red";
                    document.getElementById('console').innerText = "❌ S-a blocat: " + err.message;
                    console.error(err);
                });
            }

            function pollStatus(taskId, melodieId) {
                let interval = setInterval(() => {
                    fetch(`/api/status/${taskId}/`)
                    .then(r => r.json())
                    .then(data => {
                        const cDiv = document.getElementById('console');
                        if (data.log) {
                            cDiv.innerText = data.log;
                            cDiv.scrollTop = cDiv.scrollHeight;
                        }
                        if(data.state === 'SUCCESS') {
                            clearInterval(interval);
                            incarcaIstoric();
                        }
                    });
                }, 1500);
            }

            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)

@api_view(['POST'])
def signup_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({"eroare": "Date incomplete"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"eroare": "Userul exista deja"}, status=400)
    
    user = User.objects.create_user(username=username, password=password)
    
    login(request, user)
    
    return Response({"mesaj": "Cont creat cu succes!"})

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        return Response({"mesaj": "Logat cu succes!"})
    return Response({"eroare": "Date invalide"}, status=401)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def incarca_melodie(request):
    if 'file' not in request.FILES:
        return Response({"eroare": "Lipseste fisierul"}, status=400)
    
    fisier = request.FILES['file']
    melodie_db = Melodie.objects.create(
        user=request.user,
        titlu=fisier.name,
        fisier_original=fisier
    )
    
    from .tasks import proceseaza_melodia_task
    folder_salvare = os.path.dirname(melodie_db.fisier_original.path)
    task = proceseaza_melodia_task.delay(melodie_db.id, fisier.name, folder_salvare)
    
    return Response({"task_id": task.id, "melodie_id": melodie_db.id})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def istoric_melodii(request):
    melodii = Melodie.objects.filter(user=request.user).order_by('-data_incarcare')
    rezultat = []
    
    for m in melodii:
        stemuri = m.stemuri.all()
        rezultat.append({
            "titlu": m.titlu,
            "data": m.data_incarcare.strftime("%d-%m-%Y %H:%M"),
            "stemuri": [{"tip": s.tip, "url": s.fisier_stem.url} for s in stemuri]
        })
        
    return Response(rezultat)

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({"mesaj": "Delogat cu succes!"})