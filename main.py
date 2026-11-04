import os
import re
import json
import time
import hmac
import html
import hashlib
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from functools import wraps
from urllib.parse import parse_qsl

import requests
import telebot
from flask import Flask, request, jsonify, Response, g

# ======================================================================
# الإعدادات
# ======================================================================
TOKEN = os.environ["TOKEN"]
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
WEBAPP_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#060608">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Manrope:wght@400;600;800&display=swap" rel="stylesheet">
<title>TRX Earn</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
__AD_SDK__
<style>
 :root{--bg:#060608;--gold:#f5c542;--gold1:#fff1b8;--gold3:#c8921a;--goldsoft:#fde9a8;--text:#f6f1e4;--muted:#9a9384;--line:rgba(245,197,66,.22)}
 *{-webkit-tap-highlight-color:transparent;box-sizing:border-box}
 html,body{margin:0}
 body{font-family:'Cairo','Manrope',Tahoma,Arial,sans-serif;color:var(--text);padding:15px 15px 108px;min-height:100vh;background:radial-gradient(120% 60% at 50% -10%,rgba(245,197,66,.17),transparent 60%),radial-gradient(80% 50% at 100% 100%,rgba(200,146,26,.10),transparent 60%),var(--bg);background-attachment:fixed;overflow-x:hidden}
 body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.7;background-image:radial-gradient(1.6px 1.6px at 12% 22%,rgba(245,197,66,.7) 50%,transparent 52%),radial-gradient(1.2px 1.2px at 78% 14%,rgba(255,241,184,.6) 50%,transparent 52%),radial-gradient(1.8px 1.8px at 88% 58%,rgba(245,197,66,.55) 50%,transparent 52%),radial-gradient(1.2px 1.2px at 30% 72%,rgba(255,241,184,.5) 50%,transparent 52%),radial-gradient(1.5px 1.5px at 55% 40%,rgba(245,197,66,.45) 50%,transparent 52%),radial-gradient(1.2px 1.2px at 8% 90%,rgba(245,197,66,.5) 50%,transparent 52%);animation:drift 16s ease-in-out infinite alternate}
 .header,#welcome,#view{position:relative;z-index:1}
 .header{position:sticky;top:0;z-index:50;display:flex;align-items:center;justify-content:space-between;margin:-15px -15px 12px;padding:12px 15px;background:rgba(6,6,8,.74);-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}
 .header h2{flex:1;margin:0;text-align:center;font-size:16px;font-weight:700;letter-spacing:.4px;background:linear-gradient(180deg,var(--gold1),var(--gold) 60%,var(--gold3));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
 .menu-btn{width:36px;height:36px;border-radius:12px;border:1px solid var(--line);background:rgba(245,197,66,.07);color:var(--gold);font-size:19px;cursor:pointer;display:grid;place-items:center;}
 .logo{width:36px;height:36px;display:grid;place-items:center}
 .logo svg{width:30px;height:30px;filter:drop-shadow(0 0 8px rgba(245,197,66,.55))}
 #welcome{text-align:center;margin:0 0 4px}
 .muted{font-size:12px;color:var(--muted);line-height:1.7}
 .card{position:relative;margin:12px 0;padding:16px;border-radius:20px;text-align:center;border:1px solid transparent;background:linear-gradient(160deg,rgba(255,255,255,.07),rgba(255,255,255,.02)) padding-box,linear-gradient(#0d0b07,#0d0b07) padding-box,linear-gradient(135deg,rgba(255,226,130,.55),rgba(245,197,66,.07) 40%,rgba(245,197,66,.34)) border-box;-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);box-shadow:0 10px 30px rgba(0,0,0,.5);animation:rise .45s ease both}
 .card h3{margin:0 0 8px;font-size:16px;color:var(--gold)}
 .big{font-size:36px;font-weight:800;margin:8px 0;direction:ltr;background:linear-gradient(180deg,#fff7cf,#f5c542 55%,#c8921a);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 12px rgba(245,197,66,.35))}
 .hero{position:relative;overflow:hidden;margin:12px 0;padding:18px 18px 16px;border-radius:24px;text-align:start;border:1px solid transparent;background:linear-gradient(135deg,#221a08 0%,#0b0905 48%,#2b2009 100%) padding-box,linear-gradient(135deg,rgba(255,232,150,.95),rgba(245,197,66,.10) 38%,rgba(245,197,66,.6) 100%) border-box;box-shadow:0 18px 44px rgba(0,0,0,.65),0 0 0 1px rgba(245,197,66,.05),0 0 40px rgba(245,197,66,.10);animation:rise .5s ease both}
 .hero::before{content:"";position:absolute;top:-60%;left:-40%;width:45%;height:220%;transform:rotate(18deg);background:linear-gradient(90deg,transparent,rgba(255,241,184,.16),transparent);animation:sweep 6.5s ease-in-out infinite}
 .hero::after{content:"";position:absolute;width:190px;height:190px;right:-60px;top:-70px;border-radius:50%;background:radial-gradient(circle,rgba(245,197,66,.28),transparent 68%)}
 .hero>*{position:relative;z-index:1}
 .hero-top{display:flex;justify-content:space-between;align-items:center;direction:ltr}
 .chip{width:42px;height:31px;border-radius:7px;background:repeating-linear-gradient(90deg,rgba(0,0,0,.18) 0 2px,transparent 2px 9px),linear-gradient(135deg,#fbe9a0,#b9861b);box-shadow:inset 0 0 0 1px rgba(255,255,255,.25),0 2px 8px rgba(0,0,0,.5)}
 .brand{font-size:11px;letter-spacing:3.5px;font-weight:800;color:var(--gold);opacity:.95}
 .hero-label{margin-top:16px;font-size:12px;color:#c9b98a;letter-spacing:.6px}
 .amt{display:flex;align-items:baseline;gap:8px;direction:ltr;margin:2px 0 12px}
 .amt .cur{font-size:15px;font-weight:800;color:var(--gold);letter-spacing:2px}
 .amt .amt-n{font-size:42px;font-weight:800;line-height:1.1;background:linear-gradient(180deg,#fffbe0,#f5c542 52%,#c8921a);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 14px rgba(245,197,66,.4))}
 .prog{height:7px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden;direction:ltr}
 .prog i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#c8921a,#f5c542,#fff1b8);box-shadow:0 0 12px rgba(245,197,66,.6);transition:width 1.1s cubic-bezier(.2,.8,.2,1)}
 .prog-txt{display:flex;justify-content:space-between;margin-top:7px;font-size:11px;color:#b7a77a}
 .prog-txt b{color:var(--gold)}
 .who{display:flex;align-items:center;gap:10px;margin-top:14px;padding-top:12px;border-top:1px solid rgba(245,197,66,.14);font-size:13px;color:#e8dcb8}
 .av{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;font-weight:800;font-size:14px;color:#1c1403;background:linear-gradient(135deg,#fff1b8,#c8921a);box-shadow:0 0 0 2px rgba(245,197,66,.25)}
 .tiles{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}
 .tile{padding:13px;border-radius:18px;text-align:start;border:1px solid var(--line);background:linear-gradient(160deg,rgba(255,255,255,.06),rgba(255,255,255,.02));animation:rise .55s ease both}
 .tile small{display:block;font-size:11px;color:var(--muted);margin-bottom:5px}
 .tile b{font-size:18px;color:var(--gold);direction:ltr;display:inline-block}
 .grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}
 .earn{display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px 8px;border-radius:20px;cursor:pointer;color:var(--text);font-family:inherit;border:1px solid var(--line);background:linear-gradient(160deg,rgba(245,197,66,.10),rgba(255,255,255,.02));transition:transform .15s,border-color .15s;animation:rise .6s ease both}
 .earn:active{transform:scale(.96);border-color:var(--gold)}
 .earn .ic{width:50px;height:50px;border-radius:16px;display:grid;place-items:center;background:radial-gradient(circle at 30% 25%,rgba(255,241,184,.28),rgba(245,197,66,.07));border:1px solid rgba(245,197,66,.4);box-shadow:0 0 18px rgba(245,197,66,.18);color:var(--gold)}
 .earn .ic svg{width:26px;height:26px}
 .earn .lb{font-size:12px;font-weight:700;line-height:1.35;text-align:center;color:var(--goldsoft)}
 .btn{position:relative;overflow:hidden;width:100%;margin-top:10px;padding:13px;border:none;border-radius:14px;cursor:pointer;font-family:inherit;font-size:15px;font-weight:800;color:#1c1403;text-shadow:0 1px 0 rgba(255,255,255,.35);background:linear-gradient(135deg,#fff1b8 0%,#f5c542 38%,#c8921a 72%,#f2c548 100%);box-shadow:0 6px 18px rgba(245,197,66,.28),inset 0 1px 0 rgba(255,255,255,.55);transition:transform .12s,filter .12s}
 .btn::after{content:"";position:absolute;top:0;left:-70%;width:45%;height:100%;transform:skewX(-20deg);background:linear-gradient(90deg,transparent,rgba(255,255,255,.55),transparent);animation:shine 4.2s ease-in-out infinite}
 .btn:active{transform:scale(.97);filter:brightness(.93)}
 .btn.green{background:linear-gradient(135deg,#fff1b8 0%,#f5c542 38%,#c8921a 72%,#f2c548 100%)}
 .btn.red{color:#ffe9b0;text-shadow:none;background:linear-gradient(135deg,#9f1239,#e11d48 55%,#7f0f2e);box-shadow:0 6px 18px rgba(225,29,72,.35),inset 0 1px 0 rgba(255,255,255,.25)}
 input{width:100%;margin-top:8px;padding:12px;border-radius:14px;direction:ltr;text-align:center;outline:none;color:var(--goldsoft);font-family:inherit;border:1px solid var(--line);background:rgba(0,0,0,.45)}
 input:focus{border-color:var(--gold);box-shadow:0 0 0 3px rgba(245,197,66,.16)}
 input[readonly]{opacity:.85}
 details.card{text-align:start}
 summary{cursor:pointer;font-size:15px;font-weight:700;color:var(--gold)}
 .pre{white-space:pre-line;text-align:start;font-size:13px;color:#e4dcc4;line-height:1.85;margin:4px 0 12px}
 h4{margin:14px 0 2px;padding-top:12px;text-align:start;font-size:14px;color:var(--gold);border-top:1px solid var(--line)}
 h4:first-of-type{border-top:none;padding-top:0}
 .offer{display:flex;align-items:center;gap:11px;margin-top:10px;padding:11px;border-radius:18px;text-align:start;border:1px solid var(--line);background:linear-gradient(160deg,rgba(255,255,255,.05),rgba(0,0,0,.25))}
 .oic{flex:none;width:44px;height:44px;border-radius:14px;display:grid;place-items:center;background:radial-gradient(circle at 30% 25%,rgba(255,241,184,.28),rgba(245,197,66,.07));border:1px solid rgba(245,197,66,.4);color:var(--gold)}
 .oic svg{width:22px;height:22px}
 .otx{flex:1;min-width:0}
 .otx b{display:block;font-size:14px;color:var(--text);margin-bottom:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .pill{display:inline-block;padding:2px 10px;border-radius:99px;font-size:12px;font-weight:800;color:#1c1403;direction:ltr;background:linear-gradient(135deg,#fff1b8,#f5c542)}
 .offer .btn{flex:none;width:auto;margin:0;padding:10px 16px}
 .overlay{position:fixed;inset:0;z-index:1500;display:none;background:rgba(0,0,0,.7);-webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px)}.overlay.on{display:block}
 .drawer{position:fixed;top:0;inset-inline-end:-300px;z-index:1600;width:280px;height:100%;display:flex;flex-direction:column;padding:16px 12px;overflow-y:auto;transition:.32s cubic-bezier(.2,.8,.2,1);background:linear-gradient(180deg,#17130a,#060608);border-inline-start:1px solid var(--line)}
 .drawer.on{inset-inline-end:0}
 .dhead{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--line);color:var(--gold);font-weight:800}
 .dhead button{background:none;border:none;color:#fb7185;font-size:22px;cursor:pointer}
 .item{width:100%;margin-bottom:7px;padding:12px;text-align:start;cursor:pointer;font-family:inherit;font-size:13px;color:#e4dcc4;border-radius:14px;border:1px solid rgba(245,197,66,.12);background:rgba(255,255,255,.03);display:flex;align-items:center;gap:10px;}
 .item.active{color:var(--gold);font-weight:800;border-color:var(--gold);background:linear-gradient(135deg,rgba(245,197,66,.22),rgba(245,197,66,.05))}
 .item svg{width:20px;height:20px;flex:none;}
 .item .nav-svg{color:var(--muted);display:flex;}
 .item.active .nav-svg{color:var(--gold);}
 select{width:100%;margin-top:6px;padding:9px;border-radius:12px;color:var(--goldsoft);font-family:inherit;border:1px solid var(--line);background:rgba(0,0,0,.5)}
 #bottom{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:900;height:66px;display:flex;align-items:center;justify-content:space-around;padding:0 6px;border-radius:24px;border:1px solid rgba(245,197,66,.3);background:rgba(16,13,7,.86);-webkit-backdrop-filter:blur(18px);backdrop-filter:blur(18px);box-shadow:0 14px 34px rgba(0,0,0,.7),0 0 26px rgba(245,197,66,.08)}
 .nb{position:relative;flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 0;background:none;border:none;cursor:pointer;font-family:inherit;font-size:10px;color:var(--muted);transition:color .2s}
 .nb .ni{width:22px;height:22px;display:grid;place-items:center;transition:.2s}
 .nb .ni svg{width:100%;height:100%}
 .nb.on{color:var(--gold);font-weight:800}
 .nb.on .ni{transform:translateY(-2px) scale(1.12);filter:drop-shadow(0 0 8px rgba(245,197,66,.6))}
 .nb.on::before{content:"";position:absolute;top:-1px;width:24px;height:3px;border-radius:0 0 4px 4px;background:var(--gold);box-shadow:0 0 12px var(--gold)}
 @keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
 @keyframes sweep{0%,55%{left:-60%}100%{left:130%}}
 @keyframes shine{0%,60%{left:-70%}100%{left:140%}}
 @keyframes drift{from{transform:translateY(0)}to{transform:translateY(-22px)}}
 @media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
 .adstage{padding:6px 4px 2px;text-align:center}
 .adstage b{font-size:15px;color:var(--text)}
 .adstep{font-size:11px;letter-spacing:1px;color:var(--muted);margin-bottom:5px}
 .adearn{margin-top:12px;font-size:13px;color:var(--goldsoft)}
 .adlock{text-align:center;padding:14px 6px 8px}
 .adlock b{font-size:16px;color:var(--gold)}
 .adlock-ic{display:grid;place-items:center;margin:0 auto 8px;color:var(--gold)}
 .adlock-ic svg{width:38px;height:38px;filter:drop-shadow(0 0 8px rgba(245,197,66,.45))}
 .adbox{padding:18px 16px}
 .adclosed{opacity:.62}
 .adclosed .adlock-ic{color:var(--muted)}
 .adclock{margin-top:8px;font-size:36px;font-weight:800;letter-spacing:2px;direction:ltr;background:linear-gradient(180deg,#fff7cf,#f5c542 55%,#c8921a);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 12px rgba(245,197,66,.35))}
 .btn:disabled{opacity:.55;filter:grayscale(.3);cursor:default}
 .btn.pulse{animation:pulseG 1.7s ease-in-out infinite}
 @keyframes pulseG{0%,100%{box-shadow:0 6px 18px rgba(245,197,66,.28)}50%{box-shadow:0 6px 30px rgba(245,197,66,.65)}}
</style>
</head>
<body>
<div class="header">
  <button class="menu-btn" id="menu-open">☰</button>
  <h2 id="title"></h2>
  <span class="logo">
    <svg viewBox="0 0 32 32" fill="none">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#fff1b8"/>
          <stop offset=".55" stop-color="#f5c542"/>
          <stop offset="1" stop-color="#b9861b"/>
        </linearGradient>
      </defs>
      <circle cx="16" cy="16" r="14" stroke="url(#g)" stroke-width="2"/>
      <path d="M16 6L24 16L16 26L8 16L16 6Z" fill="url(#g)"/>
      <path d="M16 11L20 16L16 21L12 16L16 11Z" fill="#060608"/>
    </svg>
  </span>
</div>
<div class="overlay" id="overlay"></div>
<div class="drawer" id="drawer">
  <div class="dhead"><button id="menu-close">✕</button><span id="menu-title"></span></div>
  <div id="nav"></div>
</div>
<p id="welcome" class="muted" style="text-align:center;margin:0"></p>
<div id="view"></div>
<div id="bottom"></div>
<script>
const UI=__UI__, TERMS=__TERMS__, LANG_NAMES=__LANG_NAMES__, AD_ZONE='__AD_ZONE__', OC_SPOT='__OC_SPOT__';
const tg=window.Telegram.WebApp; tg.ready(); tg.expand();
try{tg.setHeaderColor('#060608');tg.setBackgroundColor('#060608');}catch(e){}
const INIT=tg.initData||"";
const $=id=>document.getElementById(id);
const NAVKEY={home:'home',ref:'ref',phone:'phone',app:'apps',site:'sites',ad:'watch',wallet:'wallet',withdraw:'withdraw',terms:'terms'};
const OFFER_KINDS=['phone','app','site','ad'];

const ICONS = {
  home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  ref: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  wallet: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>',
  withdraw: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>',
  menu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>',
  phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>',
  app: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>',
  site: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
  ad: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>',
  terms: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
  lang: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
};

let lang=localStorage.getItem('lang')||((tg.initDataUnsafe&&tg.initDataUnsafe.user&&tg.initDataUnsafe.user.language_code)||'ar').slice(0,2);
if(!UI[lang]) lang='ar';
let state={me:null,tab:'home',offers:null,offerErr:null,err:null,editing:false};

const PAIDL={ar:'الرصيد المنسحب بنجاح',en:'Successfully withdrawn',es:'Retirado con éxito',de:'Erfolgreich ausgezahlt',fr:'Retiré avec succès',ru:'Успешно выведено',pt:'Sacado com sucesso',nl:'Succesvol opgenomen',pl:'Pomyślnie wypłacono'};
const T=k=>(UI[lang]&&UI[lang][k])||UI.en[k]||k;
function h(tag,attrs,...kids){const e=document.createElement(tag);
  for(const k in (attrs||{})){const v=attrs[k];
    if(k==='class') e.className=v; 
    else if(k==='innerHTML') e.innerHTML=v;
    else if(k in e) e[k]=v; else e.setAttribute(k,v);}
  kids.flat().forEach(c=>{if(c==null)return; e.append(c.nodeType?c:document.createTextNode(String(c)));});
  return e;}
function msg(t){ if(tg.showAlert) tg.showAlert(t); else alert(t); }
async function api(path,body){
  const opt={headers:{'X-Init-Data':INIT,'Content-Type':'application/json'}};
  if(body!==undefined){opt.method='POST';opt.body=JSON.stringify(body);}
  try{const r=await fetch(path,opt);return await r.json();}catch(e){return{success:false,code:'err'};}
}
function codeMsg(code){return T('c_'+(code||'err'));}
async function copyText(s){
  try{await navigator.clipboard.writeText(s);}catch(e){const i=h('input',{value:s});document.body.append(i);i.select();document.execCommand('copy');i.remove();}
  msg(T('copied'));
}
function card(...kids){return h('div',{class:'card'},...kids);}

async function loadMe(){const d=await api('/api/me'); if(d.success){state.me=d;state.err=null;}else{state.err=d.code||'err';} render();}
async function go(tab){
  state.tab=tab; closeDrawer(); state.editing=false;
  if(OFFER_KINDS.includes(tab)){
    state.offers=null; state.offerErr=null; render();
    const d=await api('/api/offers?kind='+tab);
    if(d.success){state.offers=d.offers;adApply(d.ads||null);} else {state.offers=[];state.offerErr=d.code;}
  }
  render();
}
function openDrawer(){$('drawer').classList.add('on');$('overlay').classList.add('on');}
function closeDrawer(){$('drawer').classList.remove('on');$('overlay').classList.remove('on');}
$('menu-open').onclick=openDrawer; $('menu-close').onclick=closeDrawer; $('overlay').onclick=closeDrawer;

function buildNav(){
  const nav=$('nav'); nav.replaceChildren();
  const drawerTabs = ['phone','app','site','ad','terms']; 
  drawerTabs.forEach(tab=>{
    const isActive = state.tab === tab;
    nav.append(h('button',{class:'item'+(isActive?' active':''),onclick:()=>go(tab)},
       h('span',{class:'nav-svg',innerHTML:ICONS[tab]}),
       h('span',{},stripLead(T(NAVKEY[tab])))
    ));
  });
  const langWrap = h('div',{style:'margin-top:20px;padding-top:15px;border-top:1px solid rgba(245,197,66,.15)'});
  langWrap.append(h('div',{class:'muted',style:'display:flex;align-items:center;gap:8px;margin-bottom:8px;font-weight:700;color:var(--gold)'}, h('span',{innerHTML:ICONS.lang}), T('lang')));
  const sel=h('select',{onchange:e=>{lang=e.target.value;localStorage.setItem('lang',lang);api('/api/lang',{lang});render();}},
    Object.keys(LANG_NAMES).map(l=>h('option',{value:l,selected:l===lang},LANG_NAMES[l])));
  langWrap.append(sel);
  nav.append(langWrap);
}

const BOT=[['home'],['ref'],['wallet'],['withdraw']];
const stripLead=s=>String(s).replace(/^[^\p{L}\p{N}]+/u,'').trim();
const stripAll=s=>String(s).replace(/[^\p{L}\p{N}\s]+/gu,'').replace(/\s+/g,' ').trim();
function countUp(el,to){
  const t0=performance.now(), dur=1100;
  (function step(t){const k=Math.min(1,(t-t0)/dur), e=1-Math.pow(1-k,3);
    el.textContent=k<1?(to*e).toFixed(2):fb(to); if(k<1) requestAnimationFrame(step);})(t0);
}
function buildBottom(){
  const b=$('bottom'); b.replaceChildren();
  BOT.forEach(([tab])=>b.append(h('button',{class:'nb'+(state.tab===tab?' on':''),onclick:()=>go(tab)},
    h('span',{class:'ni',innerHTML:ICONS[tab]}),h('span',{},stripLead(T(NAVKEY[tab]))))));
  b.append(h('button',{class:'nb'+(BOT.some(x=>x[0]===state.tab)?'':' on'),onclick:openDrawer},
    h('span',{class:'ni',innerHTML:ICONS.menu}),h('span',{},stripAll(T('menu')))));
}

let adBusy=false;
const CLOCK_SVG='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>';
const LOCK_SVG='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>';
const fm=n=>String(+Number(n).toFixed(6));
const fb=n=>{const s=String(+Number(n).toFixed(6));return ((s.split('.')[1]||'').length>=2)?s:Number(n).toFixed(2);};
const hms=s=>[Math.floor(s/3600),Math.floor(s%3600/60),s%60].map(n=>String(n).padStart(2,'0')).join(':');
const secsLeft=base=>Math.max(0,Math.ceil(base-(Date.now()-(state.adsAt||Date.now()))/1000));
function adApply(a){state.ads=a; state.adsAt=Date.now();}
async function refreshAds(){
  const o=await api('/api/offers?kind=ad');
  if(o.success){state.offers=o.offers; adApply(o.ads||null);}
  if(state.tab==='ad') render();
}
let ocP=null;
function ocShow(){
  if(!ocP){
    if(typeof window.initCdTma!=='function') return Promise.reject(new Error('sdk'));
    ocP=Promise.resolve(window.initCdTma({id:OC_SPOT})).catch(e=>{ocP=null;throw e;});
  }
  return ocP.then(r=>{
    let f=null;
    if(typeof r==='function') f=r;
    else if(r&&typeof r==='object'){
      const k=['show','showAd','showVideo','showRewarded','play','run','start','open'].find(n=>typeof r[n]==='function')
        ||Object.keys(r).find(n=>typeof r[n]==='function');
      if(k) f=r[k].bind(r);
    }
    if(!f&&typeof window.show==='function') f=window.show;
    if(!f){ocP=null;throw new Error('no show() from SDK | result='+typeof r+(r&&typeof r==='object'?' keys='+Object.keys(r).join(','):' value='+String(r))+' | window.show='+typeof window.show+' | spot='+OC_SPOT);}
    return f();
  });
}
async function watchAd(btn,i){
  if(adBusy) return;
  const show=window['show_'+AD_ZONE];
  const fid=(state.ads&&state.ads.stages[i].id)||'';
  if(fid==='oc'?typeof window.initCdTma!=='function':(fid==='mt'&&typeof show!=='function')){msg(T('c_ad_sdk'));return;}
  adBusy=true; btn.disabled=true;
  try{
    state.adErr='';
    const s=await api('/api/ad/start',{stage:i});
    if(!s.success){msg(codeMsg(s.code)); state.adErr=s.detail||''; await refreshAds(); return;}
    if(s.fmt==='ab'){state.ab={token:s.token,i:i,at:Date.now()}; msg(T('adSent')); return;}
    try{
      if(s.fmt==='oc'){ await ocShow(); } else { await show(); }
    }catch(e){
      let r=''; try{r=(e&&(e.message||e.error||e.description||e.reason||e.code))||(typeof e==='string'?e:JSON.stringify(e)||'');}catch(_){}
      msg(T('c_ad_fail')); state.adErr=String(r||'').slice(0,300); return;
    }
    const d=await api('/api/ad/complete',{token:s.token});
    if(d.success){adApply(d.ads);} else {msg(codeMsg(d.code)); await refreshAds();}
  }finally{
    adBusy=false; if(state.tab==='ad') render();
  }
}
async function confirmAb(btn){
  if(adBusy||!state.ab) return;
  adBusy=true; btn.disabled=true;
  try{
    const t=state.ab.token; const d=await api('/api/ad/complete',{token:t}); state.ab=null;
    if(d.success){adApply(d.ads);} else {msg(codeMsg(d.code)); await refreshAds();}
  }finally{
    adBusy=false; if(state.tab==='ad') render();
  }
}
async function collectAd(btn,i){
  if(adBusy) return;
  adBusy=true; btn.disabled=true;
  try{
    const d=await api('/api/ad/collect',{stage:i});
    if(d.success){adApply(d.ads); msg(T('c_ok_collect').replace('{r}',fm(d.reward))); await loadMe();}
    else {msg(codeMsg(d.code)); await refreshAds();}
  }finally{
    adBusy=false; if(state.tab==='ad') render();
  }
}
function adCards(root){
  const a=state.ads; if(!a) return;
  const names=[T('adInterT'),T('adPopT'),T('adInterT')];
  a.stages.forEach((s,i)=>{
    const head=[...(a.stages.length>1?[h('div',{class:'adstep'},T('adStepOf').replace('{a}',i+1).replace('{b}',a.stages.length))]:[]),h('b',{},names[i]||'')];
    if(s.lock_left>0){
      root.append(h('div',{class:'card adbox adlock'},...head,
        h('div',{class:'adlock-ic',style:'margin-top:10px',innerHTML:CLOCK_SVG}),
        h('b',{},T('adLockedT')),
        h('p',{class:'muted'},T('adLockedD')),
        h('div',{class:'adclock','data-lock':i},hms(secsLeft(s.lock_left)))));
      return;
    }
    if(!s.open){
      root.append(h('div',{class:'card adbox adclosed'},...head,
        h('div',{class:'adlock-ic',style:'margin-top:10px',innerHTML:LOCK_SVG}),
        h('p',{class:'muted'},T('adClosedT'))));
      return;
    }
    const pct=Math.min(100,Math.round(s.views/s.target*100));
    const box=h('div',{class:'card adbox adstage'},...head,
      h('div',{class:'prog',style:'margin-top:12px'},h('i',{style:'width:'+pct+'%'})),
      h('div',{class:'prog-txt'},h('span',{},T('adProgress').replace('{v}',s.views).replace('{t}',s.target)),h('b',{},pct+'%')),
      h('div',{class:'adearn'},T('adEarned').replace('{r}',fm(s.earned))));
    if(s.ready){
      box.append(h('p',{class:'muted'},T('adDoneHint')));
      const cb=h('button',{class:'btn pulse'},T('adCollect'));
      cb.onclick=()=>collectAd(cb,i); box.append(cb);
    }else if(state.ab&&state.ab.i===i){
      const left=Math.max(0,6-Math.floor((Date.now()-state.ab.at)/1000));
      const ab=h('button',{class:'btn green','data-ab':'1'},left>0?T('adConfirmWait').replace('{s}',left):T('adConfirm'));
      ab.disabled=left>0; ab.onclick=()=>confirmAb(ab); box.append(ab);
    }else{
      const w=a.wait>0?secsLeft(a.wait):0;
      const wb=h('button',{class:'btn green','data-watch':'1'},w>0?T('adWait').replace('{s}',w):T('adWatch'));
      wb.disabled=w>0; wb.onclick=()=>watchAd(wb,i); box.append(wb);
    }
    root.append(box);
  });
  if(state.adErr) root.append(h('p',{class:'muted',dir:'ltr',style:'text-align:left;font-size:11px;word-break:break-all;color:#fda4af'},state.adErr));
}
setInterval(()=>{
  const a=state.ads; if(state.tab!=='ad'||!a||adBusy) return;
  let expired=false;
  document.querySelectorAll('[data-lock]').forEach(el=>{
    const l=secsLeft(a.stages[+el.dataset.lock].lock_left);
    el.textContent=hms(l); if(l<=0) expired=true;
  });
  if(expired){refreshAds();return;}
  if(state.ab){
    const left=Math.max(0,6-Math.floor((Date.now()-state.ab.at)/1000));
    document.querySelectorAll('[data-ab]').forEach(b=>{b.disabled=left>0; b.textContent=left>0?T('adConfirmWait').replace('{s}',left):T('adConfirm');});
  }
  if(a.wait>0){
    const w=secsLeft(a.wait);
    document.querySelectorAll('[data-watch]').forEach(btn=>{
      if(w>0){btn.disabled=true; btn.textContent=T('adWait').replace('{s}',w);}
      else{btn.disabled=false; btn.textContent=T('adWatch');}
    });
    if(w<=0) a.wait=0;
  }
},1000);


const VIEWS={
 home(v){
  const m=state.me, pct=m.min_withdraw>0?Math.min(100,Math.round(m.balance/m.min_withdraw*100)):0;
  const amt=h('span',{class:'amt-n'},fb(m.balance));
  const initial=((m.name||'U').trim()[0]||'U').toUpperCase();
  v.append(h('div',{class:'hero'},
    h('div',{class:'hero-top'},h('div',{class:'chip'}),h('div',{class:'brand'},'TRX EARN')),
    h('div',{class:'hero-label'},T('bal')),
    h('div',{class:'amt'},h('span',{class:'cur'},'TRX'),amt),
    ...(m.min_withdraw>0?[h('div',{class:'prog'},h('i',{style:'width:'+pct+'%'})),
    h('div',{class:'prog-txt'},h('span',{},T('minline').replace('{n}',m.min_withdraw)),h('b',{},pct+'%'))]:[]),
    h('div',{class:'who'},h('div',{class:'av'},initial),h('span',{},m.name||''))));
  if(!state.counted){state.counted=true;countUp(amt,m.balance);}
  v.append(h('div',{class:'tiles'},
    h('div',{class:'tile'},h('small',{},T('pend')),h('b',{},'TRX '+fb(m.pending))),
    h('div',{class:'tile'},h('small',{},T('refCnt')),h('b',{},m.active_referrals)),
    h('div',{class:'tile',style:'grid-column:1/-1'},h('small',{},PAIDL[lang]||PAIDL.en),h('b',{},'TRX '+fb(m.paid_wd||0)))));
  const grid=h('div',{class:'grid2'});
  ['phone','app','site','ad'].forEach(k=>grid.append(h('button',{class:'earn',onclick:()=>go(k)},
    h('span',{class:'ic',innerHTML:ICONS[k]}),h('span',{class:'lb'},stripLead(T(NAVKEY[k]))))));
  v.append(grid);
  v.append(h('details',{class:'card',style:'margin-top:15px;padding:16px'},h('summary',{style:'font-size:14px;line-height:1.5;color:var(--gold);margin-bottom:10px'},T('faqT')),h('p',{class:'muted',style:'white-space:pre-line;font-size:12px;line-height:1.8;color:#e8dcb8;margin:0'},T('faqD'))));
 },
 ref(v){
  const m=state.me;
  v.append(card(h('h3',{},T('refT')),
    h('p',{},T('refCnt')+': ',h('b',{style:'color:var(--gold)'},m.active_referrals)),
    h('p',{class:'muted'},T('refD')),
    h('input',{value:m.ref_link,readOnly:true,onclick:e=>e.target.select()}),
    h('button',{class:'btn',onclick:()=>copyText(m.ref_link)},T('copy'))));
 },
 offers(v,kind){
  const titleKey=NAVKEY[kind];
  const c=card(h('h3',{},T(titleKey)));
  if(kind!=='ad') c.append(h('p',{class:'muted'},T('pendNote')));
  if(state.offers===null) c.append(h('p',{class:'muted'},T('loading')));
  else if(state.offerErr) c.append(h('p',{style:'color:#fda4af'},codeMsg(state.offerErr)));
  else if(!state.offers.length && !(kind==='ad'&&state.ads)) c.append(h('p',{class:'muted'},T('noOffers')));
  else { if(kind==='ad'){v.append(c); adCards(v);} state.offers.forEach(o=>{
    c.append(h('div',{class:'offer'},h('div',{class:'oic',innerHTML:ICONS[kind]}),h('div',{class:'otx'},h('b',{},o.title),h('span',{class:'pill'},'+'+o.reward+' TRX')),
      h('button',{class:'btn green',onclick:()=>{ if(tg.openLink) tg.openLink(o.url); else window.open(o.url,'_blank'); }},T('go'))));
  });}
  if(!c.parentNode) v.append(c);
 },
 wallet(v){
  const m=state.me, has=!!m.trx_address;
  const inp=h('input',{id:'addr',placeholder:'T...',value:m.trx_address,readOnly:has&&!state.editing});
  const btn=h('button',{class:'btn',onclick:async()=>{
    if(has&&!state.editing){state.editing=true;render();return;}
    const d=await api('/api/address',{address:inp.value.trim()});
    if(d.success){state.editing=false;msg(T('c_ok_addr'));await loadMe();} else msg(codeMsg(d.code));
  }},(has&&!state.editing)?T('change'):T('save'));
  v.append(card(h('h3',{},T('wallet')),h('p',{class:'muted'},has&&!state.editing?T('wSaved'):T('wDesc')),inp,btn));
 },
 withdraw(v){
  const m=state.me;
  v.append(card(h('h3',{},T('withdraw')),
    h('div',{class:'big'},'TRX '+fb(m.balance)),
    h('p',{class:'muted'},T('wSaved')),
    h('p',{style:'color:var(--goldsoft);font-weight:bold;word-break:break-all;direction:ltr'},m.trx_address||T('noAddr')),
    h('p',{class:'muted'},T('wdInfo').replace('{n}',m.min_withdraw)),
    ...(m.pending_wd>0?[h('div',{class:'adearn',style:'margin:10px 0'},'⏳ '+T('wdPending').replace('{r}',+m.pending_wd.toFixed(4)))]:[]),
    h('button',{class:'btn red',onclick:async()=>{
      const d=await api('/api/withdraw',{});
      msg(d.success?T('c_ok_withdraw'):codeMsg(d.code)); await loadMe();
    }},T('wdBtn'))));
 },
 terms(v){
  const t=TERMS[lang]||TERMS.en;
  const c=card(h('h3',{},t.title));
  t.sections.forEach(s=>{c.append(h('h4',{},s[0]),h('div',{class:'pre'},s[1]));});
  c.style.textAlign='start'; v.append(c);
 }
};

function render(){
  document.documentElement.lang=lang; document.documentElement.dir=(lang==='ar')?'rtl':'ltr';
  $('title').textContent=T(NAVKEY[state.tab]); $('menu-title').textContent=T('menu'); buildNav(); buildBottom();
  const v=$('view'); v.replaceChildren();
  if(state.err){
    const errorMsg = state.err === 'banned' && UI[lang].c_banned_reversed ? UI[lang].c_banned_reversed : codeMsg(state.err);
    v.append(card(h('p',{},errorMsg))); 
    return;
  }
  if(!state.me){v.append(h('p',{class:'muted',style:'text-align:center'},T('loading'))); return;}
  $('welcome').textContent=T('welcome')+(state.me.name?': '+state.me.name:'');
  if(OFFER_KINDS.includes(state.tab)) VIEWS.offers(v,state.tab); else VIEWS[state.tab](v);
}
if(!INIT){state.err='auth';}
render(); if(INIT){ api('/api/lang',{lang}); loadMe(); }
</script>
</body>
</html>
"""

DB_PATH = os.environ.get("DB_PATH", "bot_database.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()   # رابط PostgreSQL الخارجي: يحفظ البيانات بعد كل نشر
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)
POSTBACK_SECRET = os.environ.get("POSTBACK_SECRET", "")
VERIFY_HOURS = min(72, max(24, int(os.environ.get("VERIFY_HOURS", "48"))))
WITHDRAW_HOURS = int(os.environ.get("WITHDRAW_HOURS", "48"))   # مهلة تنفيذ السحب يدوياً
ADMIN_TZ = int(os.environ.get("ADMIN_TZ_HOURS", "3"))          # فرق التوقيت لعرض الموعد (الأردن +3)
MIN_WITHDRAW = int(os.environ.get("MIN_WITHDRAW", "0"))
REQUIRE_REFERRAL = os.environ.get("REQUIRE_REFERRAL", "0") == "1"   # شرط الإحالة للسحب: ضع 1 لتفعيله
ADS_ENABLED = os.environ.get("ADS_ENABLED", "1") == "1"             # ضع 0 لإيقاف الإعلانات مؤقتاً
REF_PERCENT = float(os.environ.get("REF_PERCENT", "0.03"))
REF_ON_AD = os.environ.get("REF_ON_AD", "1") == "1"                 # 1 = تُحتسب الإحالة بعد أول مشاهدة إعلان للمدعو، 0 = بعد عرض ناجح فقط
IPQS_KEY = os.environ.get("IPQS_KEY", "")
MICRO = 1_000_000

bot = telebot.TeleBot(TOKEN, threaded=False)
server = Flask(__name__)

KINDS = ("phone", "app", "site", "ad")

# إعلانات Monetag: مرحلتان (الأولى فيديو 50 مشاهدة، الثانية سريع 100 مشاهدة). كل القيم قابلة للتغيير من متغيرات البيئة
MONETAG_ZONE = "".join(ch for ch in os.environ.get("MONETAG_ZONE", "12130531") if ch.isdigit()) or "12130531"
MONETAG_SDK_URL = os.environ.get("MONETAG_SDK_URL", "https://libtl.com/sdk.js")
OC_SDK_URL = os.environ.get("OC_SDK_URL", "https://js.onclckvd.com/in-stream-ad-admanager/tma.js")   # Onclicka
OC_SPOT = "".join(ch for ch in os.environ.get("OC_SPOT_ID", "6154562") if ch.isalnum()) or "6154562"
ADSGRAM_TOKEN = os.environ.get("ADSGRAM_TOKEN", "").strip()
ADSGRAM_BLOCK = "".join(ch for ch in os.environ.get("ADSGRAM_BLOCK", "57655") if ch.isdigit()) or "57655"
# oc = Onclicka ، mt = Monetag ، ab = AdsGram (إعلان يُرسل لمحادثة البوت؛ لا يعمل إلا مع ADSGRAM_TOKEN) — بالترتيب
AD_NETS = [x for x in dict.fromkeys(t.strip() for t in os.environ.get("AD_NET", "oc,mt,ab").lower().split(",")) if x in ("mt", "oc") or (x == "ab" and ADSGRAM_TOKEN)] or ["oc", "mt"]
AD_STAGES = [{"fmt": n, "views": int(os.environ.get("AD_VIEWS", "10")), "reward": float(os.environ.get("AD_REWARD", "0.0005")), "min": 6 if n == "ab" else 2} for n in AD_NETS]
AD_COOLDOWN = int(os.environ.get("AD_COOLDOWN_SECONDS", "2"))   # الفاصل بين مشاهدة وأخرى
AD_LOCK_HOURS = int(os.environ.get("AD_LOCK_HOURS", "24"))        # قفل كل مرحلة بعد جمع رصيدها

def load_offers():
    try:
        raw = json.loads(os.environ.get("OFFERS_JSON", "[]"))
    except Exception:
        raw = []
    if not isinstance(raw, list):
        return {}
    offers = {}
    for o in raw:
        if not isinstance(o, dict):
            continue
        try:
            reward = float(o.get("reward", 0))
        except (ValueError, TypeError):
            continue
        if (o.get("id") and o.get("kind") in KINDS
                and str(o.get("url", "")).startswith("https://") and reward > 0):
            offers[str(o["id"])] = o
    return offers

OFFERS = load_offers()

# ======================================================================
# قاعدة البيانات
# ======================================================================
@contextmanager
def tx_sqlite():
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()

DB_PG_SRC = r'''"""
طبقة PostgreSQL: تجعل main.py يحفظ كل البيانات (الأرصدة، المستخدمون، الإحالات...) في قاعدة بيانات خارجية
تبقى كما هي بعد كل نشر أو إعادة تشغيل. تُفعَّل فقط عند وضع المتغير DATABASE_URL.
واجهتها تحاكي sqlite3 المستخدمة في main.py، فلا يتغير منطق البوت.
"""
import queue
import re
import threading
from contextlib import contextmanager
from decimal import Decimal

import psycopg2

LOCK_KEY = 73020261  # قفل عام: يجعل المعاملات تنفَّذ واحدة تلو الأخرى (مثل BEGIN IMMEDIATE في SQLite)

_INSERT_IGNORE = re.compile(r"^\s*INSERT\s+OR\s+IGNORE\s+INTO\s", re.I)
_MAX_TWO = re.compile(r"\bMAX\(([^()]*,[^()]*)\)", re.I)
_RETURN_ID = re.compile(r"^\s*INSERT\s+INTO\s+(withdrawals|transactions)\b", re.I)


class Row(tuple):
    """صف يُقرأ بالرقم row[0] وبالاسم row["balance"] مثل sqlite3.Row."""
    def __new__(cls, names, values):
        r = super().__new__(cls, values)
        r._names = list(names)
        return r

    def __getitem__(self, k):
        if isinstance(k, str):
            return tuple.__getitem__(self, self._names.index(k))
        return tuple.__getitem__(self, k)

    def keys(self):
        return list(self._names)


def translate(sql, escape=True):
    """يحوّل لغة SQLite المستخدمة في main.py إلى لغة PostgreSQL."""
    s = sql.strip().rstrip(";")
    if _INSERT_IGNORE.match(s):
        s = _INSERT_IGNORE.sub("INSERT INTO ", s, count=1) + " ON CONFLICT DO NOTHING"
    s = _MAX_TWO.sub(r"GREATEST(\1)", s)
    if escape:
        s = s.replace("%", "%%").replace("?", "%s")
    return s


def translate_ddl(stmt):
    s = stmt.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
    return re.sub(r"\bINTEGER\b", "BIGINT", s)


def _num(v):
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    return v


class Cursor:
    def __init__(self, raw):
        self._c = raw.cursor()
        self.lastrowid = None
        self.rowcount = -1

    def execute(self, sql, params=()):
        args = tuple(params) if params else None
        s = translate(sql, escape=args is not None)
        want_id = bool(_RETURN_ID.match(s)) and "ON CONFLICT" not in s.upper()
        if want_id:
            s += " RETURNING id"
        self._c.execute(s, args)
        self.rowcount = self._c.rowcount
        if want_id:
            self.lastrowid = self._c.fetchone()[0]
        return self

    def _row(self, values):
        names = [d[0] for d in self._c.description]
        return Row(names, [_num(v) for v in values])

    def fetchone(self):
        r = self._c.fetchone()
        return None if r is None else self._row(r)

    def fetchall(self):
        return [self._row(r) for r in self._c.fetchall()]


class Conn:
    def __init__(self, raw):
        self.raw = raw

    def execute(self, sql, params=()):
        return Cursor(self.raw).execute(sql, params)


class Pool:
    """مجموعة اتصالات صغيرة؛ تتخلص من الاتصال الذي أغلقه الخادم بعد خمول طويل."""
    def __init__(self, dsn, size=5):
        self.dsn = dsn
        self.q = queue.LifoQueue()
        self.sem = threading.Semaphore(size)

    def _new(self):
        return psycopg2.connect(
            self.dsn, connect_timeout=10, keepalives=1, keepalives_idle=30,
            keepalives_interval=10, keepalives_count=3, options="-c statement_timeout=30000")

    def get(self):
        self.sem.acquire()
        try:
            while True:
                try:
                    conn = self.q.get_nowait()
                except queue.Empty:
                    return self._new()
                try:
                    if conn.closed:
                        continue
                    cur = conn.cursor()
                    cur.execute("SELECT 1")
                    cur.close()
                    conn.rollback()
                    return conn
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass
        except Exception:
            self.sem.release()
            raise

    def put(self, conn, bad=False):
        try:
            if bad or conn.closed:
                try:
                    conn.close()
                except Exception:
                    pass
            else:
                self.q.put(conn)
        finally:
            self.sem.release()


def make_tx(dsn):
    pool = Pool(dsn)

    @contextmanager
    def tx():
        raw = pool.get()
        bad = False
        try:
            cur = raw.cursor()
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_KEY,))
            cur.close()
            yield Conn(raw)
            raw.commit()
        except Exception:
            try:
                raw.rollback()
            except Exception:
                bad = True
            raise
        finally:
            pool.put(raw, bad)

    return tx


def init_schema(tx, schema):
    with tx() as c:
        for stmt in schema.split(";"):
            if stmt.strip():
                c.execute(translate_ddl(stmt))
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT ''")
'''

if DATABASE_URL:
    import types
    db_pg = types.ModuleType("db_pg")
    exec(DB_PG_SRC, db_pg.__dict__)
    tx = db_pg.make_tx(DATABASE_URL)
else:
    tx = tx_sqlite

def init_db():
    d = os.path.dirname(DB_PATH)
    if d:
        os.makedirs(d, exist_ok=True)
    schema = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            balance INTEGER NOT NULL DEFAULT 0,
            referred_by INTEGER,
            trx_address TEXT DEFAULT '',
            first_offer_done INTEGER NOT NULL DEFAULT 0,
            banned INTEGER NOT NULL DEFAULT 0,
            ban_reason TEXT DEFAULT '',
            created_at INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txid TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            offer_id TEXT DEFAULT '',
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
            release_at INTEGER NOT NULL,
            approved_at INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions(status, release_at);
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            note TEXT DEFAULT '',
            created_at INTEGER NOT NULL,
            processed_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS ad_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            fmt TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS ad_progress (
            user_id INTEGER PRIMARY KEY,
            stage INTEGER NOT NULL DEFAULT 0,
            views INTEGER NOT NULL DEFAULT 0,
            earned INTEGER NOT NULL DEFAULT 0,
            last_view INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS ad_stage (
            user_id INTEGER NOT NULL,
            stage INTEGER NOT NULL,
            views INTEGER NOT NULL DEFAULT 0,
            earned INTEGER NOT NULL DEFAULT 0,
            opened INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, stage)
        );
        """
    if DATABASE_URL:
        db_pg.init_schema(tx, schema)
        return
    with tx() as c:
        for stmt in schema.split(";"):
            if stmt.strip():
                c.execute(stmt)
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        if "lang" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT ''")

def ensure_user(conn, uid, username="", referrer=None):
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    if row:
        return row
    if referrer:
        ok = referrer != uid and conn.execute("SELECT 1 FROM users WHERE user_id=?", (referrer,)).fetchone()
        referrer = referrer if ok else None
    conn.execute(
        "INSERT INTO users(user_id, username, referred_by, created_at) VALUES(?,?,?,?)",
        (uid, username or "", referrer, int(time.time())),
    )
    return conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()

def active_referrals(conn, uid):
    return conn.execute(
        "SELECT COUNT(*) FROM users WHERE referred_by=? AND first_offer_done=1 AND banned=0", (uid,)
    ).fetchone()[0]

def ban_user(conn, uid, reason):
    conn.execute("UPDATE users SET banned=1, ban_reason=?, balance=0 WHERE user_id=?", (reason, uid))
    conn.execute("UPDATE transactions SET status='reversed' WHERE user_id=? AND status='pending'", (uid,))

def release_matured():
    now = int(time.time())
    unbanned_users = []
    with tx() as c:
        rows = c.execute(
            "SELECT * FROM transactions WHERE status='pending' AND kind!='referral' AND release_at<=?", (now,)
        ).fetchall()
        for t in rows:
            u = c.execute("SELECT * FROM users WHERE user_id=?", (t["user_id"],)).fetchone()
            if not u or u["banned"]:
                c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],))
                continue
            c.execute("UPDATE transactions SET status='approved', approved_at=? WHERE id=?", (now, t["id"]))
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (t["amount"], u["user_id"]))
            if t["kind"] != "ad" and not u["first_offer_done"]:
                c.execute("UPDATE users SET first_offer_done=1 WHERE user_id=?", (u["user_id"],))
            
            ref_id = u["referred_by"]
            if ref_id:
                ref = c.execute("SELECT banned, ban_reason FROM users WHERE user_id=?", (ref_id,)).fetchone()
                commission = int(t["amount"] * REF_PERCENT)
                
                if ref and ref["banned"] and ref["ban_reason"] == 'offer_reversed':
                    refs_count = c.execute("SELECT COUNT(*) FROM users WHERE referred_by=? AND first_offer_done=1 AND banned=0", (ref_id,)).fetchone()[0]
                    if refs_count >= 5:
                        c.execute("UPDATE users SET banned=0, ban_reason='' WHERE user_id=?", (ref_id,))
                        unbanned_users.append(ref_id)
                elif ref and not ref["banned"] and commission > 0:
                    cur = c.execute(
                        "INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at,approved_at) "
                        "VALUES(?,?,?,?,?,'approved',?,?,?)",
                        ("ref:" + t["txid"], ref_id, "referral", str(u["user_id"]), commission, now, now, now),
                    )
                    if cur.rowcount:
                        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (commission, ref_id))
    
    for u_id in unbanned_users:
        try:
            bot.send_message(u_id, "🎉 تم فتح حسابك بنجاح لأنك أحضرت 5 إحالات مكتملة! يمكنك الآن استخدام التطبيق.")
        except Exception:
            pass

def _release_loop():
    while True:
        try:
            release_matured()
        except Exception as e:
            print("release error:", e, flush=True)
        time.sleep(300)

# ======================================================================
# التحقق من الهوية
# ======================================================================
def verify_init_data(init_data):
    if not init_data:
        return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        received = pairs.pop("hash", None)
        if not received:
            return None
        check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, received):
            return None
        if time.time() - int(pairs.get("auth_date", "0")) > 86400:
            return None
        return json.loads(pairs["user"])
    except Exception:
        return None

def auth(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        u = verify_init_data(request.headers.get("X-Init-Data", ""))
        if not u or "id" not in u:
            return jsonify(success=False, code="auth"), 401
        g.user = u
        return fn(*a, **k)
    return wrapper

_ip_cache = {}
def client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    return (xff.split(",")[0].strip() if xff else request.remote_addr) or ""

def is_vpn(ip):
    if not IPQS_KEY or not ip:
        return False
    hit = _ip_cache.get(ip)
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    try:
        r = requests.get(
            f"https://www.ipqualityscore.com/api/json/ip/{IPQS_KEY}/{ip}", params={"strictness": 1}, timeout=5
        ).json()
        bad = bool(r.get("vpn") or r.get("proxy") or r.get("tor") or r.get("active_vpn"))
        _ip_cache[ip] = (time.time(), bad)
        return bad
    except Exception:
        return False

TRX_RE = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")
_bot_username = None
_bot_username_ts = 0.0

def bot_username():
    global _bot_username, _bot_username_ts
    now = time.time()
    if _bot_username and now - _bot_username_ts < 3600:
        return _bot_username
    try:
        got = bot.get_me().username
        _bot_username = got or _bot_username or "TRXEarnBot"
    except Exception:
        _bot_username = _bot_username or "TRXEarnBot"
    _bot_username_ts = now
    return _bot_username

# ======================================================================
# API
# ======================================================================
@server.route("/")
def home():
    return "TRX Bot is running 🚀"

@server.route("/api/me")
@auth
def api_me():
    try:
        release_matured()
    except Exception:
        pass
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or g.user.get("first_name", ""))
        if u["banned"]:
            return jsonify(success=False, code="banned", reason=u["ban_reason"]), 403
        pending = c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND status='pending'", (uid,)
        ).fetchone()[0]
        refs = active_referrals(c, uid)
        pwd = c.execute("SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone()[0]
        paidwd = c.execute("SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE user_id=? AND status='paid'", (uid,)).fetchone()[0]
    return jsonify(
        success=True, pending_wd=pwd / MICRO, paid_wd=paidwd / MICRO, name=g.user.get("first_name", ""), balance=u["balance"] / MICRO,
        pending=(pending + pwd) / MICRO, active_referrals=refs, ref_link=f"https://t.me/{bot_username()}?start={uid}",
        trx_address=u["trx_address"] or "", min_withdraw=MIN_WITHDRAW,
    )

@server.route("/api/offers")
@auth
def api_offers():
    kind = request.args.get("kind", "")
    if kind not in KINDS:
        return jsonify(success=False, code="err"), 400
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
    if is_vpn(client_ip()):
        return jsonify(success=False, code="vpn"), 403
    out = [{"id": o["id"], "title": o.get("title", o["id"]), "reward": float(o["reward"]), "url": o["url"].replace("{user_id}", str(uid))} for o in OFFERS.values() if o["kind"] == kind]
    resp = dict(success=True, offers=out)
    if kind == "ad" and ADS_ENABLED:
        with tx() as c:
            resp["ads"] = ad_state(c, uid, int(time.time()))
    return jsonify(resp)

@server.route("/api/address", methods=["POST"])
@auth
def api_address():
    data = request.get_json(silent=True) or {}
    address = str(data.get("address", "")).strip()
    if not TRX_RE.match(address):
        return jsonify(success=False, code="bad_address")
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        c.execute("UPDATE users SET trx_address=? WHERE user_id=?", (address, uid))
    return jsonify(success=True)

@server.route("/api/withdraw", methods=["POST"])
@auth
def api_withdraw():
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]: return jsonify(success=False, code="banned"), 403
        if not u["trx_address"]: return jsonify(success=False, code="no_address")
        if u["balance"] <= 0 or u["balance"] < MIN_WITHDRAW * MICRO: return jsonify(success=False, code="min_balance")
        if REQUIRE_REFERRAL and active_referrals(c, uid) < 1: return jsonify(success=False, code="need_referral")
        if c.execute("SELECT 1 FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone():
            return jsonify(success=False, code="pending_exists")
        amount = u["balance"]
        c.execute("UPDATE users SET balance=0 WHERE user_id=?", (uid,))
        cur = c.execute("INSERT INTO withdrawals(user_id, amount, address, created_at) VALUES(?,?,?,?)", (uid, amount, u["trx_address"], int(time.time())))
        wid = cur.lastrowid
        now_ts = int(time.time())
        address = u["trx_address"]
        uname = u["username"] or ""
    if not ADMIN_ID:
        print("WARNING: ADMIN_ID غير مضبوط، لن يصلك إشعار السحب. استخدم /withdrawals", flush=True)
    else:
        fname = str(g.user.get("first_name") or "").strip() or "-"
        body = ("💸 طلب سحب جديد #%d\n\n👤 الاسم: %s\n🔗 اليوزر: %s\n🆔 الآيدي: %d\n💰 المبلغ: %.4f TRX\n📮 عنوان TRX:\n%s\n\n%s\n\n/paid %d  أو  /reject %d"
                % (wid, "%s", "%s", uid, amount / MICRO, "%s", wd_deadline(now_ts), wid, wid))
        try:
            bot.send_message(ADMIN_ID, body % (html.escape(fname), ("@" + html.escape(uname)) if uname else "-", "<code>" + html.escape(address) + "</code>"), parse_mode="HTML", reply_markup=wd_buttons(wid))
        except Exception as e:
            print("admin notify (html) failed:", e, flush=True)
            try:
                bot.send_message(ADMIN_ID, body % (fname, ("@" + uname) if uname else "-", address), reply_markup=wd_buttons(wid))
            except Exception as e2:
                print("admin notify failed:", e2, flush=True)
    return jsonify(success=True)

# ======================================================================
# إعلانات Monetag: مراحل مشاهدة، الأرباح تتراكم ثم تُجمع بزر، وبعد آخر مرحلة قفل 24 ساعة
# ======================================================================
def ad_stage_row(conn, uid, i, now):
    """صف تقدم مرحلة واحدة؛ المرحلة الأولى مفتوحة دائماً والتالية تُفتح بعد جمع السابقة، ويُفك القفل بعد 24 ساعة."""
    q = "SELECT * FROM ad_stage WHERE user_id=? AND stage=?"
    r = conn.execute(q, (uid, i)).fetchone()
    if not r:
        conn.execute("INSERT OR IGNORE INTO ad_stage(user_id,stage,opened) VALUES(?,?,?)", (uid, i, 1 if i == 0 else 0))
        r = conn.execute(q, (uid, i)).fetchone()
    if r["locked_until"] and now >= r["locked_until"]:
        conn.execute("UPDATE ad_stage SET views=0, earned=0, locked_until=0 WHERE user_id=? AND stage=?", (uid, i))
        r = conn.execute(q, (uid, i)).fetchone()
    return r

def ad_last_view(conn, uid):
    r = conn.execute("SELECT last_view FROM ad_progress WHERE user_id=?", (uid,)).fetchone()
    if not r:
        conn.execute("INSERT OR IGNORE INTO ad_progress(user_id) VALUES(?)", (uid,))
        return 0
    return r["last_view"]

def ad_state(conn, uid, now):
    last = ad_last_view(conn, uid)
    wait = max(0, AD_COOLDOWN - (now - last)) if last else 0
    stages = []
    for i, cfg in enumerate(AD_STAGES):
        r = ad_stage_row(conn, uid, i, now)
        lock_left = max(0, r["locked_until"] - now) if r["locked_until"] else 0
        stages.append({
            "idx": i, "id": cfg["fmt"], "target": cfg["views"], "views": r["views"],
            "earned": r["earned"] / MICRO, "open": bool(r["opened"]), "lock_left": lock_left,
            "ready": bool(r["views"] >= cfg["views"] and not lock_left),
        })
    return {"stages": stages, "wait": wait}

def _ad_check(st, wait):
    """يرجع رمز الخطأ إن كانت المرحلة لا تقبل مشاهدة الآن."""
    if st["lock_left"] > 0: return "ad_locked"
    if not st["open"]: return "ad_closed"
    if st["ready"]: return "ad_collect"
    if wait > 0: return "ad_cooldown"
    return None

AB_ERR = [""]   # سبب آخر فشل (يظهر للمدير فقط)
def adsgram_send(uid, lang):
    """يطلب إعلاناً من AdsGram ويرسله لمحادثة المستخدم مع البوت. يرجع True عند النجاح."""
    AB_ERR[0] = ""
    try:
        r = requests.get("https://api.adsgram.ai/advbot", timeout=6,
                         params={"tgid": uid, "blockid": ADSGRAM_BLOCK, "language": lang, "token": ADSGRAM_TOKEN})
        if r.status_code != 200:
            AB_ERR[0] = "adsgram http %s: %s" % (r.status_code, (r.text or "")[:140].replace(ADSGRAM_TOKEN, "***")); return False
        d = r.json()
        text = d.get("text_html") or ""
        if not text or not d.get("click_url"):
            AB_ERR[0] = "adsgram empty: %s" % str(d)[:140].replace(ADSGRAM_TOKEN, "***"); return False
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton(d.get("button_name") or "Open", url=d["click_url"]))
        if d.get("reward_url"):
            kb.add(telebot.types.InlineKeyboardButton(d.get("button_reward_name") or "Reward", url=d["reward_url"]))
        img = d.get("image_url")
        kw = dict(parse_mode="HTML", reply_markup=kb)
        try:
            if img and len(text) <= 1000: bot.send_photo(uid, img, caption=text, protect_content=True, **kw)
            else: bot.send_message(uid, text, protect_content=True, **kw)
        except TypeError:
            if img and len(text) <= 1000: bot.send_photo(uid, img, caption=text, **kw)
            else: bot.send_message(uid, text, **kw)
        return True
    except Exception as e:
        AB_ERR[0] = ("error: %s" % e)[:160].replace(ADSGRAM_TOKEN, "***")
        return False

@server.route("/api/ad/start", methods=["POST"])
@auth
def api_ad_start():
    if not ADS_ENABLED:
        return jsonify(success=False, code="ad_invalid")
    uid = g.user["id"]
    if is_vpn(client_ip()):
        return jsonify(success=False, code="vpn"), 403
    try:
        i = int((request.get_json(silent=True) or {}).get("stage", 0))
    except Exception:
        i = -1
    if not 0 <= i < len(AD_STAGES):
        return jsonify(success=False, code="ad_invalid")
    now = int(time.time())
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        info = ad_state(c, uid, now)
        err = _ad_check(info["stages"][i], info["wait"])
        if err:
            return jsonify(success=False, code=err, wait=info["wait"])
        fmt = AD_STAGES[i]["fmt"]
        token = secrets.token_urlsafe(24)
        lang = user_lang(c, uid)
        c.execute("INSERT INTO ad_sessions(token,user_id,fmt,created_at) VALUES(?,?,?,?)", (token, uid, fmt, now))
        c.execute("DELETE FROM ad_sessions WHERE created_at<?", (now - 86400,))
    if fmt == "ab" and not adsgram_send(uid, lang):   # الإرسال خارج المعاملة حتى لا نقفل القاعدة أثناء طلب الشبكة
        with tx() as c:
            c.execute("DELETE FROM ad_sessions WHERE token=?", (token,))
        return jsonify(success=False, code="ad_none", detail=(AB_ERR[0] if uid == ADMIN_ID else ""))
    return jsonify(success=True, token=token, fmt=fmt)

@server.route("/api/ad/complete", methods=["POST"])
@auth
def api_ad_complete():
    if not ADS_ENABLED:
        return jsonify(success=False, code="ad_invalid")
    token = str((request.get_json(silent=True) or {}).get("token", ""))
    uid = g.user["id"]
    now = int(time.time())
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        s = c.execute("SELECT * FROM ad_sessions WHERE token=? AND user_id=?", (token, uid)).fetchone()
        if not s or s["used"] or now - s["created_at"] > 900:
            return jsonify(success=False, code="ad_invalid")
        idx = [k for k, cfg in enumerate(AD_STAGES) if cfg["fmt"] == s["fmt"]]
        if not idx:
            return jsonify(success=False, code="ad_invalid")
        i = idx[0]; cfg = AD_STAGES[i]
        if now - s["created_at"] < cfg["min"]:
            return jsonify(success=False, code="ad_early")
        info = ad_state(c, uid, now)
        err = _ad_check(info["stages"][i], info["wait"])
        if err:
            return jsonify(success=False, code=err, wait=info["wait"])
        c.execute("UPDATE ad_sessions SET used=1 WHERE token=?", (token,))
        c.execute("UPDATE ad_stage SET views=views+1, earned=earned+? WHERE user_id=? AND stage=?",
                  (int(cfg["reward"] * MICRO), uid, i))
        c.execute("UPDATE ad_progress SET last_view=? WHERE user_id=?", (now, uid))
        if REF_ON_AD:
            c.execute("UPDATE users SET first_offer_done=1 WHERE user_id=? AND first_offer_done=0", (uid,))
        out = ad_state(c, uid, now)
    return jsonify(success=True, ads=out)

@server.route("/api/ad/collect", methods=["POST"])
@auth
def api_ad_collect():
    if not ADS_ENABLED:
        return jsonify(success=False, code="ad_invalid")
    uid = g.user["id"]
    now = int(time.time())
    try:
        i = int((request.get_json(silent=True) or {}).get("stage", 0))
    except Exception:
        i = -1
    if not 0 <= i < len(AD_STAGES):
        return jsonify(success=False, code="ad_notready")
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        r = ad_stage_row(c, uid, i, now)
        st = ad_state(c, uid, now)["stages"][i]
        if st["lock_left"] > 0:
            return jsonify(success=False, code="ad_locked")
        if not st["open"] or not st["ready"]:
            return jsonify(success=False, code="ad_notready")
        amount = r["earned"]
        if amount > 0:
            c.execute(
                "INSERT INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) "
                "VALUES(?,?,?,?,?,'pending',?,?)",
                ("adclaim:%d:%s" % (uid, secrets.token_hex(8)), uid, "ad", "monetag:stage%d" % (i + 1), amount, now, now))
        c.execute("UPDATE ad_stage SET views=0, earned=0, opened=?, locked_until=? WHERE user_id=? AND stage=?",
                  (1 if i == 0 else 0, now + AD_LOCK_HOURS * 3600, uid, i))
        if i + 1 < len(AD_STAGES):
            ad_stage_row(c, uid, i + 1, now)
            c.execute("UPDATE ad_stage SET opened=1 WHERE user_id=? AND stage=?", (uid, i + 1))
        out = ad_state(c, uid, now)
    release_matured()
    return jsonify(success=True, reward=amount / MICRO, ads=out)

def _check_secret():
    if not POSTBACK_SECRET: return Response("postback disabled", 503)
    if not hmac.compare_digest(request.args.get("secret", ""), POSTBACK_SECRET): return Response("forbidden", 403)
    return None

@server.route("/postback")
def postback():
    bad = _check_secret()
    if bad: return bad
    txid = request.args.get("txid", "").strip()
    offer = OFFERS.get(request.args.get("offer_id", ""))
    try:
        uid = int(request.args.get("user_id", ""))
    except ValueError:
        return Response("bad user", 400)
    if not txid or not offer: return Response("bad request", 400)
    now = int(time.time())
    hold = 0 if offer["kind"] == "ad" else VERIFY_HOURS * 3600
    amount = int(float(offer["reward"]) * MICRO)
    with tx() as c:
        u = c.execute("SELECT banned FROM users WHERE user_id=?", (uid,)).fetchone()
        if not u or u["banned"]: return Response("ignored", 200)
        cur = c.execute("INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) VALUES(?,?,?,?,?,'pending',?,?)", (txid, uid, offer["kind"], offer["id"], amount, now, now + hold))
        if not cur.rowcount: return Response("duplicate", 200)
    if hold == 0: release_matured()
    return Response("OK", 200)

@server.route("/postback/reverse")
def postback_reverse():
    bad = _check_secret()
    if bad: return bad
    txid = request.args.get("txid", "").strip()
    uid = None
    with tx() as c:
        t = c.execute("SELECT * FROM transactions WHERE txid=? AND kind!='referral'", (txid,)).fetchone()
        if not t or t["status"] == "reversed": return Response("OK", 200)
        uid = t["user_id"]
        c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],))
        r = c.execute("SELECT * FROM transactions WHERE txid=? AND status='approved'", ("ref:" + txid,)).fetchone()
        if r:
            c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (r["id"],))
            c.execute("UPDATE users SET balance=MAX(balance-?,0) WHERE user_id=?", (r["amount"], r["user_id"]))
        ban_user(c, uid, "offer_reversed")
        lang = user_lang(c, uid)
    try:
        bot.send_message(uid, msg_for(lang, "reversed"))
    except Exception:
        pass
    return Response("OK", 200)

# ======================================================================
# النصوص والترجمات
# ======================================================================
HEADS = {"ar": ["🌍 عن البوت", "⚠️ تنبيه مهم جداً", "💰 حد السحب الأدنى", "🚫 المحظورات", "⏳ التحقق من الأرباح", "👥 نظام الإحالة", "💸 السحب"], "en": ["🌍 About", "⚠️ Important warning", "💰 Minimum withdrawal", "🚫 Prohibited", "⏳ Earnings verification", "👥 Referrals", "💸 Withdrawals"], "es": ["🌍 Sobre el bot", "⚠️ Aviso importante", "💰 Retiro mínimo", "🚫 Prohibido", "⏳ Verificación", "👥 Referidos", "💸 Retiros"], "de": ["🌍 Über den Bot", "⚠️ Wichtige Warnung", "💰 Mindestauszahlung", "🚫 Verboten", "⏳ Verifizierung", "👥 Empfehlungen", "💸 Auszahlungen"], "fr": ["🌍 À propos", "⚠️ Avertissement important", "💰 Retrait minimum", "🚫 Interdit", "⏳ Vérification", "👥 Parrainage", "💸 Retraits"], "ru": ["🌍 О боте", "⚠️ Важное предупреждение", "💰 Минимум для вывода", "🚫 Запрещено", "⏳ Проверка начислений", "👥 Рефералы", "💸 Вывод"], "pt": ["🌍 Sobre o bot", "⚠️ Aviso importante", "💰 Saque mínimo", "🚫 Proibido", "⏳ Verificação", "👥 Indicações", "💸 Saques"], "nl": ["🌍 Over de bot", "⚠️ Belangrijke waarschuwing", "💰 Minimum opname", "🚫 Verboden", "⏳ Verificatie", "👥 Referrals", "💸 Opnames"], "pl": ["🌍 O bocie", "⚠️ Ważne ostrzeżenie", "💰 Minimalna wypłata", "🚫 Zakazy", "⏳ Weryfikacja", "👥 Polecenia", "💸 Wypłaty"]}

BODIES = {
    "ar": ["البوت منصة لتحقيق الربح من:\n🎬 مشاهدة الإعلانات\n📱 عروض الاشتراك برقم الهاتف\n📝 عروض التسجيل\n📲 تثبيت التطبيقات", "لا تدفع أي مبلغ لأي منصة أو موقع أو شخص أثناء استخدام البوت. كل المهام مجانية بالكامل. أي جهة تطلب مالاً باسم البوت فهي احتيال، وسيتم حظر أي مستخدم يطلب أموالاً من غيره.", "السحب متاح مهما كان رصيدك.", "❌ استخدام VPN أو البروكسي\n❌ استخدام الواي فاي (المطلوب بيانات الجوال)\n❌ أكثر من حساب للشخص الواحد\n❌ بيانات وهمية أو أرقام غير حقيقية\n❌ التلاعب بالعروض أو برامج الغش", "لا يُضاف رصيد تثبيت التطبيقات أو التسجيل أو الاشتراك برقم الهاتف إلا بعد التحقق، وتستغرق من 24 إلى 72 ساعة (حالياً {h} ساعة). إذا ألغيت الاشتراك أو حذفت التطبيق أو ألغيت التسجيل فسيُلغى حسابك مباشرة مع أرباحه.", "تحصل على 3% من أرباح كل من تدعوه، مدى الحياة. لا تُحتسب الإحالة إلا بعد أن يشترك المدعو ويُكمل عرضاً ناجحاً واحداً على الأقل (اشتراك/تسجيل/تثبيت).", "لا يمكن السحب إلا بعد أن تُحضر مستخدماً حقيقياً يُكمل أول عرض ناجح له، وبعد بلوغ الحد الأدنى. تراجع الإدارة كل طلب قبل الدفع، ويحق لها حظر أي حساب مخالف وإلغاء أرباحه."],
    "en": ["A platform to earn from:\n🎬 Watching ads\n📱 Phone-number subscription offers\n📝 Registration offers\n📲 App installs", "Never pay any money to any platform, website or person while using the bot. All tasks are completely free. Anyone asking for money in the bot's name is a scammer, and users who ask others for money will be banned.", "Withdrawal is available at any balance.", "❌ VPN or proxy of any kind\n❌ Wi-Fi (mobile data is required)\n❌ More than one account per person\n❌ Fake data or unreal numbers\n❌ Cheating or manipulating offers", "Rewards for app installs, registrations and phone subscriptions are credited only after verification, which takes 24 to 72 hours (currently {h}h). If you cancel the subscription, uninstall the app or cancel the registration, your account and its earnings are cancelled immediately.", "Earn 3% of your referrals' earnings for life. A referral counts only after the invited user completes at least one successful offer (subscription/registration/install).", "You can withdraw only after bringing a real user who completes their first successful offer, and after reaching the minimum. Every request is reviewed before payment, and accounts that break the rules may be banned and their earnings cancelled."],
    "es": ["Plataforma para ganar con:\n🎬 Ver anuncios\n📱 Suscripciones con número de teléfono\n📝 Registros\n📲 Instalar apps", "No pagues dinero a ninguna plataforma, sitio o persona. Todas las tareas son gratuitas. Quien pida dinero en nombre del bot es un estafador y será bloqueado.", "El retiro está disponible con cualquier saldo.", "❌ VPN o proxy\n❌ Wi-Fi (usa datos móviles)\n❌ Más de una cuenta por persona\n❌ Datos falsos\n❌ Trampas", "El saldo de instalaciones, registros y suscripciones telefónicas se acredita solo tras verificar (24–72 h, ahora {h} h). Si cancelas la suscripción, borras la app o anulas el registro, tu cuenta y ganancias se cancelan de inmediato.", "Ganas 3% de por vida de lo que ganen tus referidos. Un referido cuenta solo cuando completa al menos una oferta exitosa.", "Solo puedes retirar después de traer a un usuario real que complete su primera oferta exitosa y alcanzar el mínimo. Cada solicitud se revisa antes de pagar."],
    "de": ["Plattform zum Verdienen durch:\n🎬 Werbung ansehen\n📱 Telefon-Abos\n📝 Registrierungen\n📲 App-Installationen", "Zahlen Sie niemals Geld an Plattformen, Websites oder Personen. Alle Aufgaben sind kostenlos. Wer im Namen des Bots Geld verlangt, ist ein Betrüger und wird gesperrt.", "Die Auszahlung ist bei jedem Guthaben möglich.", "❌ VPN oder Proxy\n❌ WLAN (Mobilfunkdaten nutzen)\n❌ Mehrere Konten pro Person\n❌ Falsche Daten\n❌ Betrug", "Belohnungen für Installationen, Registrierungen und Telefon-Abos werden erst nach Prüfung gutgeschrieben (24–72 Std., aktuell {h} Std.). Bei Kündigung, Deinstallation oder Abmeldung wird Ihr Konto sofort gelöscht.", "3% lebenslang auf die Einnahmen Ihrer Empfehlungen. Eine Empfehlung zählt erst nach mindestens einem erfolgreichen Angebot.", "Auszahlung nur, nachdem ein echter Nutzer sein erstes erfolgreiches Angebot abgeschlossen hat und das Minimum erreicht ist. Jeder Antrag wird vorher geprüft."],
    "fr": ["Plateforme pour gagner avec :\n🎬 Pubs\n📱 Abonnements par téléphone\n📝 Inscriptions\n📲 Installations d'apps", "Ne payez jamais d'argent à une plateforme, un site ou une personne. Tout est gratuit. Quiconque demande de l'argent au nom du bot est un escroc et sera banni.", "Le retrait est disponible quel que soit le solde.", "❌ VPN ou proxy\n❌ Wi-Fi (utilisez les données mobiles)\n❌ Plusieurs comptes par personne\n❌ Fausses données\n❌ Triche", "Les gains d'installation, d'inscription et d'abonnement téléphonique sont crédités après vérification (24–72 h, actuellement {h} h). Si vous annulez l'abonnement, désinstallez l'app ou annulez l'inscription, votre compte est supprimé immédiatement.", "3% à vie sur les gains de vos filleuls. Un filleul compte seulement après au moins une offre réussie.", "Retrait possible uniquement après qu'un vrai utilisateur parrainé a terminé sa première offre réussie et que le minimum est atteint. Chaque demande est examinée avant paiement."],
    "ru": ["Платформа для заработка на:\n🎬 Просмотре рекламы\n📱 Подписках по номеру телефона\n📝 Регистрациях\n📲 Установке приложений", "Никому не платите деньги. Все задания бесплатны. Тот, кто просит деньги от имени бота, — мошенник и будет заблокирован.", "Вывод доступен при любом балансе.", "❌ VPN или прокси\n❌ Wi-Fi (используйте мобильный интернет)\n❌ Несколько аккаунтов\n❌ Фейковые данные\n❌ Обман", "Начисления за установки, регистрации и подписки по телефону зачисляются только после проверки (24–72 ч, сейчас {h} ч). Если вы отмените подписку, удалите приложение или отмените регистрацию, аккаунт будет аннулирован сразу.", "3% пожизненно от заработка рефералов. Реферал засчитывается после хотя бы одного успешного задания.", "Вывод возможен только после того, как реальный приглашённый пользователь выполнит первое успешное задание, и при достижении минимума. Каждая заявка проверяется."],
    "pt": ["Plataforma para ganhar com:\n🎬 Anúncios\n📱 Assinaturas por telefone\n📝 Registros\n📲 Instalação de apps", "Não pague dinheiro a nenhuma plataforma, site ou pessoa. Tudo é gratuito. Quem pedir dinheiro em nome do bot é golpista e será banido.", "O saque está disponível com qualquer saldo.", "❌ VPN ou proxy\n❌ Wi-Fi (use dados móveis)\n❌ Contas múltiplas\n❌ Dados falsos\n❌ Trapaças", "Os ganhos de instalações, registros e assinaturas por telefone só são creditados após verificação (24–72 h, atualmente {h} h). Se cancelar a assinatura, desinstalar o app ou cancelar o registro, sua conta será cancelada imediatamente.", "3% vitalício sobre os ganhos dos seus indicados. A indicação só conta após ao menos uma oferta bem-sucedida.", "O saque só é possível depois que um usuário real indicado concluir a primeira oferta bem-sucedida e o mínimo for atingido. Cada pedido é revisado antes do pagamento."],
    "nl": ["Platform om te verdienen met:\n🎬 Advertenties\n📱 Telefoonabonnementen\n📝 Registraties\n📲 App-installaties", "Betaal nooit geld aan een platform, website of persoon. Alles is gratis. Wie namens de bot geld vraagt is een oplichter en wordt geblokkeerd.", "Opnemen is mogelijk bij elk saldo.", "❌ VPN of proxy\n❌ Wi-Fi (gebruik mobiele data)\n❌ Meerdere accounts\n❌ Nepgegevens\n❌ Valsspelen", "Beloningen voor installaties, registraties en telefoonabonnementen worden pas na verificatie bijgeschreven (24–72 uur, nu {h} uur). Bij opzeggen, verwijderen van de app of annuleren van de registratie wordt je account direct geannuleerd.", "3% levenslang van de winst van je referrals. Een referral telt pas na minstens één geslaagde aanbieding.", "Opnemen kan pas nadat een echte genodigde zijn eerste geslaagde aanbieding heeft voltooid en het minimum is bereikt. Elk verzoek wordt eerst beoordeeld."],
    "pl": ["Platforma do zarabiania na:\n🎬 Reklamach\n📱 Subskrypcjach telefonicznych\n📝 Rejestracjach\n📲 Instalacji aplikacji", "Nigdy nie płać żadnej platformie, stronie ani osobie. Wszystko jest darmowe. Kto żąda pieniędzy w imieniu bota, jest oszustem i zostanie zablokowany.", "Wypłata jest dostępna przy każdym saldzie.", "❌ VPN lub proxy\n❌ Wi-Fi (używaj danych mobilnych)\n❌ Wiele kont\n❌ Fałszywe dane\n❌ Oszustwa", "Nagrody za instalacje, rejestracje i subskrypcje telefoniczne są dodawane dopiero po weryfikacji (24–72 godz., obecnie {h} godz.). Anulowanie subskrypcji, usunięcie aplikacji lub rejestracji natychmiast anuluje konto.", "3% dożywotnio od zarobków poleconych. Polecenie liczy się po co najmniej jednej udanej ofercie.", "Wypłata możliwa dopiero po tym, jak prawdziwy zaproszony użytkownik ukończy pierwszą udaną ofertę i osiągniesz minimum. Każdy wniosek jest sprawdzany."]
}

TERMS_TITLE = {"ar": "📜 شروط وأحكام TRX Earn Bot", "en": "📜 TRX Earn Bot Terms & Conditions", "es": "📜 Términos de TRX Earn Bot", "de": "📜 AGB von TRX Earn Bot", "fr": "📜 Conditions de TRX Earn Bot", "ru": "📜 Условия TRX Earn Bot", "pt": "📜 Termos do TRX Earn Bot", "nl": "📜 Voorwaarden van TRX Earn Bot", "pl": "📜 Regulamin TRX Earn Bot"}
AGREE_BTN = {"ar": "أوافق وأفتح التطبيق المصغر 🚀", "en": "I Agree & Open Mini App 🚀", "es": "Aceptar y abrir Mini App 🚀", "de": "Zustimmen & Mini App öffnen 🚀", "fr": "Accepter et ouvrir l'App 🚀", "ru": "Согласен, открыть Mini App 🚀", "pt": "Concordar e abrir Mini App 🚀", "nl": "Akkoord & Mini App openen 🚀", "pl": "Zgadzam się i otwórz 🚀"}
LANGS = list(HEADS.keys())

def terms_sections(lang):
    lang = lang if lang in HEADS else "en"
    bodies = [b.replace("{min}", str(MIN_WITHDRAW)).replace("{h}", str(VERIFY_HOURS)) for b in BODIES[lang]]
    return [[h, b] for h, b in zip(HEADS[lang], bodies)]

def terms_html(lang):
    lang = lang if lang in HEADS else "en"
    parts = [f"<b>{html.escape(TERMS_TITLE[lang])}</b>\n"]
    for h, b in terms_sections(lang):
        parts.append(f"<b>{html.escape(h)}</b>\n{html.escape(b)}\n")
    return "\n".join(parts)

UI = json.loads(r'''{
 "en": {
  "home": "🏠 Home",
  "ref": "👥 Referrals",
  "phone": "📱 Phone Subscription",
  "apps": "📲 Install Apps",
  "sites": "🌐 Register on Sites",
  "wallet": "💳 Wallet",
  "withdraw": "💸 Withdraw",
  "watch": "▶️ Watch & Earn",
  "terms": "📜 Terms",
  "menu": "Menu ⚙️",
  "welcome": "Welcome",
  "bal": "Current TRX balance",
  "pend": "Pending verification",
  "minline": "Minimum withdrawal: {n} TRX",
  "faqT": "❓ Important Rules & Instructions",
  "faqD": "💸 **Withdrawal:** You can withdraw after reaching the minimum and bringing 1 real completed referral.\n👥 **Referrals:** Earn 3% for life from your referrals' earnings.\n🚫 **Cancelling Offers:** If you cancel a subscription or delete an app, your account will be suspended. To unlock it, you must bring 5 completed referrals OR complete a new successful offer.",
  "refT": "👥 Referral system (3%)",
  "refCnt": "Active referrals",
  "refD": "Share your link and earn 3% of your referrals' earnings for life. A referral counts only after they complete one successful offer.",
  "copy": "Copy referral link 🔗",
  "copied": "Copied! 📋",
  "noOffers": "No offers available right now.",
  "go": "Start ✅",
  "reward": "Reward",
  "pendNote": "Credited after verification (24–72h). Cancelling = account ban.",
  "wDesc": "Enter your TRX (TRC20) wallet address:",
  "save": "Save 💾",
  "change": "Change 🔄",
  "wSaved": "Saved address:",
  "noAddr": "No address added yet",
  "wdBtn": "Request withdrawal 🚀",
  "wdInfo": "Your whole balance is withdrawn. Needs min {n} TRX and one real active referral.",
  "lang": "🌐 Language",
  "loading": "Loading…",
  "c_auth": "Session expired. Please close and reopen the app from the bot.",
  "c_banned": "Your account has been banned for breaking the terms.",
  "c_vpn": "VPN/Proxy detected. Turn it off and use mobile data.",
  "c_bad_address": "Invalid TRX address.",
  "c_ok_addr": "Address saved 💾",
  "c_no_address": "Please add your TRX wallet address first.",
  "c_min_balance": "Your balance is below the minimum withdrawal.",
  "c_need_referral": "You need one real referral who completed their first successful offer.",
  "c_pending_exists": "You already have a pending withdrawal.",
  "c_ok_withdraw": "Withdrawal request submitted 🚀",
  "c_err": "Something went wrong. Try again."
 },
 "ar": {
  "home": "🏠 الرئيسية",
  "ref": "👥 الإحالة",
  "phone": "📱 الربح من الاشتراك برقم هاتف",
  "apps": "📲 الربح من تثبيت تطبيقات",
  "sites": "🌐 الربح من التسجيل في المواقع",
  "wallet": "💳 المحفظة",
  "withdraw": "💸 السحب",
  "watch": "▶️ الربح من المشاهدة",
  "terms": "📜 الشروط والأحكام",
  "menu": "القائمة ⚙️",
  "welcome": "مرحباً بك",
  "bal": "رصيد TRX الحالي",
  "pend": "قيد التحقق",
  "minline": "الحد الأدنى للسحب: {n} TRX",
  "faqT": "❓ قواعد وتعليمات هامة",
  "faqD": "💸 **السحب:** يمكنك السحب بعد وصولك للحد الأدنى وإحضار إحالة حقيقية واحدة مكتملة.\n👥 **الإحالات:** تحصل على 3% مدى الحياة من أرباح إحالاتك.\n🚫 **إلغاء العروض:** في حال قمت بإلغاء اشتراك أو حذف تطبيق، سيتم إيقاف حسابك. لفتح الحساب مرة أخرى، يجب عليك إحضار 5 إحالات مكتملة (أكملن عرضاً ناجحاً) أو إكمال عرض ناجح جديد.",
  "refT": "👥 نظام الإحالة (3%)",
  "refCnt": "عدد إحالاتك النشطة",
  "refD": "شارك رابطك وخذ 3% من أرباح من تدعوه مدى الحياة. لا تُحتسب الإحالة إلا بعد إكمال المدعو عرضاً ناجحاً.",
  "copy": "نسخ رابط الإحالة 🔗",
  "copied": "تم النسخ! 📋",
  "noOffers": "لا توجد عروض متاحة حالياً.",
  "go": "ابدأ ✅",
  "reward": "المكافأة",
  "pendNote": "تُضاف بعد التحقق (24–72 ساعة). الإلغاء = حظر الحساب.",
  "wDesc": "أدخل عنوان محفظة TRX (TRC20) الخاصة بك:",
  "save": "حفظ 💾",
  "change": "تغيير 🔄",
  "wSaved": "العنوان المحفوظ:",
  "noAddr": "لم تضف عنواناً بعد",
  "wdBtn": "طلب السحب 🚀",
  "wdInfo": "يتم سحب كامل رصيدك. الشرط: {n} TRX كحد أدنى + إحالة حقيقية نشطة.",
  "lang": "🌐 اللغة",
  "loading": "جارٍ التحميل…",
  "c_auth": "انتهت الجلسة. أغلق التطبيق وافتحه من البوت من جديد.",
  "c_banned": "تم حظر حسابك لمخالفة الشروط.",
  "c_vpn": "تم اكتشاف VPN/بروكسي. أطفئه واستخدم بيانات الجوال.",
  "c_bad_address": "عنوان TRX غير صحيح.",
  "c_ok_addr": "تم حفظ العنوان 💾",
  "c_no_address": "أضف عنوان محفظة TRX أولاً.",
  "c_min_balance": "رصيدك أقل من الحد الأدنى للسحب.",
  "c_need_referral": "يجب أن تُحضر مستخدماً حقيقياً أكمل أول عرض ناجح له.",
  "c_pending_exists": "لديك طلب سحب قيد المراجعة.",
  "c_ok_withdraw": "تم تقديم طلب السحب 🚀",
  "c_err": "حدث خطأ. حاول مرة أخرى."
 },
 "es": {
  "home": "🏠 Inicio",
  "ref": "👥 Referidos",
  "phone": "📱 Suscripción telefónica",
  "apps": "📲 Instalar apps",
  "sites": "🌐 Registrarse en sitios",
  "wallet": "💳 Billetera",
  "withdraw": "💸 Retirar",
  "watch": "▶️ Ver y ganar",
  "terms": "📜 Términos",
  "menu": "Menú ⚙️",
  "welcome": "Bienvenido",
  "bal": "Saldo actual de TRX",
  "pend": "Pendiente de verificación",
  "minline": "Retiro mínimo: {n} TRX",
  "faqT": "❓ Reglas e instrucciones importantes",
  "faqD": "💸 **Retiro:** Puedes retirar al alcanzar el mínimo y traer 1 referido real completado.\n👥 **Referidos:** Gana 3% de por vida de las ganancias de tus referidos.\n🚫 **Cancelar ofertas:** Si cancelas una suscripción o eliminas una app, tu cuenta será suspendida. Para desbloquearla, debes traer 5 referidos completados O completar una nueva oferta exitosa.",
  "refT": "👥 Sistema de referidos (3%)",
  "refCnt": "Referidos activos",
  "refD": "Comparte tu enlace y gana el 3% de las ganancias de tus referidos de por vida. Un referido cuenta solo cuando completa una oferta exitosa.",
  "copy": "Copiar enlace de referido 🔗",
  "copied": "¡Copiado! 📋",
  "noOffers": "No hay ofertas disponibles ahora.",
  "go": "Empezar ✅",
  "reward": "Recompensa",
  "pendNote": "Se acredita tras la verificación (24–72 h). Cancelar = bloqueo de la cuenta.",
  "wDesc": "Introduce tu dirección de billetera TRX (TRC20):",
  "save": "Guardar 💾",
  "change": "Cambiar 🔄",
  "wSaved": "Dirección guardada:",
  "noAddr": "Aún no has añadido una dirección",
  "wdBtn": "Solicitar retiro 🚀",
  "wdInfo": "Se retira todo tu saldo. Requiere un mínimo de {n} TRX y un referido real activo.",
  "lang": "🌐 Idioma",
  "loading": "Cargando…",
  "c_auth": "La sesión expiró. Cierra y vuelve a abrir la app desde el bot.",
  "c_banned": "Tu cuenta fue bloqueada por incumplir los términos.",
  "c_vpn": "Se detectó VPN/proxy. Desactívalo y usa datos móviles.",
  "c_bad_address": "Dirección TRX no válida.",
  "c_ok_addr": "Dirección guardada 💾",
  "c_no_address": "Primero añade tu dirección de billetera TRX.",
  "c_min_balance": "Tu saldo es inferior al retiro mínimo.",
  "c_need_referral": "Necesitas un referido real que haya completado su primera oferta exitosa.",
  "c_pending_exists": "Ya tienes un retiro pendiente.",
  "c_ok_withdraw": "Solicitud de retiro enviada 🚀",
  "c_err": "Algo salió mal. Inténtalo de nuevo."
 },
 "de": {
  "home": "🏠 Startseite",
  "ref": "👥 Empfehlungen",
  "phone": "📱 Telefon-Abo",
  "apps": "📲 Apps installieren",
  "sites": "🌐 Auf Websites registrieren",
  "wallet": "💳 Wallet",
  "withdraw": "💸 Auszahlen",
  "watch": "▶️ Ansehen & verdienen",
  "terms": "📜 AGB",
  "menu": "Menü ⚙️",
  "welcome": "Willkommen",
  "bal": "Aktuelles TRX-Guthaben",
  "pend": "Wird geprüft",
  "minline": "Mindestauszahlung: {n} TRX",
  "faqT": "❓ Wichtige Regeln & Anweisungen",
  "faqD": "💸 **Auszahlung:** Du kannst auszahlen, wenn du das Minimum erreichst und 1 echte abgeschlossene Empfehlung bringst.\n👥 **Empfehlungen:** Verdiene lebenslang 3% an den Einnahmen deiner Empfehlungen.\n🚫 **Angebote abbrechen:** Wenn du ein Abo kündigst oder eine App löschst, wird dein Konto gesperrt. Um es zu entsperren, musst du 5 abgeschlossene Empfehlungen bringen ODER ein neues erfolgreiches Angebot abschließen.",
  "refT": "👥 Empfehlungssystem (3%)",
  "refCnt": "Aktive Empfehlungen",
  "refD": "Teile deinen Link und erhalte lebenslang 3% der Einnahmen deiner Empfehlungen. Eine Empfehlung zählt erst nach einem erfolgreichen Angebot.",
  "copy": "Empfehlungslink kopieren 🔗",
  "copied": "Kopiert! 📋",
  "noOffers": "Derzeit keine Angebote verfügbar.",
  "go": "Start ✅",
  "reward": "Belohnung",
  "pendNote": "Gutschrift nach Prüfung (24–72 Std.). Abbruch = Kontosperre.",
  "wDesc": "Gib deine TRX-Wallet-Adresse (TRC20) ein:",
  "save": "Speichern 💾",
  "change": "Ändern 🔄",
  "wSaved": "Gespeicherte Adresse:",
  "noAddr": "Noch keine Adresse hinzugefügt",
  "wdBtn": "Auszahlung anfordern 🚀",
  "wdInfo": "Dein gesamtes Guthaben wird ausgezahlt. Erfordert mindestens {n} TRX und eine echte aktive Empfehlung.",
  "lang": "🌐 Sprache",
  "loading": "Wird geladen…",
  "c_auth": "Sitzung abgelaufen. Schließe die App und öffne sie erneut über den Bot.",
  "c_banned": "Dein Konto wurde wegen Verstoßes gegen die Bedingungen gesperrt.",
  "c_vpn": "VPN/Proxy erkannt. Schalte es aus und nutze mobile Daten.",
  "c_bad_address": "Ungültige TRX-Adresse.",
  "c_ok_addr": "Adresse gespeichert 💾",
  "c_no_address": "Füge zuerst deine TRX-Wallet-Adresse hinzu.",
  "c_min_balance": "Dein Guthaben liegt unter der Mindestauszahlung.",
  "c_need_referral": "Du brauchst eine echte Empfehlung, die ihr erstes erfolgreiches Angebot abgeschlossen hat.",
  "c_pending_exists": "Du hast bereits eine offene Auszahlung.",
  "c_ok_withdraw": "Auszahlungsantrag gesendet 🚀",
  "c_err": "Etwas ist schiefgelaufen. Versuche es erneut."
 },
 "fr": {
  "home": "🏠 Accueil",
  "ref": "👥 Parrainage",
  "phone": "📱 Abonnement téléphone",
  "apps": "📲 Installer des apps",
  "sites": "🌐 S'inscrire sur des sites",
  "wallet": "💳 Portefeuille",
  "withdraw": "💸 Retirer",
  "watch": "▶️ Regarder et gagner",
  "terms": "📜 Conditions",
  "menu": "Menu ⚙️",
  "welcome": "Bienvenue",
  "bal": "Solde TRX actuel",
  "pend": "En cours de vérification",
  "minline": "Retrait minimum : {n} TRX",
  "faqT": "❓ Règles et instructions importantes",
  "faqD": "💸 **Retrait:** Vous pouvez retirer après avoir atteint le minimum et apporté 1 vrai filleul complété.\n👥 **Parrainage:** Gagnez 3% à vie sur les gains de vos filleuls.\n🚫 **Annuler des offres:** Si vous annulez un abonnement ou supprimez une app, votre compte sera suspendu. Pour le débloquer, vous devez apporter 5 filleuls complétés OU compléter une nouvelle offre réussie.",
  "refT": "👥 Système de parrainage (3%)",
  "refCnt": "Filleuls actifs",
  "refD": "Partagez votre lien et gagnez 3% des gains de vos filleuls à vie. Un filleul compte seulement après une offre réussie.",
  "copy": "Copier le lien de parrainage 🔗",
  "copied": "Copié ! 📋",
  "noOffers": "Aucune offre disponible pour le moment.",
  "go": "Commencer ✅",
  "reward": "Récompense",
  "pendNote": "Crédité après vérification (24–72 h). Annuler = compte banni.",
  "wDesc": "Entrez votre adresse de portefeuille TRX (TRC20) :",
  "save": "Enregistrer 💾",
  "change": "Modifier 🔄",
  "wSaved": "Adresse enregistrée :",
  "noAddr": "Aucune adresse ajoutée",
  "wdBtn": "Demander le retrait 🚀",
  "wdInfo": "Tout votre solde est retiré. Il faut au minimum {n} TRX et un vrai filleul actif.",
  "lang": "🌐 Langue",
  "loading": "Chargement…",
  "c_auth": "Session expirée. Fermez l'app et rouvrez-la depuis le bot.",
  "c_banned": "Votre compte a été banni pour non-respect des conditions.",
  "c_vpn": "VPN/proxy détecté. Désactivez-le et utilisez les données mobiles.",
  "c_bad_address": "Adresse TRX invalide.",
  "c_ok_addr": "Adresse enregistrée 💾",
  "c_no_address": "Ajoutez d'abord votre adresse de portefeuille TRX.",
  "c_min_balance": "Votre solde est inférieur au retrait minimum.",
  "c_need_referral": "Il vous faut un vrai filleul ayant terminé sa première offre réussie.",
  "c_pending_exists": "Vous avez déjà un retrait en attente.",
  "c_ok_withdraw": "Demande de retrait envoyée 🚀",
  "c_err": "Une erreur s'est produite. Réessayez."
 },
 "ru": {
  "home": "🏠 Главная",
  "ref": "👥 Рефералы",
  "phone": "📱 Подписка по телефону",
  "apps": "📲 Установка приложений",
  "sites": "🌐 Регистрация на сайтах",
  "wallet": "💳 Кошелёк",
  "withdraw": "💸 Вывод",
  "watch": "▶️ Смотреть и зарабатывать",
  "terms": "📜 Условия",
  "menu": "Меню ⚙️",
  "welcome": "Добро пожаловать",
  "bal": "Текущий баланс TRX",
  "pend": "На проверке",
  "minline": "Минимальный вывод: {n} TRX",
  "faqT": "❓ Важные правила и инструкции",
  "faqD": "💸 **Вывод:** Вы можете вывести средства после достижения минимума и привлечения 1 реального завершенного реферала.\n👥 **Рефералы:** Получайте 3% пожизненно от заработка ваших рефералов.\n🚫 **Отмена предложений:** Если вы отмените подписку или удалите приложение, ваш аккаунт будет заблокирован. Чтобы разблокировать его, вы должны привлечь 5 завершенных рефералов ИЛИ выполнить новое успешное предложение.",
  "refT": "👥 Реферальная система (3%)",
  "refCnt": "Активные рефералы",
  "refD": "Поделитесь ссылкой и получайте 3% от заработка рефералов пожизненно. Реферал засчитывается только после одного успешного задания.",
  "copy": "Копировать реферальную ссылку 🔗",
  "copied": "Скопировано! 📋",
  "noOffers": "Сейчас нет доступных предложений.",
  "go": "Начать ✅",
  "reward": "Награда",
  "pendNote": "Начисляется после проверки (24–72 ч). Отмена = блокировка аккаунта.",
  "wDesc": "Введите адрес вашего кошелька TRX (TRC20):",
  "save": "Сохранить 💾",
  "change": "Изменить 🔄",
  "wSaved": "Сохранённый адрес:",
  "noAddr": "Адрес ещё не добавлен",
  "wdBtn": "Запросить вывод 🚀",
  "wdInfo": "Выводится весь баланс. Нужно минимум {n} TRX и один реальный активный реферал.",
  "lang": "🌐 Язык",
  "loading": "Загрузка…",
  "c_auth": "Сессия истекла. Закройте приложение и откройте его снова через бота.",
  "c_banned": "Ваш аккаунт заблокирован за нарушение условий.",
  "c_vpn": "Обнаружен VPN/прокси. Отключите его и используйте мобильный интернет.",
  "c_bad_address": "Неверный адрес TRX.",
  "c_ok_addr": "Адрес сохранён 💾",
  "c_no_address": "Сначала добавьте адрес кошелька TRX.",
  "c_min_balance": "Ваш баланс ниже минимального для вывода.",
  "c_need_referral": "Нужен один реальный реферал, выполнивший первое успешное задание.",
  "c_pending_exists": "У вас уже есть заявка на вывод в обработке.",
  "c_ok_withdraw": "Заявка на вывод отправлена 🚀",
  "c_err": "Что-то пошло не так. Попробуйте ещё раз."
 },
 "pt": {
  "home": "🏠 Início",
  "ref": "👥 Indicações",
  "phone": "📱 Assinatura por telefone",
  "apps": "📲 Instalar apps",
  "sites": "🌐 Registrar em sites",
  "wallet": "💳 Carteira",
  "withdraw": "💸 Sacar",
  "watch": "▶️ Assistir e ganhar",
  "terms": "📜 Termos",
  "menu": "Menu ⚙️",
  "welcome": "Bem-vindo",
  "bal": "Saldo atual de TRX",
  "pend": "Aguardando verificação",
  "minline": "Saque mínimo: {n} TRX",
  "faqT": "❓ Regras e instruções importantes",
  "faqD": "💸 **Saque:** Você pode sacar após atingir o mínimo e trazer 1 indicado real concluído.\n👥 **Indicações:** Ganhe 3% para sempre dos ganhos dos seus indicados.\n🚫 **Cancelar ofertas:** Se você cancelar uma assinatura ou excluir um app, sua conta será suspensa. Para desbloquear, você deve trazer 5 indicados concluídos OU concluir uma nova oferta bem-sucedida.",
  "refT": "👥 Sistema de indicações (3%)",
  "refCnt": "Indicações ativas",
  "refD": "Compartilhe seu link e ganhe 3% dos ganhos dos seus indicados para sempre. Uma indicação só conta depois de uma oferta bem-sucedida.",
  "copy": "Copiar link de indicação 🔗",
  "copied": "Copiado! 📋",
  "noOffers": "Nenhuma oferta disponível no momento.",
  "go": "Começar ✅",
  "reward": "Recompensa",
  "pendNote": "Creditado após a verificação (24–72 h). Cancelar = conta banida.",
  "wDesc": "Digite o endereço da sua carteira TRX (TRC20):",
  "save": "Salvar 💾",
  "change": "Alterar 🔄",
  "wSaved": "Endereço salvo:",
  "noAddr": "Nenhum endereço adicionado ainda",
  "wdBtn": "Solicitar saque 🚀",
  "wdInfo": "Todo o seu saldo é sacado. Exige no mínimo {n} TRX e um indicado real ativo.",
  "lang": "🌐 Idioma",
  "loading": "Carregando…",
  "c_auth": "Sessão expirada. Feche o app e abra-o novamente pelo bot.",
  "c_banned": "Sua conta foi banida por violar os termos.",
  "c_vpn": "VPN/proxy detectado. Desative e use dados móveis.",
  "c_bad_address": "Endereço TRX inválido.",
  "c_ok_addr": "Endereço salvo 💾",
  "c_no_address": "Adicione primeiro o endereço da sua carteira TRX.",
  "c_min_balance": "Seu saldo está abaixo do saque mínimo.",
  "c_need_referral": "Você precisa de um indicado real que tenha concluído a primeira oferta bem-sucedida.",
  "c_pending_exists": "Você já tem um saque pendente.",
  "c_ok_withdraw": "Pedido de saque enviado 🚀",
  "c_err": "Algo deu errado. Tente novamente."
 },
 "nl": {
  "home": "🏠 Home",
  "ref": "👥 Referrals",
  "phone": "📱 Telefoonabonnement",
  "apps": "📲 Apps installeren",
  "sites": "🌐 Registreren op sites",
  "wallet": "💳 Wallet",
  "withdraw": "💸 Opnemen",
  "watch": "▶️ Kijken en verdienen",
  "terms": "📜 Voorwaarden",
  "menu": "Menu ⚙️",
  "welcome": "Welkom",
  "bal": "Huidig TRX-saldo",
  "pend": "In afwachting van verificatie",
  "minline": "Minimum opname: {n} TRX",
  "faqT": "❓ Belangrijke regels & instructies",
  "faqD": "💸 **Opname:** Je kunt opnemen na het bereiken van het minimum en het aanbrengen van 1 echte voltooide referral.\n👥 **Referrals:** Verdien levenslang 3% van de winst van je referrals.\n🚫 **Aanbiedingen annuleren:** Als je een abonnement opzegt of een app verwijdert, wordt je account geblokkeerd. Om het te deblokkeren, moet je 5 voltooide referrals aanbrengen OF een nieuwe succesvolle aanbieding voltooien.",
  "refT": "👥 Referralsysteem (3%)",
  "refCnt": "Actieve referrals",
  "refD": "Deel je link en verdien levenslang 3% van de winst van je referrals. Een referral telt pas na één geslaagde aanbieding.",
  "copy": "Referrallink kopiëren 🔗",
  "copied": "Gekopieerd! 📋",
  "noOffers": "Er zijn nu geen aanbiedingen beschikbaar.",
  "go": "Start ✅",
  "reward": "Beloning",
  "pendNote": "Bijgeschreven na verificatie (24–72 uur). Annuleren = account geblokkeerd.",
  "wDesc": "Voer je TRX-walletadres (TRC20) in:",
  "save": "Opslaan 💾",
  "change": "Wijzigen 🔄",
  "wSaved": "Opgeslagen adres:",
  "noAddr": "Nog geen adres toegevoegd",
  "wdBtn": "Opname aanvragen 🚀",
  "wdInfo": "Je hele saldo wordt opgenomen. Vereist minimaal {n} TRX en één echte actieve referral.",
  "lang": "🌐 Taal",
  "loading": "Laden…",
  "c_auth": "Sessie verlopen. Sluit de app en open hem opnieuw via de bot.",
  "c_banned": "Je account is geblokkeerd wegens schending van de voorwaarden.",
  "c_vpn": "VPN/proxy gedetecteerd. Schakel het uit en gebruik mobiele data.",
  "c_bad_address": "Ongeldig TRX-adres.",
  "c_ok_addr": "Adres opgeslagen 💾",
  "c_no_address": "Voeg eerst je TRX-walletadres toe.",
  "c_min_balance": "Je saldo is lager dan de minimale opname.",
  "c_need_referral": "Je hebt één echte referral nodig die zijn eerste geslaagde aanbieding heeft voltooid.",
  "c_pending_exists": "Je hebt al een openstaande opname.",
  "c_ok_withdraw": "Opnameverzoek verzonden 🚀",
  "c_err": "Er ging iets mis. Probeer het opnieuw."
 },
 "pl": {
  "home": "🏠 Start",
  "ref": "👥 Polecenia",
  "phone": "📱 Subskrypcja telefoniczna",
  "apps": "📲 Instaluj aplikacje",
  "sites": "🌐 Rejestracja na stronach",
  "wallet": "💳 P
