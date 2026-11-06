# واجهة التطبيق المصغّر (HTML + CSS + JS) — نص كامل غير مضغوط
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
 .pdesc{margin:8px 0 2px;text-align:start;font-size:13.5px;line-height:1.9;color:#d8cfae} .pdesc b{display:block;margin-bottom:4px;color:var(--gold);font-size:15px} .pdesc p{margin:2px 0} .btnbig{font-size:18px;padding:17px;margin-top:14px} .btn:disabled{filter:grayscale(.45) brightness(.85);cursor:default}
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



function phoneInfo(){
  const d=h('div',{class:'pdesc'},h('b',{},T('phH')));
  ['phD1','phD2','phD3','phD4','phD5'].forEach(k=>d.append(h('p',{},'• '+T(k))));
  return d;
}
function phoneBtn(o){
  const btn=h('button',{class:'btn btnbig'},T('subGo'));
  const end=Date.now()+(o.sub_left||0)*1000;
  const tick=()=>{
    const left=Math.ceil((end-Date.now())/1000);
    if(left>0){const mm=String(Math.floor(left/60)).padStart(2,'0'),ss=String(left%60).padStart(2,'0');btn.disabled=true;btn.textContent=T('subWait').replace('{t}',mm+':'+ss);}
    else{btn.disabled=false;btn.textContent=T('subGo');}
  };
  btn.onclick=()=>{if(tg.openLink) tg.openLink(o.url); else window.open(o.url,'_blank');};
  tick(); clearInterval(window._subT); if(o.sub_left>0) window._subT=setInterval(tick,1000);
  return btn;
}
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
  if(kind==='phone') c.append(phoneInfo());
  else if(kind!=='ad') c.append(h('p',{class:'muted'},T('pendNote')));
  if(state.offers===null) c.append(h('p',{class:'muted'},T('loading')));
  else if(state.offerErr) c.append(h('p',{style:'color:#fda4af'},codeMsg(state.offerErr)));
  else if(!state.offers.length && !(kind==='ad'&&state.ads)) c.append(h('p',{class:'muted'},T('noOffers')));
  else { if(kind==='ad'){v.append(c); adCards(v);} state.offers.forEach(o=>{
    if(kind==='phone'){c.append(phoneBtn(o));return;}
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
  clearInterval(window._subT);
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
