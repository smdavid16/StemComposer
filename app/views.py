import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from .tasks import proceseaza_melodia_task
from celery.result import AsyncResult
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Melodie, Stem


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def incarca_melodie(request):
    if 'file' not in request.FILES:
        return Response({"eroare": "Nu a fost trimis niciun fisier!"}, status=400)

    fisier = request.FILES['file']
    
    melodie_db = Melodie.objects.create(
        user=request.user,
        titlu=fisier.name,
        fisier_original=fisier
    )
    
    cale_fisier_original = melodie_db.fisier_original.path
    nume_fisier_salvat = os.path.basename(cale_fisier_original)
    folder_salvare = os.path.dirname(cale_fisier_original)
    
    task = proceseaza_melodia_task.delay(melodie_db.id, nume_fisier_salvat, folder_salvare)
    
    return Response({
        "task_id": task.id,
        "melodie_id": melodie_db.id
    })

@api_view(['GET'])
def verifica_status(request, task_id):
    res = AsyncResult(task_id)
    nume_fisier = request.GET.get('nume', '')
    
    nume_folder_piesa = nume_fisier.split('.')[0] if nume_fisier else ''
    
    cale_rezultate = os.path.join(os.getcwd(), 'melodii_de_procesat', 'separated', 'htdemucs', nume_folder_piesa)
    gata = os.path.exists(cale_rezultate)

    log_text = ""
    if res.state in ['PROGRESS', 'SUCCESS', 'FAILURE']:
        info = res.info
        if isinstance(info, dict):
            log_text = info.get('log', '')
        elif isinstance(info, Exception):
            log_text = str(info)
        elif info:
            log_text = str(info)

    response_data = {
        "state": res.state,
        "log": log_text,
        "gata": gata,
        "fisiere": ["vocals.wav", "drums.wav", "bass.wav", "other.wav"] if gata else []
    }
    
    if res.state == 'SUCCESS' and isinstance(res.info, dict):
        extra_data = {k: v for k, v in res.info.items() if k not in ['status', 'log']}
        response_data.update(extra_data)

    return JsonResponse(response_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schimba_instrument_view(request):
    stem_id = request.data.get('stem_id')
    target_program = request.data.get('target_program')
    instrument_name = request.data.get('instrument_name')
    
    if not stem_id or target_program is None or not instrument_name:
        return Response({"eroare": "Date incomplete!"}, status=400)
        
    try:
        stem = Stem.objects.get(id=stem_id, melodie__user=request.user)
    except Stem.DoesNotExist:
        return Response({"eroare": "Stem-ul nu exista sau nu aveti acces la el!"}, status=404)
        
    from .tasks import schimba_instrument_task
    task = schimba_instrument_task.delay(stem.id, int(target_program), instrument_name)
    
    return Response({
        "task_id": task.id,
        "mesaj": "Procesarea de schimbare a instrumentului a pornit."
    })

from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def interfata_simpla(request):
    html = """<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StemComposer Pro &mdash; Studio</title>
    <meta name="description" content="StemComposer Pro - Separa melodiile in stem-uri cu Demucs AI. Asculta, vizualizeaza si descarca vocals, drums, bass si other.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        html{scroll-behavior:smooth;}

        body{
            font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
            background:#08080f;
            color:#e2e8f0;
            min-height:100vh;
            padding:20px;
            background-image:
                radial-gradient(ellipse at 15% 50%,rgba(120,50,255,.03) 0%,transparent 50%),
                radial-gradient(ellipse at 85% 20%,rgba(244,63,94,.03) 0%,transparent 50%);
        }

        /* ---- Cards ---- */
        .card{
            background:rgba(18,18,30,.85);
            border:1px solid rgba(255,255,255,.06);
            border-radius:16px;
            padding:28px;
            max-width:800px;
            margin:16px auto;
            box-shadow:0 8px 32px rgba(0,0,0,.4);
            backdrop-filter:blur(20px);
        }
        h2{font-size:22px;font-weight:700;margin-bottom:16px;letter-spacing:-.02em;}

        /* ---- Inputs ---- */
        input[type="text"],input[type="password"]{
            width:100%;padding:12px 16px;margin:6px 0;
            background:rgba(255,255,255,.05);color:#e2e8f0;
            border:1px solid rgba(255,255,255,.1);border-radius:10px;
            font-family:inherit;font-size:14px;
            transition:border-color .2s,box-shadow .2s;outline:none;
        }
        input[type="text"]:focus,input[type="password"]:focus{
            border-color:rgba(168,85,247,.5);
            box-shadow:0 0 0 3px rgba(168,85,247,.1);
        }
        input[type="file"]{
            width:100%;padding:10px;margin:8px 0;
            background:rgba(255,255,255,.05);color:#94a3b8;
            border:1px solid rgba(255,255,255,.1);border-radius:10px;font-size:13px;
        }

        /* ---- Buttons ---- */
        .btn{
            width:100%;padding:12px;border:none;border-radius:10px;
            font-family:inherit;font-weight:600;font-size:14px;
            cursor:pointer;transition:all .2s ease;margin-top:8px;color:#fff;
        }
        .btn:hover{transform:translateY(-1px);box-shadow:0 4px 15px rgba(0,0,0,.3);}
        .btn:active{transform:translateY(0);}
        .btn-primary{background:linear-gradient(135deg,#a855f7,#7c3aed);}
        .btn-blue{background:linear-gradient(135deg,#3b82f6,#2563eb);}

        .btn-ctrl{
            padding:10px 20px;
            border:1px solid rgba(255,255,255,.1);border-radius:10px;
            background:rgba(255,255,255,.05);color:#e2e8f0;
            font-family:inherit;font-weight:500;font-size:13px;
            cursor:pointer;transition:all .2s ease;
        }
        .btn-ctrl:hover{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.2);}

        /* ---- Console ---- */
        .console-box{
            background:rgba(0,0,0,.5);color:#22c55e;
            height:200px;overflow-y:auto;padding:14px;
            border:1px solid rgba(255,255,255,.06);border-radius:10px;
            font-family:'Courier New',monospace;font-size:12px;
            display:none;margin-top:16px;
        }

        /* ---- Player ---- */
        .player-subtitle{color:#94a3b8;font-size:14px;margin-bottom:20px;}

        .track-card{
            background:rgba(10,10,20,.6);
            border:1px solid rgba(255,255,255,.04);
            border-radius:12px;padding:16px;margin-bottom:10px;
            transition:all .3s ease;
        }
        .track-card:hover{border-color:rgba(255,255,255,.08);}

        @keyframes pulseGlow{
            0%,100%{box-shadow:0 0 20px rgba(168,85,247,.05);}
            50%{box-shadow:0 0 30px rgba(168,85,247,.15);}
        }
        .track-card.playing{
            border-color:rgba(168,85,247,.25);
            animation:pulseGlow 2s ease-in-out infinite;
        }

        .track-header{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
        .track-icon{font-size:18px;}
        .track-name{font-weight:600;font-size:14px;flex:1;color:#f1f5f9;}
        .track-time{
            font-size:11px;color:#64748b;
            font-variant-numeric:tabular-nums;
            min-width:90px;text-align:right;
        }
        .track-btn{
            width:34px;height:34px;border-radius:50%;border:none;
            color:#fff;cursor:pointer;font-size:12px;
            display:flex;align-items:center;justify-content:center;
            transition:all .2s ease;flex-shrink:0;
        }
        .track-btn:hover{transform:scale(1.1);box-shadow:0 0 12px rgba(255,255,255,.15);}

        .volume-slider{
            width:70px;-webkit-appearance:none;appearance:none;
            height:4px;border-radius:2px;
            background:rgba(255,255,255,.1);outline:none;flex-shrink:0;
        }
        .volume-slider::-webkit-slider-thumb{
            -webkit-appearance:none;width:14px;height:14px;
            border-radius:50%;background:#fff;cursor:pointer;
            box-shadow:0 0 4px rgba(0,0,0,.3);
        }

        .canvas-wrapper{position:relative;border-radius:8px;overflow:hidden;}
        .spectrogram-canvas{
            width:100%;height:100px;display:block;
            cursor:crosshair;background:#06060c;border-radius:8px;
        }
        .canvas-loading{
            position:absolute;top:0;left:0;right:0;bottom:0;
            display:flex;align-items:center;justify-content:center;gap:10px;
            background:rgba(6,6,12,.9);color:#64748b;font-size:12px;
            border-radius:8px;
        }
        .canvas-loading.done{display:none;}

        @keyframes spin{to{transform:rotate(360deg);}}
        .loading-spinner{
            width:16px;height:16px;
            border:2px solid rgba(255,255,255,.1);
            border-top-color:#a855f7;border-radius:50%;
            animation:spin .8s linear infinite;
        }

        .global-controls{
            display:flex;gap:10px;margin-top:16px;
            justify-content:center;flex-wrap:wrap;
        }

        /* ---- Istoric ---- */
        .istoric-item{
            background:rgba(20,20,35,.6);padding:14px;margin-top:10px;
            border-radius:10px;border:1px solid rgba(255,255,255,.04);
            transition:border-color .2s;
        }
        .istoric-item:hover{border-color:rgba(255,255,255,.08);}

        .download-link{
            display:inline-block;
            background:linear-gradient(135deg,rgba(168,85,247,.15),rgba(124,58,237,.15));
            color:#c4b5fd;padding:4px 10px;margin:3px;
            text-decoration:none;border-radius:6px;
            font-size:11px;font-weight:500;
            border:1px solid rgba(168,85,247,.15);transition:all .2s;
        }
        .download-link:hover{
            background:linear-gradient(135deg,rgba(168,85,247,.25),rgba(124,58,237,.25));
            border-color:rgba(168,85,247,.35);
        }

        .btn-listen{
            display:inline-block;
            background:linear-gradient(135deg,rgba(245,158,11,.15),rgba(217,119,6,.15));
            color:#fbbf24;padding:4px 12px;margin:3px;
            border-radius:6px;font-size:11px;font-weight:600;
            border:1px solid rgba(245,158,11,.15);
            cursor:pointer;transition:all .2s;
        }
        .btn-listen:hover{
            background:linear-gradient(135deg,rgba(245,158,11,.25),rgba(217,119,6,.25));
            border-color:rgba(245,158,11,.3);
            box-shadow:0 0 12px rgba(245,158,11,.1);
        }

        #auth-msg{color:#fbbf24;font-size:13px;margin-top:8px;}
        #sectiune-auth, #sectiune-app,#sectiune-istoric,#sectiune-player{display:none;}

        /* ---- Hero Section ---- */
        .hero{
            text-align:center;
            padding:80px 20px 60px;
            max-width:800px;
            margin:0 auto;
            animation: fadeIn 1s ease-out;
        }
        .hero h1{
            font-size:48px;
            font-weight:700;
            margin-bottom:16px;
            background:linear-gradient(135deg,#a855f7,#3b82f6);
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
            letter-spacing:-1px;
        }
        .hero p{
            font-size:18px;
            color:#94a3b8;
            margin-bottom:32px;
            line-height:1.6;
        }
        .hero-btn{
            display:inline-block;
            padding:16px 36px;
            font-size:16px;
            font-weight:600;
            color:#fff;
            background:linear-gradient(135deg,#a855f7,#7c3aed);
            border:none;
            border-radius:30px;
            cursor:pointer;
            box-shadow:0 8px 24px rgba(168,85,247,.4);
            transition:all .3s ease;
        }
        .hero-btn:hover{
            transform:translateY(-2px) scale(1.05);
            box-shadow:0 12px 32px rgba(168,85,247,.6);
        }
        @keyframes fadeIn{
            from{opacity:0;transform:translateY(20px);}
            to{opacity:1;transform:translateY(0);}
        }

        /* ---- Chatbot FAB ---- */
        .chat-fab{
            position:fixed;bottom:28px;right:28px;z-index:9999;
            width:60px;height:60px;border-radius:50%;border:none;
            background:linear-gradient(135deg,#a855f7,#7c3aed);
            color:#fff;font-size:26px;cursor:pointer;
            box-shadow:0 6px 24px rgba(168,85,247,.4);
            transition:all .3s ease;display:none;
            align-items:center;justify-content:center;
        }
        .chat-fab:hover{transform:scale(1.1);box-shadow:0 8px 32px rgba(168,85,247,.55);}
        .chat-fab.visible{display:flex;}

        /* ---- Chatbot Panel ---- */
        .chat-panel{
            position:fixed;bottom:100px;right:28px;z-index:9998;
            width:400px;max-height:560px;
            background:rgba(14,14,26,.92);
            border:1px solid rgba(255,255,255,.08);
            border-radius:20px;
            box-shadow:0 16px 64px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.04);
            backdrop-filter:blur(24px);
            display:flex;flex-direction:column;
            transform:translateY(20px) scale(.95);opacity:0;
            pointer-events:none;
            transition:transform .35s cubic-bezier(.16,1,.3,1),opacity .25s ease;
        }
        .chat-panel.open{
            transform:translateY(0) scale(1);opacity:1;pointer-events:all;
        }

        .chat-header{
            padding:18px 20px 14px;
            border-bottom:1px solid rgba(255,255,255,.06);
            display:flex;align-items:center;gap:12px;
            background:linear-gradient(135deg,rgba(168,85,247,.08),rgba(124,58,237,.05));
            border-radius:20px 20px 0 0;
        }
        .chat-header-icon{
            width:36px;height:36px;border-radius:10px;
            background:linear-gradient(135deg,#a855f7,#7c3aed);
            display:flex;align-items:center;justify-content:center;
            font-size:18px;flex-shrink:0;
        }
        .chat-header-info{flex:1;}
        .chat-header-title{font-size:15px;font-weight:700;color:#f1f5f9;}
        .chat-header-sub{font-size:11px;color:#64748b;margin-top:1px;}
        .chat-close{
            width:32px;height:32px;border-radius:8px;border:none;
            background:rgba(255,255,255,.05);color:#94a3b8;
            font-size:16px;cursor:pointer;transition:all .2s;
            display:flex;align-items:center;justify-content:center;
        }
        .chat-close:hover{background:rgba(255,255,255,.1);color:#f1f5f9;}

        /* ---- Chat Messages ---- */
        .chat-messages{
            flex:1;overflow-y:auto;padding:16px;
            display:flex;flex-direction:column;gap:10px;
            min-height:300px;max-height:360px;
            scrollbar-width:thin;
            scrollbar-color:rgba(255,255,255,.08) transparent;
        }
        .chat-messages::-webkit-scrollbar{width:5px;}
        .chat-messages::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:4px;}

        .chat-msg{
            max-width:85%;padding:10px 14px;border-radius:14px;
            font-size:13px;line-height:1.55;
            animation:msgSlide .3s ease;
            word-wrap:break-word;
        }
        .chat-msg a{color:#c4b5fd;text-decoration:underline;}
        .chat-msg a:hover{color:#e9d5ff;}
        @keyframes msgSlide{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}

        .chat-msg.user{
            align-self:flex-end;
            background:linear-gradient(135deg,#7c3aed,#6d28d9);
            color:#f1f5f9;border-bottom-right-radius:4px;
        }
        .chat-msg.bot{
            align-self:flex-start;
            background:rgba(255,255,255,.06);
            color:#e2e8f0;border-bottom-left-radius:4px;
            border:1px solid rgba(255,255,255,.04);
        }
        .chat-msg.bot strong{color:#c4b5fd;}
        .chat-msg.system{
            align-self:center;
            background:rgba(168,85,247,.08);
            color:#a78bfa;font-size:12px;
            border:1px solid rgba(168,85,247,.12);
            text-align:center;max-width:95%;
        }

        /* ---- Typing Indicator ---- */
        .typing-indicator{
            display:flex;gap:4px;align-items:center;
            padding:10px 16px;align-self:flex-start;
        }
        .typing-dot{
            width:7px;height:7px;border-radius:50%;
            background:#a855f7;
            animation:typingBounce 1.4s ease-in-out infinite;
        }
        .typing-dot:nth-child(2){animation-delay:.2s;}
        .typing-dot:nth-child(3){animation-delay:.4s;}
        @keyframes typingBounce{
            0%,60%,100%{transform:translateY(0);opacity:.4;}
            30%{transform:translateY(-6px);opacity:1;}
        }

        /* ---- Chat Input ---- */
        .chat-input-area{
            padding:12px 14px;
            border-top:1px solid rgba(255,255,255,.06);
            display:flex;gap:8px;align-items:center;
        }
        .chat-input{
            flex:1;padding:10px 14px;
            background:rgba(255,255,255,.05);color:#e2e8f0;
            border:1px solid rgba(255,255,255,.08);border-radius:12px;
            font-family:inherit;font-size:13px;
            outline:none;transition:border-color .2s,box-shadow .2s;
            resize:none;max-height:80px;
        }
        .chat-input:focus{
            border-color:rgba(168,85,247,.4);
            box-shadow:0 0 0 3px rgba(168,85,247,.08);
        }
        .chat-input::placeholder{color:#4a5568;}
        .chat-send{
            width:38px;height:38px;border-radius:10px;border:none;
            background:linear-gradient(135deg,#a855f7,#7c3aed);
            color:#fff;font-size:16px;cursor:pointer;
            transition:all .2s;flex-shrink:0;
            display:flex;align-items:center;justify-content:center;
        }
        .chat-send:hover{transform:scale(1.05);box-shadow:0 4px 12px rgba(168,85,247,.35);}
        .chat-send:disabled{opacity:.4;cursor:not-allowed;transform:none;box-shadow:none;}

        /* ---- Song context badge ---- */
        .chat-song-badge{
            display:none;padding:6px 12px;margin:0 14px 4px;
            background:linear-gradient(135deg,rgba(245,158,11,.1),rgba(217,119,6,.08));
            border:1px solid rgba(245,158,11,.15);border-radius:8px;
            font-size:11px;color:#fbbf24;
            align-items:center;gap:6px;
        }
        .chat-song-badge.active{display:flex;}

        @media(max-width:500px){
            .chat-panel{width:calc(100vw - 20px);right:10px;bottom:90px;max-height:70vh;}
            .chat-fab{bottom:16px;right:16px;width:52px;height:52px;font-size:22px;}
        }
    </style>
</head>
<body>

    <!-- ========== HERO / LANDING PAGE ========== -->
    <div class="hero" id="sectiune-hero">
        <h1>Deconstruct to Recompose.</h1>
        <p>Extrage voci, tobe, bas si instrumente din orice melodie folosind inteligenta artificiala de ultima generatie.<br>Studio-ul tau complet de mixaj, direct in browser.</p>
        <button class="hero-btn" onclick="arataAuth()">Incepe acum</button>
    </div>

    <!-- ========== AUTH ========== -->
    <div class="card" id="sectiune-auth">
        <h2>&#128273; Autentificare</h2>
        <input type="text" id="user" placeholder="Nume utilizator">
        <input type="password" id="pass" placeholder="Parola">
        <button class="btn btn-primary" onclick="auth('/api/login/')">Login</button>
        <button class="btn btn-blue" onclick="auth('/api/signup/')">Creare Cont</button>
        <p id="auth-msg"></p>
    </div>

    <!-- ========== APP / UPLOAD ========== -->
    <div class="card" id="sectiune-app">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <h2 style="margin-bottom:0;">&#127925; Studio StemComposer</h2>
            <button class="btn-ctrl" onclick="delogare()" style="color:#f43f5e;border-color:rgba(244,63,94,.3);">&#128682; Iesi din cont</button>
        </div>
        <input type="file" id="fileInput" accept=".mp3,.wav">
        <button class="btn btn-primary" onclick="startProcesare()">Proceseaza Melodie</button>
        <div id="console" class="console-box"></div>
    </div>

    <!-- ========== PLAYER ========== -->
    <div class="card" id="sectiune-player">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <h2 style="margin-bottom:0;">&#127911; Studio Player</h2>
            <button class="btn-ctrl" onclick="inchidePlayer()" style="font-size:16px;padding:6px 12px;">&#10005;</button>
        </div>
        <p id="player-titlu" class="player-subtitle"></p>
        <div id="player-tracks"></div>
        <div class="global-controls" id="global-controls" style="display:none;">
            <button class="btn-ctrl" onclick="playAll()">&#9654; Play All</button>
            <button class="btn-ctrl" onclick="pauseAll()">&#9646;&#9646; Pause All</button>
            <button class="btn-ctrl" onclick="stopAll()">&#9632; Stop</button>
        </div>
    </div>

    <!-- ========== ISTORIC ========== -->
    <div class="card" id="sectiune-istoric">
        <h2>&#128218; Istoricul Meu</h2>
        <button class="btn btn-blue" onclick="incarcaIstoric()">Refresh Istoric</button>
        <div id="lista-istoric"></div>
    </div>

    <!-- ========== CHATBOT FAB ========== -->
    <button class="chat-fab" id="chat-fab" onclick="toggleChat()">&#129302;</button>

    <!-- ========== CHATBOT PANEL ========== -->
    <div class="chat-panel" id="chat-panel">
        <div class="chat-header">
            <div class="chat-header-icon">&#129302;</div>
            <div class="chat-header-info">
                <div class="chat-header-title">Asistent Muzical AI</div>
                <div class="chat-header-sub">Powered by Google Gemini</div>
            </div>
            <button class="chat-close" onclick="toggleChat()">&#10005;</button>
        </div>
        <div class="chat-song-badge" id="chat-song-badge">
            &#127925; <span id="chat-song-name">Nicio melodie incarcata</span>
        </div>
        <div class="chat-messages" id="chat-messages">
            <div class="chat-msg system">
                &#127925; Salut! Sunt asistentul tau muzical. Incarca o melodie si intreaba-ma despre gen, artist sau unde gasesti partituri!
            </div>
        </div>
        <div class="chat-input-area">
            <textarea class="chat-input" id="chat-input" placeholder="Scrie un mesaj..." rows="1" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChatMessage();}"></textarea>
            <button class="chat-send" id="chat-send" onclick="sendChatMessage()">&#10148;</button>
        </div>
    </div>

<script>
/* ================================================================
   STEMCOMPOSER PRO  -  Audio Player + Spectrogram Visualization
   ================================================================ */

// ===== TRACK CONFIGURATION =====
var TRACK_CFG = {
    original: {name:'Original', icon:'\\u{1F3B5}', hue:38,  color:'#f59e0b'},
    vocals:   {name:'Vocals',   icon:'\\u{1F3A4}', hue:275, color:'#a855f7'},
    drums:    {name:'Drums',    icon:'\\u{1F941}', hue:348, color:'#f43f5e'},
    bass:     {name:'Bass',     icon:'\\u{1F3B8}', hue:217, color:'#3b82f6'},
    other:    {name:'Other',    icon:'\\u{1F3B9}', hue:160, color:'#10b981'}
};
var audioCtx = null;
var tracks = {};
var animId = null;

// ===== FFT  (Cooley-Tukey radix-2) =====
function fftTransform(re, im, N) {
    var j = 0, i, k, len, half, ang, wR, wI, cR, cI, idx, tR, tI, nR, tmp;
    for (i = 0; i < N - 1; i++) {
        if (i < j) {
            tmp = re[i]; re[i] = re[j]; re[j] = tmp;
            tmp = im[i]; im[i] = im[j]; im[j] = tmp;
        }
        k = N >> 1;
        while (k <= j) { j -= k; k >>= 1; }
        j += k;
    }
    for (len = 2; len <= N; len *= 2) {
        half = len >> 1;
        ang = -2 * Math.PI / len;
        wR = Math.cos(ang);
        wI = Math.sin(ang);
        for (i = 0; i < N; i += len) {
            cR = 1; cI = 0;
            for (k = 0; k < half; k++) {
                idx = i + k + half;
                tR = cR * re[idx] - cI * im[idx];
                tI = cR * im[idx] + cI * re[idx];
                re[idx] = re[i + k] - tR;
                im[idx] = im[i + k] - tI;
                re[i + k] += tR;
                im[i + k] += tI;
                nR = cR * wR - cI * wI;
                cI = cR * wI + cI * wR;
                cR = nR;
            }
        }
    }
}

// ===== SPECTROGRAM COMPUTATION =====
function computeSpectro(audioBuffer, numCols) {
    var FFTSIZE = 1024;
    var data = audioBuffer.getChannelData(0);
    var total = data.length;
    var hop = Math.floor(total / numCols);
    var halfFFT = FFTSIZE >> 1;
    var result = [];
    var c, s, i, idx, re, im, mags, windowVal;

    for (c = 0; c < numCols; c++) {
        s = c * hop;
        re = new Float32Array(FFTSIZE);
        im = new Float32Array(FFTSIZE);
        for (i = 0; i < FFTSIZE; i++) {
            idx = s + i;
            if (idx < total) {
                windowVal = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (FFTSIZE - 1));
                re[i] = data[idx] * windowVal;
            }
        }
        fftTransform(re, im, FFTSIZE);
        mags = new Float32Array(halfFFT);
        for (i = 0; i < halfFFT; i++) {
            mags[i] = Math.sqrt(re[i] * re[i] + im[i] * im[i]);
        }
        result.push(mags);
    }
    return result;
}

// ===== COLOR HELPERS =====
function hsl2rgb(h, s, l) {
    var r, g, b, q, p;
    function h2r(pp, qq, t) {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1/6) return pp + (qq - pp) * 6 * t;
        if (t < 1/2) return qq;
        if (t < 2/3) return pp + (qq - pp) * (2/3 - t) * 6;
        return pp;
    }
    if (s === 0) { r = g = b = l; }
    else {
        q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        p = 2 * l - q;
        r = h2r(p, q, h + 1/3);
        g = h2r(p, q, h);
        b = h2r(p, q, h - 1/3);
    }
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

function spectroColor(val, hue) {
    if (val < 0.02) return [8, 8, 16];
    var t = Math.pow(val, 0.6);
    return hsl2rgb(hue / 360, 0.6 + t * 0.4, 0.06 + t * 0.55);
}

// ===== RENDER SPECTROGRAM TO CANVAS =====
function renderSpectro(canvas, spectro, hue) {
    var ctx = canvas.getContext('2d');
    var w = canvas.width, h = canvas.height;
    var nCols = spectro.length;
    var nBins = spectro[0].length;
    var showBins = Math.floor(nBins * 0.35);
    var maxM = 0, x, y, ci, bi, mag, norm, rgb, idx;

    for (ci = 0; ci < nCols; ci++)
        for (bi = 0; bi < showBins; bi++)
            if (spectro[ci][bi] > maxM) maxM = spectro[ci][bi];
    if (maxM === 0) maxM = 1;

    var img = ctx.createImageData(w, h);
    var px = img.data;

    for (x = 0; x < w; x++) {
        ci = Math.min(Math.floor(x * nCols / w), nCols - 1);
        for (y = 0; y < h; y++) {
            bi = Math.floor((1 - y / h) * showBins);
            if (bi >= showBins) bi = showBins - 1;
            mag = spectro[ci][bi];
            norm = Math.log1p(mag * 10) / Math.log1p(maxM * 10);
            rgb = spectroColor(norm, hue);
            idx = (y * w + x) << 2;
            px[idx] = rgb[0]; px[idx+1] = rgb[1]; px[idx+2] = rgb[2]; px[idx+3] = 255;
        }
    }
    ctx.putImageData(img, 0, 0);
    return img;
}

// ===== AUDIO CONTEXT =====
function initAudio() {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
}

// ===== OPEN PLAYER =====
function deschidePlayer(melodieId) {
    initAudio();
    fetch('/api/melodie/' + melodieId + '/')
    .then(function(res) {
        if (!res.ok) throw new Error('Eroare server');
        return res.json();
    })
    .then(function(data) {
        stopAll();
        tracks = {};

        document.getElementById('sectiune-player').style.display = 'block';
        document.getElementById('player-titlu').innerText = data.titlu;
        setChatSongContext(data.titlu);

        var originalStems = {};
        var transformedStems = {};

        data.stemuri.forEach(function(s) {
            if (!s.este_transformat) {
                originalStems[s.tip] = s;
            } else {
                if (!transformedStems[s.tip]) transformedStems[s.tip] = [];
                transformedStems[s.tip].push(s);
            }
        });

        var list = [{id:'original', url:data.url_original, name:'Original', isStem:false}];
        ['vocals', 'drums', 'bass', 'other'].forEach(function(tip) {
            var orig = originalStems[tip];
            if (orig) {
                list.push({
                    id: tip,
                    url: orig.url,
                    name: TRACK_CFG[tip].name,
                    isStem: true,
                    stemId: orig.id,
                    tip: tip
                });
            }
        });

        var container = document.getElementById('player-tracks');
        container.innerHTML = list.map(function(t) {
            var c = TRACK_CFG[t.id];
            
            var versionSelectorHtml = '';
            var transformHtml = '';
            
            if (t.isStem) {
                var options = ['<option value="' + t.url + '" data-stem-id="' + t.stemId + '">Original</option>'];
                var transforms = transformedStems[t.id] || [];
                transforms.forEach(function(ts) {
                    options.push('<option value="' + ts.url + '" data-stem-id="' + ts.id + '">' + ts.instrument_tinta + '</option>');
                });
                
                versionSelectorHtml = '<div style="margin-top: 6px; font-size: 12px; display: flex; align-items: center; gap: 8px;">' +
                    '<span style="color:#94a3b8;">Versiune:</span>' +
                    '<select id="ver-' + t.id + '" style="width: 110px; height: 24px; padding: 2px; font-size: 11px; background:#1e1e2f; color:#fff; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; outline: none;">' +
                        options.join('') +
                    '</select>' +
                '</div>';
                
                transformHtml = '<div style="margin-top: 6px; font-size: 12px; display: flex; align-items: center; gap: 8px;">' +
                    '<span style="color:#94a3b8;">Conversie:</span>' +
                    '<select id="target-inst-' + t.id + '" style="width: 110px; height: 24px; padding: 2px; font-size: 11px; background:#1e1e2f; color:#fff; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; outline: none;">' +
                        '<option value="0">Pian Acustic</option>' +
                        '<option value="40">Vioară</option>' +
                        '<option value="73">Flaut</option>' +
                        '<option value="19">Orgă</option>' +
                        '<option value="80">Sintetizator</option>' +
                    '</select>' +
                    '<button class="btn-ctrl" id="btn-transform-' + t.id + '" style="font-size: 11px; padding: 2px 8px; border-radius: 4px; height: 24px; margin: 0;">🔄 Schimbă</button>' +
                '</div>';
            }
            
            return '<div class="track-card" id="track-' + t.id + '">' +
                '<div class="track-header">' +
                    '<span class="track-icon">' + c.icon + '</span>' +
                    '<span class="track-name">' + c.name + '</span>' +
                    '<span class="track-time" id="time-' + t.id + '">0:00 / 0:00</span>' +
                    '<button class="track-btn" id="btn-' + t.id + '" style="background:' + c.color + '">&#9654;</button>' +
                    '<input type="range" class="volume-slider" id="vol-' + t.id + '" min="0" max="100" value="100">' +
                '</div>' +
                '<div class="canvas-wrapper">' +
                    '<canvas id="canvas-' + t.id + '" class="spectrogram-canvas"></canvas>' +
                    '<div class="canvas-loading" id="loading-' + t.id + '">' +
                        '<div class="loading-spinner"></div>' +
                        '<span>Se incarca...</span>' +
                    '</div>' +
                '</div>' +
                '<div style="display: flex; gap: 20px; flex-wrap: wrap; margin-top: 10px;">' +
                    versionSelectorHtml +
                    transformHtml +
                '</div>' +
            '</div>';
        }).join('');

        // Attach event listeners & setup canvases
        list.forEach(function(t) {
            document.getElementById('btn-' + t.id).addEventListener('click', function() { toggleTrack(t.id); });
            document.getElementById('vol-' + t.id).addEventListener('input', function() { setVol(t.id, this.value); });

            var cv = document.getElementById('canvas-' + t.id);
            var rect = cv.getBoundingClientRect();
            cv.width  = Math.floor(rect.width);
            cv.height = Math.floor(rect.height);

            cv.addEventListener('click', function(e) {
                var tr = tracks[t.id];
                if (tr && tr.buffer) {
                    var ratio = e.offsetX / cv.clientWidth;
                    seekAll(ratio * tr.buffer.duration);
                }
            });
            cv.addEventListener('mousemove', function(e) {
                var tr = tracks[t.id];
                if (tr && tr.buffer) {
                    cv.title = fmtTime((e.offsetX / cv.clientWidth) * tr.buffer.duration);
                }
            });

            if (t.isStem) {
                var selectEl = document.getElementById('ver-' + t.id);
                selectEl.addEventListener('change', function() {
                    var newUrl = this.value;
                    var loadingEl = document.getElementById('loading-' + t.id);
                    loadingEl.classList.remove('done');
                    loadingEl.innerHTML = '<div class="loading-spinner"></div><span>Se reincarca...</span>';
                    
                    var tObj = tracks[t.id];
                    var wasPlaying = false;
                    var pauseOff = 0;
                    if (tObj) {
                        wasPlaying = tObj.isPlaying;
                        pauseOff = tObj.pauseOff;
                        if (tObj.isPlaying) {
                            tObj.source.onended = null;
                            tObj.source.stop();
                            tObj.isPlaying = false;
                        }
                    }
                    
                    loadTrack(t.id, newUrl).then(function() {
                        var newTObj = tracks[t.id];
                        if (newTObj) {
                            newTObj.pauseOff = pauseOff;
                            if (wasPlaying) {
                                playTrack(t.id);
                            } else {
                                drawProgress(t.id);
                            }
                        }
                    });
                });
                
                var transformBtn = document.getElementById('btn-transform-' + t.id);
                transformBtn.addEventListener('click', function() {
                    try {
                        var selectInst = document.getElementById('target-inst-' + t.id);
                        var instVal = selectInst.value;
                        var instLabel = selectInst.options[selectInst.selectedIndex].text;
                        var currentStemId = selectEl.options[selectEl.selectedIndex].getAttribute('data-stem-id');
                        
                        lanseazaConversie(melodieId, currentStemId, instVal, instLabel, t.id);
                    } catch (err) {
                        alert("Eroare JavaScript la click pe Schimbă:\\n" + err.message + "\\n\\nStack:\\n" + err.stack);
                    }
                });
            }
        });

        // Load all tracks in parallel
        var loadPromises = list.map(function(t) { return loadTrack(t.id, t.url); });
        Promise.allSettled(loadPromises).then(function() {
            document.getElementById('global-controls').style.display = 'flex';
        });

        document.getElementById('sectiune-player').scrollIntoView({behavior:'smooth'});
    })
    .catch(function(err) {
        alert('Eroare la deschiderea playerului: ' + err.message);
    });
}

// ===== LAUNCH INSTRUMENT CONVERSION =====
function lanseazaConversie(melodieId, stemId, targetProgram, instrumentName, trackId) {
    var consoleDiv = document.getElementById('console');
    consoleDiv.style.display = 'block';
    consoleDiv.style.color = '#22c55e';
    consoleDiv.innerText = 'Se trimite cererea de conversie pentru ' + TRACK_CFG[trackId].name + ' -> ' + instrumentName + '...\\n(Procesarea pe CPU durează în jur de 1-3 minute, te rugăm să aștepți)';
    
    var btn = document.getElementById('btn-transform-' + trackId);
    if (btn) {
        btn.disabled = true;
        btn.innerText = '🔄 Se schimbă...';
        btn.style.opacity = '0.6';
        btn.style.cursor = 'not-allowed';
    }

    function restoreButton() {
        if (btn) {
            btn.disabled = false;
            btn.innerText = '🔄 Schimbă';
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }
    }

    var csrf = getCookie('csrftoken');
    
    fetch('/api/schimba-instrument/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        },
        body: JSON.stringify({
            stem_id: stemId,
            target_program: targetProgram,
            instrument_name: instrumentName
        })
    })
    .then(function(r) {
        if (!r.ok) return r.text().then(function(txt) { throw new Error(txt); });
        return r.json();
    })
    .then(function(data) {
        if (data.eroare) throw new Error(data.eroare);
        consoleDiv.innerText = 'Conversia a pornit. Se proceseaza cu Basic Pitch si FluidSynth...\\n(Durată estimată: 1-3 minute. Te rugăm să nu mai apeși din nou butonul)';
        
        var interval = setInterval(function() {
            fetch('/api/status/' + data.task_id + '/')
            .then(function(r) { return r.json(); })
            .then(function(resData) {
                if (resData.log) {
                    consoleDiv.innerText = resData.log;
                    consoleDiv.scrollTop = consoleDiv.scrollHeight;
                }
                
                if (resData.state === 'SUCCESS') {
                    clearInterval(interval);
                    consoleDiv.innerText = 'Conversia s-a finalizat cu succes!';
                    restoreButton();
                    deschidePlayer(melodieId);
                    incarcaIstoric();
                } else if (resData.state === 'FAILURE') {
                    clearInterval(interval);
                    consoleDiv.style.color = '#f43f5e';
                    restoreButton();
                    if (!resData.log) {
                        consoleDiv.innerText = 'Eroare la conversia instrumentului pe server.';
                    }
                }
            })
            .catch(function(err) {
                // Ignore transient network errors during status checks
            });
        }, 2000);
    })
    .catch(function(err) {
        consoleDiv.style.color = '#f43f5e';
        consoleDiv.innerText = 'Eroare la pornirea conversiei: ' + err.message;
        restoreButton();
    });
}

// ===== LOAD SINGLE TRACK =====
function loadTrack(id, url) {
    return fetch(url)
    .then(function(resp) { return resp.arrayBuffer(); })
    .then(function(ab) { return audioCtx.decodeAudioData(ab); })
    .then(function(buffer) {
        var gain = audioCtx.createGain();
        gain.connect(audioCtx.destination);

        var cv = document.getElementById('canvas-' + id);
        var spectro = computeSpectro(buffer, cv.width);
        var imgData = renderSpectro(cv, spectro, TRACK_CFG[id].hue);

        tracks[id] = {
            buffer: buffer, gain: gain, source: null, canvas: cv,
            img: imgData, isPlaying: false, startT: 0, pauseOff: 0
        };

        document.getElementById('time-' + id).innerText = '0:00 / ' + fmtTime(buffer.duration);
        document.getElementById('loading-' + id).classList.add('done');
    })
    .catch(function(err) {
        console.error('Eroare track ' + id + ':', err);
        document.getElementById('loading-' + id).innerHTML = '<span style="color:#f43f5e;">Eroare la incarcare</span>';
    });
}

// ===== PLAYBACK CONTROLS =====
function toggleTrack(id) {
    var t = tracks[id];
    if (!t) return;
    if (t.isPlaying) pauseTrack(id); else playTrack(id);
}

function playTrack(id) {
    var t = tracks[id];
    if (!t || t.isPlaying) return;
    initAudio();
    var src = audioCtx.createBufferSource();
    src.buffer = t.buffer;
    src.connect(t.gain);
    var off = Math.min(t.pauseOff, t.buffer.duration - 0.01);
    if (off < 0) off = 0;
    src.start(0, off);
    t.source = src;
    t.startT = audioCtx.currentTime - off;
    t.isPlaying = true;

    src.onended = function() {
        if (t.isPlaying) {
            t.isPlaying = false;
            t.pauseOff = 0;
            updateBtn(id);
            drawProgress(id);
        }
    };
    updateBtn(id);
    startAnim();
}

function pauseTrack(id) {
    var t = tracks[id];
    if (!t || !t.isPlaying) return;
    t.pauseOff = audioCtx.currentTime - t.startT;
    t.source.onended = null;
    t.source.stop();
    t.isPlaying = false;
    updateBtn(id);
    var anyPlaying = false;
    for (var k in tracks) { if (tracks[k].isPlaying) { anyPlaying = true; break; } }
    if (!anyPlaying) stopAnim();
}

function seekAll(time) {
    for (var id in tracks) {
        var t = tracks[id];
        if (!t) continue;
        var was = t.isPlaying;
        if (was) { t.source.onended = null; t.source.stop(); t.isPlaying = false; }
        t.pauseOff = Math.max(0, Math.min(time, t.buffer.duration - 0.01));
        if (was) playTrack(id);
        else drawProgress(id);
    }
}

function playAll() {
    for (var id in tracks) { if (!tracks[id].isPlaying) playTrack(id); }
}

function pauseAll() {
    for (var id in tracks) { pauseTrack(id); }
}

function stopAll() {
    for (var id in tracks) {
        var t = tracks[id];
        if (!t) continue;
        if (t.isPlaying) { t.source.onended = null; t.source.stop(); t.isPlaying = false; }
        t.pauseOff = 0;
        updateBtn(id);
        drawProgress(id);
    }
    stopAnim();
}

function setVol(id, v) {
    if (tracks[id]) tracks[id].gain.gain.value = v / 100;
}

function inchidePlayer() {
    stopAll();
    tracks = {};
    document.getElementById('sectiune-player').style.display = 'none';
    document.getElementById('global-controls').style.display = 'none';
    setChatSongContext('');
}

// ===== ANIMATION LOOP =====
function startAnim() { if (!animId) animate(); }
function stopAnim()  { if (animId) { cancelAnimationFrame(animId); animId = null; } }

function animate() {
    var anyPlaying = false;
    for (var id in tracks) {
        drawProgress(id);
        if (tracks[id].isPlaying) anyPlaying = true;
    }
    if (anyPlaying) animId = requestAnimationFrame(animate);
    else animId = null;
}

// ===== DRAW PROGRESS ON CANVAS =====
function drawProgress(id) {
    var t = tracks[id];
    if (!t || !t.img) return;
    var cv = t.canvas;
    var ctx = cv.getContext('2d');
    var w = cv.width, h = cv.height;

    // Redraw cached spectrogram
    ctx.putImageData(t.img, 0, 0);

    var cur = t.isPlaying ? (audioCtx.currentTime - t.startT) : t.pauseOff;
    if (cur < 0) cur = 0;
    var dur = t.buffer.duration;
    var prog = Math.min(cur / dur, 1);
    var x = prog * w;

    // Played-region tint
    ctx.fillStyle = 'rgba(255,255,255,.04)';
    ctx.fillRect(0, 0, x, h);

    // Progress line with glow
    ctx.save();
    ctx.shadowColor = 'rgba(255,255,255,.7)';
    ctx.shadowBlur = 8;
    ctx.strokeStyle = 'rgba(255,255,255,.85)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
    ctx.restore();

    // Progress dot (center marker)
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(x, h / 2, 4, 0, Math.PI * 2);
    ctx.fill();

    // Update time label
    var el = document.getElementById('time-' + id);
    if (el) el.innerText = fmtTime(cur) + ' / ' + fmtTime(dur);
}

function updateBtn(id) {
    var t = tracks[id];
    if (!t) return;
    var btn = document.getElementById('btn-' + id);
    var card = document.getElementById('track-' + id);
    if (!btn || !card) return;
    if (t.isPlaying) {
        btn.innerHTML = '&#9646;&#9646;';
        card.classList.add('playing');
    } else {
        btn.innerHTML = '&#9654;';
        card.classList.remove('playing');
    }
}

function fmtTime(s) {
    if (isNaN(s) || s < 0) s = 0;
    var m = Math.floor(s / 60);
    var sec = Math.floor(s % 60);
    return m + ':' + (sec < 10 ? '0' : '') + sec;
}

// ===== AUTHENTICATION =====
function auth(url) {
    try {
        var u = document.getElementById('user').value;
        var p = document.getElementById('pass').value;
        var csrf = getCookie('csrftoken');
        var msgEl = document.getElementById('auth-msg');
        msgEl.style.color = '#fbbf24';
        msgEl.innerText = 'Se trimite cererea...';

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf
            },
            body: JSON.stringify({username: u, password: p})
        })
        .then(function(res) {
            if (!res.ok) {
                var contentType = res.headers.get("content-type");
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    return res.json().then(function(d) {
                        throw new Error(d.eroare || ('Eroare server (' + res.status + ')'));
                    });
                } else {
                    return res.text().then(function(t) {
                        throw new Error('Eroare server (' + res.status + '): ' + t.substring(0, 100));
                    });
                }
            }
            return res.json();
        })
        .then(function(data) {
            msgEl.innerText = '';
            document.getElementById('sectiune-auth').style.display = 'none';
            document.getElementById('sectiune-app').style.display = 'block';
            document.getElementById('sectiune-istoric').style.display = 'block';
            showChatFab();
            incarcaIstoric();
        })
        .catch(function(err) {
            msgEl.style.color = '#f43f5e';
            msgEl.innerText = err.message;
            console.error("Auth error:", err);
            alert("Eroare autentificare:\\n" + err.message);
        });
    } catch (e) {
        alert("Eroare in scriptul de login:\\n" + e.message);
    }
}

function delogare() {
    var csrf = getCookie('csrftoken');
    fetch('/api/logout/', {method:'POST', headers:{'X-CSRFToken':csrf}})
    .then(function() {
        document.getElementById('sectiune-app').style.display = 'none';
        document.getElementById('sectiune-istoric').style.display = 'none';
        document.getElementById('sectiune-player').style.display = 'none';
        document.getElementById('sectiune-auth').style.display = 'block';
        document.getElementById('user').value = '';
        document.getElementById('pass').value = '';
        document.getElementById('auth-msg').style.color = '#22c55e';
        document.getElementById('auth-msg').innerText = 'Te-ai delogat cu succes!';
        document.getElementById('lista-istoric').innerHTML = '';
        stopAll();
        tracks = {};
        hideChatFab();
        setChatSongContext('');
        chatHistory = [];
    });
}

function arataAuth() {
    document.getElementById('sectiune-hero').style.display = 'none';
    document.getElementById('sectiune-auth').style.display = 'block';
}

// ===== ISTORIC =====
function incarcaIstoric() {
    fetch('/api/istoric/')
    .then(function(res) { if (!res.ok) throw new Error(); return res.json(); })
    .then(function(date) {
        var div = document.getElementById('lista-istoric');
        div.innerHTML = '';
        date.forEach(function(m) {
            var item = document.createElement('div');
            item.className = 'istoric-item';

            var stemLinks = m.stemuri.map(function(s) {
                return '<a class="download-link" href="' + s.url + '" download>' + s.tip + '</a>';
            }).join('');

            item.innerHTML = '<strong>' + m.titlu + '</strong><br>' +
                '<small style="color:#64748b;">Procesat la: ' + m.data + '</small><br>' +
                stemLinks;

            if (m.stemuri.length > 0) {
                var btn = document.createElement('span');
                btn.className = 'btn-listen';
                btn.innerHTML = '&#127911; Asculta';
                btn.addEventListener('click', (function(mid) {
                    return function() { deschidePlayer(mid); };
                })(m.id));
                item.appendChild(btn);
            } else {
                item.innerHTML += ' <small style="color:orange;">Inca se proceseaza...</small>';
            }
            div.appendChild(item);
        });
    })
    .catch(function() {});
}

// ===== UPLOAD & PROCESARE =====
function startProcesare() {
    var file = document.getElementById('fileInput').files[0];
    if (!file) return alert('Alege fisier!');

    var fd = new FormData();
    fd.append('file', file);

    document.getElementById('console').style.display = 'block';
    document.getElementById('console').style.color = '#22c55e';
    document.getElementById('console').innerText = 'Se trimite catre server...';

    var csrf = getCookie('csrftoken');

    fetch('/api/upload/', {method:'POST', body:fd, headers:{'X-CSRFToken':csrf}})
    .then(function(r) {
        if (!r.ok) return r.text().then(function(txt) { throw new Error('Eroare Server (' + r.status + '): ' + txt.substring(0,100)); });
        return r.json();
    })
    .then(function(data) {
        if (data.eroare) throw new Error(data.eroare);
        document.getElementById('console').innerText = 'Fisier salvat. Asteptam procesarea Celery...';
        pollStatus(data.task_id);
    })
    .catch(function(err) {
        document.getElementById('console').style.color = '#f43f5e';
        document.getElementById('console').innerText = 'Eroare: ' + err.message;
    });
}

function pollStatus(taskId) {
    var interval = setInterval(function() {
        fetch('/api/status/' + taskId + '/')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var cDiv = document.getElementById('console');
            if (data.log) { cDiv.innerText = data.log; cDiv.scrollTop = cDiv.scrollHeight; }
            if (data.state === 'SUCCESS') { clearInterval(interval); incarcaIstoric(); }
            else if (data.state === 'FAILURE') { clearInterval(interval); incarcaIstoric(); }
        });
    }, 1500);
}

// ===== COOKIE HELPER =====
function getCookie(name) {
    var val = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var c = cookies[i].trim();
            if (c.substring(0, name.length + 1) === (name + '=')) {
                val = decodeURIComponent(c.substring(name.length + 1));
                break;
            }
        }
    }
    return val;
}

// ===== CHATBOT =====
var chatHistory = [];
var chatOpen = false;
var currentSongTitle = '';

function toggleChat() {
    chatOpen = !chatOpen;
    var panel = document.getElementById('chat-panel');
    if (chatOpen) {
        panel.classList.add('open');
        document.getElementById('chat-input').focus();
        var msgs = document.getElementById('chat-messages');
        msgs.scrollTop = msgs.scrollHeight;
    } else {
        panel.classList.remove('open');
    }
}

function showChatFab() {
    document.getElementById('chat-fab').classList.add('visible');
}

function hideChatFab() {
    document.getElementById('chat-fab').classList.remove('visible');
    var panel = document.getElementById('chat-panel');
    panel.classList.remove('open');
    chatOpen = false;
}

function setChatSongContext(title) {
    currentSongTitle = title || '';
    var badge = document.getElementById('chat-song-badge');
    var nameEl = document.getElementById('chat-song-name');
    if (currentSongTitle) {
        nameEl.innerText = currentSongTitle;
        badge.classList.add('active');
    } else {
        badge.classList.remove('active');
    }
}

function addChatMessage(text, type) {
    var msgs = document.getElementById('chat-messages');
    var div = document.createElement('div');
    div.className = 'chat-msg ' + type;

    if (type === 'bot') {
        div.innerHTML = formatBotMessage(text);
    } else {
        div.textContent = text;
    }

    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
}

function formatBotMessage(text) {
    // Basic markdown-like formatting
    var html = text;
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Links — turn URLs into clickable links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    // Plain URLs
    html = html.replace(/(https?:\/\/[^\s<]+)/g, function(match) {
        // Don't double-wrap already linked URLs
        if (html.indexOf('href="' + match) !== -1) return match;
        return '<a href="' + match + '" target="_blank" rel="noopener">' + match + '</a>';
    });
    // Line breaks
    html = html.replace(/\\n/g, '<br>');
    return html;
}

function showTypingIndicator() {
    var msgs = document.getElementById('chat-messages');
    var div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typing-indicator';
    div.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
}

function removeTypingIndicator() {
    var el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

function sendChatMessage() {
    var input = document.getElementById('chat-input');
    var message = input.value.trim();
    if (!message) return;

    var sendBtn = document.getElementById('chat-send');
    sendBtn.disabled = true;
    input.value = '';
    input.style.height = 'auto';

    addChatMessage(message, 'user');
    showTypingIndicator();

    var songCtx = '';
    if (currentSongTitle) {
        songCtx = 'Melodia incarcata in player: "' + currentSongTitle + '". Stem-urile disponibile: vocals, drums, bass, other.';
    }

    var csrf = getCookie('csrftoken');

    fetch('/api/chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        },
        body: JSON.stringify({
            message: message,
            song_context: songCtx,
            history: chatHistory
        })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        removeTypingIndicator();
        sendBtn.disabled = false;

        if (data.reply) {
            chatHistory.push({role: 'user', text: message});
            chatHistory.push({role: 'bot', text: data.reply});
            // Keep history manageable (last 20 messages)
            if (chatHistory.length > 20) {
                chatHistory = chatHistory.slice(chatHistory.length - 20);
            }
            addChatMessage(data.reply, 'bot');
        } else if (data.eroare) {
            addChatMessage('Eroare: ' + data.eroare, 'system');
        }

        input.focus();
    })
    .catch(function(err) {
        removeTypingIndicator();
        sendBtn.disabled = false;
        addChatMessage('Eroare de conexiune: ' + err.message, 'system');
        input.focus();
    });
}

// Auto-resize textarea
document.getElementById('chat-input').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 80) + 'px';
});
</script>
</body>
</html>"""
    return HttpResponse(html)

@api_view(['POST'])
def signup_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({"eroare": "Date incomplete"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"eroare": "Userul exista deja"}, status=400)
    
    user = User.objects.create_user(username=username, password=password)
    
    login(request, user)
    
    return Response({"mesaj": "Cont creat cu succes!"})

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        return Response({"mesaj": "Logat cu succes!"})
    return Response({"eroare": "Date invalide"}, status=401)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def istoric_melodii(request):
    melodii = Melodie.objects.filter(user=request.user).order_by('-data_incarcare')
    rezultat = []
    
    for m in melodii:
        stemuri = m.stemuri.all()
        rezultat.append({
            "id": m.id,
            "titlu": m.titlu,
            "data": m.data_incarcare.strftime("%d-%m-%Y %H:%M"),
            "url_original": m.fisier_original.url,
            "stemuri": [
                {
                    "tip": s.tip,
                    "url": s.fisier_stem.url,
                    "este_transformat": s.este_transformat,
                    "instrument_tinta": s.instrument_tinta
                }
                for s in stemuri
            ]
        })
        
    return Response(rezultat)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalii_melodie(request, melodie_id):
    try:
        melodie = Melodie.objects.get(id=melodie_id, user=request.user)
    except Melodie.DoesNotExist:
        return Response({"eroare": "Melodia nu a fost gasita"}, status=404)
    
    stemuri = melodie.stemuri.all()
    return Response({
        "id": melodie.id,
        "titlu": melodie.titlu,
        "url_original": melodie.fisier_original.url,
        "stemuri": [
            {
                "id": s.id,
                "tip": s.tip,
                "url": s.fisier_stem.url,
                "este_transformat": s.este_transformat,
                "instrument_tinta": s.instrument_tinta,
                "stem_parinte_id": s.stem_parinte_id
            }
            for s in stemuri
        ]
    })

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({"mesaj": "Delogat cu succes!"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gemini_chat(request):
    from django.conf import settings as django_settings
    # pyrefly: ignore [missing-import]
    from google import genai

    user_message = request.data.get('message', '')
    song_context = request.data.get('song_context', '')
    history = request.data.get('history', [])

    if not user_message:
        return Response({"eroare": "Mesajul lipseste"}, status=400)

    api_key = django_settings.GEMINI_API_KEY
    if not api_key:
        return Response({"eroare": "Cheia API Gemini nu este configurata"}, status=500)

    system_prompt = (
        "Esti un asistent muzical inteligent pentru aplicatia StemComposer. "
        "StemComposer este o aplicatie care separa melodiile in stem-uri individuale "
        "(vocals, drums, bass, other) folosind inteligenta artificiala.\n\n"
        "RASPUNDE INTOTDEAUNA IN LIMBA ROMANA.\n\n"
        "Cand utilizatorul intreaba despre o melodie sau cand primesti context despre o melodie, trebuie sa:\n"
        "1. Identifici NUMELE MELODIEI, ARTISTUL si GENUL MUZICAL\n"
        "2. Recomanzi RESURSE ONLINE pentru partituri/sheet music pentru fiecare instrument din melodie:\n"
        "   - Musescore (musescore.com) - partituri gratuite si premium\n"
        "   - IMSLP (imslp.org) - partituri clasice gratuite\n"
        "   - Musicnotes (musicnotes.com) - partituri profesionale\n"
        "   - Ultimate Guitar (ultimate-guitar.com) - tablaturi chitara si bass\n"
        "   - Flat.io (flat.io) - partituri interactive\n"
        "   - SheetMusicDirect (sheetmusicdirect.com)\n"
        "   - Songsterr (songsterr.com) - tablaturi interactive\n"
        "3. Ofera link-uri de cautare specifice pentru fiecare instrument (vocals/voce, drums/tobe, bass, other/alte instrumente)\n\n"
        "Formateaza raspunsurile frumos cu emoji-uri relevante si structura clara.\n"
        "Fii prietenos, entuziast si util. Daca nu cunosti melodia exact, ofera sugestii bazate pe numele fisierului."
    )

    if song_context:
        system_prompt += f"\n\nCONTEXT MELODIE CURENTA: {song_context}"

    try:
        client = genai.Client(api_key=api_key)

        contents = []
        for msg in history:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=contents,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.7,
                "max_output_tokens": 2048,
            }
        )

        reply = response.text if response.text else "Nu am putut genera un raspuns."
        return Response({"reply": reply})

    except Exception as e:
        return Response({"eroare": f"Eroare Gemini API: {str(e)}"}, status=500)