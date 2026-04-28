# StemComposer

**Deconstruct to Recompose.**

StemComposer is a full-stack web application designed to separate any mixed audio track into its individual, high-fidelity stems. Built with a Django backend and powered by AI source separation models, it provides users with a seamless, browser-based studio experience to extract vocals, drums, bass, and other instruments.

### What it does
By leveraging the industry-leading Demucs machine learning model (running securely within a Docker container), StemComposer takes a single audio file (MP3 or WAV) and splits it into four isolated tracks:
- Vocals
- Drums
- Bass
- Other Instruments (Piano, Synth, Guitar, etc.)

### Current State & Key Features
The project has evolved from a simple script into a robust web platform. Current features include:

* **Web-Based Studio Interface:** A clean, responsive frontend allowing users to upload files and download extracted stems directly from the browser.
* **User Authentication:** Secure signup, login, and logout functionality. Users have private accounts to manage their own music.
* **Database Persistence:** Every uploaded song and its resulting stems are saved to a database, creating a personal "History" dashboard for each user to access past projects anytime.
* **Asynchronous Processing:** Powered by Celery and Redis, the heavy AI processing runs in the background. The web server remains fast and responsive while tracks are being separated.
* **Real-Time Live Console:** Users can see the actual live terminal output of the AI model rendering their stems via a dynamic UI element.
* **Hardware Acceleration:** Automatic detection and utilization of NVIDIA GPUs for significantly faster extraction times.

### Tech Stack
* **Backend:** Django, Django REST Framework, SQLite
* **Task Queue:** Celery, Redis
* **AI Engine:** Dockerized Demucs
* **Frontend:** Vanilla HTML / CSS / JavaScript 

### Getting Started
The project includes an automated startup script that handles the virtual environment, dependencies, database migrations, and background workers.

To run the application locally:
1. Ensure `docker`, `redis-server`, and `python3` are installed on your system.
2. Run the startup script:
   ```bash
   ./start.sh