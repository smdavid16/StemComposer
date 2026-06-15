import os
import subprocess
from celery import shared_task

def are_nvidia_gpu():
    try:
        # Check if Docker has the NVIDIA runtime installed
        output = subprocess.check_output(["docker", "info"], stderr=subprocess.STDOUT, text=True)
        return "nvidia" in output.lower()
    except Exception:
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
    
    try:
        proces = subprocess.Popen(comanda, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError as e:
        raise Exception("Eroare: Comanda 'docker' nu a fost gasita. Asigura-te ca Docker Desktop este pornit si ca integrarea cu distributia de WSL este activata in setarile Docker Desktop (Settings -> Resources -> WSL integration).")
    except Exception as e:
        raise Exception(f"Eroare la pornirea procesului docker: {str(e)}")
    
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
        raise Exception(log_complet)

@shared_task(bind=True)
def schimba_instrument_task(self, stem_id, target_program, instrument_name):
    from .models import Stem, Melodie
    from django.conf import settings
    
    try:
        stem = Stem.objects.get(id=stem_id)
    except Stem.DoesNotExist:
        raise Exception(f"Eroare: Stem-ul cu ID-ul {stem_id} nu exista.")
        
    melodie = stem.melodie
    nume_original_far_ext = os.path.splitext(os.path.basename(stem.fisier_stem.name))[0]
    nume_iesire = f"{nume_original_far_ext}_to_{instrument_name.lower()}.wav"
    cale_iesire_rel = f"separated/transformed/{nume_iesire}"
    cale_iesire_abs_gazda = os.path.join(settings.MEDIA_ROOT, 'separated', 'transformed', nume_iesire)
    
    # Creeaza folderul de transformari daca nu exista
    os.makedirs(os.path.dirname(cale_iesire_abs_gazda), exist_ok=True)
    
    cwd_abs = os.path.abspath(os.getcwd())
    
    comanda = ["docker", "run", "--rm"]
    if are_nvidia_gpu():
        comanda.extend(["--gpus", "all"])
        
    comanda.extend([
        "-v", f"{cwd_abs}:/app",
        "stemcomposer",
        "python3", "/app/convert_instrument.py",
        f"/app/media/{stem.fisier_stem.name}",
        str(target_program),
        f"/app/media/{cale_iesire_rel}"
    ])
    
    self.update_state(state='PROGRESS', meta={'log': 'Se porneste containerul Docker pentru conversie instrument...'})
    
    try:
        proces = subprocess.Popen(comanda, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError:
        raise Exception("Eroare: Comanda 'docker' nu a fost gasita. Asigura-te ca Docker Desktop este pornit si integrarea WSL este activa.")
    except Exception as e:
        raise Exception(f"Eroare la pornirea procesului docker: {str(e)}")
        
    log_complet = ""
    for linie in proces.stdout:
        log_complet += linie
        self.update_state(state='PROGRESS', meta={'log': log_complet})
        
    proces.wait()
    
    if proces.returncode == 0 and os.path.exists(cale_iesire_abs_gazda):
        noul_stem = Stem.objects.create(
            melodie=melodie,
            tip=stem.tip,
            fisier_stem=cale_iesire_rel,
            este_transformat=True,
            instrument_tinta=instrument_name,
            stem_parinte=stem
        )
        return {'status': 'Succes', 'log': log_complet, 'stem_id': noul_stem.id, 'url': noul_stem.fisier_stem.url}
    else:
        raise Exception(log_complet)