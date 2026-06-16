<p align="center">
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/PyTorch-2.2-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch"/>
  <img src="https://img.shields.io/badge/CUDA-12.1-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="CUDA"/>
  <img src="https://img.shields.io/badge/Docker-Container-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Gemini-API-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini"/>
</p>

# 🎵 StemComposer

### *Deconstruct to Recompose.*

**StemComposer** este o aplicație web full-stack care utilizează **trei agenți AI locali** — **Demucs** (separare audio), **Basic Pitch** (transcriere MIDI) și **Google Gemini** (asistent conversațional) — pentru a oferi un studio complet de separare și manipulare audio direct în browser. Aplicația este construită pe arhitectura **Model-View-Controller (MVC)** prin intermediul framework-ului **Django** și suportă **accelerare GPU NVIDIA CUDA** pentru procesare în timp real.

---

## 📑 Cuprins

- [Arhitectura MVC (Model-View-Controller)](#-arhitectura-mvc-model-view-controller-prin-django)
- [Agenți AI Integrați](#-agenți-ai-integrați)
- [Accelerare GPU (NVIDIA CUDA)](#-accelerare-gpu-nvidia-cuda)
- [Capabilități și Funcționalități](#-capabilități-și-funcționalități)
- [Structura Proiectului](#-structura-proiectului)
- [Stiva Tehnologică](#-stiva-tehnologică)
- [Cerințe de Sistem (Requirements)](#-cerințe-de-sistem-requirements)
- [Instalare și Pornire](#-instalare-și-pornire)
- [Pipeline CI/CD](#-pipeline-cicd)
- [Teste](#-teste)
- [API Endpoints](#-api-endpoints)

---

## 🏗 Arhitectura MVC (Model-View-Controller) prin Django

StemComposer implementează riguros **design pattern-ul Model-View-Controller (MVC)** prin convențiile Django (numit și **MVT — Model-View-Template** în terminologia Django, unde View-ul Django corespunde Controller-ului din MVC clasic).

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                             │
│                   HTML / CSS / JavaScript                           │
│              Spectrogram Canvas · Audio Player                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP / REST API
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CONTROLLER (Views)                             │
│                      app/views.py                                   │
│                                                                     │
│   incarca_melodie()  ──  Upload & dispatch Celery task              │
│   verifica_status()  ──  Polling stare task asincron                │
│   schimba_instrument_view()  ──  Conversie instrument               │
│   signup_view() / login_view() / logout_view()  ──  Autentificare  │
│   istoric_melodii() / detalii_melodie()  ──  Istoric utilizator    │
│   gemini_chat()  ──  Asistent AI conversațional                     │
│   interfata_simpla()  ──  Randare pagina principală (Template)      │
└────────────┬────────────────────────────────────┬───────────────────┘
             │                                    │
             ▼                                    ▼
┌────────────────────────┐          ┌─────────────────────────────────┐
│     MODEL (ORM)        │          │     TEMPLATE (View/UI)          │
│     app/models.py      │          │     inline HTML in views.py     │
│                        │          │     + frontend/ (prototip)      │
│  ┌──────────────────┐  │          │                                 │
│  │    Melodie        │  │          │  • Hero landing page            │
│  │  - user (FK)      │  │          │  • Formular autentificare       │
│  │  - titlu          │  │          │  • Studio upload & consolă      │
│  │  - fisier_original│  │          │  • Player multi-track           │
│  │  - data_incarcare │  │          │  • Istoric melodii              │
│  └──────────────────┘  │          │  • Chatbot Gemini               │
│  ┌──────────────────┐  │          └─────────────────────────────────┘
│  │    Stem           │  │
│  │  - melodie (FK)   │  │
│  │  - tip            │  │
│  │  - fisier_stem    │  │
│  │  - este_transformat│ │
│  │  - instrument_tinta│ │
│  │  - stem_parinte   │  │
│  └──────────────────┘  │
└────────────────────────┘
```

### Separarea responsabilităților MVC:

| Componentă MVC | Implementare Django | Fișier(e) | Responsabilitate |
|---|---|---|---|
| **Model** | Django ORM | `app/models.py` | Definirea entităților `Melodie` și `Stem`, relații `ForeignKey`, validări, persistență în SQLite |
| **View (Template)** | HTML inline + JS | `app/views.py` (funcția `interfata_simpla`) | Randarea interfeței utilizator, spectrograme, player audio, chatbot |
| **Controller** | Django Views + DRF | `app/views.py` (funcțiile API) | Logica de business, rutare cereri, autentificare, orchestrare agenți AI |
| **URL Router** | Django URLconf | `core/urls.py` | Maparea URL-urilor la funcțiile controller corespunzătoare |
| **Middleware** | Django Middleware | `core/settings.py` | CSRF, autentificare sesiune, securitate |

---

## 🤖 Agenți AI Integrați

StemComposer utilizează **trei agenți AI** care rulează local (containerizat) sau prin API cloud:

### 1. 🎼 Demucs — Separare Audio în Stem-uri (Agent Local)

**Demucs** (de la Meta/Facebook Research) este un model de rețea neurală profundă bazat pe **Hybrid Transformer** care separă o pistă audio mixtă în **4 stem-uri izolate**:

| Stem | Descriere | Exemplu |
|---|---|---|
| 🎤 **Vocals** | Vocea umană, inclusiv armonii și ad-lib-uri | Solist, cor |
| 🥁 **Drums** | Tobe, percuții, hi-hat, cinele | Kit de tobe complet |
| 🎸 **Bass** | Linia de bas, bass synth | Bass electric, contrabas |
| 🎹 **Other** | Toate celelalte instrumente | Pian, chitară, sintetizator, coarde |

**Cum funcționează în StemComposer:**
- Modelul **htdemucs** (Hybrid Transformer Demucs) rulează într-un **container Docker** izolat
- Imaginea Docker este bazată pe `pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime`
- Task-ul Celery (`proceseaza_melodia_task`) lansează containerul cu `docker run`
- Ieșirea live a modelului este capturată și transmisă către client prin **polling asincron**

```python
# app/tasks.py — Lansarea agentului Demucs
comanda = ["docker", "run", "--rm"]
if are_nvidia_gpu():
    comanda.extend(["--gpus", "all"])    # ← Accelerare GPU automată
comanda.extend(["-v", f"{cale_abs}:/app", "stemcomposer", "demucs", nume_fisier])
```

### 2. 🎹 Basic Pitch + FluidSynth — Conversie Instrument (Agent Local)

Agentul de **conversie instrument** combină două tehnologii AI/audio:

| Tehnologie | Rol | Tip |
|---|---|---|
| **Basic Pitch** (Spotify) | Transcrierea audio → MIDI folosind rețele neurale | Model ML local |
| **FluidSynth** | Sintetizare MIDI → audio WAV folosind SoundFonts (FluidR3 GM) | Motor de sinteză |

**Pipeline-ul de conversie:**
```
Audio WAV ──► Basic Pitch (AI) ──► MIDI ──► Schimbare Program ──► FluidSynth ──► WAV nou
                                            (instrument țintă)
```

**Instrumente disponibile pentru conversie:**
- 🎹 Pian Acustic (program 0)
- 🎻 Vioară (program 40)
- 🪈 Flaut (program 73)
- ⛪ Orgă (program 19)
- 🎛️ Sintetizator (program 80)

```python
# convert_instrument.py — Pipeline-ul de conversie
model_output, midi_data, note_events = predict(input_path)   # Basic Pitch AI
for instrument in midi_data.instruments:
    instrument.program = program_num                          # Schimbare instrument
midi_data.write(temp_midi_path)                               # Export MIDI
subprocess.run(["fluidsynth", "-ni", sf2_path, temp_midi_path, "-F", output_path])
```

### 3. 💬 Google Gemini — Asistent Muzical Conversațional (API Cloud)

**Gemini** (Google DeepMind) este integrat ca un **chatbot muzical inteligent** care oferă informații contextuale despre melodiile încărcate:

| Capabilitate | Descriere |
|---|---|
| **Identificare melodie** | Recunoașterea artistului, genului muzical și informațiilor despre melodie |
| **Recomandări partituri** | Link-uri către resurse de sheet music (MuseScore, IMSLP, Ultimate Guitar etc.) |
| **Context melodie** | Analiză contextuală bazată pe melodia încărcată în player |
| **Conversație cu memorie** | Istoricul conversației (ultimele 20 de mesaje) pentru context continuu |

**Configurare:** API-ul Gemini este accesat prin **API Key** stocat în fișierul `.env`:
```bash
# .env
GEMINI_API_KEY=cheia_ta_api_gemini
```

```python
# app/views.py — Integrare Gemini API
from google import genai
client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents=contents,
    config={"system_instruction": system_prompt, "temperature": 0.7}
)
```

---

## ⚡ Accelerare GPU (NVIDIA CUDA)

StemComposer implementează **detecție automată** și **utilizare a GPU-urilor NVIDIA** pentru a accelera semnificativ procesarea AI:

### Arhitectura GPU

```
┌─────────────────────────────────────────────────────────────┐
│                    HOST (WSL2 / Linux)                       │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          Docker Container (stemcomposer)               │  │
│  │                                                       │  │
│  │  FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime   │  │
│  │                                                       │  │
│  │  ┌─────────────┐    ┌──────────────────┐              │  │
│  │  │   Demucs     │    │   Basic Pitch    │              │  │
│  │  │  (PyTorch)   │    │  (TensorFlow)    │              │  │
│  │  └──────┬──────┘    └────────┬─────────┘              │  │
│  │         │                    │                         │  │
│  │         ▼                    ▼                         │  │
│  │  ┌──────────────────────────────────────┐             │  │
│  │  │      CUDA 12.1 + cuDNN 8 Runtime     │             │  │
│  │  └──────────────────────────────────────┘             │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          NVIDIA Container Toolkit                      │  │
│  │          (nvidia-ctk runtime)                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              NVIDIA GPU Driver                         │  │
│  │              (Host / WSL2)                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Detecție automată GPU

```python
# app/tasks.py
def are_nvidia_gpu():
    """Detectează automat dacă Docker are runtime-ul NVIDIA instalat."""
    try:
        output = subprocess.check_output(["docker", "info"], stderr=subprocess.STDOUT, text=True)
        return "nvidia" in output.lower()
    except Exception:
        return False
```

Dacă un GPU NVIDIA este detectat, containerul Docker este lansat cu flag-ul `--gpus all`, permițând accesul complet la hardware-ul GPU:

```python
comanda = ["docker", "run", "--rm"]
if are_nvidia_gpu():
    comanda.extend(["--gpus", "all"])   # Activare CUDA în container
```

### Script de Instalare GPU

Proiectul include scriptul `install_nvidia.sh` care automatizează configurarea NVIDIA Container Toolkit:

```bash
# Instalare NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
apt-get install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
service docker restart
```

### Performanță GPU vs. CPU

| Operație | CPU (estimat) | GPU NVIDIA (estimat) |
|---|---|---|
| Separare Demucs (5 min melodie) | ~3-5 minute | ~15-30 secunde |
| Transcriere Basic Pitch | ~1-2 minute | ~10-20 secunde |

---

## 🎯 Capabilități și Funcționalități

### 🔐 Sistem de Autentificare
- **Creare cont** (signup) cu validare username unic
- **Autentificare** (login) cu sesiune Django securizată
- **Delogare** (logout) cu curățare sesiune
- **Protecție CSRF** pe toate endpoint-urile POST
- **Permisiuni per-utilizator** — fiecare utilizator vede doar propriile melodii

### 🎵 Upload și Procesare Audio
- Upload fișiere **MP3** și **WAV**
- Stocare fișiere originale în directorul `media/originale/`
- Procesare asincronă prin **Celery + Redis** (serverul nu se blochează)
- **Consolă live** — output-ul în timp real al procesării AI vizibil în browser

### 🎧 Studio Player Multi-Track
- **5 track-uri simultane**: Original + Vocals + Drums + Bass + Other
- **Spectrograme** generate client-side cu **FFT Cooley-Tukey** (radix-2, 1024 bins)
- **Control volum individual** per track cu slider-e
- **Play / Pause / Stop** sincronizat pe toate track-urile
- **Seek** prin click pe spectrogramă (navigare la orice punct din melodie)
- **Animație playhead** cu glow effect și indicator de progres
- **Cod culori** unic per stem (violet vocals, roșu drums, albastru bass, verde other)

### 🔄 Conversie Instrumente AI
- Transformare stem → alt instrument (Pian, Vioară, Flaut, Orgă, Sintetizator)
- **Selector versiuni** — comutare între versiunea originală și cea transformată
- Istoricul transformărilor persistat în baza de date

### 🤖 Chatbot AI (Google Gemini)
- **Floating Action Button** (FAB) cu animație
- Panel de chat cu design glassmorphism
- **Typing indicator** animat
- Formatare răspunsuri (bold, italic, linkuri)
- **Context melodie** — chatbot-ul știe ce melodie e încărcată în player
- Recomandări partituri de pe MuseScore, IMSLP, Ultimate Guitar etc.

### 📚 Istoric Personal
- Dashboard cu toate melodiile procesate de utilizator
- **Download direct** al fiecărui stem
- **Buton Ascultă** — deschide direct melodia în Studio Player
- Afișare data și ora procesării

## 🛠 Stiva Tehnologică

### Backend
| Tehnologie | Versiune | Rol |
|---|---|---|
| **Django** | ≥ 5.0 | Framework web MVC, ORM, autentificare, middleware |
| **Django REST Framework** | ≥ 3.14 | Construire API REST (decoratori `@api_view`, permisiuni) |
| **Celery** | ≥ 5.3 | Task queue asincron pentru procesare AI |
| **Redis** | ≥ 5.0 | Message broker pentru Celery + backend de rezultate |
| **Gunicorn** | ≥ 21.0 | Server WSGI pentru producție |
| **SQLite** | 3.x | Baza de date (via Django ORM) |
| **python-dotenv** | ≥ 1.0 | Încărcare variabile de mediu din `.env` |

### Agenți AI (în container Docker)
| Tehnologie | Rol |
|---|---|
| **Demucs** (Meta Research) | Separare audio în 4 stem-uri (model htdemucs) |
| **Basic Pitch** (Spotify) | Transcriere audio → MIDI via rețele neurale |
| **FluidSynth** + FluidR3 GM | Sinteză MIDI → WAV cu SoundFonts |
| **PyTorch 2.2** + CUDA 12.1 + cuDNN 8 | Runtime GPU pentru Demucs |
| **TensorFlow CPU 2.15** | Runtime pentru Basic Pitch |
| **librosa** | Procesare și analiză audio |
| **pretty_midi** | Manipulare fișiere MIDI |
| **nussl** | Bibliotecă de separare surse (utilitare auxiliare) |

### Agent Cloud
| Tehnologie | Rol |
|---|---|
| **Google Gemini API** (model `gemini-3.1-flash-lite`) | Chatbot muzical, identificare melodii, recomandări partituri |
| **google-genai** (Python SDK) | Client SDK pentru apeluri Gemini |

### Frontend
| Tehnologie | Rol |
|---|---|
| **HTML5** | Structura paginii (inline în views.py) |
| **CSS3** | Stilizare premium (glassmorphism, gradienți, animații) |
| **JavaScript (Vanilla)** | Logică client (FFT, spectrograme, audio player, chatbot) |
| **Web Audio API** | Decodare și redare audio multi-track |
| **Canvas API** | Renderare spectrograme (pixel-level) |

### Infrastructură
| Tehnologie | Rol |
|---|---|
| **Docker** | Containerizare agenți AI (izolare + portabilitate) |
| **Docker Compose** | Orchestrare multi-container (Django + Celery Worker + Redis) |
| **NVIDIA Container Toolkit** | Passthrough GPU către containere Docker |
| **GitHub Actions** | Pipeline-uri CI/CD automatizate |
| **GitHub Container Registry (GHCR)** | Publicare imagini Docker versionate |

---

## 📋 Cerințe de Sistem (Requirements)

### Cerințe Software Obligatorii

| Cerință | Versiune minimă | Notă |
|---|---|---|
| **Python** | 3.11+ | Recomandat 3.12 |
| **Docker** | 20.10+ | Necesar pentru agenții AI (Demucs, Basic Pitch) |
| **Redis Server** | 6.0+ | Message broker pentru Celery |
| **pip** | 21.0+ | Manager pachete Python |
| **WSL2** (Windows) | — | Necesar pentru Docker cu GPU pe Windows |

### Cerințe Hardware

| Componentă | Minim | Recomandat |
|---|---|---|
| **RAM** | 8 GB | 16 GB |
| **Spațiu disk** | 15 GB (imagini Docker) | 30+ GB |
| **GPU** (opțional) | NVIDIA cu CUDA Compute ≥ 5.0 | NVIDIA RTX 3060+ |
| **VRAM GPU** | 4 GB | 8+ GB |

### Dependințe Python (`requirements.txt`)

```
django>=5.0,<7.0
djangorestframework>=3.14,<4.0
celery>=5.3,<6.0
redis>=5.0,<6.0
gunicorn>=21.0,<23.0
python-dotenv>=1.0.0
```

### Dependințe adiționale (instalate de `start.sh`)

```
google-genai                   # SDK Google Gemini API
```

### Dependințe Development (`requirements-dev.txt`)

```
flake8>=7.0                    # Linter Python
coverage>=7.0                  # Code coverage
```

### Dependințe Docker Container (AI)

```dockerfile
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

# Sistem: ffmpeg, libsndfile1, fluidsynth, fluid-soundfont-gm
# Python: demucs, librosa, basic-pitch, pretty_midi
#         tensorflow-cpu==2.15.0, soundfile, nussl
```

---

## 🚀 Instalare și Pornire

Scriptul `start.sh` automatizează: crearea venv, instalarea dependințelor, migrații DB, build Docker, pornirea Redis, Celery și Django:

```bash
# 1. Clonează repository-ul
git clone https://github.com/<user>/StemComposer.git
cd StemComposer

# 2. Configurează cheia API Gemini
echo "GEMINI_API_KEY=cheia_ta_gemini" > .env

# 3. (Opțional) Instalează suport GPU NVIDIA
sudo ./install_nvidia.sh

# 4. Pornește aplicația
./start.sh
```

## 🔄 Pipeline CI/CD

### CI — Continuous Integration (`ci.yml`)

Rulează automat la fiecare **push** pe `main`/`backend` și la fiecare **Pull Request**:

```
Push / PR ──► 🧹 Lint (flake8) ──► 🧪 Teste Django (Python 3.11 + 3.12) ──► 🐳 Docker Build Check
                                        │
                                        ├── Coverage ≥ 70% (obligatoriu)
                                        └── Upload coverage report
```

### CD — Continuous Deployment (`cd.yml`)

Rulează automat **după** ce CI-ul trece cu succes pe branch-ul `main`:

```
CI Success ──► 🚀 Build & Push Docker Images ──► GitHub Container Registry (GHCR)
                  ├── ghcr.io/<repo>/django:latest
                  └── ghcr.io/<repo>/demucs:latest
```

### Docker Publish (`docker-publish.yml`)

Publicare imagini versionate la crearea unui **git tag** (ex: `v1.0.0`):

```bash
git tag v1.0.0 && git push --tags
# → Publică imagini cu tag-uri semver (v1.0.0, v1.0, latest)
```

---

## 🧪 Teste

Suita de teste conține **30+ teste unitare și de integrare** organizate pe componente:

| Categorie | Teste | Ce verifică |
|---|---|---|
| **Model Melodie** | 4 teste | Creare, `__str__`, relație user, cascade delete |
| **Model Stem** | 5 teste | Creare, `__str__`, relație melodie, cascade delete, tipuri valide |
| **Signup API** | 4 teste | Succes, username duplicat, câmpuri lipsă |
| **Login API** | 4 teste | Succes, parolă greșită, user inexistent, sesiune activă |
| **Logout API** | 2 teste | Succes, curățare sesiune |
| **Upload API** | 3 teste | Succes (mock Celery), fără fișier, neautentificat |
| **Istoric API** | 5 teste | Melodii proprii, include stemuri, izolare per-user, structură răspuns |
| **Detalii Melodie API** | 5 teste | Melodie proprie, acces interzis, inexistentă, structură răspuns |
| **Home Page** | 3 teste | Încărcare 200, conține titlu, conține secțiune auth |


## 📡 API Endpoints

| Metodă | Endpoint | Autentificare | Descriere |
|---|---|---|---|
| `GET` | `/` | ❌ | Pagina principală (Studio UI) |
| `POST` | `/api/signup/` | ❌ | Creare cont nou |
| `POST` | `/api/login/` | ❌ | Autentificare |
| `POST` | `/api/logout/` | ❌ | Delogare |
| `POST` | `/api/upload/` | ✅ | Upload fișier audio + lansare separare Demucs |
| `GET` | `/api/status/<task_id>/` | ❌ | Verificare status task Celery (polling) |
| `GET` | `/api/istoric/` | ✅ | Listare melodii procesate ale utilizatorului |
| `GET` | `/api/melodie/<id>/` | ✅ | Detalii melodie + URL-uri stem-uri |
| `POST` | `/api/schimba-instrument/` | ✅ | Lansare conversie instrument (Basic Pitch) |
| `POST` | `/api/chat/` | ✅ | Trimitere mesaj către chatbot-ul Gemini AI |

---

## 📄 Licență

Proiect realizat în cadrul cursului **Metode de Dezvoltare Software**.