"""
SmartPrint AI — Premium Landing Page (Final Architecture)

Uses st.components.v1.html() for all visual HTML to bypass Streamlit's
markdown parser completely. Only routing buttons use real st.button().
"""
import streamlit as st
import streamlit.components.v1 as components


def show_landing():
    # Inject base CSS reset into Streamlit shell
    st.html(_SHELL_CSS)

    # Render entire landing page directly into the main DOM (no iframe!)
    st.html(_FULL_HTML)


# ─── Shell CSS: hides Streamlit chrome + styles routing buttons ──────────────
_SHELL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800;900&display=swap');
html,body,.stApp,.stApp>div,section.main,.block-container,
[data-testid="stAppViewContainer"],[data-testid="stMainBlockContainer"],
[data-testid="stMain"],[data-testid="stVerticalBlock"]{
  background:#050505!important;color:#fff!important;
  font-family:'Space Grotesk','Inter',sans-serif!important;
}
.appview-container .main .block-container{padding:0!important;max-width:100%!important;margin:0!important;}
[data-testid="stMainBlockContainer"]{padding:0!important;}
[data-testid="stVerticalBlockBorderWrapper"]{padding:0!important;}
#MainMenu,footer,header,[data-testid="stDecoration"],[data-testid="stStatusWidget"]{visibility:hidden!important;height:0!important;overflow:hidden!important;}
*,*::before,*::after{box-sizing:border-box;}
::-webkit-scrollbar{width:4px;}::-webkit-scrollbar-track{background:#050505;}::-webkit-scrollbar-thumb{background:rgba(0,217,255,.4);border-radius:4px;}
</style>
"""


# ─── Full landing page HTML (rendered inside st.components.v1.html) ───────────
_FULL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{font-family:'Space Grotesk','Inter',sans-serif;background:#050505;color:#fff;overflow-x:hidden;}
body{background:#050505;min-height:100%;}
::-webkit-scrollbar{width:4px;}::-webkit-scrollbar-track{background:#050505;}::-webkit-scrollbar-thumb{background:rgba(0,217,255,.4);border-radius:4px;}

/* ═══ HERO BACKGROUND — premium volumetric lighting ═══ */
.bg{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;}

/* Volumetric orbs — dark, barely-there depth */
.orb{position:absolute;border-radius:50%;filter:blur(140px);animation:orbanim 24s ease-in-out infinite;}
.o1{width:1000px;height:1000px;background:radial-gradient(circle,rgba(0,100,55,.10),transparent 65%);top:-400px;left:-350px;}
.o2{width:720px;height:720px;background:radial-gradient(circle,rgba(0,120,80,.08),transparent 65%);top:15%;right:-260px;animation-delay:-9s;}
.o3{width:620px;height:620px;background:radial-gradient(circle,rgba(0,70,150,.08),transparent 65%);bottom:-120px;left:18%;animation-delay:-18s;}
.o4{width:440px;height:440px;background:radial-gradient(circle,rgba(0,217,255,.05),transparent 65%);bottom:12%;right:6%;animation-delay:-5s;filter:blur(130px);}
/* Subtle center depth orb */
.o5{width:340px;height:340px;background:radial-gradient(circle,rgba(124,255,0,.04),transparent 65%);top:35%;left:38%;animation-delay:-12s;filter:blur(110px);}
@keyframes orbanim{0%,100%{transform:translate(0,0);}25%{transform:translate(30px,-30px);}50%{transform:translate(50px,20px);}75%{transform:translate(-20px,40px);}}

/* Cyberpunk grid — near invisible, just a hint */
.grid{position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(0,217,255,.012) 1px,transparent 1px),linear-gradient(90deg,rgba(0,217,255,.012) 1px,transparent 1px);
  background-size:70px 70px;}

/* Energy light streaks — very subtle */
.streak{position:fixed;pointer-events:none;z-index:0;opacity:0;animation:streakfly linear infinite;}
.sk1{top:22%;left:0;width:35%;height:1px;background:linear-gradient(90deg,transparent,rgba(0,217,255,.12),transparent);animation-duration:10s;animation-delay:0s;}
.sk2{top:56%;left:0;width:50%;height:1px;background:linear-gradient(90deg,transparent,rgba(124,255,0,.08),transparent);animation-duration:13s;animation-delay:-5s;}
.sk3{top:78%;left:0;width:28%;height:1px;background:linear-gradient(90deg,transparent,rgba(0,245,255,.10),transparent);animation-duration:15s;animation-delay:-8s;}
@keyframes streakfly{0%{opacity:0;transform:translateX(-100%);}10%{opacity:1;}90%{opacity:.5;}100%{opacity:0;transform:translateX(300%);}}

/* Ambient fog rings — removed for darker feel */
.ring{display:none;}

.pt{position:fixed;border-radius:50%;animation:ptup linear infinite;pointer-events:none;z-index:0;}
.p1{width:2px;height:2px;background:#00D9FF;left:7%;animation-duration:24s;opacity:.7;}
.p2{width:3px;height:3px;background:#7CFF00;left:19%;animation-duration:31s;animation-delay:-8s;opacity:.5;}
.p3{width:2px;height:2px;background:#00F5FF;left:38%;animation-duration:21s;animation-delay:-14s;opacity:.65;}
.p4{width:3px;height:3px;background:#39FF14;left:55%;animation-duration:28s;animation-delay:-5s;opacity:.4;}
.p5{width:2px;height:2px;background:#00D9FF;left:70%;animation-duration:23s;animation-delay:-11s;opacity:.7;}
.p6{width:2px;height:2px;background:#00FF66;left:84%;animation-duration:19s;animation-delay:-3s;opacity:.6;}
@keyframes ptup{0%{transform:translateY(100vh);opacity:0;}5%{opacity:1;}95%{opacity:.6;}100%{transform:translateY(-8vh);opacity:0;}}

/* Live dot */
.dot{width:6px;height:6px;border-radius:50%;background:#10b981;animation:dotpulse 2s infinite;display:inline-block;vertical-align:middle;margin-right:5px;}
@keyframes dotpulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(16,185,129,.5);}50%{opacity:.4;box-shadow:0 0 0 5px rgba(16,185,129,0);}}

/* PAGE WRAPPER */
.page-wrap{width:100%;max-width:1500px;margin:0 auto;padding:0 48px;box-sizing:border-box;}

/* ═══ PREMIUM NAVBAR ═══ */
nav{
  display:flex;align-items:center;justify-content:space-between;
  padding:12px 24px;margin:20px 0 0;width:100%;
  border-radius:22px;
  background:rgba(4,6,18,.88);backdrop-filter:blur(32px) saturate(180%);
  border:1px solid rgba(0,217,255,.1);
  box-shadow:0 8px 48px rgba(0,0,0,.7),inset 0 1px 0 rgba(255,255,255,.06),0 0 0 1px rgba(0,217,255,.04);
  position:sticky;top:16px;z-index:600;
  transition:box-shadow .3s ease;
}
nav:hover{box-shadow:0 8px 60px rgba(0,0,0,.75),inset 0 1px 0 rgba(255,255,255,.07),0 0 0 1px rgba(0,217,255,.08),0 0 30px rgba(0,217,255,.05);}
.nav-actions{display:flex;gap:12px;align-items:center;}

/* Login button */
.btn-li-nav{
  display:inline-flex;align-items:center;gap:6px;
  background:rgba(255,255,255,.05);
  border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:10px 20px;
  color:#c8d8e8;font-size:.83rem;font-weight:700;text-decoration:none;
  transition:all .28s ease;font-family:'Space Grotesk',sans-serif;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.06);
}
.btn-li-nav:hover{background:rgba(0,217,255,.1);border-color:rgba(0,217,255,.4);color:#fff;transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.08);}

/* Get Started button */
.btn-gs-nav{
  display:inline-flex;align-items:center;gap:7px;
  background:linear-gradient(135deg,#00D9FF,#7CFF00);
  border:none;border-radius:12px;padding:10px 20px;
  color:#000;font-size:.83rem;font-weight:800;text-decoration:none;
  box-shadow:0 4px 18px rgba(0,217,255,.45),0 0 0 1px rgba(0,217,255,.2);
  transition:all .28s cubic-bezier(.22,1,.36,1);font-family:'Space Grotesk',sans-serif;
  position:relative;overflow:hidden;
}
.btn-gs-nav::after{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(255,255,255,.18),transparent 60%);border-radius:12px;}
.btn-gs-nav:hover{transform:translateY(-2px) scale(1.03);box-shadow:0 10px 32px rgba(0,217,255,.60),0 0 0 1px rgba(0,217,255,.3);}

.logo{font-size:1.12rem;font-weight:900;display:flex;align-items:center;gap:9px;}
.logo-ico{
  width:34px;height:34px;border-radius:10px;
  background:linear-gradient(135deg,#00D9FF,#7CFF00);
  display:flex;align-items:center;justify-content:center;font-size:1rem;
  box-shadow:0 4px 16px rgba(0,217,255,.55),inset 0 1px 0 rgba(255,255,255,.3);
  position:relative;
}
.logo span{background:linear-gradient(135deg,#00F5FF,#7CFF00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-.3px;}

/* Nav links — now clickable with smooth scroll */
.nav-links{display:flex;gap:6px;align-items:center;}
.nav-l{
  font-size:.79rem;font-weight:600;color:rgba(255,255,255,.4);
  cursor:pointer;transition:all .22s ease;
  padding:6px 12px;border-radius:10px;position:relative;
  text-decoration:none;border:none;background:none;
}
.nav-l:hover{color:rgba(255,255,255,.9);background:rgba(255,255,255,.05);}
.nav-l.on{color:#fff;background:rgba(0,217,255,.07);}
.nav-l.on::after{
  content:'';position:absolute;bottom:2px;left:12px;right:12px;height:2px;
  border-radius:2px;background:linear-gradient(90deg,#00D9FF,#7CFF00);
}
.nav-l:focus{outline:none;}
.badge{display:flex;align-items:center;gap:5px;font-size:.6rem;font-weight:800;color:#10b981;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);padding:4px 12px;border-radius:18px;letter-spacing:.8px;}

/* ═══ PREMIUM HERO ═══ */
.hero{
  display:grid;grid-template-columns:1fr 1fr;gap:48px;
  padding:48px 0 0;margin:0;width:100%;
  position:relative;z-index:1;align-items:center;
  min-height:calc(100vh - 120px);
}

/* Left side entrance animation */
.hero-l{animation:hlfade .7s ease both;}
@keyframes hlfade{from{opacity:0;transform:translateY(22px);}to{opacity:1;transform:none;}}

/* Eyebrow badge */
.eyebrow{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(0,217,255,.08);border:1px solid rgba(0,217,255,.3);
  color:#00F5FF;font-size:.6rem;font-weight:800;letter-spacing:2.5px;
  text-transform:uppercase;padding:6px 16px;border-radius:20px;margin-bottom:22px;
  box-shadow:0 0 20px rgba(0,217,255,.12),inset 0 1px 0 rgba(255,255,255,.08);
  animation:eyebrowglow 3s ease-in-out infinite;
}
@keyframes eyebrowglow{0%,100%{box-shadow:0 0 14px rgba(0,217,255,.1);}50%{box-shadow:0 0 28px rgba(0,217,255,.25);}}

/* Headline */
h1{
  font-size:5rem;font-weight:900;
  line-height:.95;letter-spacing:-4px;
  margin-bottom:22px;
  filter:drop-shadow(0 4px 24px rgba(0,217,255,.12));
}
.h1w{
  display:block;color:#fff;
  text-shadow:0 2px 40px rgba(255,255,255,.08);
  letter-spacing:-3px;
}
.h1g{
  display:block;
  background:linear-gradient(135deg,#00D9FF 0%,#00F5FF 30%,#7CFF00 65%,#39FF14 100%);
  background-size:200% 200%;
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  animation:hg 4s ease-in-out infinite;
  filter:drop-shadow(0 0 30px rgba(0,217,255,.3));
}
@keyframes hg{0%,100%{background-position:0% 50%;}50%{background-position:100% 50%;}}

/* Sub text */
.hsub{
  font-size:.97rem;color:rgba(255,255,255,.48);
  line-height:1.88;max-width:460px;margin-bottom:34px;
  font-weight:400;letter-spacing:.1px;
}

/* Button row */
.btn-row{display:flex;gap:14px;margin-bottom:30px;flex-wrap:wrap;}

/* Primary CTA — Get Started */
.btn-gs{
  display:inline-flex;align-items:center;gap:8px;
  background:linear-gradient(135deg,#00D9FF 0%,#00F5FF 40%,#7CFF00 100%);
  border:none;border-radius:14px;padding:15px 30px;
  color:#000;font-size:.93rem;font-weight:800;
  font-family:'Space Grotesk',sans-serif;cursor:pointer;
  box-shadow:0 6px 30px rgba(0,217,255,.55),0 0 0 1px rgba(0,217,255,.2),inset 0 1px 0 rgba(255,255,255,.3);
  transition:all .35s cubic-bezier(.22,1,.36,1);
  position:relative;overflow:hidden;
  text-decoration:none;
}
.btn-gs::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(255,255,255,.22) 0%,transparent 55%);
  border-radius:14px;
}
.btn-gs::after{
  content:'';position:absolute;inset:0;border-radius:14px;
  background:radial-gradient(ellipse at 30% 30%,rgba(255,255,255,.15),transparent 60%);
  opacity:0;transition:opacity .3s;
}
.btn-gs:hover{transform:translateY(-5px) scale(1.04);box-shadow:0 18px 50px rgba(0,217,255,.70),0 0 0 1px rgba(0,217,255,.35);}
.btn-gs:hover::after{opacity:1;}
.btn-gs:active{transform:translateY(-2px) scale(1.01);}

/* Secondary — Login */
.btn-li{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(255,255,255,.05);
  border:1px solid rgba(255,255,255,.14);
  border-radius:14px;padding:15px 26px;
  color:#d0e8ff;font-size:.93rem;font-weight:700;
  font-family:'Space Grotesk',sans-serif;cursor:pointer;
  box-shadow:0 4px 18px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.07);
  transition:all .3s ease;
  text-decoration:none;position:relative;overflow:hidden;
  backdrop-filter:blur(10px);
}
.btn-li::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(0,217,255,.08),transparent 60%);
  opacity:0;transition:opacity .3s;border-radius:14px;
}
.btn-li:hover{background:rgba(0,217,255,.1);border-color:rgba(0,217,255,.45);color:#fff;transform:translateY(-4px);box-shadow:0 12px 36px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.1),0 0 20px rgba(0,217,255,.12);}
.btn-li:hover::before{opacity:1;}

/* Tags */
.tags{display:flex;flex-wrap:wrap;gap:8px;}
.tag{display:inline-flex;align-items:center;gap:5px;font-size:.62rem;font-weight:700;letter-spacing:.7px;text-transform:uppercase;padding:5px 13px;border-radius:20px;backdrop-filter:blur(10px);transition:all .25s ease;cursor:default;}
.tag:hover{transform:translateY(-2px);}
.ta{background:rgba(0,217,255,.1);border:1px solid rgba(0,217,255,.22);color:#00D9FF;}
.tb{background:rgba(0,255,102,.1);border:1px solid rgba(0,255,102,.22);color:#39FF14;}
.tc{background:rgba(0,245,255,.1);border:1px solid rgba(0,245,255,.22);color:#00F5FF;}
.td{background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.22);color:#34d399;}
.te{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.22);color:#fbbf24;}
.tf{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.22);color:#f87171;}
.tg{background:rgba(0,183,255,.1);border:1px solid rgba(0,183,255,.22);color:#00B7FF;}
.th{background:rgba(124,255,0,.1);border:1px solid rgba(124,255,0,.22);color:#7CFF00;}

/* ═══ HERO RIGHT — Premium 3D Dashboard ═══ */
.hero-r{
  position:relative;display:flex;align-items:flex-start;
  justify-content:center;padding-top:14px;
  animation:hrfade .8s ease .15s both;
}
@keyframes hrfade{from{opacity:0;transform:translateX(32px);}to{opacity:1;transform:none;}}

/* Ground glow platform */
.platform{
  position:absolute;bottom:-20px;left:50%;transform:translateX(-50%);
  width:85%;height:28px;
  background:radial-gradient(ellipse,rgba(0,217,255,.65),rgba(0,245,255,.35) 55%,transparent 78%);
  filter:blur(20px);border-radius:50%;animation:platf 3.5s ease-in-out infinite;
}
@keyframes platf{0%,100%{opacity:.65;transform:translateX(-50%) scaleX(1);}50%{opacity:1;transform:translateX(-50%) scaleX(1.15);}}

/* Dashboard card */
.dash{
  background:linear-gradient(160deg,rgba(6,14,20,.97) 0%,rgba(4,10,16,.98) 100%);
  border:1px solid rgba(0,217,255,.22);
  border-radius:26px;padding:22px;
  width:100%;max-width:455px;
  box-shadow:
    0 0 0 1px rgba(255,255,255,.03),
    0 40px 100px rgba(0,0,0,.95),
    0 0 80px rgba(0,217,255,.1),
    inset 0 1px 0 rgba(255,255,255,.07),
    inset 1px 0 0 rgba(0,217,255,.05);
  transform:perspective(1200px) rotateY(-7deg) rotateX(4deg);
  transition:transform .6s cubic-bezier(.22,1,.36,1),box-shadow .6s ease;
  position:relative;overflow:hidden;
}
.dash:hover{
  transform:perspective(1200px) rotateY(-2deg) rotateX(1deg);
  box-shadow:
    0 0 0 1px rgba(255,255,255,.04),
    0 50px 120px rgba(0,0,0,.95),
    0 0 100px rgba(0,217,255,.16),
    inset 0 1px 0 rgba(255,255,255,.09);
}
/* Top edge gradient bar */
.dash::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent 0%,#00D9FF 30%,#7CFF00 60%,#00F5FF 80%,transparent 100%);
  animation:topbar 3s ease-in-out infinite;
}
@keyframes topbar{0%,100%{opacity:.45;}50%{opacity:1;}}
/* Corner reflections */
.dash::after{
  content:'';position:absolute;top:0;left:0;
  width:200px;height:200px;
  background:radial-gradient(ellipse at top left,rgba(0,217,255,.08),transparent 60%);
  border-radius:26px;
}
/* Scan line */
.scan{
  position:absolute;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,rgba(0,217,255,.85),rgba(0,245,255,1),rgba(0,217,255,.85),transparent);
  box-shadow:0 0 12px rgba(0,245,255,.9),0 0 30px rgba(0,217,255,.4);
  animation:scan 3.2s ease-in-out infinite;z-index:10;pointer-events:none;
}
@keyframes scan{0%{top:0;opacity:0;}8%{opacity:1;}88%{opacity:.8;}100%{top:100%;opacity:0;}}

/* Dashboard header */
.dh{
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:14px;padding-bottom:10px;
  border-bottom:1px solid rgba(255,255,255,.05);
}
.dht{font-size:.68rem;font-weight:800;color:rgba(255,255,255,.45);letter-spacing:1.5px;text-transform:uppercase;}
.live{display:flex;align-items:center;gap:5px;font-size:.58rem;font-weight:800;color:#10b981;background:rgba(16,185,129,.09);border:1px solid rgba(16,185,129,.22);padding:3px 10px;border-radius:16px;letter-spacing:.8px;}

/* GPU Perf bar at top of dashboard */
.gpu-bar{display:flex;gap:6px;margin-bottom:10px;align-items:center;}
.gpu-bar-label{font-size:.52rem;font-weight:800;color:rgba(0,217,255,.6);letter-spacing:1px;text-transform:uppercase;flex-shrink:0;}
.gpu-bar-track{flex:1;height:5px;background:rgba(255,255,255,.05);border-radius:99px;overflow:hidden;}
.gpu-bar-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,#00D9FF,#7CFF00);box-shadow:0 0 8px rgba(0,217,255,.6);animation:gpufill 2.5s ease both;}
@keyframes gpufill{from{width:0!important;}}

.dr1{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;}
.doc{background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:12px;overflow:hidden;}
.docn{font-size:.58rem;font-weight:700;color:rgba(255,255,255,.35);margin-bottom:8px;letter-spacing:.4px;}
.docn em{color:#00D9FF;font-style:normal;margin-right:4px;}
.dlines{display:flex;flex-direction:column;gap:5px;}
.dl{height:4px;border-radius:3px;background:rgba(255,255,255,.055);}
/* Animated document lines */
.dl-a{animation:dlscan 2.8s ease-in-out infinite;}
.dl-b{animation:dlscan 2.8s ease-in-out infinite;animation-delay:-.4s;}
.dl-c{animation:dlscan 2.8s ease-in-out infinite;animation-delay:-.8s;}
@keyframes dlscan{0%,100%{opacity:.4;}50%{opacity:1;}}

.qc{display:flex;flex-direction:column;gap:8px;}
.mc{background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:10px 12px;display:flex;align-items:center;gap:10px;flex:1;}
.mlbl{font-size:.52rem;font-weight:800;text-transform:uppercase;letter-spacing:1.5px;color:rgba(255,255,255,.28);}
.mval{font-size:1.32rem;font-weight:900;letter-spacing:-1px;}
.dr2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;}
.ic{background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:12px;}
.icl{font-size:.52rem;font-weight:800;text-transform:uppercase;letter-spacing:1.5px;color:rgba(255,255,255,.25);margin-bottom:5px;}
.icv{font-size:.98rem;font-weight:800;color:#fff;letter-spacing:-.2px;}
.ics{font-size:.58rem;color:#10b981;font-weight:700;margin-top:2px;}
.ict{font-size:1.1rem;font-weight:900;color:#10b981;letter-spacing:-1px;}
.icq{font-size:.6rem;color:#fbbf24;font-weight:700;margin-top:3px;}
.db{display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,.015);border:1px solid rgba(255,255,255,.05);border-radius:12px;padding:10px 14px;gap:6px;}
.bb{text-align:center;}
.bbl{font-size:.48rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:rgba(255,255,255,.22);margin-bottom:3px;}
.bbv{font-size:.7rem;font-weight:800;color:rgba(255,255,255,.75);}
.bbv.g{color:#10b981;}.bbv.p{color:#00D9FF;}.bbv.b{color:#60a5fa;}
.sep{width:1px;height:28px;background:rgba(255,255,255,.06);}

/* ═══ PREMIUM ROBOT ARM ═══ */
.arm{
  position:absolute;right:-4px;top:20px;width:108px;
  animation:armfl 5s ease-in-out infinite;
  filter:
    drop-shadow(0 0 18px rgba(0,217,255,.70))
    drop-shadow(0 6px 28px rgba(0,0,0,.8));
  pointer-events:none;z-index:2;
}
@keyframes armfl{
  0%,100%{transform:translateY(0) rotate(0deg);}
  30%{transform:translateY(-8px) rotate(1.2deg);}
  60%{transform:translateY(-14px) rotate(-0.8deg);}
  80%{transform:translateY(-6px) rotate(1.5deg);}
}

/* Floating particles around dashboard */
.fp{position:absolute;border-radius:50%;pointer-events:none;animation:fpfl ease-in-out infinite;}
.fp1{width:7px;height:7px;background:#00D9FF;top:10%;left:-8%;animation-duration:3.5s;box-shadow:0 0 10px #00D9FF,0 0 20px rgba(0,217,255,.4);}
.fp2{width:5px;height:5px;background:#7CFF00;top:30%;right:-7%;animation-duration:4.2s;animation-delay:-1s;box-shadow:0 0 8px #7CFF00,0 0 16px rgba(124,255,0,.4);}
.fp3{width:6px;height:6px;background:#00F5FF;top:65%;left:-6%;animation-duration:3.8s;animation-delay:-2s;box-shadow:0 0 10px #00F5FF,0 0 20px rgba(0,245,255,.4);}
.fp4{width:5px;height:5px;background:#39FF14;bottom:15%;right:-6%;animation-duration:4.5s;animation-delay:-.5s;box-shadow:0 0 8px #39FF14,0 0 16px rgba(57,255,20,.4);}
.fp5{width:3px;height:3px;background:#00D9FF;top:50%;left:-4%;animation-duration:5s;animation-delay:-3s;box-shadow:0 0 6px #00D9FF;}
@keyframes fpfl{0%,100%{transform:translateY(0) scale(1);}50%{transform:translateY(-16px) scale(1.1);}}

/* DIVIDER */
.divider{height:1px;margin:70px 0 0;background:linear-gradient(90deg,transparent,rgba(0,217,255,.2),rgba(0,245,255,.2),transparent);}

/* SECTION HELPERS */
section{position:relative;z-index:1;}
.pill{display:inline-flex;align-items:center;gap:6px;font-size:.6rem;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;padding:5px 15px;border-radius:20px;margin-bottom:16px;}
.sec-h2{font-size:2.55rem;font-weight:900;letter-spacing:-1.3px;line-height:1.16;text-align:center;margin-bottom:12px;}
.sec-sub{text-align:center;font-size:.88rem;color:rgba(255,255,255,.38);max-width:520px;margin:0 auto 44px;line-height:1.82;}

/* FEATURES */
.feat{padding:70px 0 0;margin:0;}
.feat-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;}
.fc{background:rgba(8,8,28,.9);border:1px solid rgba(255,255,255,.065);border-radius:20px;padding:22px 18px 18px;position:relative;overflow:hidden;backdrop-filter:blur(18px);box-shadow:0 8px 32px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.04);transition:all .42s cubic-bezier(.22,1,.36,1);cursor:default;}
.fcbar{position:absolute;top:0;left:0;right:0;height:2px;border-radius:20px 20px 0 0;opacity:.65;transition:opacity .3s;}
.fc::before{content:'';position:absolute;inset:0;border-radius:20px;background:radial-gradient(ellipse at top left,rgba(0,217,255,.06),transparent 60%);opacity:0;transition:opacity .4s;}
.fc:hover::before{opacity:1;}.fc:hover .fcbar{opacity:1;}
.fc:hover{transform:translateY(-10px);border-color:rgba(0,217,255,.2);box-shadow:0 28px 72px rgba(0,0,0,.75),0 0 44px rgba(0,217,255,.06),inset 0 1px 0 rgba(255,255,255,.07);}
.fcico{width:52px;height:52px;border-radius:16px;margin-bottom:16px;display:flex;align-items:center;justify-content:center;font-size:1.55rem;border:1px solid rgba(255,255,255,.055);box-shadow:0 8px 22px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.07);animation:icfl 3.8s ease-in-out infinite;}
.fc:nth-child(2) .fcico{animation-delay:-.6s;}.fc:nth-child(3) .fcico{animation-delay:-1.2s;}.fc:nth-child(4) .fcico{animation-delay:-1.8s;}.fc:nth-child(5) .fcico{animation-delay:-2.4s;}.fc:nth-child(6) .fcico{animation-delay:-3s;}
@keyframes icfl{0%,100%{transform:translateY(0);}50%{transform:translateY(-7px);}}
.fctit{font-size:.84rem;font-weight:800;color:#fff;margin-bottom:8px;letter-spacing:-.2px;line-height:1.3;}
.fcdesc{font-size:.7rem;color:rgba(255,255,255,.32);line-height:1.68;}
.fcex{display:inline-flex;align-items:center;gap:4px;margin-top:12px;font-size:.62rem;font-weight:700;color:rgba(255,255,255,.24);transition:color .2s;}
.fc:hover .fcex{color:rgba(255,255,255,.6);}

/* WORKFLOW */
.wf{padding:70px 0 0;margin:0;}
.wrow{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:0;margin-top:22px;}
.wn{display:flex;flex-direction:column;align-items:center;text-align:center;}
.wcard{width:76px;height:76px;border-radius:22px;margin-bottom:10px;display:flex;align-items:center;justify-content:center;font-size:1.55rem;background:rgba(5,12,12,.92);border:1px solid rgba(0,217,255,.24);box-shadow:0 8px 26px rgba(0,0,0,.65),inset 0 1px 0 rgba(255,255,255,.05);position:relative;transition:all .35s ease;cursor:default;animation:wcard 4s ease-in-out infinite;}
.wn:nth-child(odd) .wcard{animation-delay:.4s;}.wn:nth-child(3n) .wcard{animation-delay:.8s;}
@keyframes wcard{0%,100%{border-color:rgba(0,217,255,.24);box-shadow:0 8px 26px rgba(0,0,0,.65);}50%{border-color:rgba(0,245,255,.55);box-shadow:0 8px 26px rgba(0,0,0,.65),0 0 28px rgba(0,217,255,.22);}}
.wcard:hover{transform:scale(1.12) translateY(-5px);box-shadow:0 18px 44px rgba(0,0,0,.7),0 0 40px rgba(0,217,255,.4)!important;}
.wnum{position:absolute;top:-9px;right:-9px;width:20px;height:20px;border-radius:50%;background:linear-gradient(135deg,#00D9FF,#7CFF00);font-size:.55rem;font-weight:900;color:#000000;display:flex;align-items:center;justify-content:center;box-shadow:0 0 8px rgba(0,217,255,.6);}
.wlbl{font-size:.59rem;font-weight:700;color:rgba(255,255,255,.32);text-transform:uppercase;letter-spacing:.6px;max-width:72px;line-height:1.3;}
.wsub{font-size:.5rem;color:rgba(255,255,255,.18);font-weight:600;margin-top:2px;}
.wconn{display:flex;align-items:center;padding-bottom:34px;margin:0 1px;}
.wline{width:26px;height:1px;background:linear-gradient(90deg,rgba(0,217,255,.5),rgba(0,245,255,.7));}
.warr{font-size:.9rem;color:#00D9FF;margin-left:2px;animation:warr 2s ease-in-out infinite;}
@keyframes warr{0%,100%{opacity:.35;transform:translateX(0);}50%{opacity:1;transform:translateX(3px);}}

/* STATS */
.sts{padding:70px 0 0;margin:0;}
.sg{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;}
.sc{background:rgba(8,8,28,.9);border:1px solid rgba(255,255,255,.058);border-radius:18px;padding:24px 14px;text-align:center;transition:all .38s ease;position:relative;overflow:hidden;backdrop-filter:blur(14px);cursor:default;}
.sc::before{content:'';position:absolute;inset:0;border-radius:18px;background:radial-gradient(ellipse at top,rgba(0,217,255,.06),transparent 65%);opacity:0;transition:opacity .3s;}
.sc:hover::before{opacity:1;}
.sc:hover{transform:translateY(-8px);border-color:rgba(0,217,255,.18);box-shadow:0 24px 60px rgba(0,0,0,.65);}
.sico{font-size:1.6rem;margin-bottom:8px;display:block;animation:sico 3.5s ease-in-out infinite;}
.sc:nth-child(2) .sico{animation-delay:-.5s;}.sc:nth-child(3) .sico{animation-delay:-1s;}.sc:nth-child(4) .sico{animation-delay:-1.5s;}.sc:nth-child(5) .sico{animation-delay:-2s;}.sc:nth-child(6) .sico{animation-delay:-2.5s;}
@keyframes sico{0%,100%{transform:scale(1);}50%{transform:scale(1.12);}}
.sn{font-size:2.1rem;font-weight:900;letter-spacing:-1.5px;background:linear-gradient(135deg,#00D9FF,#7CFF00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.sl{font-size:.6rem;color:rgba(255,255,255,.26);font-weight:700;text-transform:uppercase;letter-spacing:1.2px;margin-top:6px;}

/* NVIDIA */
.nv{padding:70px 0 0;margin:0;}
.nvw{display:grid;grid-template-columns:1fr 1.1fr 1.2fr;gap:36px;align-items:center;background:rgba(2,14,8,.95);border:1px solid rgba(16,185,129,.13);border-radius:26px;padding:52px 48px;position:relative;overflow:hidden;}
.nvw::before{content:'';position:absolute;inset:0;border-radius:26px;background:radial-gradient(ellipse at 30% 50%,rgba(16,185,129,.06),transparent 60%);pointer-events:none;}
.nvc{position:absolute;inset:0;overflow:hidden;border-radius:26px;pointer-events:none;}
.ch{position:absolute;height:1px;opacity:0;animation:chlp 5.5s linear infinite;background:linear-gradient(90deg,transparent,rgba(16,185,129,.5),transparent);}
.ch1{top:18%;width:100%;animation-delay:0s;}.ch2{top:48%;width:72%;left:14%;animation-delay:-2.8s;}.ch3{top:74%;width:86%;left:6%;animation-delay:-4.5s;}
@keyframes chlp{0%{opacity:0;transform:translateX(-100%);}15%{opacity:1;}85%{opacity:.8;}100%{opacity:0;transform:translateX(100%);}}
.nvey{font-size:.58rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;color:rgba(16,185,129,.65);margin-bottom:12px;}
.nvh{font-size:1.8rem;font-weight:900;color:#fff;line-height:1.15;letter-spacing:-.7px;margin-bottom:14px;}
.nvd{font-size:.78rem;color:rgba(255,255,255,.32);line-height:1.78;margin-bottom:18px;}
.nvb{display:flex;flex-direction:column;gap:7px;margin-bottom:20px;}
.nvbi{display:flex;align-items:center;gap:8px;font-size:.73rem;color:rgba(255,255,255,.45);}
.nvbi::before{content:'✓';color:#10b981;font-weight:900;flex-shrink:0;}
.nvst{display:inline-flex;align-items:center;gap:6px;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);color:#10b981;font-size:.62rem;font-weight:800;letter-spacing:1px;padding:6px 14px;border-radius:14px;}
.gpu-center{display:flex;flex-direction:column;align-items:center;text-align:center;}
.gpuw{position:relative;display:inline-flex;align-items:center;justify-content:center;width:172px;height:172px;margin-bottom:14px;}
.ra{position:absolute;inset:-16px;border-radius:50%;border:1.5px solid rgba(16,185,129,.2);animation:gra 5s linear infinite;}
.rb{position:absolute;inset:-28px;border-radius:50%;border:1px dashed rgba(16,185,129,.1);animation:gra 7s linear infinite reverse;}
@keyframes gra{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
.chip{width:144px;height:144px;border-radius:24px;background:linear-gradient(135deg,#0a2e1a,#0d3d22);border:2px solid rgba(16,185,129,.32);display:flex;align-items:center;justify-content:center;box-shadow:0 0 50px rgba(16,185,129,.32),0 0 100px rgba(16,185,129,.1),inset 0 0 30px rgba(16,185,129,.05);animation:chipg 2.8s ease-in-out infinite;position:relative;overflow:hidden;}
@keyframes chipg{0%,100%{box-shadow:0 0 40px rgba(16,185,129,.28),0 0 80px rgba(16,185,129,.09);}50%{box-shadow:0 0 70px rgba(16,185,129,.55),0 0 130px rgba(16,185,129,.18);}}
.chip::before{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(16,185,129,.09) 1px,transparent 1px),linear-gradient(90deg,rgba(16,185,129,.09) 1px,transparent 1px);background-size:18px 18px;}
.chipico{font-size:3.1rem;position:relative;z-index:1;filter:drop-shadow(0 0 14px rgba(16,185,129,.75));}
.gpuglow{width:110px;height:12px;background:radial-gradient(ellipse,rgba(16,185,129,.52),transparent 72%);filter:blur(10px);border-radius:50%;margin:0 auto;animation:glowp 2.8s ease-in-out infinite;}
@keyframes glowp{0%,100%{opacity:.6;transform:scaleX(1);}50%{opacity:1;transform:scaleX(1.15);}}
.gpul{font-size:1.2rem;font-weight:900;color:#10b981;margin-top:10px;}
.gpus{font-size:.7rem;color:rgba(255,255,255,.28);margin-top:3px;}
.nvg{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.nvc2{background:rgba(16,185,129,.04);border:1px solid rgba(16,185,129,.12);border-radius:14px;padding:14px 16px;transition:all .3s ease;}
.nvc2:hover{background:rgba(16,185,129,.08);transform:translateY(-3px);box-shadow:0 12px 30px rgba(16,185,129,.1);}
.nvc2.full{grid-column:span 2;}
.ncl{font-size:.52rem;font-weight:800;text-transform:uppercase;letter-spacing:1.5px;color:rgba(16,185,129,.52);margin-bottom:4px;}
.ncv{font-size:1.12rem;font-weight:900;color:#10b981;letter-spacing:-.5px;}
.ncs{font-size:.58rem;color:rgba(255,255,255,.26);margin-top:2px;}
.ndot{display:inline-block;width:5px;height:5px;border-radius:50%;background:#10b981;margin-right:4px;animation:dotpulse 1.8s infinite;vertical-align:middle;}
.gt{height:6px;background:rgba(255,255,255,.04);border-radius:99px;overflow:hidden;margin:8px 0 4px;}
.gf{height:100%;border-radius:99px;background:linear-gradient(90deg,#10b981,#34d399);box-shadow:0 0 8px rgba(16,185,129,.6);animation:gfa 2s ease both;}
@keyframes gfa{from{width:0!important;}}
.gl{display:flex;justify-content:space-between;font-size:.52rem;color:rgba(255,255,255,.22);}

/* TESTIMONIALS */
.tst{padding:70px 0 0;margin:0;}
.tg{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;}
.tc{background:rgba(8,8,28,.9);border:1px solid rgba(255,255,255,.065);border-radius:22px;padding:26px;transition:all .4s ease;position:relative;overflow:hidden;backdrop-filter:blur(16px);cursor:default;}
.tc::before{content:'';position:absolute;inset:0;border-radius:22px;background:radial-gradient(ellipse at top right,rgba(0,217,255,.045),transparent 60%);opacity:0;transition:opacity .3s;}
.tc:hover::before{opacity:1;}
.tc::after{content:'"';position:absolute;top:-18px;right:16px;font-size:9rem;color:rgba(0,217,255,.025);font-family:Georgia,serif;line-height:1;pointer-events:none;}
.tc:hover{transform:translateY(-8px);border-color:rgba(0,217,255,.16);box-shadow:0 26px 66px rgba(0,0,0,.65);}
.tstar{color:#f59e0b;font-size:.78rem;margin-bottom:14px;letter-spacing:2px;}
.ttext{font-size:.8rem;color:rgba(255,255,255,.42);line-height:1.82;margin-bottom:20px;font-style:italic;}
.tauth{display:flex;align-items:center;gap:12px;}
.tav{width:44px;height:44px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1.05rem;font-weight:900;color:#fff;box-shadow:0 0 18px rgba(0,0,0,.4);}
.tname{font-size:.84rem;font-weight:700;color:#fff;}
.trole{font-size:.63rem;color:rgba(255,255,255,.26);margin-top:2px;}

/* FAB */
.fab{position:fixed;bottom:22px;right:24px;z-index:9999;width:52px;height:52px;border-radius:50%;background:rgba(5,12,12,.94);border:1px solid rgba(0,217,255,.3);display:flex;align-items:center;justify-content:center;font-size:1.45rem;box-shadow:0 0 24px rgba(0,217,255,.35),0 8px 28px rgba(0,0,0,.65);backdrop-filter:blur(18px);animation:fab 3.5s ease-in-out infinite;cursor:default;}
@keyframes fab{0%,100%{transform:scale(1);box-shadow:0 0 24px rgba(0,217,255,.38),0 8px 28px rgba(0,0,0,.65);}50%{transform:scale(1.07);box-shadow:0 0 40px rgba(0,217,255,.60),0 8px 36px rgba(0,0,0,.65);}}

/* FOOTER */
footer{border-top:1px solid rgba(255,255,255,.04);padding:56px 0 20px;margin:0;display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1.5fr;gap:44px;position:relative;z-index:1;}
.ftlogo{font-size:1.1rem;font-weight:900;margin-bottom:12px;background:linear-gradient(135deg,#00D9FF,#7CFF00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.ftdesc{font-size:.75rem;color:rgba(255,255,255,.22);line-height:1.76;max-width:240px;margin-bottom:16px;}
.ftsoc{display:flex;gap:8px;}
.soc{width:32px;height:32px;border-radius:9px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.065);display:flex;align-items:center;justify-content:center;font-size:.78rem;transition:all .22s ease;cursor:default;}
.soc:hover{background:rgba(0,217,255,.12);border-color:rgba(0,217,255,.28);}
.fth{font-size:.6rem;font-weight:800;color:rgba(255,255,255,.3);text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;}
.ftl{display:block;font-size:.75rem;color:rgba(255,255,255,.22);margin-bottom:10px;cursor:default;transition:color .2s;}
.ftl:hover{color:rgba(255,255,255,.6);}
.ftnl{display:flex;gap:6px;margin-top:10px;}
.ftnl input{flex:1;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:8px 12px;color:#fff;font-size:.73rem;font-family:'Space Grotesk',sans-serif;outline:none;transition:border-color .2s;}
.ftnl input:focus{border-color:rgba(0,217,255,.38);}
.ftnl input::placeholder{color:rgba(255,255,255,.18);}
.ftsbtn{background:linear-gradient(135deg,#00D9FF,#7CFF00);border:none;border-radius:10px;padding:8px 14px;color:#000000;font-size:.73rem;font-weight:700;cursor:default;font-family:'Space Grotesk',sans-serif;flex-shrink:0;box-shadow:0 4px 14px rgba(0,217,255,.42);transition:all .25s ease;}
.ftsbtn:hover{box-shadow:0 8px 24px rgba(0,217,255,.62);transform:translateY(-1px);}
.ftbtm{border-top:1px solid rgba(255,255,255,.04);padding:16px 64px;position:relative;z-index:1;display:flex;justify-content:space-between;align-items:center;font-size:.68rem;color:rgba(255,255,255,.14);}
.pad70{padding-bottom:70px;}
</style>
</head>
<body>
<!-- Background -->
<div class="bg">
  <div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div><div class="orb o4"></div><div class="orb o5"></div>
</div>
<div class="grid"></div>
<div class="streak sk1"></div><div class="streak sk2"></div><div class="streak sk3"></div>
<div class="ring rg1"></div><div class="ring rg2"></div>
<div class="pt p1"></div><div class="pt p2"></div><div class="pt p3"></div>
<div class="pt p4"></div><div class="pt p5"></div><div class="pt p6"></div>

<!-- PAGE WRAPPER: single centered container -->
<div class="page-wrap">

<!-- NAVBAR -->
<nav id="top">
  <div class="logo">
    <div class="logo-ico">&#9889;</div>
    <span>SmartPrint AI</span>
  </div>
  <div class="nav-links">
    <a class="nav-l on" href="#top" onclick="smoothTo(event,'top')">Home</a>
    <a class="nav-l" href="#features" onclick="smoothTo(event,'features')">Features</a>
    <a class="nav-l" href="#ai-tech" onclick="smoothTo(event,'ai-tech')">AI Technology</a>
    <a class="nav-l" href="#how-it-works" onclick="smoothTo(event,'how-it-works')">How It Works</a>
    <a class="nav-l" href="#smart-numbers" onclick="smoothTo(event,'smart-numbers')">Pricing</a>
    <a class="nav-l" href="#about" onclick="smoothTo(event,'about')">About</a>
  </div>
  <div class="nav-actions">
    <a href="?nav_route=login" target="_parent" class="btn-li-nav">👤 Login</a>
    <a href="?nav_route=register" target="_parent" class="btn-gs-nav">🚀 Get Started</a>
  </div>
</nav>

<!-- HERO -->
<div class="hero">
  <!-- Left -->
  <div class="hero-l">
    <div class="eyebrow"><span class="dot"></span>AI Powered Printing Ecosystem</div>
    <h1>
      <span class="h1w">PRINTING</span>
      <span class="h1g">REIMAGINED</span>
      <span class="h1g">WITH AI</span>
    </h1>
    <p class="hsub">Smart queue management, AI-powered document analysis, intelligent printer recommendation and seamless printing all in one next-gen platform.</p>
    <div class="btn-row">
      <a href="?nav_route=register" target="_parent" class="btn-gs">&#128640; Get Started &#8594;</a>
      <a href="?nav_route=login" target="_parent" class="btn-li">&#128100; Login &#8594;</a>
    </div>
    <div class="tags">
      <span class="tag ta">&#129504; AI Analysis</span>
      <span class="tag tb">&#9201; Smart Queue</span>
      <span class="tag tc">&#9889; GPU Accelerated</span>
      <span class="tag td">&#128065; Computer Vision</span>
      <span class="tag te">&#128300; TensorFlow</span>
      <span class="tag tf">&#127919; OpenCV</span>
      <span class="tag tg">&#128260; Transfer Learning</span>
      <span class="tag th">&#128154; NVIDIA CUDA</span>
    </div>
  </div>

  <!-- Right: Premium 3D Dashboard -->
  <div class="hero-r">
    <div class="fp fp1"></div><div class="fp fp2"></div><div class="fp fp3"></div><div class="fp fp4"></div><div class="fp fp5"></div>
    <div class="dash">
      <div class="scan"></div>
      <!-- Dashboard Header -->
      <div class="dh">
        <span class="dht">&#9000; AI Document Scan</span>
        <span class="live"><span class="dot"></span>LIVE</span>
      </div>
      <!-- GPU Bar -->
      <div class="gpu-bar">
        <span class="gpu-bar-label">GPU</span>
        <div class="gpu-bar-track"><div class="gpu-bar-fill" style="width:84%;"></div></div>
        <span style="font-size:.52rem;font-weight:800;color:#7CFF00;flex-shrink:0;">84%</span>
      </div>
      <!-- Row 1 -->
      <div class="dr1">
        <div class="doc">
          <div class="docn"><em>&#128196;</em>project_report.pdf</div>
          <div class="dlines">
            <div class="dl dl-a" style="background:rgba(0,217,255,.55);width:92%;height:5px;border-radius:4px;"></div>
            <div class="dl dl-b" style="width:88%;"></div>
            <div class="dl dl-c" style="width:75%;"></div>
            <div class="dl dl-a" style="width:82%;"></div>
            <div class="dl dl-b" style="width:63%;"></div>
            <div class="dl dl-c" style="width:89%;"></div>
          </div>
        </div>
        <div class="qc">
          <div class="mc">
            <svg width="46" height="46" viewBox="0 0 46 46" style="flex-shrink:0;">
              <defs><linearGradient id="qg1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#00D9FF"/><stop offset="100%" stop-color="#7CFF00"/></linearGradient></defs>
              <circle cx="23" cy="23" r="18" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="5"/>
              <circle cx="23" cy="23" r="18" fill="none" stroke="url(#qg1)" stroke-width="5" stroke-linecap="round" stroke-dasharray="97 113" stroke-dashoffset="28" transform="rotate(-90 23 23)"><animate attributeName="stroke-dasharray" from="0 113" to="97 113" dur="1.8s" fill="freeze"/></circle>
              <text x="23" y="27" text-anchor="middle" font-size="9" font-weight="900" fill="#00D9FF" font-family="Inter">96</text>
            </svg>
            <div>
              <div class="mlbl">Quality Score</div>
              <div class="mval" style="color:#00D9FF;">96%</div>
            </div>
          </div>
          <div class="mc">
            <div style="flex:1;">
              <div class="mlbl">Confidence</div>
              <div class="mval" style="color:#7CFF00;">99.2%</div>
              <svg width="100%" height="26" viewBox="0 0 90 26" style="margin-top:4px;" preserveAspectRatio="none">
                <polyline fill="rgba(124,255,0,.1)" stroke="none" points="0,22 12,17 22,19 34,9 44,13 56,4 66,9 78,2 90,6 90,26 0,26"/>
                <polyline fill="none" stroke="#7CFF00" stroke-width="1.6" points="0,22 12,17 22,19 34,9 44,13 56,4 66,9 78,2 90,6"/>
              </svg>
            </div>
          </div>
        </div>
      </div>
      <!-- Row 2 -->
      <div class="dr2">
        <div class="ic">
          <div class="icl">Recommended Printer</div>
          <div class="icv">&#128424; Printer A</div>
          <div class="ics">&#10003; Best Match</div>
        </div>
        <div class="ic">
          <div class="icl">Estimated Wait Time</div>
          <div class="ict">2 min 15 sec</div>
          <div class="icq">&#9889; Low Queue</div>
        </div>
      </div>
      <!-- Bottom badges -->
      <div class="db">
        <div class="bb"><div class="bbl">AI Model</div><div class="bbv p">MobileNetV2</div></div>
        <div class="sep"></div>
        <div class="bb"><div class="bbl">Framework</div><div class="bbv b">TensorFlow</div></div>
        <div class="sep"></div>
        <div class="bb"><div class="bbl">Hardware</div><div class="bbv g">NVIDIA RTX</div></div>
      </div>
    </div>

    <!-- Premium Robotic Arm -->
    <div class="arm">
      <svg viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <!-- Main gradient: cyan to green -->
          <linearGradient id="ag" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#00D9FF" stop-opacity=".95"/>
            <stop offset="100%" stop-color="#7CFF00" stop-opacity=".78"/>
          </linearGradient>
          <!-- Metal highlight -->
          <linearGradient id="ag-hi" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="rgba(255,255,255,.35)"/>
            <stop offset="100%" stop-color="rgba(255,255,255,.04)"/>
          </linearGradient>
          <!-- Glow filter -->
          <filter id="ag-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          <!-- Strong glow for joints -->
          <filter id="jglow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="4" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>
        <!-- Shadow ellipse -->
        <ellipse cx="50" cy="292" rx="36" ry="8" fill="rgba(0,217,255,.28)" filter="url(#ag-glow)"/>
        <!-- Base -->
        <rect x="36" y="260" width="28" height="34" rx="8" fill="url(#ag)" filter="url(#ag-glow)"/>
        <rect x="38" y="261" width="24" height="10" rx="4" fill="url(#ag-hi)" opacity=".5"/>
        <!-- Lower arm -->
        <rect x="43" y="180" width="14" height="86" rx="7" fill="url(#ag)" filter="url(#ag-glow)"/>
        <rect x="44" y="181" width="6" height="30" rx="3" fill="url(#ag-hi)" opacity=".4"/>
        <!-- Joint 1 -->
        <circle cx="50" cy="180" r="11" fill="#0a1f1f" stroke="url(#ag)" stroke-width="3.5" filter="url(#jglow)"/>
        <circle cx="50" cy="180" r="5.5" fill="#00D9FF" filter="url(#jglow)"/>
        <circle cx="50" cy="180" r="2.5" fill="#fff" opacity=".7"/>
        <!-- Mid arm -->
        <rect x="47" y="105" width="13" height="80" rx="6.5" fill="url(#ag)" transform="rotate(-14 50 180)" filter="url(#ag-glow)"/>
        <!-- Joint 2 -->
        <circle cx="66" cy="112" r="10" fill="#0a1f1f" stroke="url(#ag)" stroke-width="3" filter="url(#jglow)"/>
        <circle cx="66" cy="112" r="4.5" fill="#7CFF00" filter="url(#jglow)"/>
        <circle cx="66" cy="112" r="2" fill="#fff" opacity=".7"/>
        <!-- Upper arm -->
        <rect x="62" y="44" width="11" height="72" rx="5.5" fill="url(#ag)" transform="rotate(18 66 112)" filter="url(#ag-glow)"/>
        <!-- Joint 3 -->
        <circle cx="79" cy="49" r="9" fill="#0a1f1f" stroke="url(#ag)" stroke-width="2.5" filter="url(#jglow)"/>
        <circle cx="79" cy="49" r="4" fill="#00F5FF" filter="url(#jglow)"/>
        <circle cx="79" cy="49" r="1.8" fill="#fff" opacity=".7"/>
        <!-- End effector / gripper -->
        <line x1="79" y1="40" x2="70" y2="16" stroke="url(#ag)" stroke-width="5" stroke-linecap="round" filter="url(#ag-glow)"/>
        <line x1="79" y1="40" x2="89" y2="15" stroke="url(#ag)" stroke-width="5" stroke-linecap="round" filter="url(#ag-glow)"/>
        <!-- Tip joints -->
        <circle cx="70" cy="15" r="5" fill="#00D9FF" filter="url(#jglow)"/>
        <circle cx="70" cy="15" r="2.2" fill="#fff" opacity=".8"/>
        <circle cx="89" cy="13" r="5" fill="#7CFF00" filter="url(#jglow)"/>
        <circle cx="89" cy="13" r="2.2" fill="#fff" opacity=".8"/>
      </svg>
    </div>
    <div class="platform"></div>
  </div>
</div><!-- end hero -->

<!-- Smooth scroll script -->
<script>
function smoothTo(e, id) {
  e.preventDefault();
  var el = document.getElementById(id);
  if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }
  // Update active state
  document.querySelectorAll('.nav-l').forEach(function(n){ n.classList.remove('on'); });
  e.currentTarget.classList.add('on');
}
// Intersection observer to auto-highlight nav on scroll
var sections = ['features','ai-tech','how-it-works','smart-numbers','about'];
var navLinks = document.querySelectorAll('.nav-l');
function setActive(id) {
  navLinks.forEach(function(n){
    var href = n.getAttribute('href');
    n.classList.toggle('on', href === '#' + id || (id==='top' && href==='#top'));
  });
}
var io = new IntersectionObserver(function(entries){
  entries.forEach(function(entry){
    if(entry.isIntersecting){ setActive(entry.target.id); }
  });
}, {threshold:0.3});
sections.forEach(function(id){
  var el = document.getElementById(id);
  if(el) io.observe(el);
});
</script>

<!-- FEATURES -->
<div class="divider" style="margin-top:48px;"></div>
<section class="feat" id="features">
  <div style="text-align:center;margin-bottom:6px;"><span class="pill" style="background:rgba(0,217,255,.09);border:1px solid rgba(0,217,255,.18);color:#00D9FF;">Features</span></div>
  <div class="sec-h2">Everything AI. Nothing Ordinary.</div>
  <div class="sec-sub">Six intelligent modules working seamlessly to deliver a premium campus printing experience.</div>
  <div class="feat-grid">
    <div class="fc"><div class="fcbar" style="background:linear-gradient(90deg,#00D9FF,#00B7FF);"></div><div class="fcico" style="background:rgba(0,217,255,.08);border-color:rgba(0,217,255,.13);">&#129504;</div><div class="fctit">AI Document Analysis</div><div class="fcdesc">Deep learning models analyze quality, blur, skew, contrast and readability.</div><div class="fcex">Explore &#8594;</div></div>
    <div class="fc"><div class="fcbar" style="background:linear-gradient(90deg,#7CFF00,#39FF14);"></div><div class="fcico" style="background:rgba(124,255,0,.08);border-color:rgba(124,255,0,.13);">&#9201;</div><div class="fctit">Smart Queue Prediction</div><div class="fcdesc">ML models predict real-time waiting time with high accuracy.</div><div class="fcex">Explore &#8594;</div></div>
    <div class="fc"><div class="fcbar" style="background:linear-gradient(90deg,#00F5FF,#00D9FF);"></div><div class="fcico" style="background:rgba(0,245,255,.08);border-color:rgba(0,245,255,.13);">&#128424;</div><div class="fctit">Printer Recommendation</div><div class="fcdesc">AI recommends the best printer based on speed, queue and efficiency.</div><div class="fcex">Explore &#8594;</div></div>
    <div class="fc"><div class="fcbar" style="background:linear-gradient(90deg,#10b981,#059669);"></div><div class="fcico" style="background:rgba(16,185,129,.08);border-color:rgba(16,185,129,.13);">&#9889;</div><div class="fctit">GPU Acceleration</div><div class="fcdesc">NVIDIA GPU powers fast AI inference and real-time processing.</div><div class="fcex">Explore &#8594;</div></div>
    <div class="fc"><div class="fcbar" style="background:linear-gradient(90deg,#ec4899,#db2777);"></div><div class="fcico" style="background:rgba(236,72,153,.08);border-color:rgba(236,72,153,.13);">&#128179;</div><div class="fctit">Secure Payments</div><div class="fcdesc">Safe, fast and encrypted payments for a seamless experience.</div><div class="fcex">Explore &#8594;</div></div>
    <div class="fc"><div class="fcbar" style="background:linear-gradient(90deg,#f59e0b,#d97706);"></div><div class="fcico" style="background:rgba(245,158,11,.08);border-color:rgba(245,158,11,.13);">&#128276;</div><div class="fctit">Real-time Notifications</div><div class="fcdesc">Live updates on your print status, queue and printer activity.</div><div class="fcex">Explore &#8594;</div></div>
  </div>
</section>

<!-- WORKFLOW -->
<div class="divider" style="margin-top:70px;"></div>
<section class="wf" id="how-it-works">
  <div style="text-align:center;margin-bottom:6px;"><span class="pill" style="background:rgba(0,217,255,.09);border:1px solid rgba(0,217,255,.18);color:#00D9FF;">AI Powered Workflow</span></div>
  <div class="sec-h2">How SmartPrint AI Works</div>
  <div class="sec-sub">Every document passes through an 8-stage intelligent pipeline &#8212; quality analysis to live print status.</div>
  <div class="wrow">
    <div class="wn"><div class="wcard"><div class="wnum">1</div>&#128196;</div><div class="wlbl">Upload</div><div class="wsub">Document</div></div>
    <div class="wconn"><div class="wline"></div><span class="warr">&#8250;</span></div>
    <div class="wn"><div class="wcard"><div class="wnum">2</div>&#128065;</div><div class="wlbl">AI Preprocessing</div><div class="wsub">OpenCV</div></div>
    <div class="wconn"><div class="wline"></div><span class="warr">&#8250;</span></div>
    <div class="wn"><div class="wcard"><div class="wnum">3</div>&#129504;</div><div class="wlbl">Quality Analysis</div><div class="wsub">CNN</div></div>
    <div class="wconn"><div class="wline"></div><span class="warr">&#8250;</span></div>
    <div class="wn"><div class="wcard"><div class="wnum">4</div>&#128424;</div><div class="wlbl">Printer</div><div class="wsub">Recommendation</div></div>
    <div class="wconn"><div class="wline"></div><span class="warr">&#8250;</span></div>
    <div class="wn"><div class="wcard"><div class="wnum">5</div>&#9201;</div><div class="wlbl">Queue Time</div><div class="wsub">Prediction (ML)</div></div>
    <div class="wconn"><div class="wline"></div><span class="warr">&#8250;</span></div>
    <div class="wn"><div class="wcard"><div class="wnum">6</div>&#128179;</div><div class="wlbl">Secure</div><div class="wsub">Payment</div></div>
    <div class="wconn"><div class="wline"></div><span class="warr">&#8250;</span></div>
    <div class="wn"><div class="wcard"><div class="wnum">7</div>&#128260;</div><div class="wlbl">Live Printing</div><div class="wsub">Status</div></div>
  </div>
</section>

<!-- STATS -->
<div class="divider" style="margin-top:70px;"></div>
<section class="sts" id="smart-numbers">
  <div style="text-align:center;margin-bottom:6px;"><span class="pill" style="background:rgba(0,217,255,.09);border:1px solid rgba(0,217,255,.18);color:#00D9FF;">Trusted by Thousands</span></div>
  <div class="sec-h2">Smart Numbers</div>
  <div class="sec-sub">Real metrics from a live AI system used by thousands of campus users.</div>
  <div class="sg">
    <div class="sc"><span class="sico">&#128424;</span><div class="sn">25K+</div><div class="sl">Print Jobs</div></div>
    <div class="sc"><span class="sico">&#128101;</span><div class="sn">1,200+</div><div class="sl">Active Students</div></div>
    <div class="sc"><span class="sico">&#127919;</span><div class="sn">99.9%</div><div class="sl">AI Accuracy</div></div>
    <div class="sc"><span class="sico">&#9889;</span><div class="sn">15 sec</div><div class="sl">Avg. Queue Time</div></div>
    <div class="sc"><span class="sico">&#128640;</span><div class="sn">98%</div><div class="sl">GPU Utilization</div></div>
    <div class="sc"><span class="sico">&#11088;</span><div class="sn">4.9&#9733;</div><div class="sl">User Rating</div></div>
  </div>
</section>

<!-- NVIDIA -->
<div class="divider" style="margin-top:70px;"></div>
<section class="nv" id="ai-tech">
  <div class="nvw">
    <div class="nvc"><div class="ch ch1"></div><div class="ch ch2"></div><div class="ch ch3"></div></div>
    <div>
      <div class="nvey">POWERED BY NVIDIA AI</div>
      <div class="nvh">NVIDIA GPU<br>Accelerated AI</div>
      <div class="nvd">Our AI engine runs on NVIDIA GPUs for blazing-fast inference and training, with auto CUDA detection and GPU-optimized TensorFlow runtime.</div>
      <div class="nvb">
        <div class="nvbi">CUDA Enabled</div>
        <div class="nvbi">cuDNN Optimized</div>
        <div class="nvbi">TensorFlow GPU</div>
        <div class="nvbi">Real-time AI Processing</div>
      </div>
      <div class="nvst"><span class="ndot"></span>GPU Status: ACTIVE</div>
    </div>
    <div class="gpu-center">
      <div class="gpuw">
        <div class="ra"></div><div class="rb"></div>
        <div class="chip"><span class="chipico">&#127918;</span></div>
      </div>
      <div class="gpuglow"></div>
      <div class="gpul">RTX 4060</div>
      <div class="gpus">NVIDIA GeForce GPU</div>
    </div>
    <div class="nvg">
      <div class="nvc2"><div class="ncl">GPU Model</div><div class="ncv"><span class="ndot"></span>RTX 4060</div><div class="ncs">NVIDIA GeForce</div></div>
      <div class="nvc2"><div class="ncl">CUDA Version</div><div class="ncv">12.6</div><div class="ncs">TF Compatible</div></div>
      <div class="nvc2"><div class="ncl">VRAM</div><div class="ncv">6.2 / 8 GB</div><div class="ncs">Dedicated VRAM</div></div>
      <div class="nvc2"><div class="ncl">Inference Speed</div><div class="ncv">32 ms</div><div class="ncs">Per Document</div></div>
      <div class="nvc2"><div class="ncl">TensorFlow</div><div class="ncv" style="font-size:.88rem;">&#10003; GPU Enabled</div><div class="ncs">v2.21</div></div>
      <div class="nvc2"><div class="ncl">cuDNN</div><div class="ncv" style="font-size:.88rem;">&#10003; Detected</div><div class="ncs">Optimized</div></div>
      <div class="nvc2 full"><div class="ncl">GPU Usage</div><div class="gt"><div class="gf" style="width:87%;"></div></div><div class="gl"><span>0%</span><span style="color:#10b981;font-weight:700;">87%</span><span>100%</span></div></div>
    </div>
  </div>
</section>

<!-- TESTIMONIALS -->
<div class="divider" style="margin-top:70px;"></div>
<section class="tst" id="testimonials">
  <div style="text-align:center;margin-bottom:6px;"><span class="pill" style="background:rgba(0,217,255,.09);border:1px solid rgba(0,217,255,.18);color:#00D9FF;">What Users Say</span></div>
  <div class="sec-h2">Loved by Students &amp; Faculty</div>
  <div class="sec-sub">What the campus community says about SmartPrint AI.</div>
  <div class="tg">
    <div class="tc"><div class="tstar">&#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="ttext">"SmartPrint AI reduced my waiting time to almost nothing. The AI quality check is super accurate!"</div><div class="tauth"><div class="tav" style="background:linear-gradient(135deg,#00D9FF,#00B7FF);">A</div><div><div class="tname">Arjun Sharma</div><div class="trole">Student</div></div></div></div>
    <div class="tc"><div class="tstar">&#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="ttext">"The printer recommendation feature is a game changer for our entire campus printing system."</div><div class="tauth"><div class="tav" style="background:linear-gradient(135deg,#7CFF00,#39FF14);">P</div><div><div class="tname">Priya Nair</div><div class="trole">Faculty</div></div></div></div>
    <div class="tc"><div class="tstar">&#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="ttext">"The UI is smooth, the AI is genuinely smart, and the system is extremely reliable."</div><div class="tauth"><div class="tav" style="background:linear-gradient(135deg,#10b981,#06b6d4);">R</div><div><div class="tname">Rahul Verma</div><div class="trole">Student</div></div></div></div>
  </div>
</section>

<!-- FOOTER -->
<div class="divider" style="margin-top:70px;"></div>
<footer id="about">
  <div>
    <div class="ftlogo">&#9889; SmartPrint AI</div>
    <div class="ftdesc">An intelligent AI printing ecosystem powered by CNN, Machine Learning, Deep Learning and NVIDIA GPU technology.</div>
    <div class="ftsoc">
      <div class="soc">&#120143;</div><div class="soc">in</div><div class="soc">gh</div><div class="soc">yt</div>
    </div>
  </div>
  <div>
    <div class="fth">Product</div>
    <span class="ftl">Features</span><span class="ftl">How It Works</span><span class="ftl">AI Technology</span><span class="ftl">Pricing</span>
  </div>
  <div>
    <div class="fth">Company</div>
    <span class="ftl">About Us</span><span class="ftl">Blog</span><span class="ftl">Privacy Policy</span><span class="ftl">Careers</span><span class="ftl">Contact</span>
  </div>
  <div>
    <div class="fth">Support</div>
    <span class="ftl">Help Center</span><span class="ftl">Documentation</span><span class="ftl">API Reference</span><span class="ftl">Terms of Service</span><span class="ftl">System Status</span>
  </div>
  <div>
    <div class="fth">Stay Updated</div>
    <div style="font-size:.75rem;color:rgba(255,255,255,.22);line-height:1.72;margin-bottom:8px;">Subscribe for latest updates and features.</div>
    <div class="ftnl">
      <input type="email" placeholder="Enter your email"/>
      <button class="ftsbtn">&#8594;</button>
    </div>
  </div>
</footer>
<div class="ftbtm pad70">
  <span>&#169; 2025 SmartPrint AI. All rights reserved.</span>
  <span>Built with &#129504; AI &#183; &#9889; NVIDIA GPU &#183; &#10084; Open Source</span>
</div>

</div><!-- end .page-wrap -->

<!-- Robot FAB -->
<div class="fab">&#129302;</div>
</body>
</html>"""
