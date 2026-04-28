import os
import subprocess
from celery import shared_task

@shared_task(bind=True)
def proceseaza_melodia_task(self, nume_fisier, cale_folder_melodii):
    cale_abs = os.path.abspath(cale_folder_melodii)
    
    comanda = [
        "docker", "run", "--rm",
        "-v", f"{cale_abs}:/app",
        "stemcomposer",
        "demucs",
        nume_fisier
    ]
    
    proces = subprocess.Popen(comanda, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    log_complet = ""
    for linie in proces.stdout:
        log_complet += linie
        self.update_state(state='PROGRESS', meta={'log': log_complet})
        
    proces.wait()
    
    if proces.returncode == 0:
        return {'status': 'Succes', 'log': log_complet}
    else:
        return {'status': 'Eroare', 'log': log_complet}