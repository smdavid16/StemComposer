from celery import shared_task
import os
import subprocess

@shared_task
def proceseaza_melodia_task(nume_fisier, cale_folder_melodii):
    cale_abs = os.path.abspath(cale_folder_melodii)
    nume_fisier = nume_fisier.strip()
    
    comanda = [
        "docker", "run", "--rm",
        "-v", f"{cale_abs}:/app",
        "-w", "/app",
        "stemcomposer",
        "demucs",
        nume_fisier
    ]
    
    print(f"Executăm: {' '.join(comanda)}")
    
    rezultat = subprocess.run(comanda, capture_output=True, text=True)
    
    print(f"STDOUT: {rezultat.stdout}")
    print(f"STDERR: {rezultat.stderr}")
    
    if rezultat.returncode == 0:
        return f"Succes pentru {nume_fisier}"
    else:
        return f"Eroare: {rezultat.stderr}"