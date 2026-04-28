import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from .tasks import proceseaza_melodia_task
from celery.result import AsyncResult
from django.http import JsonResponse
from django.http import HttpResponse


@api_view(['POST'])
def incarca_melodie(request):
    
    if 'file' not in request.FILES:
        return Response({"eroare": "Nu a fost trimis niciun fisier!"}, status=400)

    fisier = request.FILES['file']
    
    folder_baza = os.getcwd()
    folder_salvare = os.path.join(folder_baza, 'melodii_de_procesat')
    
    os.makedirs(folder_salvare, exist_ok=True)
    
    fs = FileSystemStorage(location=folder_salvare)
    nume_salvat = fs.save(fisier.name, fisier)
    
    proceseaza_melodia_task.delay(nume_salvat, folder_salvare)

    task = proceseaza_melodia_task.delay(nume_salvat, folder_salvare)
    return Response({
        "task_id": task.id,
        "nume_piesa": nume_salvat.split('.')[0] # luam numele fara .mp3
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

def interfata_simpla(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StemComposer Console</title>
        <style>
            body { font-family: 'Courier New', monospace; background: #121212; color: white; padding: 30px; }
            .card { background: #1e1e1e; padding: 20px; border-radius: 8px; max-width: 800px; margin: auto; }
            .btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; font-weight: bold; margin-bottom: 20px; }
            .console-box { background: #000; color: #0f0; height: 300px; overflow-y: scroll; padding: 15px; border: 1px solid #333; text-align: left; font-size: 14px; white-space: pre-wrap; display: none; }
            .download-link { display: inline-block; background: #2196F3; color: white; padding: 8px 15px; margin: 5px; text-decoration: none; border-radius: 4px; font-family: Arial;}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>StemComposer Studio</h2>
            <input type="file" id="fileInput" accept=".mp3,.wav">
            <button class="btn" onclick="startProcesare()">Incarca si Separa</button>
            
            <p id="msg"></p>
            <div id="console" class="console-box">Asteptare conectare...</div>
            <div id="rezultate" style="margin-top: 20px;"></div>
        </div>

        <script>
            let interval;
            function startProcesare() {
                const file = document.getElementById('fileInput').files[0];
                if(!file) return alert("Selecteaza o melodie!");

                let fd = new FormData();
                fd.append('file', file);

                document.getElementById('console').style.display = 'block';
                document.getElementById('console').innerText = "Incarcare fisier...";
                document.getElementById('rezultate').innerHTML = "";

                fetch('/api/upload/', { method: 'POST', body: fd })
                .then(r => r.json())
                .then(data => {
                    pollStatus(data.task_id, data.nume_piesa);
                });
            }

            function pollStatus(taskId, numePiesa) {
                interval = setInterval(() => {
                    fetch(`/api/status/${taskId}/?nume=${numePiesa}`)
                    .then(r => r.json())
                    .then(data => {
                        const consoleDiv = document.getElementById('console');
                        
                        // Actualizam consola doar daca avem text nou
                        if (data.log) {
                            consoleDiv.innerText = data.log;
                            consoleDiv.scrollTop = consoleDiv.scrollHeight; // Autoscroll la final
                        }

                        // Daca a terminat, oprim intervalul si punem butoanele
                        if(data.gata || data.state === 'SUCCESS') {
                            clearInterval(interval);
                            document.getElementById('msg').innerText = "Procesare completa!";
                            
                            // Numele folderului nu are extensia .mp3
                            let numeFolder = numePiesa.split('.')[0];
                            afiseazaDownload(numeFolder, data.fisiere);
                        }
                    });
                }, 1500); // Intreaba serverul la fiecare 1.5 secunde
            }

            function afiseazaDownload(nume, fisiere) {
                const div = document.getElementById('rezultate');
                div.innerHTML = "<h3>Fisiere Extrase:</h3>";
                fisiere.forEach(f => {
                    div.innerHTML += `<a class="download-link" href="/media/htdemucs/${nume}/${f}" download>${f}</a>`;
                });
            }
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)