"""
IntelliPrint Nexus — World-Class Campus AI Platform Landing Page
Built to Apple · Stripe · OpenAI · NVIDIA · Linear · Vercel standards.
Three.js campus visualization · GSAP scroll · Canvas particles · Micro-animations
"""
import streamlit as st


def show_landing():
    st.html(_SHELL_CSS)
    st.html(_FULL_HTML)


_SHELL_CSS = """
<style>
html,body,.stApp,.stApp>div,section.main,.block-container,
[data-testid="stAppViewContainer"],[data-testid="stMainBlockContainer"],
[data-testid="stMain"],[data-testid="stVerticalBlock"]{
  background:#06070D!important;color:#fff!important;
  font-family:'Inter',system-ui,-apple-system,sans-serif!important;
}
.appview-container .main .block-container{padding:0!important;max-width:100%!important;margin:0!important;}
[data-testid="stMainBlockContainer"]{padding:0!important;}
[data-testid="stVerticalBlockBorderWrapper"]{padding:0!important;}
#MainMenu,footer,header,[data-testid="stDecoration"],[data-testid="stStatusWidget"]{visibility:hidden!important;height:0!important;overflow:hidden!important;}
*,*::before,*::after{box-sizing:border-box;}
::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-track{background:#06070D;}
::-webkit-scrollbar-thumb{background:rgba(59,130,246,.35);border-radius:5px;}
::-webkit-scrollbar-thumb:hover{background:rgba(59,130,246,.55);}
</style>
"""

_FULL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI-Powered Campus Printing Network — IntelliPrint Nexus</title>
<meta name="description" content="Transforming University Printing through AI Document Intelligence, Smart Queue Optimization, Intelligent Printer Selection, Secure QR Pickup, and Fully Automated Campus Print Management.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">

<style>
/* ═══════════════════════════════════════════════════════
   DESIGN TOKENS & RESET
═══════════════════════════════════════════════════════ */
:root {
  --bg:          #06070D;
  --bg-2:        #0A0C16;
  --surface:     #0D1117;
  --surface-2:   #111827;
  --card:        rgba(13,17,23,0.7);
  --border:      rgba(255,255,255,0.07);
  --border-2:    rgba(255,255,255,0.12);

  --blue:        #3B82F6;
  --blue-bright: #60A5FA;
  --blue-dim:    rgba(59,130,246,0.15);
  --cyan:        #06B6D4;
  --cyan-bright: #67E8F9;
  --emerald:     #10B981;
  --emerald-dim: rgba(16,185,129,0.12);
  --purple:      #8B5CF6;
  --purple-bright:#A78BFA;
  --amber:       #F59E0B;

  --grad-brand:  linear-gradient(135deg,#3B82F6,#06B6D4,#10B981);
  --grad-hero:   linear-gradient(135deg,#3B82F6 0%,#8B5CF6 50%,#06B6D4 100%);
  --grad-blue:   linear-gradient(135deg,#3B82F6,#06B6D4);
  --grad-green:  linear-gradient(135deg,#10B981,#06B6D4);
  --grad-purple: linear-gradient(135deg,#8B5CF6,#3B82F6);

  --font: 'Inter',system-ui,-apple-system,sans-serif;
  --radius-sm: 8px;
  --radius:    16px;
  --radius-lg: 24px;
  --radius-xl: 32px;
  --ease:      cubic-bezier(0.4,0,0.2,1);
  --ease-out:  cubic-bezier(0,0,0.2,1);
  --spring:    cubic-bezier(0.34,1.56,0.64,1);
}

*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }

html {
  font-family: var(--font);
  background: var(--bg);
  color: #fff;
  overflow-x: hidden;
  scroll-behavior: smooth;
}
body { background: var(--bg); min-height: 100%; }

/* ═══ BACKGROUND LAYERS ═══ */
#bg-canvas {
  position: fixed; inset: 0; z-index: 0;
  pointer-events: none; width: 100%; height: 100%;
}
.gradient-mesh {
  position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden;
}
.gradient-mesh::before,
.gradient-mesh::after,
.gradient-mesh .blob3 {
  content: ''; position: absolute; border-radius: 50%;
  filter: blur(120px); will-change: transform;
}
.gradient-mesh::before {
  width: 70vw; height: 70vw; max-width: 900px; max-height: 900px;
  top: -20%; left: -15%;
  background: radial-gradient(circle, rgba(59,130,246,0.09) 0%, transparent 70%);
  animation: blobDrift1 18s ease-in-out infinite alternate;
}
.gradient-mesh::after {
  width: 60vw; height: 60vw; max-width: 800px; max-height: 800px;
  bottom: -15%; right: -10%;
  background: radial-gradient(circle, rgba(16,185,129,0.07) 0%, transparent 70%);
  animation: blobDrift2 22s ease-in-out infinite alternate;
}
@keyframes blobDrift1 { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(6vw,8vh) scale(1.12); } }
@keyframes blobDrift2 { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(-8vw,-6vh) scale(1.1); } }
.noise {
  position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: 0.022;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}
/* Dot grid overlay */
.dot-grid {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: radial-gradient(circle, rgba(255,255,255,0.032) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(ellipse 100% 100% at 50% 50%, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse 100% 100% at 50% 50%, black 30%, transparent 80%);
}

/* ═══ PAGE WRAPPER ═══ */
#landing-root { position: relative; z-index: 1; }
.container {
  width: 100%; max-width: 1280px;
  margin: 0 auto; padding: 0 48px;
}
@media(max-width:768px) { .container { padding: 0 24px; } }

/* ═══ NAVBAR ═══ */
#navbar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 9000;
  padding: 16px 0;
  transition: all 0.4s var(--ease);
}
#navbar.scrolled {
  background: rgba(6,7,13,0.85);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-bottom: 1px solid var(--border);
  padding: 12px 0;
}
.nav-inner {
  display: flex; align-items: center; justify-content: space-between;
  max-width: 1280px; margin: 0 auto; padding: 0 48px;
}
.nav-logo {
  display: flex; align-items: center; gap: 10px;
  font-size: 0.95rem; font-weight: 700; color: #fff;
  text-decoration: none;
}
.nav-logo-mark {
  width: 32px; height: 32px; border-radius: 10px;
  background: var(--grad-brand);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; font-weight: 900;
  box-shadow: 0 0 20px rgba(59,130,246,0.4);
}
.nav-links {
  display: flex; align-items: center; gap: 2px;
}
.nav-link {
  padding: 6px 14px; border-radius: 8px;
  font-size: 0.82rem; font-weight: 500;
  color: rgba(255,255,255,0.5); text-decoration: none;
  transition: all 0.2s var(--ease); border: none; background: none; cursor: pointer;
}
.nav-link:hover { color: rgba(255,255,255,0.9); background: rgba(255,255,255,0.05); }
.nav-ctas { display: flex; align-items: center; gap: 10px; }
.btn-nav-ghost {
  padding: 7px 18px; border-radius: 10px; font-size: 0.82rem;
  font-weight: 600; color: rgba(255,255,255,0.6);
  border: 1px solid var(--border); background: transparent;
  text-decoration: none; transition: all 0.25s var(--ease); cursor: pointer;
}
.btn-nav-ghost:hover { border-color: var(--border-2); color: #fff; background: rgba(255,255,255,0.04); }
.btn-nav-primary {
  padding: 7px 18px; border-radius: 10px; font-size: 0.82rem;
  font-weight: 700; color: #fff; border: none;
  background: var(--blue); text-decoration: none;
  box-shadow: 0 0 0 1px rgba(59,130,246,0.3), 0 4px 16px rgba(59,130,246,0.3);
  transition: all 0.25s var(--ease); cursor: pointer; position: relative; overflow: hidden;
}
.btn-nav-primary::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg,rgba(255,255,255,0.12),transparent 60%);
  border-radius: 10px;
}
.btn-nav-primary:hover { background: #2563EB; box-shadow: 0 0 0 1px rgba(59,130,246,0.4), 0 8px 28px rgba(59,130,246,0.45); transform: translateY(-1px); }
@media(max-width:768px) { .nav-links { display: none; } .nav-inner { padding: 0 24px; } }

/* ═══ HERO ═══ */
#hero {
  min-height: 100vh; display: flex; align-items: center;
  padding-top: 130px; position: relative;
}
.hero-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 60px; align-items: center;
}
.hero-eyebrow {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 5px 14px; border-radius: 20px;
  border: 1px solid rgba(59,130,246,0.25);
  background: rgba(59,130,246,0.08);
  font-size: 0.7rem; font-weight: 600; letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--blue-bright);
  margin-bottom: 28px;
  animation: eyebrowIn 0.8s var(--ease-out) 0.1s both;
}
.eyebrow-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--emerald); box-shadow: 0 0 8px var(--emerald);
  animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
  0%,100% { opacity: 1; box-shadow: 0 0 0 0 rgba(16,185,129,0.5); }
  50% { opacity: 0.7; box-shadow: 0 0 0 6px rgba(16,185,129,0); }
}
.hero-h1 {
  font-size: clamp(2.8rem, 5.5vw, 5.2rem);
  font-weight: 900; line-height: 1.01;
  letter-spacing: -0.04em; margin-bottom: 24px;
  animation: heroH1In 0.9s var(--ease-out) 0.2s both;
}
.h1-white { display: block; color: #fff; }
.h1-gradient {
  display: block;
  background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 40%, #34D399 80%, #67E8F9 100%);
  background-size: 200% 200%;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradShift 6s ease-in-out infinite;
}
@keyframes gradShift {
  0%,100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
.hero-p {
  font-size: 1.05rem; line-height: 1.72;
  color: rgba(255,255,255,0.48); font-weight: 400;
  max-width: 480px; margin-bottom: 36px;
  animation: heroFade 1s var(--ease-out) 0.35s both;
}
.hero-chips {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-bottom: 36px;
  animation: heroFade 1s var(--ease-out) 0.45s both;
}
.chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 20px;
  font-size: 0.72rem; font-weight: 600;
  border: 1px solid var(--border);
  background: rgba(255,255,255,0.03);
  color: rgba(255,255,255,0.55);
  backdrop-filter: blur(10px);
  transition: all 0.25s var(--ease); cursor: default;
}
.chip:hover { border-color: rgba(59,130,246,0.3); color: rgba(255,255,255,0.8); background: rgba(59,130,246,0.06); transform: translateY(-1px); }
.chip-ico { font-size: 0.88rem; }
.hero-btns {
  display: flex; gap: 14px; flex-wrap: wrap;
  animation: heroFade 1s var(--ease-out) 0.55s both;
}
.btn-hero-primary {
  display: inline-flex; align-items: center; gap: 9px;
  padding: 15px 30px; border-radius: 13px;
  font-size: 0.94rem; font-weight: 700; color: #fff;
  background: linear-gradient(135deg,#3B82F6,#2563EB);
  border: 1px solid rgba(255,255,255,0.12);
  text-decoration: none;
  box-shadow: 0 0 0 1px rgba(59,130,246,0.3), 0 8px 32px rgba(59,130,246,0.45), inset 0 1px 0 rgba(255,255,255,0.14);
  transition: all 0.3s var(--spring); position: relative; overflow: hidden;
}
.btn-hero-primary::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(145deg,rgba(255,255,255,0.16),transparent 55%);
}
.btn-hero-primary::after { content: none; }
/* Ripple is now JS-injected via .btn-ripple span */
.btn-ripple { position: absolute; border-radius: 50%; background: rgba(255,255,255,0.22);
  transform: scale(0); animation: rippleExp 0.55s cubic-bezier(0.4,0,0.2,1) forwards;
  pointer-events: none;
}
@keyframes rippleExp { to { transform: scale(4); opacity: 0; } }
.btn-hero-primary:hover { transform: translateY(-3px) scale(1.025); box-shadow: 0 0 0 1px rgba(59,130,246,0.45), 0 18px 52px rgba(59,130,246,0.6), inset 0 1px 0 rgba(255,255,255,0.16); }
.btn-hero-secondary {
  display: inline-flex; align-items: center; gap: 9px;
  padding: 14px 26px; border-radius: 13px;
  font-size: 0.94rem; font-weight: 600; color: rgba(255,255,255,0.72);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.09);
  text-decoration: none;
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  transition: all 0.3s var(--ease); position: relative; overflow: hidden;
}
.btn-hero-secondary:hover { border-color: rgba(255,255,255,0.18); color: #fff; background: rgba(255,255,255,0.08); transform: translateY(-2px); box-shadow: 0 8px 28px rgba(0,0,0,0.3); }
.btn-arrow { transition: transform 0.3s var(--spring); display: inline-block; }
.btn-hero-primary:hover .btn-arrow { transform: translateX(4px); }

/* Hero Right - Canvas */
.hero-visual {
  position: relative; height: 600px;
}
#campus-canvas {
  width: 100%; height: 100%; border-radius: var(--radius-xl);
  display: block;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.04), 0 40px 100px rgba(0,0,0,0.5);
}
.hero-float-card {
  position: absolute; border-radius: 14px;
  background: rgba(10,12,20,0.88);
  backdrop-filter: blur(24px) saturate(160%); -webkit-backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid rgba(255,255,255,0.1);
  padding: 14px 18px; min-width: 160px;
  box-shadow: 0 24px 64px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.03), inset 0 1px 0 rgba(255,255,255,0.06);
  animation: floatCard 5s ease-in-out infinite;
  pointer-events: none; position: absolute;
}
/* Gradient border ring on float cards */
.hero-float-card::before {
  content: ''; position: absolute; inset: 0; border-radius: 14px;
  padding: 1px;
  background: linear-gradient(135deg,rgba(59,130,246,0.4),rgba(139,92,246,0.2),rgba(16,185,129,0.15));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  pointer-events: none;
}
.hfc-1 { bottom: 56px; left: -32px; animation-delay: 0s; }
.hfc-2 { top: 72px; right: -24px; animation-delay: -2.2s; }
.hfc-3 { bottom: 168px; right: -18px; animation-delay: -1.4s; }
@keyframes floatCard {
  0%,100% { transform: translateY(0) rotate(0deg); }
  33% { transform: translateY(-8px) rotate(0.3deg); }
  66% { transform: translateY(-14px) rotate(-0.2deg); }
}
.hfc-label { font-size: 0.58rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(255,255,255,0.3); margin-bottom: 3px; }
.hfc-value { font-size: 1rem; font-weight: 800; color: #fff; }
.hfc-sub { font-size: 0.62rem; color: rgba(255,255,255,0.35); margin-top: 2px; }
.hfc-badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 8px; font-size: 0.58rem; font-weight: 700; margin-top: 4px; }
.hfc-badge.green { background: rgba(16,185,129,0.12); color: var(--emerald); border: 1px solid rgba(16,185,129,0.2); }
.hfc-badge.blue { background: rgba(59,130,246,0.12); color: var(--blue-bright); border: 1px solid rgba(59,130,246,0.2); }

/* Scroll hint */
.scroll-hint {
  position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  color: rgba(255,255,255,0.2); font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase;
  animation: scrollHint 3s ease-in-out infinite;
}
.scroll-line { width: 1px; height: 40px; background: linear-gradient(to bottom, rgba(255,255,255,0.15), transparent); }
@keyframes scrollHint { 0%,100% { opacity: 0.4; transform: translateX(-50%) translateY(0); } 50% { opacity: 1; transform: translateX(-50%) translateY(6px); } }

@keyframes eyebrowIn { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes heroH1In { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes heroFade { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }

/* ═══ SECTION SYSTEM ═══ */
.section { padding: clamp(96px,10vw,180px) 0; position: relative; }
.section-eyebrow {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 4px 14px; border-radius: 20px;
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
  margin-bottom: 18px;
}
.eyebrow-blue { background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2); color: var(--blue-bright); }
.eyebrow-green { background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); color: #6EE7B7; }
.eyebrow-purple { background: rgba(139,92,246,0.08); border: 1px solid rgba(139,92,246,0.2); color: var(--purple-bright); }
.eyebrow-cyan { background: rgba(6,182,212,0.08); border: 1px solid rgba(6,182,212,0.2); color: var(--cyan-bright); }
.section-h2 {
  font-size: clamp(2rem,4vw,3.2rem); font-weight: 900;
  letter-spacing: -0.035em; line-height: 1.1;
  color: #fff; margin-bottom: 14px;
}
.section-p {
  font-size: 1.02rem; line-height: 1.8; color: rgba(255,255,255,0.52);
  max-width: 540px;
}
.section-header { margin-bottom: 72px; }
.section-header.centered { text-align: center; }
.section-header.centered .section-p { margin: 0 auto; }

/* Divider */
.section-divider {
  height: 1px; margin: 0;
  background: linear-gradient(90deg,transparent,rgba(255,255,255,0.06) 30%,rgba(255,255,255,0.06) 70%,transparent);
}

/* ═══ BENTO FEATURES ═══ */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4,1fr);
  grid-template-rows: auto;
  gap: 18px;
}
.bento-card {
  background: rgba(10,13,22,0.8);
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 20px;
  padding: 32px; position: relative; overflow: hidden;
  transition: transform 0.4s cubic-bezier(0.34,1.2,0.64,1), box-shadow 0.4s var(--ease), border-color 0.3s var(--ease); cursor: default;
}
/* Gradient border on hover via pseudo overlay */
.bento-card::after {
  content: ''; position: absolute; inset: 0; border-radius: 20px;
  padding: 1px;
  background: linear-gradient(135deg,rgba(59,130,246,0.35),rgba(139,92,246,0.2),rgba(16,185,129,0.2));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  opacity: 0; transition: opacity 0.4s var(--ease); pointer-events: none;
}
.bento-card::before {
  content: ''; position: absolute; inset: 0; border-radius: 20px;
  background: radial-gradient(ellipse at top left, rgba(59,130,246,0.07), transparent 65%);
  opacity: 0; transition: opacity 0.4s var(--ease);
}
.bento-card:hover::before { opacity: 1; }
.bento-card:hover::after { opacity: 1; }
.bento-card:hover {
  border-color: rgba(59,130,246,0.15);
  box-shadow: 0 0 0 0 transparent, 0 28px 72px rgba(0,0,0,0.55), 0 0 60px rgba(59,130,246,0.08), inset 0 1px 0 rgba(255,255,255,0.04);
  transform: translateY(-5px);
}
.bento-card.span-2 { grid-column: span 2; }
.bento-card.span-3 { grid-column: span 3; }
.bento-card.tall { grid-row: span 2; }
.bento-top-glow {
  position: absolute; top: 0; left: 0; right: 0; height: 1.5px;
  border-radius: 20px 20px 0 0;
  opacity: 0.5; transition: opacity 0.35s var(--ease), box-shadow 0.35s var(--ease);
}
.bento-card:hover .bento-top-glow { opacity: 1; box-shadow: 0 0 20px rgba(59,130,246,0.4); }

.bento-icon {
  width: 52px; height: 52px; border-radius: 15px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.35rem; margin-bottom: 20px;
  border: 1px solid rgba(255,255,255,0.08);
  position: relative; overflow: hidden;
  box-shadow: 0 4px 16px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.08);
}
.bento-icon::before {
  content: ''; position: absolute; inset: 0; border-radius: 15px;
  background: linear-gradient(145deg,rgba(255,255,255,0.12),transparent 55%);
}
.bento-title { font-size: 1.05rem; font-weight: 700; color: #fff; margin-bottom: 9px; letter-spacing: -0.01em; }
.bento-desc { font-size: 0.82rem; line-height: 1.7; color: rgba(255,255,255,0.42); }
.bento-stat {
  display: flex; align-items: baseline; gap: 7px;
  margin-top: 22px;
}
.bento-stat-num { font-size: 2rem; font-weight: 900; letter-spacing: -0.045em; }
.bento-stat-label { font-size: 0.74rem; color: rgba(255,255,255,0.35); font-weight: 500; }

/* Mini animated bars */
.mini-bars { display: flex; gap: 4px; align-items: flex-end; margin-top: 18px; height: 36px; }
.mini-bar {
  flex: 1; border-radius: 4px; position: relative; overflow: hidden;
  animation: barPulse 2s ease-in-out infinite;
}
.mini-bar::after { content: ''; position: absolute; inset: 0; background: linear-gradient(to top, rgba(255,255,255,0.1), transparent); border-radius: 4px; }
.mb1 { height: 60%; animation-delay: 0s; }
.mb2 { height: 85%; animation-delay: 0.15s; }
.mb3 { height: 45%; animation-delay: 0.3s; }
.mb4 { height: 70%; animation-delay: 0.45s; }
.mb5 { height: 95%; animation-delay: 0.6s; }
.mb6 { height: 55%; animation-delay: 0.75s; }
@keyframes barPulse {
  0%,100% { opacity: 0.6; transform: scaleY(1); }
  50% { opacity: 1; transform: scaleY(1.05); }
}

/* Status dots */
.status-row { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; }
.status-pill {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 10px; border-radius: 20px;
  font-size: 0.62rem; font-weight: 600;
  background: rgba(16,185,129,0.08); color: #6EE7B7;
  border: 1px solid rgba(16,185,129,0.15);
}
.status-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--emerald); animation: pulse-dot 2s infinite; }

/* Progress arc */
.arc-container { position: relative; width: 80px; height: 80px; margin-top: 16px; }

/* ═══ WORKFLOW SECTION ═══ */
.workflow-path {
  display: flex; align-items: flex-start;
  gap: 0; padding: 48px 0; position: relative;
  overflow-x: auto; scrollbar-width: none;
}
.workflow-path::-webkit-scrollbar { display: none; }
.wf-step {
  display: flex; flex-direction: column; align-items: center;
  min-width: 104px; text-align: center; position: relative;
}
.wf-node {
  width: 72px; height: 72px; border-radius: 20px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.4rem; position: relative;
  background: rgba(11,14,24,0.9);
  border: 1px solid rgba(255,255,255,0.09);
  box-shadow: 0 8px 28px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06);
  transition: all 0.35s var(--spring);
  cursor: default; margin-bottom: 14px;
  backdrop-filter: blur(12px);
}
.wf-node::before {
  content: ''; position: absolute; inset: -1px; border-radius: 20px;
  background: var(--grad-blue); opacity: 0; transition: opacity 0.35s var(--ease);
  z-index: -1;
}
.wf-node:hover { transform: scale(1.12) translateY(-5px); box-shadow: 0 16px 40px rgba(59,130,246,0.25); }
.wf-node:hover::before { opacity: 0.35; }
.wf-step-num {
  position: absolute; top: -9px; right: -9px;
  width: 22px; height: 22px; border-radius: 50%;
  background: linear-gradient(135deg,#3B82F6,#2563EB); font-size: 0.6rem; font-weight: 800;
  display: flex; align-items: center; justify-content: center; color: #fff;
  box-shadow: 0 0 12px rgba(59,130,246,0.6), 0 2px 6px rgba(0,0,0,0.4);
}
.wf-label { font-size: 0.65rem; font-weight: 700; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.04em; line-height: 1.45; max-width: 78px; }
.wf-sub { font-size: 0.55rem; color: rgba(255,255,255,0.25); margin-top: 4px; }
.wf-connector {
  flex: 1; min-width: 20px; display: flex; align-items: center;
  padding-bottom: 46px; position: relative;
}
.wf-line {
  flex: 1; height: 1.5px; position: relative; overflow: hidden;
  background: rgba(59,130,246,0.12);
  border-radius: 2px;
}
.wf-line::after {
  content: ''; position: absolute; top: 0; left: -100%;
  width: 55%; height: 100%;
  background: linear-gradient(90deg, transparent, var(--blue-bright), transparent);
  animation: lineSweep 2.4s cubic-bezier(0.4,0,0.6,1) infinite;
}
@keyframes lineSweep { 0% { left: -55%; opacity: 0; } 20% { opacity: 1; } 80% { opacity: 1; } 100% { left: 110%; opacity: 0; } }
.wf-arrow { font-size: 0.75rem; color: rgba(59,130,246,0.45); flex-shrink: 0; margin-left: 2px; }

/* ═══ AI SECTION ═══ */
.ai-section { overflow: hidden; }
.ai-grid { display: grid; grid-template-columns: 1fr 1.1fr; gap: 80px; align-items: center; }
.ai-visual { position: relative; height: 460px; }
#neural-canvas { width: 100%; height: 100%; }

.ai-tech-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 36px; }
.ai-tech-card {
  padding: 16px 18px; border-radius: var(--radius);
  background: rgba(10,13,22,0.75); border: 1px solid rgba(255,255,255,0.07);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  display: flex; align-items: center; gap: 12px;
  transition: all 0.3s var(--ease); position: relative; overflow: hidden;
}
.ai-tech-card::before {
  content: ''; position: absolute; left: 0; top: 0; width: 2px; height: 100%;
  background: var(--grad-blue); border-radius: 2px 0 0 2px;
  opacity: 0; transition: opacity 0.3s var(--ease);
}
.ai-tech-card:hover { border-color: rgba(255,255,255,0.12); transform: translateX(5px); background: rgba(59,130,246,0.04); }
.ai-tech-card:hover::before { opacity: 1; }
.atc-ico { font-size: 1.25rem; flex-shrink: 0; }
.atc-name { font-size: 0.82rem; font-weight: 700; color: #fff; }
.atc-tag { font-size: 0.62rem; color: rgba(255,255,255,0.35); margin-top: 2px; }
.atc-bar { flex: 1; height: 3px; border-radius: 3px; background: rgba(255,255,255,0.06); overflow: hidden; min-width: 0; }
.atc-fill { height: 100%; border-radius: 3px; animation: barGrow 1.5s var(--ease-out) both; }
@keyframes barGrow { from { width: 0 !important; } }

/* ═══ STATS SECTION ═══ */
.stats-grid {
  display: grid; grid-template-columns: repeat(5,1fr);
  gap: 1px; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.07); border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.02), 0 40px 100px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04);
}
.stat-cell {
  padding: 48px 28px; text-align: center;
  background: rgba(8,10,18,0.95);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  transition: background 0.3s var(--ease); cursor: default; position: relative;
}
.stat-cell::before {
  content: ''; position: absolute; top: 0; left: 50%; transform: translateX(-50%);
  width: 60%; height: 1px;
  background: linear-gradient(90deg,transparent,rgba(59,130,246,0.25),transparent);
  opacity: 0; transition: opacity 0.3s;
}
.stat-cell:hover::before { opacity: 1; }
.stat-cell:hover { background: rgba(59,130,246,0.04); }
.stat-num {
  font-size: clamp(2.2rem,3.5vw,3.2rem); font-weight: 900;
  letter-spacing: -0.045em;
  background: linear-gradient(135deg,#fff 30%,rgba(255,255,255,0.55) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px; display: block;
}
.stat-label { font-size: 0.8rem; color: rgba(255,255,255,0.36); font-weight: 500; }
.stat-sub { font-size: 0.64rem; color: rgba(59,130,246,0.75); margin-top: 5px; font-weight: 700; letter-spacing: 0.02em; }

/* ═══ TECH ORBIT SECTION ═══ */
.tech-orbit-wrap {
  display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: center;
}
.orbit-container { position: relative; width: 380px; height: 380px; margin: 0 auto; }
.orbit-core {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 80px; height: 80px; border-radius: 50%;
  background: var(--grad-brand);
  box-shadow: 0 0 60px rgba(59,130,246,0.6), 0 0 120px rgba(59,130,246,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.8rem; z-index: 10;
  animation: coreGlow 3s ease-in-out infinite;
}
@keyframes coreGlow {
  0%,100% { box-shadow: 0 0 60px rgba(59,130,246,0.6), 0 0 120px rgba(59,130,246,0.2); }
  50% { box-shadow: 0 0 80px rgba(59,130,246,0.9), 0 0 160px rgba(59,130,246,0.35); }
}
.orbit-ring {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  border-radius: 50%; border: 1px solid rgba(59,130,246,0.12);
}
.orbit-ring-1 { width: 160px; height: 160px; animation: ringRotate 12s linear infinite; }
.orbit-ring-2 { width: 260px; height: 260px; animation: ringRotate 20s linear infinite reverse; border-color: rgba(139,92,246,0.1); }
.orbit-ring-3 { width: 360px; height: 360px; animation: ringRotate 30s linear infinite; border-color: rgba(16,185,129,0.08); }
@keyframes ringRotate { from { transform: translate(-50%,-50%) rotate(0deg); } to { transform: translate(-50%,-50%) rotate(360deg); } }
.orbit-icon {
  position: absolute; width: 44px; height: 44px; border-radius: 12px;
  background: var(--surface-2); border: 1px solid var(--border-2);
  display: flex; align-items: center; justify-content: center; font-size: 1.1rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  transition: all 0.3s var(--ease); cursor: default;
}
.orbit-icon:hover { transform: scale(1.2); border-color: rgba(59,130,246,0.4); box-shadow: 0 8px 32px rgba(59,130,246,0.3); }

.tech-list { display: flex; flex-direction: column; gap: 12px; }
.tech-item {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 20px; border-radius: var(--radius);
  background: var(--card); border: 1px solid var(--border);
  transition: all 0.3s var(--ease);
}
.tech-item:hover { border-color: var(--border-2); transform: translateX(6px); background: rgba(59,130,246,0.04); }
.tech-ico { font-size: 1.2rem; }
.tech-name { font-size: 0.88rem; font-weight: 700; color: #fff; }
.tech-desc { font-size: 0.72rem; color: rgba(255,255,255,0.3); margin-top: 1px; }
.tech-badge {
  margin-left: auto; padding: 3px 10px; border-radius: 20px;
  font-size: 0.6rem; font-weight: 700;
}

/* ═══ CAMPUS NETWORK ═══ */
.campus-network {
  display: flex; flex-direction: column; align-items: center;
  gap: 0; position: relative; padding: 20px 0;
}
.cn-node {
  padding: 14px 32px; border-radius: 14px;
  font-size: 0.85rem; font-weight: 700;
  display: flex; align-items: center; gap: 10px;
  cursor: default;
}
.cn-node.primary {
  background: linear-gradient(135deg,rgba(59,130,246,0.2),rgba(139,92,246,0.15));
  border: 1px solid rgba(59,130,246,0.3);
  color: #fff; font-size: 0.95rem;
  box-shadow: 0 0 40px rgba(59,130,246,0.15), inset 0 1px 0 rgba(255,255,255,0.08);
}
.cn-node.center {
  background: var(--card); border: 1px solid var(--border);
  color: rgba(255,255,255,0.7);
  animation: cnPulse 3s ease-in-out infinite;
}
.cn-node.center:nth-child(2) { animation-delay: -1s; }
.cn-node.center:nth-child(3) { animation-delay: -2s; }
@keyframes cnPulse { 0%,100% { border-color: rgba(59,130,246,0.12); } 50% { border-color: rgba(59,130,246,0.35); } }
.cn-node.leaf { background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); color: #6EE7B7; }
.cn-connector { display: flex; flex-direction: column; align-items: center; padding: 6px 0; }
.cn-line {
  width: 2px; height: 28px;
  background: linear-gradient(180deg,rgba(59,130,246,0.4),rgba(16,185,129,0.3));
  position: relative; overflow: hidden;
}
.cn-line::after {
  content: ''; position: absolute; width: 100%; height: 40%;
  background: linear-gradient(180deg,transparent,rgba(255,255,255,0.9),transparent);
  animation: dataFlow 1.8s linear infinite;
}
@keyframes dataFlow { 0% { top: -40%; } 100% { top: 140%; } }
.cn-arrow { font-size: 0.65rem; color: rgba(59,130,246,0.6); }
.cn-centers-row { display: flex; gap: 16px; align-items: flex-start; }
.cn-center-col { display: flex; flex-direction: column; align-items: center; }
.cn-h-connector { display: flex; align-items: center; gap: 0; padding-bottom: 26px; }
.cn-h-line { width: 24px; height: 2px; background: rgba(59,130,246,0.25); position: relative; overflow: hidden; }
.cn-h-line::after { content: ''; position: absolute; height: 100%; width: 50%; background: linear-gradient(90deg,transparent,rgba(59,130,246,0.8),transparent); animation: hDataFlow 1.5s linear infinite; }
@keyframes hDataFlow { 0% { left: -50%; } 100% { left: 150%; } }
.cn-center-label { font-size: 0.58rem; color: rgba(255,255,255,0.25); margin-top: 6px; font-weight: 600; }

/* ═══ LIVE DASHBOARD ═══ */
.live-dash {
  background: rgba(8,10,18,0.92);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 24px;
  padding: 28px; position: relative; overflow: hidden;
  box-shadow: 0 48px 128px rgba(0,0,0,0.65), 0 0 0 1px rgba(255,255,255,0.03), inset 0 1px 0 rgba(255,255,255,0.05);
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
}
.live-dash::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1.5px;
  background: linear-gradient(90deg,transparent,rgba(59,130,246,0.6) 25%,rgba(16,185,129,0.5) 60%,rgba(139,92,246,0.4) 80%,transparent);
}
.live-dash::after {
  content: ''; position: absolute; top: 0; left: 20%; right: 20%; height: 60px;
  background: radial-gradient(ellipse at center top, rgba(59,130,246,0.07), transparent 70%);
  pointer-events: none;
}
.dash-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px; }
.dash-title { font-size: 0.74rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: rgba(255,255,255,0.45); }
.dash-live { display: flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 20px; font-size: 0.62rem; font-weight: 700; background: rgba(16,185,129,0.1); color: #6EE7B7; border: 1px solid rgba(16,185,129,0.25); animation: livePulse 2s ease-in-out infinite; }
@keyframes livePulse { 0%,100% { box-shadow: 0 0 0 0 rgba(16,185,129,0.2); } 50% { box-shadow: 0 0 0 4px rgba(16,185,129,0); } }
.dash-metrics { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin-bottom: 16px; }
.dash-metric {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px; padding: 16px; position: relative; overflow: hidden;
}
.dash-metric::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg,transparent,rgba(255,255,255,0.08),transparent);
}
.dm-label { font-size: 0.56rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; color: rgba(255,255,255,0.3); margin-bottom: 7px; }
.dm-value { font-size: 1.35rem; font-weight: 900; letter-spacing: -0.04em; }
.dm-sub { font-size: 0.58rem; color: rgba(255,255,255,0.28); margin-top: 4px; }
.dash-activity { background: rgba(255,255,255,0.018); border: 1px solid rgba(255,255,255,0.05); border-radius: 14px; padding: 16px; }
.da-row { display: flex; align-items: center; gap: 11px; padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.da-row:last-child { border-bottom: none; }
.da-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.da-text { font-size: 0.68rem; color: rgba(255,255,255,0.45); flex: 1; }
.da-time { font-size: 0.6rem; color: rgba(255,255,255,0.22); white-space: nowrap; }

/* Graph line */
.spark-container { height: 50px; position: relative; overflow: hidden; }
.spark-line { width: 100%; height: 100%; }

/* ═══ CTA SECTION ═══ */
.cta-card {
  position: relative; border-radius: 28px;
  background: rgba(8,10,18,0.85);
  backdrop-filter: blur(32px); -webkit-backdrop-filter: blur(32px);
  border: 1px solid rgba(255,255,255,0.08);
  padding: clamp(56px,8vw,96px) clamp(32px,6vw,80px);
  text-align: center; overflow: hidden;
  box-shadow: 0 60px 140px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.03), inset 0 1px 0 rgba(255,255,255,0.05);
}
/* Animated gradient border ring */
.cta-card::before {
  content: ''; position: absolute; inset: 0; border-radius: 28px; padding: 1px;
  background: linear-gradient(135deg,rgba(59,130,246,0.5),rgba(139,92,246,0.3),rgba(16,185,129,0.3),rgba(59,130,246,0.5));
  background-size: 300% 300%;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  animation: ctaBorderFlow 6s linear infinite; pointer-events: none;
}
@keyframes ctaBorderFlow { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
.cta-bg-glow {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 600px; height: 300px;
  background: radial-gradient(ellipse at center, rgba(59,130,246,0.12) 0%, rgba(139,92,246,0.06) 50%, transparent 70%);
  pointer-events: none; z-index: 0;
  animation: ctaGlowPulse 4s ease-in-out infinite;
}
@keyframes ctaGlowPulse { 0%,100% { opacity: 0.7; transform: translate(-50%,-50%) scale(1); } 50% { opacity: 1; transform: translate(-50%,-50%) scale(1.1); } }
.cta-eyebrow {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 5px 16px; border-radius: 20px;
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.2); color: #60A5FA;
  margin-bottom: 28px; position: relative; z-index: 1;
}
.cta-h2 {
  font-size: clamp(2.2rem,4.5vw,3.6rem); font-weight: 900;
  letter-spacing: -0.04em; line-height: 1.08; color: #fff;
  margin-bottom: 20px; position: relative; z-index: 1;
}
.cta-p {
  font-size: 1.05rem; line-height: 1.78; color: rgba(255,255,255,0.5);
  max-width: 580px; margin: 0 auto 40px; position: relative; z-index: 1;
}
.cta-btns {
  display: flex; gap: 16px; justify-content: center; flex-wrap: wrap;
  margin-bottom: 44px; position: relative; z-index: 1;
}
.cta-badges {
  display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;
  position: relative; z-index: 1;
}
.cta-badge {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 16px; border-radius: 20px;
  font-size: 0.74rem; font-weight: 600; color: rgba(255,255,255,0.45);
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  transition: all 0.25s var(--ease);
}
.cta-badge:hover { border-color: rgba(59,130,246,0.25); color: rgba(255,255,255,0.7); background: rgba(59,130,246,0.06); }
@media(max-width:768px) { .cta-btns { flex-direction: column; align-items: center; } .cta-badges { gap: 8px; } }

/* ═══ FOOTER ═══ */
#footer {
  border-top: 1px solid rgba(255,255,255,0.06);
  padding: 88px 0 40px;
  position: relative; z-index: 1;
  background: linear-gradient(180deg, transparent, rgba(6,7,13,0.8));
}
.footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 56px; margin-bottom: 56px; }
.ft-brand { font-size: 1rem; font-weight: 700; color: #fff; margin-bottom: 12px; display: flex; align-items: center; gap: 10px; }
.ft-desc { font-size: 0.8rem; color: rgba(255,255,255,0.28); line-height: 1.78; max-width: 240px; margin-bottom: 24px; }
.ft-socials { display: flex; gap: 8px; }
.ft-soc {
  width: 36px; height: 36px; border-radius: 10px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  display: flex; align-items: center; justify-content: center; font-size: 0.9rem;
  cursor: pointer; transition: all 0.25s var(--spring);
}
.ft-soc:hover { background: rgba(59,130,246,0.1); border-color: rgba(59,130,246,0.3); transform: translateY(-3px); box-shadow: 0 8px 24px rgba(59,130,246,0.2); }
.ft-col-title { font-size: 0.66rem; font-weight: 800; letter-spacing: 0.09em; text-transform: uppercase; color: rgba(255,255,255,0.35); margin-bottom: 18px; }
.ft-link { display: block; font-size: 0.82rem; color: rgba(255,255,255,0.26); margin-bottom: 12px; cursor: pointer; transition: color 0.22s, transform 0.22s; text-decoration: none; }
.ft-link:hover { color: rgba(255,255,255,0.7); transform: translateX(3px); }
.footer-bottom { display: flex; justify-content: space-between; align-items: center; padding-top: 32px; border-top: 1px solid rgba(255,255,255,0.06); }
.footer-copy { font-size: 0.74rem; color: rgba(255,255,255,0.2); }
.footer-badges { display: flex; gap: 8px; }
.footer-badge { display: flex; align-items: center; gap: 5px; padding: 5px 13px; border-radius: 20px; font-size: 0.62rem; font-weight: 700; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); color: rgba(255,255,255,0.3); }

/* ═══ SCROLL REVEAL ═══ */
.reveal { opacity: 1; transform: translateY(0); transition: opacity 0.75s cubic-bezier(0,0,0.2,1), transform 0.75s cubic-bezier(0,0,0.2,1); }
.reveal.visible { opacity: 1; transform: translateY(0); }
.reveal-d1 { transition-delay: 0.08s; }
.reveal-d2 { transition-delay: 0.18s; }
.reveal-d3 { transition-delay: 0.28s; }
.reveal-d4 { transition-delay: 0.38s; }
.reveal-scale { opacity: 0; transform: scale(0.97) translateY(18px); transition: opacity 0.65s cubic-bezier(0,0,0.2,1), transform 0.65s cubic-bezier(0,0,0.2,1); }
.reveal-scale.visible { opacity: 1; transform: scale(1) translateY(0); }

/* Card tilt */
.tilt-card { transform-style: preserve-3d; will-change: transform; }

/* ═══ RESPONSIVE ═══ */
@media(max-width:1024px) {
  .hero-grid { grid-template-columns: 1fr; gap: 48px; }
  .hero-visual { height: 400px; }
  .bento-grid { grid-template-columns: repeat(2,1fr); }
  .bento-card.span-2,.bento-card.span-3 { grid-column: span 2; }
  .ai-grid,.tech-orbit-wrap { grid-template-columns: 1fr; gap: 48px; }
  .orbit-container { width: 300px; height: 300px; }
  .stats-grid { grid-template-columns: repeat(3,1fr); }
  .footer-grid { grid-template-columns: 1fr 1fr; gap: 32px; }
}
@media(max-width:768px) {
  .hero-visual { height: 300px; }
  .hfc-1,.hfc-2,.hfc-3 { display: none; }
  .bento-grid { grid-template-columns: 1fr; }
  .bento-card.span-2,.bento-card.span-3,.bento-card.tall { grid-column: span 1; grid-row: span 1; }
  .stats-grid { grid-template-columns: repeat(2,1fr); }
  .footer-grid { grid-template-columns: 1fr; gap: 28px; }
  .footer-bottom { flex-direction: column; gap: 14px; text-align: center; }
  .workflow-path { gap: 0; }
  .cn-centers-row { flex-direction: column; align-items: center; gap: 0; }
  .cn-h-connector { display: none; }
  .dash-metrics { grid-template-columns: 1fr 1fr; }
}
@media(max-width:480px) {
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .hero-h1 { font-size: 2.4rem; }
}

/* ═══ CURSOR GLOW ═══ */
.cursor-glow {
  position: fixed; width: 500px; height: 500px; border-radius: 50%;
  pointer-events: none; z-index: 0;
  background: radial-gradient(circle,rgba(59,130,246,0.055),transparent 65%);
  transition: transform 0.12s linear;
  transform: translate(-50%,-50%);
  will-change: transform;
}

/* ═══ ORBIT ICON LABELS ═══ */
.orbit-icon-wrap {
  position: absolute; display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.orbit-icon-label { font-size: 0.52rem; font-weight: 700; color: rgba(255,255,255,0.3); white-space: nowrap; letter-spacing: 0.05em; }

/* ═══ SECTION ACCENT LINES ═══ */
.section-accent {
  position: absolute; top: 0; left: 50%; transform: translateX(-50%);
  width: 1px; height: 80px;
  background: linear-gradient(180deg,transparent,rgba(59,130,246,0.4),transparent);
}

/* ═══ CINEMATIC MOTION DESIGN ═══ */

/* ── Scroll Progress Bar ── */
#scroll-progress {
  position: fixed; top: 0; left: 0; z-index: 9999;
  height: 2px; width: 0%; border-radius: 0 2px 2px 0;
  background: linear-gradient(90deg,#3B82F6,#8B5CF6,#06B6D4);
  box-shadow: 0 0 12px rgba(59,130,246,0.7);
  transition: width 0.1s linear;
  pointer-events: none;
}

/* ── Hero Blur-Scale-Reveal ── */
.hero-blur-in {
  animation: heroBR 1s cubic-bezier(0,0,0.2,1) both;
}
.hero-blur-in-d1 { animation-delay: 0.05s; }
.hero-blur-in-d2 { animation-delay: 0.18s; }
.hero-blur-in-d3 { animation-delay: 0.30s; }
.hero-blur-in-d4 { animation-delay: 0.44s; }
.hero-blur-in-d5 { animation-delay: 0.58s; }
@keyframes heroBR {
  from { opacity: 0; transform: translateY(22px) scale(0.97); filter: blur(8px); }
  to   { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
}
.hero-visual-in {
  animation: heroVisIn 1.2s cubic-bezier(0,0,0.2,1) 0.25s both;
}
@keyframes heroVisIn {
  from { opacity: 0; transform: translateX(40px) scale(0.96); filter: blur(12px); }
  to   { opacity: 1; transform: translateX(0) scale(1); filter: blur(0); }
}

/* ── Gradient Sweep Button ── */
.btn-sweep {
  position: relative; overflow: hidden;
}
.btn-sweep::after {
  content: ''; position: absolute; top: 0; left: -120%;
  width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
  transform: skewX(-20deg);
  transition: none;
  pointer-events: none;
}
.btn-sweep:hover::after {
  animation: sweepShine 0.6s cubic-bezier(0.4,0,0.2,1) forwards;
}
@keyframes sweepShine {
  from { left: -120%; }
  to   { left: 140%; }
}

/* ── Magnetic Button Wrapper ── */
.mag-btn { display: inline-block; }

/* ── Staggered Bento Reveal ── */
/* Note: bento-seq is only added by JS to cards that DON'T already have .visible from reveal observer */
.bento-card.bento-seq { opacity: 0; transform: translateY(32px) scale(0.97); filter: blur(4px); transition: none; }
.bento-card.bento-seq.bento-in { opacity: 1; transform: translateY(0) scale(1); filter: blur(0);
  transition: opacity 0.65s cubic-bezier(0,0,0.2,1), transform 0.65s cubic-bezier(0,0,0.2,1), filter 0.65s cubic-bezier(0,0,0.2,1);
}

/* ── Parallax Layers ── */
.parallax-slow { will-change: transform; }
.parallax-mid  { will-change: transform; }

/* ── Nav Active Glow ── */
.nav-link.nav-active {
  color: rgba(255,255,255,0.95) !important;
  background: rgba(59,130,246,0.1) !important;
  box-shadow: 0 0 0 1px rgba(59,130,246,0.2), 0 0 16px rgba(59,130,246,0.12);
}

/* ── Floating Icon Animation ── */
@keyframes floatIcon {
  0%,100% { transform: translateY(0) rotate(0deg); }
  25%  { transform: translateY(-6px) rotate(2deg); }
  75%  { transform: translateY(4px) rotate(-1.5deg); }
}
@keyframes spinSlow {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes pulseIcon {
  0%,100% { transform: scale(1); opacity: 1; }
  50%  { transform: scale(1.12); opacity: 0.8; }
}
.ico-float { animation: floatIcon 4s ease-in-out infinite; }
.ico-spin  { animation: spinSlow 8s linear infinite; display: inline-block; }
.ico-pulse { animation: pulseIcon 2.5s ease-in-out infinite; display: inline-block; }

/* ── Section Parallax Offset ── */
.section-parallax { transition: transform 0.1s linear; }

/* ── Workflow AI Pulse ── */
@keyframes wfPulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(59,130,246,0.3), 0 8px 28px rgba(0,0,0,0.5); }
  50%     { box-shadow: 0 0 0 8px rgba(59,130,246,0), 0 8px 28px rgba(0,0,0,0.5); }
}
.wf-node-active { animation: wfPulse 2s ease-in-out infinite; }

/* ── Smooth scrollbar ── */
html { scroll-behavior: smooth; }

/* ── Word-by-word heading reveal ── */
.word-reveal .word {
  display: inline-block; opacity: 0;
  transform: translateY(18px) rotateX(-20deg);
  transform-origin: top center;
  transition: opacity 0.5s cubic-bezier(0,0,0.2,1), transform 0.5s cubic-bezier(0,0,0.2,1);
}
.word-reveal.visible .word { opacity: 1; transform: translateY(0) rotateX(0deg); }

/* ── Typing cursor ── */
.typing-cursor::after {
  content: '|'; display: inline-block;
  animation: cursorBlink 1s step-end infinite;
  color: rgba(96,165,250,0.9); font-weight: 300; margin-left: 2px;
}
@keyframes cursorBlink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

/* ── Section divider glow ── */
.section-divider {
  height: 1px; margin: 0; position: relative;
  background: linear-gradient(90deg,transparent,rgba(255,255,255,0.05) 30%,rgba(255,255,255,0.05) 70%,transparent);
}
.section-divider::after {
  content: ''; position: absolute; top: 0; left: 50%; transform: translateX(-50%);
  width: 120px; height: 1px;
  background: linear-gradient(90deg,transparent,rgba(59,130,246,0.5),transparent);
  animation: divGlow 4s ease-in-out infinite;
}
@keyframes divGlow { 0%,100% { opacity: 0.4; width: 80px; } 50% { opacity: 1; width: 200px; } }

/* ── Stat cell number glow on hover ── */
.stat-cell:hover .stat-num {
  background: linear-gradient(135deg,#fff 20%,#60A5FA 100%);
  -webkit-background-clip: text; background-clip: text;
}

/* ── AI tech card bar animated fill ── */
.atc-fill { transition: width 1.2s cubic-bezier(0,0,0.2,1) !important; }

/* ── Smooth section transitions ── */
.section { position: relative; }

/* ═══ REDUCED MOTION ═══ */
@media(prefers-reduced-motion:reduce) {
  *,.reveal,.reveal-scale { animation-duration:0.01ms!important; transition-duration:0.01ms!important; }
  .reveal,.reveal-scale { opacity:1!important; transform:none!important; }
  .gradient-mesh::before,.gradient-mesh::after { animation: none !important; }
  .hero-blur-in,.hero-visual-in,.bento-seq { opacity:1!important; transform:none!important; filter:none!important; animation:none!important; }
  .word-reveal .word { opacity:1!important; transform:none!important; }
}
</style>
</head>
<body>

<!-- Background -->
<canvas id="bg-canvas"></canvas>
<div class="gradient-mesh"></div>
<div class="dot-grid"></div>
<div class="noise"></div>
<div class="cursor-glow" id="cursor-glow"></div>
<div id="scroll-progress"></div>

<div id="landing-root">

<!-- ════ NAVBAR ════ -->
<nav id="navbar">
  <div class="nav-inner">
    <a class="nav-logo" href="#hero">
      <div class="nav-logo-mark">🎓</div>
      IntelliPrint Nexus
    </a>
    <div class="nav-links">
      <a class="nav-link" href="#features">Features</a>
      <a class="nav-link" href="#workflow">How It Works</a>
      <a class="nav-link" href="#ai-section">AI Engine</a>
      <a class="nav-link" href="#stats">Impact</a>
      <a class="nav-link" href="#tech">Technology</a>
    </div>
    <div class="nav-ctas">
      <a class="btn-nav-ghost" href="?nav_route=login" target="_parent">Sign In</a>
      <a class="btn-nav-primary" href="?nav_route=register" target="_parent">Launch Platform</a>
    </div>
  </div>
</nav>

<!-- ════ HERO ════ -->
<section id="hero" class="section" style="padding-top:0;min-height:100vh;display:flex;align-items:center;">
  <div class="container">
    <div class="hero-grid">
      <!-- Left -->
      <div class="hero-left">
        <div class="hero-eyebrow hero-blur-in hero-blur-in-d1">
          <span class="eyebrow-dot"></span>
          Built exclusively for Universities &amp; Campuses
        </div>
        <h1 class="hero-h1 hero-blur-in hero-blur-in-d2">
          <span class="h1-white">Printing That</span>
          <span class="h1-gradient">Thinks Before</span>
          <span class="h1-white">It Prints.</span>
        </h1>
        <p class="hero-p hero-blur-in hero-blur-in-d3">Transforming university printing through AI Document Intelligence, Smart Queue Optimization, Intelligent Printer Selection, Secure QR Pickup, and Fully Automated Campus Print Management.</p>
        <div class="hero-chips hero-blur-in hero-blur-in-d4">
          <span class="chip"><span class="chip-ico ico-pulse">🧠</span>Document Intelligence</span>
          <span class="chip"><span class="chip-ico ico-float">⚡</span>Queue Prediction</span>
          <span class="chip"><span class="chip-ico">🖨️</span>Smart Routing</span>
          <span class="chip"><span class="chip-ico">🎓</span>University-Native</span>
          <span class="chip"><span class="chip-ico ico-pulse">🔐</span>QR Verification</span>
        </div>
        <div class="hero-btns hero-blur-in hero-blur-in-d5">
          <span class="mag-btn">
            <a class="btn-hero-primary btn-sweep" href="?nav_route=register" target="_parent">
              Get Early Access <span class="btn-arrow">→</span>
            </a>
          </span>
          <span class="mag-btn">
            <a class="btn-hero-secondary btn-sweep" href="#features">
              ▶ &nbsp;See How It Works
            </a>
          </span>
        </div>
      </div>
      <!-- Right: Three.js Campus -->
      <div class="hero-visual hero-visual-in parallax-slow">
        <canvas id="campus-canvas"></canvas>
        <!-- Floating cards -->
        <div class="hero-float-card hfc-1">
          <div class="hfc-label">AI Confidence Score</div>
          <div class="hfc-value" id="hfc-score">98.7%</div>
          <div class="hfc-badge green"><span style="width:5px;height:5px;border-radius:50%;background:#10B981;display:inline-block;"></span> Print-Ready</div>
        </div>
        <div class="hero-float-card hfc-2">
          <div class="hfc-label">Active Printers</div>
          <div class="hfc-value">35 Online</div>
          <div class="hfc-sub">Across 3 Campuses</div>
          <div class="hfc-badge blue">● Fully Balanced</div>
        </div>
        <div class="hero-float-card hfc-3">
          <div class="hfc-label">Avg. Queue Time</div>
          <div class="hfc-value">1m 12s</div>
          <div class="hfc-badge green">↓ 82% Faster</div>
        </div>
      </div>
    </div>
  </div>
  <div class="scroll-hint">
    <div class="scroll-line"></div>
    Scroll
  </div>
</section>

<div class="section-divider"></div>

<!-- ════ FEATURES BENTO ════ -->
<section class="section" id="features">
  <div class="container">
    <div class="section-header reveal">
      <div class="section-eyebrow eyebrow-blue">What It Does</div>
      <h2 class="section-h2">Eight modules.<br>One seamless experience.</h2>
      <p class="section-p">Every feature is purpose-built for universities — from the document you upload to the print you collect.</p>
    </div>
    <div class="bento-grid">

      <!-- Card 1 — Large: AI Analysis -->
      <div class="bento-card span-2 tall reveal reveal-d1 tilt-card">
        <div class="bento-top-glow" style="background:linear-gradient(90deg,#3B82F6,#06B6D4);"></div>
        <div class="bento-icon" style="background:rgba(59,130,246,0.12);">🧠</div>
        <div class="bento-title">Your document, verified before it prints.</div>
        <div class="bento-desc">The AI reads every page for blur, skew, contrast failures, and layout issues — catching defects a human reviewer would miss. Nothing wasteful reaches the printer.</div>
        <div class="mini-bars" style="margin-top:24px;">
          <div class="mini-bar mb1" style="background:rgba(59,130,246,0.6);"></div>
          <div class="mini-bar mb2" style="background:rgba(59,130,246,0.75);"></div>
          <div class="mini-bar mb3" style="background:rgba(59,130,246,0.5);"></div>
          <div class="mini-bar mb4" style="background:rgba(59,130,246,0.8);"></div>
          <div class="mini-bar mb5" style="background:rgba(59,130,246,0.9);"></div>
          <div class="mini-bar mb6" style="background:rgba(59,130,246,0.65);"></div>
          <div class="mini-bar" style="height:78%;background:rgba(59,130,246,0.7);animation:barPulse 2s ease-in-out infinite;animation-delay:0.9s;"></div>
          <div class="mini-bar" style="height:88%;background:rgba(59,130,246,0.85);animation:barPulse 2s ease-in-out infinite;animation-delay:1.05s;"></div>
        </div>
        <div class="bento-stat">
          <span class="bento-stat-num" style="background:var(--grad-blue);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">99%</span>
          <span class="bento-stat-label">Detection Accuracy</span>
        </div>
      </div>

      <!-- Card 2 — Queue Prediction -->
      <div class="bento-card reveal reveal-d2 tilt-card">
        <div class="bento-top-glow" style="background:linear-gradient(90deg,#10B981,#06B6D4);"></div>
        <div class="bento-icon" style="background:rgba(16,185,129,0.12);">⚡</div>
        <div class="bento-title">No more guessing how long it'll take.</div>
        <div class="bento-desc">The system predicts your exact wait time based on live campus load — before you even confirm your print.</div>
        <div class="bento-stat">
          <span class="bento-stat-num" style="color:#10B981;">96%</span>
          <span class="bento-stat-label">Prediction Accuracy</span>
        </div>
      </div>

      <!-- Card 3 — Printer Intelligence -->
      <div class="bento-card reveal reveal-d3 tilt-card">
        <div class="bento-top-glow" style="background:linear-gradient(90deg,#8B5CF6,#3B82F6);"></div>
        <div class="bento-icon" style="background:rgba(139,92,246,0.12);">🖨️</div>
        <div class="bento-title">The right printer, chosen automatically.</div>
        <div class="bento-desc">AI evaluates load, proximity, and paper type across every connected printer — routing jobs to the fastest available option.</div>
        <div class="status-row">
          <span class="status-pill"><span class="status-dot"></span> 35 Active</span>
          <span class="status-pill"><span class="status-dot"></span> Balanced</span>
        </div>
      </div>

      <!-- Card 4 — QR Pickup -->
      <div class="bento-card reveal reveal-d2 tilt-card">
        <div class="bento-top-glow" style="background:linear-gradient(90deg,#F59E0B,#EF4444);"></div>
        <div class="bento-icon" style="background:rgba(245,158,11,0.12);">🔐</div>
        <div class="bento-title">Your prints can only be collected by you.</div>
        <div class="bento-desc">Each job generates a cryptographic QR code tied to your identity. Scan and collect. No mix-ups, no queues.</div>
        <div class="bento-stat">
          <span class="bento-stat-num" style="color:#F59E0B;">100%</span>
          <span class="bento-stat-label">Identity Verified</span>
        </div>
      </div>

      <!-- Card 5 — Analytics (wide) -->
      <div class="bento-card span-2 reveal reveal-d1 tilt-card">
        <div class="bento-top-glow" style="background:linear-gradient(90deg,#06B6D4,#10B981);"></div>
        <div style="display:flex;gap:28px;align-items:flex-start;">
          <div style="flex:1;">
            <div class="bento-icon" style="background:rgba(6,182,212,0.12);">📊</div>
            <div class="bento-title">See everything, in real time.</div>
            <div class="bento-desc">Usage patterns, departmental costs, queue forecasts — all available to administrators without pulling a single report.</div>
          </div>
          <div style="flex:1;">
            <canvas id="spark-chart" height="90" style="width:100%;"></canvas>
          </div>
        </div>
      </div>

      <!-- Card 6 — Payments -->
      <div class="bento-card reveal reveal-d3 tilt-card">
        <div class="bento-top-glow" style="background:linear-gradient(90deg,#10B981,#34D399);"></div>
        <div class="bento-icon" style="background:rgba(16,185,129,0.12);">💳</div>
        <div class="bento-title">Pay per page. Nothing more.</div>
        <div class="bento-desc">Students load a campus wallet and pay only for what they print. Full history, instant receipts.</div>
      </div>

      <!-- Card 7 — GPU -->
      <div class="bento-card reveal reveal-d2 tilt-card">
        <div class="bento-top-glow" style="background:linear-gradient(90deg,#34D399,#10B981);"></div>
        <div class="bento-icon" style="background:rgba(52,211,153,0.1);">🚀</div>
        <div class="bento-title">Analysis in 32 milliseconds.</div>
        <div class="bento-desc">GPU-accelerated inference means no student waits for the AI to catch up. Every document, analyzed before you blink.</div>
        <div class="bento-stat">
          <span class="bento-stat-num" style="color:#34D399;">32ms</span>
          <span class="bento-stat-label">Per Document</span>
        </div>
      </div>

      <!-- Card 8 — Real-time -->
      <div class="bento-card reveal reveal-d1 tilt-card">
        <div class="bento-top-glow" style="background:linear-gradient(90deg,#A78BFA,#8B5CF6);"></div>
        <div class="bento-icon" style="background:rgba(167,139,250,0.12);">📡</div>
        <div class="bento-title">Students always know where their job stands.</div>
        <div class="bento-desc">Queue position, printer assignment, and completion — pushed live, the moment it changes.</div>
        <div class="status-row" style="margin-top:14px;">
          <span class="status-pill"><span class="status-dot"></span>Live Updates</span>
        </div>
      </div>

    </div>
  </div>
</section>

<div class="section-divider"></div>

<!-- ════ HOW IT WORKS ════ -->
<section class="section" id="workflow">
  <div class="container">
    <div class="section-header centered reveal">
      <div class="section-eyebrow eyebrow-purple">From Upload to Pickup</div>
      <h2 class="section-h2">Nine steps. Zero friction.<br>Under three minutes.</h2>
      <p class="section-p">Each step hands off to the next automatically — no manual action, no waiting, no uncertainty.</p>
    </div>
    <div class="workflow-path reveal">
      <div class="wf-step"><div class="wf-node" style="background:rgba(59,130,246,0.12);border-color:rgba(59,130,246,0.25);">🎓<div class="wf-step-num">1</div></div><div class="wf-label">Sign In</div><div class="wf-sub">Secure Access</div></div>
      <div class="wf-connector"><div class="wf-line"></div><span class="wf-arrow">›</span></div>
      <div class="wf-step"><div class="wf-node" style="background:rgba(16,185,129,0.1);border-color:rgba(16,185,129,0.2);">📤<div class="wf-step-num">2</div></div><div class="wf-label">Upload File</div><div class="wf-sub">PDF · Word · Image</div></div>
      <div class="wf-connector"><div class="wf-line"></div><span class="wf-arrow">›</span></div>
      <div class="wf-step"><div class="wf-node" style="background:rgba(139,92,246,0.1);border-color:rgba(139,92,246,0.22);">🧠<div class="wf-step-num">3</div></div><div class="wf-label">AI Inspection</div><div class="wf-sub">Quality Gate</div></div>
      <div class="wf-connector"><div class="wf-line"></div><span class="wf-arrow">›</span></div>
      <div class="wf-step"><div class="wf-node" style="background:rgba(6,182,212,0.1);border-color:rgba(6,182,212,0.22);">⚡<div class="wf-step-num">4</div></div><div class="wf-label">Wait Estimate</div><div class="wf-sub">ML Forecast</div></div>
      <div class="wf-connector"><div class="wf-line"></div><span class="wf-arrow">›</span></div>
      <div class="wf-step"><div class="wf-node" style="background:rgba(16,185,129,0.1);border-color:rgba(16,185,129,0.2);">🖨️<div class="wf-step-num">5</div></div><div class="wf-label">Printer Selected</div><div class="wf-sub">Optimal Route</div></div>
      <div class="wf-connector"><div class="wf-line"></div><span class="wf-arrow">›</span></div>
      <div class="wf-step"><div class="wf-node" style="background:rgba(245,158,11,0.1);border-color:rgba(245,158,11,0.22);">💳<div class="wf-step-num">6</div></div><div class="wf-label">Pay &amp; Confirm</div><div class="wf-sub">Campus Wallet</div></div>
      <div class="wf-connector"><div class="wf-line"></div><span class="wf-arrow">›</span></div>
      <div class="wf-step"><div class="wf-node" style="background:rgba(59,130,246,0.1);border-color:rgba(59,130,246,0.2);">⚙️<div class="wf-step-num">7</div></div><div class="wf-label">Printing Starts</div><div class="wf-sub">Auto-Queued</div></div>
      <div class="wf-connector"><div class="wf-line"></div><span class="wf-arrow">›</span></div>
      <div class="wf-step"><div class="wf-node" style="background:rgba(139,92,246,0.1);border-color:rgba(139,92,246,0.2);">🔐<div class="wf-step-num">8</div></div><div class="wf-label">QR Issued</div><div class="wf-sub">Cryptographic</div></div>
      <div class="wf-connector"><div class="wf-line"></div><span class="wf-arrow">›</span></div>
      <div class="wf-step"><div class="wf-node" style="background:rgba(16,185,129,0.12);border-color:rgba(16,185,129,0.3);box-shadow:0 0 20px rgba(16,185,129,0.2);">✅<div class="wf-step-num">9</div></div><div class="wf-label">Collected</div><div class="wf-sub">Verified &amp; Done</div></div>
    </div>
  </div>
</section>

<div class="section-divider"></div>

<!-- ════ AI ENGINE ════ -->
<section class="section ai-section" id="ai-section">
  <div class="container">
    <div class="ai-grid">
      <!-- Neural Network Canvas -->
      <div class="ai-visual reveal">
        <canvas id="neural-canvas"></canvas>
      </div>
      <!-- AI Content -->
      <div class="reveal reveal-d2">
        <div class="section-eyebrow eyebrow-purple">Under the Hood</div>
        <h2 class="section-h2">An AI stack built for campus scale</h2>
        <p class="section-p">Each print job passes through a multi-layer inference pipeline — running live on campus hardware, with no data leaving your institution.</p>
        <div class="ai-tech-grid">
          <div class="ai-tech-card">
            <div class="atc-ico">🔬</div>
            <div style="flex:1;min-width:0;"><div class="atc-name">TensorFlow</div><div class="atc-tag">Document Classification</div></div>
            <div class="atc-bar"><div class="atc-fill" style="width:92%;background:linear-gradient(90deg,#3B82F6,#60A5FA);"></div></div>
          </div>
          <div class="ai-tech-card">
            <div class="atc-ico">👁️</div>
            <div style="flex:1;min-width:0;"><div class="atc-name">OpenCV</div><div class="atc-tag">Visual Quality Analysis</div></div>
            <div class="atc-bar"><div class="atc-fill" style="width:88%;background:linear-gradient(90deg,#10B981,#34D399);"></div></div>
          </div>
          <div class="ai-tech-card">
            <div class="atc-ico">🧠</div>
            <div style="flex:1;min-width:0;"><div class="atc-name">MobileNetV2</div><div class="atc-tag">Defect Detection Model</div></div>
            <div class="atc-bar"><div class="atc-fill" style="width:99%;background:linear-gradient(90deg,#8B5CF6,#A78BFA);"></div></div>
          </div>
          <div class="ai-tech-card">
            <div class="atc-ico">📈</div>
            <div style="flex:1;min-width:0;"><div class="atc-name">Queue Forecasting</div><div class="atc-tag">ML Regression Model</div></div>
            <div class="atc-bar"><div class="atc-fill" style="width:96%;background:linear-gradient(90deg,#06B6D4,#67E8F9);"></div></div>
          </div>
          <div class="ai-tech-card">
            <div class="atc-ico">🚀</div>
            <div style="flex:1;min-width:0;"><div class="atc-name">NVIDIA CUDA</div><div class="atc-tag">32ms GPU Inference</div></div>
            <div class="atc-bar"><div class="atc-fill" style="width:87%;background:linear-gradient(90deg,#10B981,#06B6D4);"></div></div>
          </div>
          <div class="ai-tech-card">
            <div class="atc-ico">⚡</div>
            <div style="flex:1;min-width:0;"><div class="atc-name">FastAPI</div><div class="atc-tag">Async Event Pipeline</div></div>
            <div class="atc-bar"><div class="atc-fill" style="width:100%;background:linear-gradient(90deg,#F59E0B,#FBBF24);"></div></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<div class="section-divider"></div>

<!-- ════ LIVE DASHBOARD ════ -->
<section class="section" id="dashboard">
  <div class="container">
    <div class="section-header centered reveal">
      <div class="section-eyebrow eyebrow-cyan">Live Operations</div>
      <h2 class="section-h2">Every role, one dashboard.<br>Total campus visibility.</h2>
    </div>
    <div style="max-width:800px;margin:0 auto;" class="reveal reveal-d2">
      <div class="live-dash">
        <div class="dash-header">
          <span class="dash-title">🏛️ Campus Operations — Live</span>
          <span class="dash-live"><span style="width:5px;height:5px;border-radius:50%;background:#10B981;display:inline-block;"></span>&nbsp;LIVE</span>
        </div>
        <div class="dash-metrics">
          <div class="dash-metric">
            <div class="dm-label">Print Jobs Today</div>
            <div class="dm-value" style="color:#60A5FA;" id="live-jobs">247</div>
            <div class="dm-sub">↑ 18% vs. yesterday</div>
          </div>
          <div class="dash-metric">
            <div class="dm-label">Avg. Wait Time</div>
            <div class="dm-value" style="color:#10B981;">1m 12s</div>
            <div class="dm-sub">↓ 82% vs. manual</div>
          </div>
          <div class="dash-metric">
            <div class="dm-label">AI Model Accuracy</div>
            <div class="dm-value" style="color:#A78BFA;">98.7%</div>
            <div class="dm-sub">Live inference</div>
          </div>
        </div>
        <div class="dash-activity" id="live-activity">
          <div class="da-row"><div class="da-dot" style="background:#10B981;box-shadow:0 0 6px #10B981;"></div><div class="da-text">Job #1284 complete — Arjun Sharma — Engineering Block</div><div class="da-time">now</div></div>
          <div class="da-row"><div class="da-dot" style="background:#3B82F6;box-shadow:0 0 6px #3B82F6;"></div><div class="da-text">AI rerouted 8 jobs from Printer 3 → Printer 7 to reduce wait</div><div class="da-time">12s</div></div>
          <div class="da-row"><div class="da-dot" style="background:#8B5CF6;box-shadow:0 0 6px #8B5CF6;"></div><div class="da-text">QR verified — Priya Nair — Library Print Center</div><div class="da-time">34s</div></div>
          <div class="da-row"><div class="da-dot" style="background:#F59E0B;box-shadow:0 0 6px #F59E0B;"></div><div class="da-text">Load spike on GPU node — auto-throttled, no degradation</div><div class="da-time">1m 2s</div></div>
          <div class="da-row"><div class="da-dot" style="background:#10B981;box-shadow:0 0 6px #10B981;"></div><div class="da-text">Payment confirmed ₹24.00 — Rahul Verma — 3 pages</div><div class="da-time">1m 18s</div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<div class="section-divider"></div>

<!-- ════ STATS ════ -->
<section class="section" id="stats">
  <div class="container">
    <div class="section-header centered reveal">
      <div class="section-eyebrow eyebrow-green">Real-World Results</div>
      <h2 class="section-h2">The difference is<br>measurable.</h2>
    </div>
    <div class="stats-grid reveal reveal-d1">
      <div class="stat-cell">
        <div class="stat-num" id="cnt-students">0</div>
        <div class="stat-label">Students Served</div>
        <div class="stat-sub">Across the university</div>
      </div>
      <div class="stat-cell">
        <div class="stat-num" id="cnt-printers">0</div>
        <div class="stat-label">Printers Managed</div>
        <div class="stat-sub">3 print centers</div>
      </div>
      <div class="stat-cell">
        <div class="stat-num" id="cnt-acc">0<span style="font-size:0.6em;">%</span></div>
        <div class="stat-label">AI Accuracy</div>
        <div class="stat-sub">Detection &amp; prediction</div>
      </div>
      <div class="stat-cell">
        <div class="stat-num" id="cnt-queue">0<span style="font-size:0.6em;">%</span></div>
        <div class="stat-label">Shorter Queues</div>
        <div class="stat-sub">vs. unmanaged printing</div>
      </div>
      <div class="stat-cell">
        <div class="stat-num" id="cnt-paper">0<span style="font-size:0.6em;">%</span></div>
        <div class="stat-label">Waste Reduction</div>
        <div class="stat-sub">Caught before printing</div>
      </div>
    </div>
  </div>
</section>

<div class="section-divider"></div>

<!-- ════ TECH ORBIT ════ -->
<section class="section" id="tech">
  <div class="container">
    <div class="tech-orbit-wrap">
      <!-- Orbit -->
      <div class="reveal">
        <div class="orbit-container">
          <div class="orbit-ring orbit-ring-3"></div>
          <div class="orbit-ring orbit-ring-2"></div>
          <div class="orbit-ring orbit-ring-1"></div>
          <div class="orbit-core">🧠</div>
          <!-- Ring 1 icons (160px) -->
          <div class="orbit-icon" id="oi-python" style="top:calc(50% - 22px - 80px);left:calc(50% - 22px);">🐍</div>
          <div class="orbit-icon" id="oi-tf" style="top:calc(50% - 22px + 80px);left:calc(50% - 22px);">🔬</div>
          <!-- Ring 2 icons (260px) -->
          <div class="orbit-icon" id="oi-cv" style="top:calc(50% - 22px);left:calc(50% - 22px - 130px);">👁️</div>
          <div class="orbit-icon" id="oi-api" style="top:calc(50% - 22px);left:calc(50% - 22px + 130px);">⚡</div>
          <!-- Ring 3 icons (360px) -->
          <div class="orbit-icon" id="oi-db" style="top:calc(50% - 22px - 180px);left:calc(50% - 22px);">🗄️</div>
          <div class="orbit-icon" id="oi-gpu" style="top:calc(50% - 22px);left:calc(50% - 22px + 180px);">🚀</div>
          <div class="orbit-icon" id="oi-qr" style="top:calc(50% - 22px + 180px);left:calc(50% - 22px);">🔐</div>
          <div class="orbit-icon" id="oi-ml" style="top:calc(50% - 22px);left:calc(50% - 22px - 180px);">📈</div>
        </div>
      </div>
      <!-- Tech list -->
      <div class="reveal reveal-d2">
        <div class="section-eyebrow eyebrow-blue">Built on Proven Infrastructure</div>
        <h2 class="section-h2">No experimental tools.<br>Only production-grade AI.</h2>
        <div class="tech-list">
          <div class="tech-item"><div class="tech-ico">🐍</div><div><div class="tech-name">Python 3.11+</div><div class="tech-desc">The foundation for every AI model, pipeline, and API</div></div><span class="tech-badge" style="background:rgba(59,130,246,0.1);color:#60A5FA;border:1px solid rgba(59,130,246,0.2);">Core</span></div>
          <div class="tech-item"><div class="tech-ico">🔬</div><div><div class="tech-name">TensorFlow 2.21</div><div class="tech-desc">GPU-accelerated training and live document inference</div></div><span class="tech-badge" style="background:rgba(245,158,11,0.1);color:#FBBF24;border:1px solid rgba(245,158,11,0.2);">GPU</span></div>
          <div class="tech-item"><div class="tech-ico">👁️</div><div><div class="tech-name">OpenCV</div><div class="tech-desc">Pixel-level quality analysis before every print</div></div><span class="tech-badge" style="background:rgba(16,185,129,0.1);color:#34D399;border:1px solid rgba(16,185,129,0.2);">Vision</span></div>
          <div class="tech-item"><div class="tech-ico">⚡</div><div><div class="tech-name">FastAPI</div><div class="tech-desc">Async event pipeline handling thousands of concurrent jobs</div></div><span class="tech-badge" style="background:rgba(139,92,246,0.1);color:#A78BFA;border:1px solid rgba(139,92,246,0.2);">API</span></div>
          <div class="tech-item"><div class="tech-ico">🗄️</div><div><div class="tech-name">SQLite WAL</div><div class="tech-desc">Reliable, zero-config data store — runs entirely on campus</div></div><span class="tech-badge" style="background:rgba(6,182,212,0.1);color:#67E8F9;border:1px solid rgba(6,182,212,0.2);">DB</span></div>
        </div>
      </div>
    </div>
  </div>
</section>

<div class="section-divider"></div>

<!-- ════ CAMPUS NETWORK ════ -->
<section class="section" id="network">
  <div class="container">
    <div class="section-header centered reveal">
      <div class="section-eyebrow eyebrow-green">Campus-Wide Coverage</div>
      <h2 class="section-h2">One system. Every building.<br>Every student.</h2>
      <p class="section-p">A single AI layer connects your central administration to every print center and student terminal — with no fragmentation.</p>
    </div>
    <div style="max-width:560px;margin:0 auto;" class="reveal reveal-d1">
      <div class="campus-network">
        <div class="cn-node primary">🏛️ University Administration</div>
        <div class="cn-connector"><div class="cn-line"></div><div class="cn-arrow">▼</div></div>
        <div class="cn-centers-row">
          <div class="cn-center-col">
            <div class="cn-node center">🖨️ Print Center A</div>
            <div class="cn-connector" style="padding:4px 0;"><div class="cn-line" style="height:20px;"></div></div>
            <div class="cn-center-label">Engineering · 12 Printers</div>
          </div>
          <div class="cn-h-connector"><div class="cn-h-line"></div><div class="cn-h-line"></div></div>
          <div class="cn-center-col">
            <div class="cn-node center">🖨️ Print Center B</div>
            <div class="cn-connector" style="padding:4px 0;"><div class="cn-line" style="height:20px;"></div></div>
            <div class="cn-center-label">Library · 15 Printers</div>
          </div>
          <div class="cn-h-connector"><div class="cn-h-line"></div><div class="cn-h-line"></div></div>
          <div class="cn-center-col">
            <div class="cn-node center">🖨️ Print Center C</div>
            <div class="cn-connector" style="padding:4px 0;"><div class="cn-line" style="height:20px;"></div></div>
            <div class="cn-center-label">Admin Block · 8 Printers</div>
          </div>
        </div>
        <div class="cn-connector"><div class="cn-line"></div><div class="cn-arrow">▼</div></div>
        <div class="cn-node leaf">🎓 10,000+ Students — Scan &amp; Collect</div>
      </div>
    </div>
  </div>
</section>

<div class="section-divider"></div>

<!-- ════ CTA / SOCIAL PROOF ════ -->
<section class="section" id="cta" style="padding:clamp(80px,8vw,140px) 0;">
  <div class="container">
    <div class="cta-card reveal">
      <div class="cta-bg-glow"></div>
      <div class="cta-eyebrow"><span class="eyebrow-dot" style="background:#3B82F6;box-shadow:0 0 8px #3B82F6;"></span> Start with your campus today</div>
      <h2 class="cta-h2">Less waiting. Less waste.<br>Better printing.</h2>
      <p class="cta-p">IntelliPrint Nexus is ready to deploy on your campus infrastructure. No third-party cloud. No data leaving your institution.</p>
      <div class="cta-btns">
        <a class="btn-hero-primary btn-sweep" href="?nav_route=register" target="_parent" style="font-size:0.98rem;padding:16px 36px;">Get Early Access <span class="btn-arrow">→</span></a>
        <a class="btn-hero-secondary" href="?nav_route=login" target="_parent" style="font-size:0.98rem;padding:15px 28px;">Sign In</a>
      </div>
      <div class="cta-badges">
        <div class="cta-badge"><span>🧠</span> AI-Native</div>
        <div class="cta-badge"><span>🔐</span> On-Premise Secure</div>
        <div class="cta-badge"><span>🚀</span> GPU-Accelerated</div>
        <div class="cta-badge"><span>🎓</span> University-Only</div>
      </div>
    </div>
  </div>
</section>

<div class="section-divider"></div>

<!-- ════ FOOTER ════ -->
<footer id="footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="ft-brand">
          <div class="nav-logo-mark" style="width:28px;height:28px;font-size:0.85rem;">🎓</div>
          IntelliPrint Nexus
        </div>
        <div class="ft-desc">The AI-native printing platform built exclusively for universities. On-premise, secure, and built for scale.</div>
        <div class="ft-socials">
          <div class="ft-soc">𝕏</div>
          <div class="ft-soc">in</div>
          <div class="ft-soc">⌨</div>
          <div class="ft-soc">▶</div>
        </div>
      </div>
      <div>
        <div class="ft-col-title">Platform</div>
        <a class="ft-link" href="#features">Features</a>
        <a class="ft-link" href="#workflow">How It Works</a>
        <a class="ft-link" href="#ai-section">AI Engine</a>
        <a class="ft-link" href="#tech">Technology</a>
      </div>
      <div>
        <div class="ft-col-title">Resources</div>
        <span class="ft-link">Documentation</span>
        <span class="ft-link">API Reference</span>
        <span class="ft-link">University Guide</span>
        <span class="ft-link">Privacy Policy</span>
      </div>
      <div>
        <div class="ft-col-title">Contact</div>
        <span class="ft-link">GitHub</span>
        <span class="ft-link">Support Center</span>
        <span class="ft-link">Campus Onboarding</span>
        <span class="ft-link">System Status</span>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="footer-copy">© 2025 IntelliPrint Nexus. Designed for universities. All rights reserved.</div>
      <div class="footer-badges">
        <span class="footer-badge">🧠 AI-Native</span>
        <span class="footer-badge">🚀 GPU Accelerated</span>
        <span class="footer-badge">🎓 Campus-First</span>
      </div>
    </div>
  </div>
</footer>

</div><!-- #root -->

<!-- ════ SCRIPTS ════ -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js" integrity="sha512-oA6E5A0Sm4hFCBOfVkf2JHjDGXuD1hnZVIuPBg8Ohlz+EQvBFtDcxJ5C0RR0VFtR+mE5i/eNRLLBk5mnZeVA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
<script>
(function() {
'use strict';

// ── Cursor Glow ──────────────────────────────────────────────────────
const cursorGlow = document.getElementById('cursor-glow');
let cx = window.innerWidth/2, cy = window.innerHeight/2;
document.addEventListener('mousemove', e => {
  cx = e.clientX; cy = e.clientY;
  cursorGlow.style.transform = 'translate(' + cx + 'px,' + cy + 'px) translate(-50%,-50%)';
});

// ── Navbar scroll ───────────────────────────────────────────────────
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 60) navbar.classList.add('scrolled');
  else navbar.classList.remove('scrolled');
}, { passive: true });

// ── Background Canvas (particles + circuit lines) ───────────────────
(function initBg() {
  const canvas = document.getElementById('bg-canvas');
  const ctx = canvas.getContext('2d');
  let W, H;

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const PARTICLES = 110;
  const pts = Array.from({length: PARTICLES}, () => ({
    x: Math.random() * W, y: Math.random() * H,
    vx: (Math.random()-0.5)*0.28, vy: (Math.random()-0.5)*0.28,
    r: Math.random() * 1.6 + 0.4,
    alpha: Math.random() * 0.45 + 0.08,
  }));

  function draw() {
    ctx.clearRect(0, 0, W, H);
    const MX = cx, MY = cy;

    pts.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(59,130,246,' + p.alpha + ')';
      ctx.fill();
    });

    // Connect nearby + mouse
    pts.forEach((a, i) => {
      for (let j = i+1; j < pts.length; j++) {
        const b = pts[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = 'rgba(59,130,246,' + (0.07*(1-dist/120)) + ')';
          ctx.lineWidth = 0.7; ctx.stroke();
        }
      }
      const mdx = a.x - MX, mdy = a.y - MY;
      const md = Math.sqrt(mdx*mdx + mdy*mdy);
      if (md < 160) {
        ctx.beginPath();
        ctx.moveTo(a.x, a.y); ctx.lineTo(MX, MY);
        ctx.strokeStyle = 'rgba(96,165,250,' + (0.18*(1-md/160)) + ')';
        ctx.lineWidth = 0.9; ctx.stroke();
      }
    });

    requestAnimationFrame(draw);
  }
  draw();
})();

// ── Three.js Campus Scene ────────────────────────────────────────────
(function initCampus() {
  const canvas = document.getElementById('campus-canvas');
  if (!canvas || !window.THREE) return;

  const parent = canvas.parentElement;
  const W = parent.offsetWidth;
  const H = parent.offsetHeight;

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(48, W/H, 0.1, 1000);
  camera.position.set(0, 18, 28);
  camera.lookAt(0, 0, 0);

  // Lights
  scene.add(new THREE.AmbientLight(0x111827, 4));
  const pl1 = new THREE.PointLight(0x3B82F6, 3, 40);
  pl1.position.set(0, 12, 0); scene.add(pl1);
  const pl2 = new THREE.PointLight(0x10B981, 2, 25);
  pl2.position.set(-10, 6, -4); scene.add(pl2);
  const pl3 = new THREE.PointLight(0x8B5CF6, 2, 25);
  pl3.position.set(10, 6, -4); scene.add(pl3);

  // Ground grid
  const grid = new THREE.GridHelper(38, 18, 0x1e3a5f, 0x0d2137);
  grid.position.y = -2; scene.add(grid);

  // Nodes
  const nodeData = [
    { id:'uni',  pos:[0,0,0],     col:0x3B82F6, r:1.6, emit:0.6 },
    { id:'ai',   pos:[0,7,-2],    col:0x8B5CF6, r:1.2, emit:0.5 },
    { id:'cloud',pos:[0,11,1],    col:0x06B6D4, r:1.0, emit:0.4 },
    { id:'pc1',  pos:[-8,0,-5],   col:0x10B981, r:0.9, emit:0.4 },
    { id:'pc2',  pos:[8,0,-5],    col:0x10B981, r:0.9, emit:0.4 },
    { id:'pc3',  pos:[0,0,-10],   col:0x10B981, r:0.9, emit:0.4 },
    { id:'s1',   pos:[-5,0,8],    col:0xFBBF24, r:0.55,emit:0.35 },
    { id:'s2',   pos:[5,0,8],     col:0xFBBF24, r:0.55,emit:0.35 },
    { id:'s3',   pos:[0,0,10],    col:0xFBBF24, r:0.55,emit:0.35 },
    { id:'s4',   pos:[-3,0,7],    col:0xFBBF24, r:0.45,emit:0.3 },
    { id:'s5',   pos:[3,0,7],     col:0xFBBF24, r:0.45,emit:0.3 },
  ];

  const meshMap = {};
  nodeData.forEach(n => {
    const geo = new THREE.SphereGeometry(n.r, 24, 24);
    const mat = new THREE.MeshStandardMaterial({
      color: n.col, emissive: n.col, emissiveIntensity: n.emit,
      metalness: 0.2, roughness: 0.5
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(...n.pos); scene.add(mesh);
    meshMap[n.id] = mesh;

    // Glow ring at base
    const rg = new THREE.RingGeometry(n.r*1.4, n.r*1.7, 32);
    const rm = new THREE.MeshBasicMaterial({ color: n.col, side: THREE.DoubleSide, transparent: true, opacity: 0.15 });
    const ring = new THREE.Mesh(rg, rm);
    ring.rotation.x = -Math.PI/2;
    ring.position.set(n.pos[0], n.pos[1]-n.r+0.05, n.pos[2]);
    scene.add(ring);
  });

  // Connection lines
  const conns = [
    ['uni','ai'],['ai','cloud'],
    ['uni','pc1'],['uni','pc2'],['uni','pc3'],
    ['ai','pc1'],['ai','pc2'],['ai','pc3'],
    ['uni','s1'],['uni','s2'],['uni','s3'],
    ['s1','pc1'],['s2','pc2'],['s3','pc3'],
  ];
  conns.forEach(([a,b]) => {
    const na = nodeData.find(n=>n.id===a);
    const nb = nodeData.find(n=>n.id===b);
    if (!na||!nb) return;
    const pts = [new THREE.Vector3(...na.pos), new THREE.Vector3(...nb.pos)];
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    const mat = new THREE.LineBasicMaterial({ color:0x1d4ed8, transparent:true, opacity:0.22 });
    scene.add(new THREE.Line(geo, mat));
  });

  // Data packets
  const packets = [];
  const packetConns = [
    ['uni','ai'],['ai','pc1'],['ai','pc2'],['uni','s1'],['s2','pc2'],['ai','cloud']
  ];
  packetConns.forEach(([a,b]) => {
    const na = nodeData.find(n=>n.id===a);
    const nb = nodeData.find(n=>n.id===b);
    if (!na||!nb) return;
    const geo = new THREE.SphereGeometry(0.18, 8, 8);
    const mat = new THREE.MeshBasicMaterial({ color: 0x67E8F9 });
    const mesh = new THREE.Mesh(geo, mat); scene.add(mesh);
    packets.push({
      mesh,
      start: new THREE.Vector3(...na.pos),
      end: new THREE.Vector3(...nb.pos),
      t: Math.random(), speed: 0.004 + Math.random()*0.004
    });
  });

  // Floating particles
  const pGeo = new THREE.BufferGeometry();
  const pCount = 180;
  const pPos = new Float32Array(pCount*3);
  for (let i=0; i<pCount*3; i++) pPos[i]=(Math.random()-0.5)*44;
  pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
  const pMat = new THREE.PointsMaterial({ color:0x2563EB, size:0.12, transparent:true, opacity:0.35 });
  const particles = new THREE.Points(pGeo, pMat);
  scene.add(particles);

  // Mouse tracking
  let mx = 0, my = 0;
  document.addEventListener('mousemove', e => {
    mx = (e.clientX/window.innerWidth - 0.5)*2;
    my = (e.clientY/window.innerHeight - 0.5)*2;
  });

  let t = 0;
  function tick() {
    requestAnimationFrame(tick);
    t += 0.004;

    // Camera slow orbit
    camera.position.x = Math.sin(t*0.16)*3.5 + mx*2;
    camera.position.y = 17 + my*-1.2 + Math.sin(t*0.1)*1.2;
    camera.position.z = Math.cos(t*0.16)*3.5 + 27;
    camera.lookAt(0, 2, 0);

    // Node pulse
    nodeData.forEach((n,i) => {
      const m = meshMap[n.id];
      if (!m) return;
      const s = 1 + Math.sin(t*2.2+i*0.8)*0.06;
      m.scale.setScalar(s);
      m.material.emissiveIntensity = n.emit + Math.sin(t*2.2+i*0.8)*0.15;
    });

    // Packets
    packets.forEach(p => {
      p.t += p.speed;
      if (p.t > 1) p.t = 0;
      p.mesh.position.lerpVectors(p.start, p.end, p.t);
    });

    particles.rotation.y = t * 0.04;
    renderer.render(scene, camera);
  }
  tick();

  window.addEventListener('resize', () => {
    const W2 = parent.offsetWidth, H2 = parent.offsetHeight;
    renderer.setSize(W2, H2);
    camera.aspect = W2/H2;
    camera.updateProjectionMatrix();
  });
})();

// ── Neural Network Canvas ────────────────────────────────────────────
(function initNeural() {
  const canvas = document.getElementById('neural-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    const p = canvas.parentElement;
    canvas.width = p.offsetWidth;
    canvas.height = p.offsetHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const LAYERS = [4, 6, 6, 4, 3];
  const nodes = [];
  let W, H;

  function buildNodes() {
    W = canvas.width; H = canvas.height;
    nodes.length = 0;
    const lx = W * 0.12;
    const lGap = (W * 0.76) / (LAYERS.length - 1);
    LAYERS.forEach((count, li) => {
      const x = lx + li * lGap;
      const totalH = (count-1) * (H/(Math.max(...LAYERS)+1));
      const startY = (H - totalH)/2;
      for (let ni = 0; ni < count; ni++) {
        const y = startY + ni * (H/(Math.max(...LAYERS)+1));
        nodes.push({ x, y, layer:li, idx:ni, phase: Math.random()*Math.PI*2 });
      }
    });
  }
  buildNodes();
  window.addEventListener('resize', buildNodes);

  const COLORS = ['#3B82F6','#8B5CF6','#06B6D4','#10B981','#F59E0B'];

  let t = 0;
  function drawNeural() {
    W = canvas.width; H = canvas.height;
    ctx.clearRect(0,0,W,H);
    t += 0.018;

  // Stable packet pool: one per connection pair
  const packets = nodes
    .filter(n => n.layer < LAYERS.length - 1)
    .flatMap(n => {
      const nexts = nodes.filter(m => m.layer === n.layer + 1);
      return nexts.slice(0, 2).map(m => ({
        from: n, to: m, t: Math.random(),
        speed: 0.006 + Math.random() * 0.006,
        col: COLORS[n.layer]
      }));
    })
    .filter((_, i) => i % 3 === 0); // keep 1/3 for performance

    // Draw connections
    nodes.forEach(n => {
      if (n.layer >= LAYERS.length-1) return;
      nodes.filter(m => m.layer === n.layer+1).forEach(m => {
        const alpha = Math.sin(t*1.5 + n.phase)*0.12 + 0.06;
        ctx.beginPath(); ctx.moveTo(n.x,n.y); ctx.lineTo(m.x,m.y);
        ctx.strokeStyle = 'rgba(59,130,246,'+alpha+')';
        ctx.lineWidth = 0.9; ctx.stroke();
      });
    });

    // Draw stable packets
    packets.forEach(p => {
      p.t += p.speed;
      if (p.t > 1) p.t = 0;
      const px = p.from.x + (p.to.x - p.from.x) * p.t;
      const py = p.from.y + (p.to.y - p.from.y) * p.t;
      ctx.beginPath(); ctx.arc(px, py, 2.8, 0, Math.PI*2);
      ctx.fillStyle = p.col;
      ctx.shadowColor = p.col; ctx.shadowBlur = 10;
      ctx.fill(); ctx.shadowBlur = 0;
    });

    // Draw nodes
    nodes.forEach(n => {
      const pulse = Math.sin(t*2 + n.phase)*0.3 + 0.7;
      const r = 8 * pulse;

      // Outer glow
      const grad = ctx.createRadialGradient(n.x,n.y,0,n.x,n.y,r*2.5);
      grad.addColorStop(0, COLORS[n.layer]+'55');
      grad.addColorStop(1, 'transparent');
      ctx.beginPath(); ctx.arc(n.x,n.y,r*2.5,0,Math.PI*2);
      ctx.fillStyle = grad; ctx.fill();

      // Core
      ctx.beginPath(); ctx.arc(n.x,n.y,r,0,Math.PI*2);
      ctx.fillStyle = COLORS[n.layer];
      ctx.shadowColor = COLORS[n.layer]; ctx.shadowBlur = 14;
      ctx.fill(); ctx.shadowBlur = 0;

      // Inner highlight
      ctx.beginPath(); ctx.arc(n.x-r*0.25, n.y-r*0.25, r*0.35, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.fill();
    });

    requestAnimationFrame(drawNeural);
  }
  drawNeural();
})();

// ── Spark Chart (bento) ──────────────────────────────────────────────
(function initSpark() {
  const canvas = document.getElementById('spark-chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const data = [40,55,48,72,65,80,74,89,82,95,88,100,94,98];
  let t = 0;

  function draw() {
    const W = canvas.width = canvas.parentElement?.offsetWidth || 200;
    const H = canvas.height = 90;
    ctx.clearRect(0,0,W,H);
    t += 0.025;

    const animated = data.map((v,i) => v + Math.sin(t + i*0.5)*4);
    const max = Math.max(...animated), min = Math.min(...animated);
    const pts = animated.map((v,i) => [
      (i/(data.length-1))*W,
      H - ((v-min)/(max-min))*(H*0.8) - H*0.1
    ]);

    // Smooth bezier line
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length - 1; i++) {
      const mx2 = (pts[i][0] + pts[i+1][0]) / 2;
      const my2 = (pts[i][1] + pts[i+1][1]) / 2;
      ctx.quadraticCurveTo(pts[i][0], pts[i][1], mx2, my2);
    }
    ctx.lineTo(pts[pts.length-1][0], pts[pts.length-1][1]);
    ctx.strokeStyle = '#06B6D4'; ctx.lineWidth = 2.5;
    ctx.shadowColor = '#06B6D4'; ctx.shadowBlur = 10;
    ctx.stroke(); ctx.shadowBlur = 0;

    // Smooth fill area
    ctx.beginPath();
    ctx.moveTo(pts[0][0], H);
    pts.forEach(([x,y]) => ctx.lineTo(x,y));
    ctx.lineTo(pts[pts.length-1][0], H);
    ctx.closePath(); ctx.fillStyle = grad; ctx.fill();

    // Dot at end
    const last = pts[pts.length-1];
    ctx.beginPath(); ctx.arc(last[0],last[1],4,0,Math.PI*2);
    ctx.fillStyle = '#06B6D4';
    ctx.shadowColor = '#06B6D4'; ctx.shadowBlur = 12;
    ctx.fill(); ctx.shadowBlur = 0;

    requestAnimationFrame(draw);
  }
  draw();
})();

// ── Live Dashboard Feed ──────────────────────────────────────────────
(function initLiveFeed() {
  const events = [
    { col:'#10B981', text:'Job #1291 complete — Arjun Sharma — Engineering Block, 8 pages' },
    { col:'#3B82F6', text:'AI rerouted 5 jobs: Printer 3 → Printer 9 — wait reduced by 40s' },
    { col:'#8B5CF6', text:'QR verified — Priya Nair — Library Print Center' },
    { col:'#F59E0B', text:'GPU load spike detected — auto-throttled, zero degradation' },
    { col:'#10B981', text:'Payment confirmed ₹18.50 — Rahul Verma — 5 pages' },
    { col:'#3B82F6', text:'AI inspection passed — Document #4821 — Confidence: 98.2%' },
    { col:'#06B6D4', text:'Queue forecast updated — Printer 7 estimated wait: 45s' },
    { col:'#A78BFA', text:'New print job queued — Sneha Iyer — Position 2 of 6' },
    { col:'#10B981', text:'Job #1292 complete — Meera Pillai — Admin Block' },
    { col:'#3B82F6', text:'Load rebalance — Printer 12 now handling overflow from Printer 4' },
  ];
  const activity = document.getElementById('live-activity');
  const jobsEl = document.getElementById('live-jobs');
  if (!activity) return;
  let jobCount = 247;
  let ptr = 0;

  setInterval(() => {
    const e = events[ptr % events.length]; ptr++;
    jobCount++;
    if (jobsEl) jobsEl.textContent = jobCount;
    const rows = activity.querySelectorAll('.da-row');
    // Shift rows up
    for (let i = rows.length-1; i > 0; i--) {
      rows[i].querySelector('.da-text').textContent = rows[i-1].querySelector('.da-text').textContent;
      rows[i].querySelector('.da-dot').style.background = rows[i-1].querySelector('.da-dot').style.background;
      rows[i].querySelector('.da-dot').style.boxShadow = rows[i-1].querySelector('.da-dot').style.boxShadow;
      const t0 = parseInt(rows[i-1].querySelector('.da-time').textContent);
      rows[i].querySelector('.da-time').textContent = isNaN(t0) ? '1s' : (t0+1)+'s';
    }
    // Insert new at top
    rows[0].querySelector('.da-dot').style.background = e.col;
    rows[0].querySelector('.da-dot').style.boxShadow = '0 0 6px '+e.col;
    rows[0].querySelector('.da-text').textContent = e.text;
    rows[0].querySelector('.da-time').textContent = 'now';
  }, 2200);
})();

// ── Scroll Reveal ────────────────────────────────────────────────────
const revealObs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); revealObs.unobserve(e.target); }
  });
}, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });

document.querySelectorAll('.reveal,.reveal-scale').forEach(el => revealObs.observe(el));

// ── Animated Counters ────────────────────────────────────────────────
const counterData = [
  { id:'cnt-students', target:10000, suffix:'+', duration:2000 },
  { id:'cnt-printers', target:35,    suffix:'+', duration:1500 },
  { id:'cnt-acc',      target:98,    suffix:'',  duration:1800, el_id:'cnt-acc' },
  { id:'cnt-queue',    target:82,    suffix:'',  duration:1600 },
  { id:'cnt-paper',    target:91,    suffix:'',  duration:1700 },
];

const statsObs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    counterData.forEach(c => {
      const el = document.getElementById(c.id);
      if (!el) return;
      const suffix = el.querySelector('span');
      const suffixHTML = suffix ? suffix.outerHTML : '';
      let start = 0;
      const easeOut = (t) => 1 - Math.pow(1 - t, 3);
      const startTime = performance.now();
      const step = () => {
        const elapsed = performance.now() - startTime;
        const progress = Math.min(elapsed / c.duration, 1);
        const easedVal = Math.floor(easeOut(progress) * c.target);
        const display = c.target >= 1000 ? easedVal.toLocaleString() : easedVal;
        el.innerHTML = display + c.suffix + suffixHTML;
        if (progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
    statsObs.disconnect();
  });
}, { threshold: 0.3 });

const statsSection = document.getElementById('stats');
if (statsSection) statsObs.observe(statsSection);

// ── Card Tilt Effect ─────────────────────────────────────────────────
document.querySelectorAll('.tilt-card').forEach(card => {
  let rafId;
  card.addEventListener('mousemove', e => {
    cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(() => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left - rect.width/2) / rect.width;
      const y = (e.clientY - rect.top - rect.height/2) / rect.height;
      card.style.transform = 'translateY(-6px) perspective(1000px) rotateY('+(x*4)+'deg) rotateX('+(-y*4)+'deg)';
    });
  });
  card.addEventListener('mouseleave', () => {
    cancelAnimationFrame(rafId);
    card.style.transition = 'transform 0.6s cubic-bezier(0.34,1.2,0.64,1)';
    card.style.transform = '';
    setTimeout(() => { card.style.transition = ''; }, 650);
  });
  card.addEventListener('mouseenter', () => {
    card.style.transition = 'none';
  });
});

// ── Orbit Animation (JS) ─────────────────────────────────────────────
(function initOrbit() {
  const icons = [
    {id:'oi-python', r:80, speed:0.5, offset:0},
    {id:'oi-tf',     r:80, speed:0.5, offset:Math.PI},
    {id:'oi-cv',     r:130, speed:0.3, offset:0},
    {id:'oi-api',    r:130, speed:0.3, offset:Math.PI},
    {id:'oi-db',     r:180, speed:0.2, offset:0},
    {id:'oi-gpu',    r:180, speed:0.2, offset:Math.PI/2},
    {id:'oi-qr',     r:180, speed:0.2, offset:Math.PI},
    {id:'oi-ml',     r:180, speed:0.2, offset:3*Math.PI/2},
  ];

  const container = document.querySelector('.orbit-container');
  if (!container) return;

  // Smooth interpolated positions
  const current = {};
  icons.forEach(ic => { current[ic.id] = { x: 0, y: 0 }; });

  let ot = 0;
  function animOrbit() {
    ot += 0.007;
    icons.forEach(ic => {
      const el = document.getElementById(ic.id);
      if (!el) return;
      const angle = ot * ic.speed + ic.offset;
      const tx = Math.cos(angle) * ic.r;
      const ty = Math.sin(angle) * ic.r;
      const cW = container.offsetWidth / 2;
      const cH = container.offsetHeight / 2;
      // Lerp for smooth motion
      current[ic.id].x += (tx - current[ic.id].x) * 0.08;
      current[ic.id].y += (ty - current[ic.id].y) * 0.08;
      el.style.left = (cW + current[ic.id].x - 22) + 'px';
      el.style.top  = (cH + current[ic.id].y - 22) + 'px';
    });
    requestAnimationFrame(animOrbit);
  }
  animOrbit();
})();

// ── Smooth nav scroll ────────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const id = a.getAttribute('href').slice(1);
    const el = document.getElementById(id);
    if (el) { e.preventDefault(); el.scrollIntoView({behavior:'smooth', block:'start'}); }
  });
});

// ═══════════════════════════════════════════════════════
// CINEMATIC MOTION ENGINE
// ═══════════════════════════════════════════════════════

// ── Scroll Progress Bar ──────────────────────────────────────────────
(function initScrollProgress() {
  const bar = document.getElementById('scroll-progress');
  if (!bar) return;
  const update = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
    bar.style.width = pct + '%';
  };
  window.addEventListener('scroll', update, { passive: true });
  update();
})();

// ── Nav Active Section Highlight ─────────────────────────────────────
(function initNavActive() {
  const sections = ['features','workflow','ai-section','stats','tech'];
  const links = document.querySelectorAll('.nav-link');
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        links.forEach(l => l.classList.remove('nav-active'));
        const active = document.querySelector('.nav-link[href="#' + e.target.id + '"]');
        if (active) active.classList.add('nav-active');
      }
    });
  }, { threshold: 0.35, rootMargin: '-80px 0px -40% 0px' });
  sections.forEach(id => {
    const el = document.getElementById(id);
    if (el) obs.observe(el);
  });
})();

// ── Staggered Bento Card Reveal ──────────────────────────────────────
(function initBentoReveal() {
  const cards = document.querySelectorAll('.bento-card');
  cards.forEach(c => c.classList.add('bento-seq'));
  const obs = new IntersectionObserver(entries => {
    if (entries.some(e => e.isIntersecting)) {
      cards.forEach((c, i) => {
        setTimeout(() => c.classList.add('bento-in'), i * 80);
      });
      obs.disconnect();
    }
  }, { threshold: 0.08 });
  const grid = document.querySelector('.bento-grid');
  if (grid) obs.observe(grid);
})();

// ── Magnetic Button Effect ────────────────────────────────────────────
(function initMagnetic() {
  const STRENGTH = 0.35;
  document.querySelectorAll('.mag-btn').forEach(wrap => {
    const btn = wrap.querySelector('a');
    if (!btn) return;
    let bounds;
    wrap.addEventListener('mouseenter', () => { bounds = wrap.getBoundingClientRect(); });
    wrap.addEventListener('mousemove', e => {
      if (!bounds) bounds = wrap.getBoundingClientRect();
      const dx = e.clientX - (bounds.left + bounds.width / 2);
      const dy = e.clientY - (bounds.top + bounds.height / 2);
      btn.style.transform = 'translate(' + (dx * STRENGTH) + 'px,' + (dy * STRENGTH) + 'px)';
    });
    wrap.addEventListener('mouseleave', () => {
      btn.style.transition = 'transform 0.5s cubic-bezier(0.34,1.4,0.64,1)';
      btn.style.transform = 'translate(0,0)';
      setTimeout(() => { btn.style.transition = ''; }, 520);
    });
    wrap.addEventListener('mouseenter', () => { btn.style.transition = 'none'; });
  });
})();

// ── Parallax Scroll ───────────────────────────────────────────────────
(function initParallax() {
  const heroVisual = document.querySelector('.parallax-slow');
  const heroBg = document.querySelector('.gradient-mesh');
  let ticking = false;
  const update = () => {
    const sy = window.scrollY;
    if (heroVisual) heroVisual.style.transform = 'translateY(' + (sy * 0.12) + 'px)';
    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(update); ticking = true; }
  }, { passive: true });
})();

// ── Circuit Lines Background Overlay ─────────────────────────────────
(function initCircuit() {
  const canvas = document.getElementById('bg-canvas');
  // We'll draw circuit overlay on top of existing particles
  // This hooks into the existing draw loop by reading the existing canvas
  // We add a second canvas for circuits only
  const cc = document.createElement('canvas');
  cc.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:0;opacity:0.55;';
  document.body.insertBefore(cc, canvas.nextSibling);
  const ctx = cc.getContext('2d');
  let W, H;
  const resize = () => { W = cc.width = window.innerWidth; H = cc.height = window.innerHeight; };
  resize(); window.addEventListener('resize', resize);

  // Generate circuit nodes (fixed grid-snapped positions)
  const GRID = 80;
  const circNodes = [];
  for (let x = GRID; x < 1600; x += GRID * (2 + Math.floor(Math.random()*3))) {
    for (let y = GRID; y < 900; y += GRID * (2 + Math.floor(Math.random()*3))) {
      if (Math.random() > 0.55) circNodes.push({ x, y, lit: Math.random() > 0.5 });
    }
  }
  // Build circuit paths (horizontal/vertical only)
  const paths = [];
  circNodes.forEach((a, i) => {
    if (i + 1 < circNodes.length && Math.random() > 0.4) {
      const b = circNodes[i + 1];
      paths.push({ ax:a.x, ay:a.y, bx:b.x, by:a.y }); // horizontal
      paths.push({ ax:b.x, ay:a.y, bx:b.x, by:b.y }); // vertical turn
    }
  });

  // Packets travelling along paths
  const cpkts = paths.filter((_,i)=>i%4===0).map(p => ({
    path: p, t: Math.random(), speed: 0.003 + Math.random()*0.004
  }));

  let ct = 0;
  function drawCircuit() {
    ctx.clearRect(0,0,W,H);
    ct += 0.012;
    // Draw paths
    paths.forEach(p => {
      const alpha = 0.04 + Math.sin(ct + p.ax*0.01)*0.015;
      ctx.beginPath();
      ctx.moveTo(p.ax, p.ay); ctx.lineTo(p.bx, p.by);
      ctx.strokeStyle = 'rgba(59,130,246,' + alpha + ')';
      ctx.lineWidth = 1; ctx.stroke();
    });
    // Nodes
    circNodes.forEach(n => {
      const a = 0.08 + Math.sin(ct*1.2 + n.x*0.02)*0.04;
      ctx.beginPath(); ctx.arc(n.x, n.y, 2, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(59,130,246,' + a + ')'; ctx.fill();
    });
    // Moving packets
    cpkts.forEach(pk => {
      pk.t += pk.speed; if (pk.t > 1) pk.t = 0;
      const p = pk.path;
      // Travel horizontal then vertical
      const x = pk.t < 0.5 ? p.ax + (p.bx-p.ax)*(pk.t*2) : p.bx;
      const y = pk.t < 0.5 ? p.ay : p.ay + (p.by-p.ay)*((pk.t-0.5)*2);
      ctx.beginPath(); ctx.arc(x, y, 1.5, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(96,165,250,0.6)'; ctx.fill();
      // Tail glow
      ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(59,130,246,0.06)'; ctx.fill();
    });
    requestAnimationFrame(drawCircuit);
  }
  drawCircuit();
})();

// ── Workflow Node AI Pulse ────────────────────────────────────────────
(function initWorkflowPulse() {
  const nodes = document.querySelectorAll('.wf-node');
  const obs = new IntersectionObserver(entries => {
    if (entries.some(e => e.isIntersecting)) {
      nodes.forEach((n, i) => {
        setTimeout(() => {
          n.classList.add('wf-node-active');
          // After pulse animates in, keep cycling glow
          n.style.animationDelay = (i * 0.22) + 's';
        }, i * 120);
      });
      obs.disconnect();
    }
  }, { threshold: 0.2 });
  const wf = document.querySelector('.workflow-path');
  if (wf) obs.observe(wf);
})();

// ── Floating Bento Icons ──────────────────────────────────────────────
(function initFloatingIcons() {
  const icons = document.querySelectorAll('.bento-icon');
  icons.forEach((el, i) => {
    el.style.animation = 'floatIcon ' + (3.5 + i * 0.4) + 's ease-in-out ' + (i * 0.3) + 's infinite';
  });
})();

// ── Hero Section Entrance Timing ─────────────────────────────────────
// Already handled by CSS hero-blur-in classes above

// ── JS Ripple Injector (all buttons) ─────────────────────────────────
(function initRipple() {
  document.querySelectorAll('.btn-hero-primary,.btn-hero-secondary,.btn-nav-primary,.btn-sweep').forEach(btn => {
    btn.addEventListener('pointerdown', e => {
      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height) * 1.4;
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      const ripple = document.createElement('span');
      ripple.className = 'btn-ripple';
      ripple.style.cssText = 'position:absolute;left:'+x+'px;top:'+y+'px;width:'+size+'px;height:'+size+'px;';
      btn.appendChild(ripple);
      ripple.addEventListener('animationend', () => ripple.remove());
    });
  });
})();

// ── Section Heading Word-by-Word Reveal ──────────────────────────────
(function initWordReveal() {
  // Split section h2 elements into individual word spans
  document.querySelectorAll('.section-h2').forEach((h2, hi) => {
    h2.classList.add('word-reveal');
    // Preserve <br> tags
    const html = h2.innerHTML;
    const parts = html.split(/(<br>|<br[/]>)/i);
    h2.innerHTML = parts.map(part => {
      if (/^<br/i.test(part)) return '<br>';
      return part.split(' ').filter(w => w).map((word, wi) =>
        '<span class="word" style="transition-delay:' + (wi * 0.06 + hi * 0.02) + 's">' + word + '</span> '
      ).join('');
    }).join('');
  });

  // Observer to trigger reveal
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.2, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.word-reveal').forEach(el => obs.observe(el));
})();

// ── Hero Typing Cursor Effect ─────────────────────────────────────────
(function initTypingCursor() {
  const el = document.querySelector('.hero-p');
  if (!el) return;
  const phrases = [
    'Every document inspected by AI. Every job routed to the fastest printer. Every pickup secured by QR.',
    'No queues. No wasted prints. No data leaving your campus.',
    'From upload to collection in under three minutes — fully automated, end to end.'
  ];
  let pi = 0, ci = 0, deleting = false;
  el.classList.add('typing-cursor');
  el.textContent = '';

  function type() {
    const phrase = phrases[pi];
    if (!deleting) {
      el.textContent = phrase.slice(0, ++ci);
      if (ci === phrase.length) {
        deleting = true;
        setTimeout(type, 2800); return;
      }
      setTimeout(type, 28);
    } else {
      el.textContent = phrase.slice(0, --ci);
      if (ci === 0) {
        deleting = false;
        pi = (pi + 1) % phrases.length;
        setTimeout(type, 420); return;
      }
      setTimeout(type, 14);
    }
  }
  // Start after hero reveal animation
  setTimeout(type, 900);
})();

// ── AI Tech Card Bar Animate-In ───────────────────────────────────────
(function initTechBars() {
  const cards = document.querySelectorAll('.ai-tech-card');
  // Set bars to 0 width initially
  cards.forEach(c => {
    const fill = c.querySelector('.atc-fill');
    if (fill) { fill._targetWidth = fill.style.width; fill.style.width = '0%'; }
  });
  const obs = new IntersectionObserver(entries => {
    if (entries.some(e => e.isIntersecting)) {
      cards.forEach((c, i) => {
        setTimeout(() => {
          const fill = c.querySelector('.atc-fill');
          if (fill && fill._targetWidth) fill.style.width = fill._targetWidth;
        }, i * 120);
      });
      obs.disconnect();
    }
  }, { threshold: 0.15 });
  const grid = document.querySelector('.ai-tech-grid');
  if (grid) obs.observe(grid);
})();

// ── Smooth Stat Hover Glow (CSS already handles it) ──────────────────
// stat-cell hover is pure CSS via .stat-cell:hover .stat-num

// ── Multi-layer Section Parallax ─────────────────────────────────────
(function initDeepParallax() {
  const layers = [
    { el: document.querySelector('.gradient-mesh'), speed: 0.06 },
    { el: document.querySelector('.dot-grid'),      speed: 0.03 },
  ];
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const sy = window.scrollY;
      layers.forEach(l => {
        if (l.el) l.el.style.transform = 'translateY(' + (sy * l.speed) + 'px)';
      });
      ticking = false;
    });
  }, { passive: true });
})();

// ── Orbit Core Pulse ─────────────────────────────────────────────────
(function initOrbitCorePulse() {
  const core = document.querySelector('.orbit-core');
  if (!core) return;
  let t = 0;
  function pulse() {
    t += 0.04;
    const s = 1 + Math.sin(t) * 0.06;
    const shadow = 'rgba(139,92,246,' + (0.3 + Math.sin(t)*0.15) + ')';
    core.style.transform = 'translate(-50%,-50%) scale(' + s + ')';
    core.style.boxShadow = '0 0 0 1px rgba(139,92,246,0.2), 0 0 ' + (24 + Math.sin(t)*10) + 'px ' + shadow;
    requestAnimationFrame(pulse);
  }
  pulse();
})();

// ── Nav Shrink on Scroll (already done) + Logo Pulse on Brand hover ──
(function initLogoPulse() {
  const logo = document.querySelector('.nav-logo-mark');
  if (!logo) return;
  logo.addEventListener('mouseenter', () => {
    logo.style.transition = 'transform 0.3s cubic-bezier(0.34,1.5,0.64,1)';
    logo.style.transform = 'scale(1.2) rotate(-8deg)';
  });
  logo.addEventListener('mouseleave', () => {
    logo.style.transform = 'scale(1) rotate(0deg)';
  });
})();

})();
</script>
</body>
</html>"""
