from celery import shared_task
import subprocess
import os

@shared_task
def proceseaza_melodia_task(nume_fisier, cale_folder_melodii):
    director_lucru = "/home/toma/t/StemComposer-backend/" 
    
    comanda_docker = [
        "sudo", "docker", "run", "--rm",
        "-v", f"{director_lucru}:/app",
        "stemcomposer",
        "demucs",
        nume_fisier
    ]
    
    
    rezultat = subprocess.run(comanda_docker, capture_output=True, text=True)
    
    
    if rezultat.returncode == 0:
        return f"Succes! Am extras stem-urile pentru {nume_fisier}."
    else:
        return f"Eroare la procesare: {rezultat.stderr}"