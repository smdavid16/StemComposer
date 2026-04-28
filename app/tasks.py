import os
import subprocess
from celery import shared_task

def are_nvidia_gpu():
    try:
        subprocess.check_output(["nvidia-smi", "-L"], stderr=subprocess.STDOUT)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

@shared_task(bind=True)
def proceseaza_melodia_task(self, melodie_id, nume_fisier, cale_folder_melodii):
    cale_abs = os.path.abspath(cale_folder_melodii)
    
    comanda = ["docker", "run", "--rm"]
    
    if are_nvidia_gpu():
        comanda.extend(["--gpus", "all"])
    
    comanda.extend([
        "-v", f"{cale_abs}:/app",
        "stemcomposer",
        "demucs",
        nume_fisier
    ])
    
    proces = subprocess.Popen(comanda, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    log_complet = ""
    for linie in proces.stdout:
        log_complet += linie
        self.update_state(state='PROGRESS', meta={'log': log_complet})
        
    proces.wait()
    
    if proces.returncode == 0:
        from .models import Melodie, Stem
        melodie_db = Melodie.objects.get(id=melodie_id)
        nume_folder = nume_fisier.split('.')[0]
        
        tipuri = ['vocals', 'drums', 'bass', 'other']
        for t in tipuri:
            cale_relativa = f"originale/separated/htdemucs/{nume_folder}/{t}.wav"
            Stem.objects.create(melodie=melodie_db, tip=t, fisier_stem=cale_relativa)
            
        return {'status': 'Succes', 'log': log_complet}
    else:
        return {'status': 'Eroare', 'log': log_complet}