from celery import shared_task
import os
import subprocess

def is_gpu_available():
    """
    Funcție ajutătoare internă. Verifică rapid dacă sistemul gazdă 
    are acces la o placă video NVIDIA funcțională.
    """
    try:
        rezultat = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        # Dacă returncode e 0, comanda a rulat cu succes -> avem GPU
        return rezultat.returncode == 0
    except FileNotFoundError:
        # nvidia-smi nu există pe acest sistem -> nu avem GPU
        return False

@shared_task
def verifica_gpu_task():
    """
    Task care poate fi apelat din frontend/shell doar pentru a verifica statusul.
    """
    if is_gpu_available():
        rezultat = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        linii_output = rezultat.stdout.split('\n')
        nume_placa = linii_output[8] if len(linii_output) > 8 else "Placă video NVIDIA"
        return f"GPU detectat și gata de acțiune! Info: {nume_placa.strip()}"
    else:
        return "Nu s-a găsit o placă video NVIDIA (sau lipsesc driverele). Procesarea se va face pe CPU."

@shared_task
def proceseaza_melodia_task(nume_fisier, cale_folder_melodii):
    """
    Procesează melodia adaptându-se automat la hardware (GPU sau CPU).
    """
    cale_abs = os.path.abspath(cale_folder_melodii)
    nume_fisier = nume_fisier.strip()
    
    # 1. Construim prima jumătate a comenzii Docker
    comanda = [
        "docker", "run", "--rm",
        "-v", f"{cale_abs}:/app",
        "-w", "/app"
    ]
    
    # 2. Adăugăm accelerarea hardware DOAR DACĂ este disponibilă
    if is_gpu_available():
        print("🚀 GPU NVIDIA detectat! Adăugăm '--gpus all' la comandă.")
        comanda.extend(["--gpus", "all"])
    else:
        print("🐢 Niciun GPU detectat. Rulăm standard pe CPU.")
        
    # 3. Completăm cu restul comenzii (imaginea, algoritmul, fișierul)
    comanda.extend([
        "stemcomposer",
        "demucs",
        nume_fisier
    ])
    
    print(f"Executăm: {' '.join(comanda)}")
    
    # 4. Lansăm Docker-ul în execuție
    rezultat = subprocess.run(comanda, capture_output=True, text=True)
    
    # 5. Logăm rezultatele (util pentru debugging în terminalul Celery)
    print(f"STDOUT: {rezultat.stdout}")
    print(f"STDERR: {rezultat.stderr}")
    
    if rezultat.returncode == 0:
        return f"Succes! Am separat stem-urile pentru {nume_fisier}."
    else:
        return f"Eroare Docker: {rezultat.stderr}"