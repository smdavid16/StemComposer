const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
let wavesurfers = []; // Reținem track-urile pentru a le sincroniza

// 1. Gestionare Drag & Drop
dropzone.onclick = () => fileInput.click();

dropzone.ondragover = (e) => { e.preventDefault(); dropzone.classList.add('hover'); };
dropzone.ondragleave = () => dropzone.classList.remove('hover');

dropzone.ondrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    uploadFile(file);
};

// 2. Trimitere fișier către Django (Backend)
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('audio_file', file);

    document.getElementById('status').classList.remove('hidden');

    // Aici apelezi API-ul făcut de colegii tăi
    const response = await fetch('http://localhost:8000/api/upload/', {
        method: 'POST',
        body: formData
    });
    const data = await response.json();

    // Începem polling-ul pentru a vedea când e gata task-ul Celery
    checkStatus(data.task_id);
}

// 3. Sincronizare Scrubbing & Play (Îmbunătățire)
function initWaveform(id, url) {
    const ws = WaveSurfer.create({
        container: `#waveform-${id}`,
        waveColor: '#4F46E5',
        progressColor: '#F43F5E',
        height: 80
    });
    ws.load(url);
    wavesurfers.push(ws);

    // Sincronizare: dacă dau click pe un track, se mută toate
    ws.on('interaction', () => {
        const time = ws.getCurrentTime();
        wavesurfers.forEach(otherWs => {
            if (otherWs !== ws) otherWs.setTime(time);
        });
    });
}

document.getElementById('playPauseBtn').onclick = () => {
    wavesurfers.forEach(ws => ws.playPause());
};

// Această funcție verifică starea task-ului din Celery
async function checkStatus(taskId) {
    const statusEndpoint = `http://localhost:8000/api/status/${taskId}/`;

    const interval = setInterval(async () => {
        try {
            const response = await fetch(statusEndpoint);
            const data = await response.json();

            if (data.status === 'SUCCESS') {
                clearInterval(interval); // Oprim verificarea
                document.getElementById('status').classList.add('hidden'); // Ascundem loader-ul
                document.getElementById('mixer').classList.remove('hidden'); // Arătăm mixerul

                // Inițializăm formele de undă cu link-urile primite de la Django
                // Presupunem că backend-ul trimite un obiect cu URL-uri
                initWaveform('vocals', data.results.vocals);
                initWaveform('drums', data.results.drums);
                initWaveform('bass', data.results.bass);
                initWaveform('other', data.results.other);

                console.log("Procesare reușită!");
            } else if (data.status === 'FAILURE') {
                clearInterval(interval);
                alert("A apărut o eroare la procesarea audio.");
            }
            // Dacă statusul e 'PENDING' sau 'PROGRESS', nu facem nimic, așteptăm următorul interval
        } catch (error) {
            console.error("Eroare la verificarea statusului:", error);
        }
    }, 3000); // Verifică la fiecare 3 secunde
}