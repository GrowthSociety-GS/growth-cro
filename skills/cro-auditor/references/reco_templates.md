# Templates de Livrables — Growth Audit

**Version:** 1.0
**Dernière mise à jour:** 2026-04-04
**Auteur:** Growth Society
**Objectif:** Définir les formats de présentation des recommandations d'audit pour les clients

---

## Vue d'ensemble

Ce document définit les **3 formats de livrable** que le skill Growth Audit génère après analyse d'une page :

1. **Dashboard HTML interactif** — Rapport d'audit visuel, performant, explorable
2. **Export PDF/DOCX** — Rapport professionnel imprimable, shareable
3. **Brief GSG** — Transmission structurée vers Growth Site Generator pour générer la page optimisée

Chaque format s'adapte au contexte client (profondeur d'audit, secteur, niveau tech) et au niveau de compétence du destinataire.

---

## FORMAT 1 — DASHBOARD HTML INTERACTIF

### 1.1 Vue d'ensemble structurelle

Le dashboard est un **single-file HTML** (CSS + JS intégrés) qui crée une expérience immersive, explorable et professionnelle du rapport d'audit.

**Avantages :**
- Chargement rapide (pas de dépendances externes, sauf polices)
- Responsive de 375px à 4K
- Animations engageantes (score au scroll, cards stagger)
- Filtres interactifs sur recommandations
- Export PDF généré côté client (pas de serveur)
- Hébergeable directement ou en iframe

**Structure générale :**

```
├── [1] HEADER
│   ├── Logo Growth Society (SVG placeholder)
│   ├── Titre "Growth Audit — {{CLIENT_NAME}}"
│   ├── Meta (date, auditeur, URL auditée)
│   └── Bouton "Mode sombre" + "Exporter PDF"
│
├── [2] HERO SCORE
│   ├── Jauges circulaires (score global, 6 catégories)
│   ├── Verdict narratif (1-2 lignes)
│   ├── Badges de niveau (Performant/À optimiser/Critique)
│   └── CTA "Voir les recommandations"
│
├── [3] TOP PROBLÈMES (🔴)
│   ├── Cartes empilées (design card style)
│   ├── Chaque : icône + titre + description + impact estimé
│   ├── Expandable pour voir le détail
│   └── Collapse automatique pour focus
│
├── [4] QUICK WINS (⚡)
│   ├── Cartes avec badge "Quick Win"
│   ├── Chaque : avant → après + effort + impact
│   ├── Checkbox "À implémenter"
│   └── Tri par effort/impact
│
├── [5] RECOMMANDATIONS DÉTAILLÉES
│   ├── Barre de filtres (catégorie, priorité, effort, impact)
│   ├── Cartes expandables pour chaque reco
│   ├── Contenu : titre + diagnostic + action + copy alt + impact + effort
│   ├── Référence à critère audit + psychologie activée
│   └── Matrice Impact × Effort interactive (2×2)
│
├── [6] COPY REWRITES
│   ├── Tableau : Élément | Actuel | Alt 1 | Alt 2 | Alt 3
│   ├── Justifications psychologiques
│   ├── Bouton "Copier" par cell
│   └── Downloadable en CSV/TXT
│
├── [7] WIREFRAME OPTIMISÉ [si Deep Dive]
│   ├── Représentation visuelle du flow recommandé
│   ├── Sections cliquables pour voir la reco associée
│   └── Annotations (changements, priorités)
│
├── [8] PLAN D'ACTION
│   ├── Timeline visuelle (Vague 1/2/3)
│   ├── Chaque action : titre + responsable + effort + impact
│   ├── Barre de progression estimée
│   └── Export en Notion/Asana (JSON payload)
│
└── [9] FOOTER
    ├── "Audit réalisé par Growth Society — {{DATE}}"
    ├── Contact pour questions
    └── CTA "Générer la page optimisée via GSG"
```

### 1.2 Design System & CSS Variables

```css
:root {
  /* Couleurs Growth Society */
  --primary: #4F46E5;           /* Indigo */
  --primary-light: #EEF2FF;
  --primary-dark: #312E81;

  --success: #10B981;           /* Vert */
  --success-light: #D1FAE5;
  --warning: #F59E0B;           /* Ambre */
  --warning-light: #FEF3C7;
  --danger: #EF4444;            /* Rouge */
  --danger-light: #FEE2E2;

  /* Neutres */
  --bg: #FFFFFF;
  --bg-secondary: #F9FAFB;
  --bg-tertiary: #F3F4F6;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --text-tertiary: #9CA3AF;
  --border: #E5E7EB;
  --border-dark: #D1D5DB;

  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-2xl: 3rem;
  --spacing-3xl: 4rem;

  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: "Fira Code", "Courier New", monospace;

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);

  /* Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);

  /* Border radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
}

/* Mode sombre */
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0F172A;
    --bg-secondary: #1E293B;
    --bg-tertiary: #334155;
    --text-primary: #F1F5F9;
    --text-secondary: #CBD5E1;
    --text-tertiary: #94A3B8;
    --border: #475569;
    --border-dark: #334155;
  }
}

/* Breakpoints */
/* Mobile: < 640px */
/* Tablet: 640px - 1024px */
/* Desktop: > 1024px */
```

### 1.3 Composants réutilisables HTML/CSS

#### Composant 1 : Score Gauge (Jauge circulaire)

```html
<!-- Usage: <gauge score="78" max="108" size="200"></gauge> -->

<script>
class GaugeComponent extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    const score = parseFloat(this.getAttribute('score')) || 0;
    const max = parseFloat(this.getAttribute('max')) || 100;
    const size = parseFloat(this.getAttribute('size')) || 120;
    const percentage = (score / max) * 100;

    const circumference = 2 * Math.PI * (size / 2 - 10);
    const offset = circumference - (percentage / 100) * circumference;

    // Déterminer couleur selon score
    let color = '#10B981'; // Vert
    if (percentage < 50) color = '#EF4444'; // Rouge
    else if (percentage < 70) color = '#F59E0B'; // Ambre

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: inline-block;
          --color: ${color};
        }

        svg {
          filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
          transform: rotate(-90deg);
        }

        .gauge-bg {
          fill: none;
          stroke: rgba(0,0,0,0.05);
          stroke-width: 8;
        }

        .gauge-fill {
          fill: none;
          stroke: var(--color);
          stroke-width: 8;
          stroke-linecap: round;
          stroke-dasharray: ${circumference};
          stroke-dashoffset: ${offset};
          transition: stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .gauge-text {
          text-anchor: middle;
          dominant-baseline: middle;
          font-weight: 700;
          font-size: ${size * 0.25}px;
          fill: currentColor;
        }
      </style>

      <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
        <circle class="gauge-bg" cx="${size/2}" cy="${size/2}" r="${size/2 - 10}"/>
        <circle class="gauge-fill" cx="${size/2}" cy="${size/2}" r="${size/2 - 10}"/>
        <text class="gauge-text" x="${size/2}" y="${size/2}">
          <tspan>${Math.round(percentage)}%</tspan>
        </text>
      </svg>
    `;
  }
}

customElements.define('gauge-circle', GaugeComponent);
</script>
```

#### Composant 2 : Recommendation Card (expandable)

```html
<!-- Usage:
<reco-card
  title="Ajouter social proof"
  priority="P1"
  impact="high"
  effort="low"
  category="persuasion">
  <div slot="diagnostic">
    Aucun testimonial ou cas d'usage visible...
  </div>
  <div slot="action">
    Ajouter 3-5 testimonials côté hero ou après CTA...
  </div>
</reco-card>
-->

<template id="reco-card-template">
  <style scoped>
    :host {
      display: block;
      margin-bottom: var(--spacing-lg);
    }

    .card {
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      background: var(--bg);
      cursor: pointer;
      transition: all var(--transition-base);
      overflow: hidden;
    }

    .card:hover {
      border-color: var(--primary);
      box-shadow: var(--shadow-md);
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--spacing-lg);
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
      cursor: pointer;
    }

    .card-header:hover {
      background: var(--bg-tertiary);
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      flex: 1;
      min-width: 0;
    }

    .header-content h3 {
      margin: 0;
      font-size: var(--text-lg);
      font-weight: 600;
      color: var(--text-primary);
    }

    .badges {
      display: flex;
      gap: var(--spacing-sm);
      flex-wrap: wrap;
      margin-top: var(--spacing-sm);
    }

    .badge {
      display: inline-block;
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: var(--radius-full);
      font-size: var(--text-xs);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .badge-p1 { background: var(--danger-light); color: #991B1B; }
    .badge-p2 { background: var(--warning-light); color: #92400E; }
    .badge-p3 { background: var(--bg-tertiary); color: var(--text-secondary); }

    .badge-impact-high { background: var(--success-light); color: #065F46; }
    .badge-impact-medium { background: var(--warning-light); color: #92400E; }
    .badge-impact-low { background: var(--bg-tertiary); color: var(--text-secondary); }

    .badge-effort-low { background: var(--success-light); color: #065F46; }
    .badge-effort-medium { background: var(--warning-light); color: #92400E; }
    .badge-effort-high { background: var(--danger-light); color: #991B1B; }

    .expand-icon {
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-secondary);
      transition: transform var(--transition-fast);
      flex-shrink: 0;
    }

    :host([open]) .expand-icon {
      transform: rotate(180deg);
    }

    .card-content {
      max-height: 0;
      overflow: hidden;
      transition: max-height var(--transition-base);
    }

    :host([open]) .card-content {
      max-height: 2000px;
    }

    .content-inner {
      padding: var(--spacing-lg);
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--spacing-xl);
    }

    @media (max-width: 768px) {
      .content-inner {
        grid-template-columns: 1fr;
        gap: var(--spacing-lg);
      }
    }

    .content-section h4 {
      margin: 0 0 var(--spacing-md) 0;
      font-size: var(--text-sm);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-secondary);
    }

    .content-section p {
      margin: 0;
      line-height: 1.6;
      color: var(--text-primary);
    }

    .copy-comparison {
      background: var(--bg-secondary);
      border-radius: var(--radius-md);
      padding: var(--spacing-md);
      margin-top: var(--spacing-md);
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      overflow-x: auto;
    }

    .copy-before {
      color: var(--danger);
      text-decoration: line-through;
      opacity: 0.7;
      margin-bottom: var(--spacing-sm);
    }

    .copy-after {
      color: var(--success);
      font-weight: 600;
    }
  </style>

  <div class="card">
    <div class="card-header">
      <div class="header-left">
        <div class="header-content">
          <h3><slot name="title"></slot></h3>
          <div class="badges">
            <span class="badge" id="priority-badge"></span>
            <span class="badge" id="impact-badge"></span>
            <span class="badge" id="effort-badge"></span>
          </div>
        </div>
      </div>
      <div class="expand-icon">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M5 7.5L10 12.5L15 7.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
    </div>

    <div class="card-content">
      <div class="content-inner">
        <div class="content-section">
          <h4>Diagnostic</h4>
          <slot name="diagnostic"></slot>
        </div>
        <div class="content-section">
          <h4>Recommandation</h4>
          <slot name="action"></slot>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
class RecoCardComponent extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    const template = document.getElementById('reco-card-template');
    this.shadowRoot.appendChild(template.content.cloneNode(true));
  }

  connectedCallback() {
    const header = this.shadowRoot.querySelector('.card-header');
    header.addEventListener('click', () => this.toggle());

    // Afficher les badges
    this.updateBadges();
  }

  toggle() {
    this.hasAttribute('open') ? this.removeAttribute('open') : this.setAttribute('open', '');
  }

  updateBadges() {
    const priority = this.getAttribute('priority') || 'P2';
    const impact = this.getAttribute('impact') || 'medium';
    const effort = this.getAttribute('effort') || 'medium';

    const labels = {
      'P1': 'P1', 'P2': 'P2', 'P3': 'P3',
      'high': 'Impact élevé', 'medium': 'Impact moyen', 'low': 'Impact faible',
      'low': 'Effort faible', 'medium': 'Effort moyen', 'high': 'Effort élevé'
    };

    this.shadowRoot.getElementById('priority-badge').textContent = priority;
    this.shadowRoot.getElementById('priority-badge').className = `badge badge-${priority.toLowerCase()}`;

    this.shadowRoot.getElementById('impact-badge').textContent = labels[impact];
    this.shadowRoot.getElementById('impact-badge').className = `badge badge-impact-${impact}`;

    this.shadowRoot.getElementById('effort-badge').textContent = labels[effort];
    this.shadowRoot.getElementById('effort-badge').className = `badge badge-effort-${effort}`;
  }
}

customElements.define('reco-card', RecoCardComponent);
</script>
```

#### Composant 3 : Matrice Impact × Effort

```html
<!-- Usage:
<impact-effort-matrix>
  <item label="Quick wins" x="low" y="high">
    <reco>Ajouter social proof</reco>
    <reco>Tester CTA rouge vs bleu</reco>
  </item>
  <item label="Projects" x="high" y="high">
    <reco>Refondre wireframe</reco>
  </item>
</impact-effort-matrix>
-->

<style>
impact-effort-matrix {
  display: block;
  margin: var(--spacing-2xl) 0;
}

.matrix-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: var(--spacing-xl);
  min-height: 400px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  border: 1px solid var(--border);
}

.quadrant {
  border: 1px dashed var(--border-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  flex-direction: column;
}

.quadrant h4 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--text-secondary);
}

.quadrant.quick-wins {
  background: rgba(16, 185, 129, 0.05);
  border-color: var(--success);
}

.quadrant.quick-wins h4 {
  color: var(--success);
}

.axis-labels {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
}

.axis-x {
  position: absolute;
  bottom: -30px;
  left: 50%;
  transform: translateX(-50%);
}

.axis-y {
  position: absolute;
  left: -80px;
  top: 50%;
  transform: translateY(-50%);
  writing-mode: vertical-rl;
  transform: rotate(180deg) translateY(-50%);
}
</style>

<script>
class ImpactEffortMatrix extends HTMLElement {
  connectedCallback() {
    this.render();
  }

  render() {
    const html = `
      <div class="matrix-container">
        <div class="quadrant quick-wins" style="grid-column: 2; grid-row: 2;">
          <h4>⚡ Quick Wins</h4>
          <div id="quick-wins"></div>
        </div>
        <div class="quadrant projects" style="grid-column: 2; grid-row: 1;">
          <h4>🚀 Projets majeurs</h4>
          <div id="projects"></div>
        </div>
        <div class="quadrant incr" style="grid-column: 1; grid-row: 2;">
          <h4>↪ Incremental</h4>
          <div id="incr"></div>
        </div>
        <div class="quadrant avoid" style="grid-column: 1; grid-row: 1;">
          <h4>❌ À éviter</h4>
          <div id="avoid"></div>
        </div>
      </div>
    `;

    this.innerHTML = html;

    // Remplir quadrants depuis les données
    this.populateQuadrants();
  }

  populateQuadrants() {
    // Implémentée par le skill lors de la génération du rapport
  }
}

customElements.define('impact-effort-matrix', ImpactEffortMatrix);
</script>
```

### 1.4 Template HTML complet du Dashboard

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Growth Audit — {{CLIENT_NAME}}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

  <style>
    :root {
      --primary: #4F46E5;
      --primary-light: #EEF2FF;
      --primary-dark: #312E81;
      --success: #10B981;
      --success-light: #D1FAE5;
      --warning: #F59E0B;
      --warning-light: #FEF3C7;
      --danger: #EF4444;
      --danger-light: #FEE2E2;

      --bg: #FFFFFF;
      --bg-secondary: #F9FAFB;
      --bg-tertiary: #F3F4F6;
      --text-primary: #111827;
      --text-secondary: #6B7280;
      --text-tertiary: #9CA3AF;
      --border: #E5E7EB;
      --border-dark: #D1D5DB;

      --spacing-xs: 0.25rem;
      --spacing-sm: 0.5rem;
      --spacing-md: 1rem;
      --spacing-lg: 1.5rem;
      --spacing-xl: 2rem;
      --spacing-2xl: 3rem;
      --spacing-3xl: 4rem;

      --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: "Fira Code", "Courier New", monospace;

      --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
      --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
      --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);

      --radius-sm: 4px;
      --radius-md: 8px;
      --radius-lg: 12px;
      --radius-xl: 16px;
      --radius-full: 9999px;

      --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
      --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
      --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }

    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0F172A;
        --bg-secondary: #1E293B;
        --bg-tertiary: #334155;
        --text-primary: #F1F5F9;
        --text-secondary: #CBD5E1;
        --text-tertiary: #94A3B8;
        --border: #475569;
        --border-dark: #334155;
      }
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    html {
      font-size: 16px;
      scroll-behavior: smooth;
    }

    body {
      font-family: var(--font-family);
      background: var(--bg);
      color: var(--text-primary);
      line-height: 1.6;
    }

    /* Header */
    header {
      position: sticky;
      top: 0;
      z-index: 100;
      background: var(--bg);
      border-bottom: 1px solid var(--border);
      backdrop-filter: blur(10px);
      background-color: rgba(255, 255, 255, 0.8);
    }

    @media (prefers-color-scheme: dark) {
      header {
        background-color: rgba(15, 23, 42, 0.8);
      }
    }

    .header-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: var(--spacing-lg) var(--spacing-xl);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: var(--spacing-lg);
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: var(--spacing-lg);
      flex: 1;
      min-width: 0;
    }

    .logo {
      width: 40px;
      height: 40px;
      flex-shrink: 0;
      background: var(--primary);
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 700;
      font-size: 20px;
    }

    .header-title {
      flex: 1;
      min-width: 0;
    }

    .header-title h1 {
      font-size: var(--text-2xl);
      font-weight: 700;
      margin: 0;
      margin-bottom: var(--spacing-xs);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .header-meta {
      display: flex;
      gap: var(--spacing-md);
      font-size: var(--text-sm);
      color: var(--text-secondary);
      overflow-x: auto;
      white-space: nowrap;
    }

    .header-meta span {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
    }

    .header-actions {
      display: flex;
      gap: var(--spacing-md);
      align-items: center;
      flex-shrink: 0;
    }

    button {
      background: none;
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: var(--spacing-sm) var(--spacing-md);
      cursor: pointer;
      font-size: var(--text-sm);
      font-weight: 500;
      color: var(--text-primary);
      transition: all var(--transition-fast);
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
    }

    button:hover {
      background: var(--bg-secondary);
      border-color: var(--border-dark);
    }

    button.primary {
      background: var(--primary);
      border-color: var(--primary);
      color: white;
    }

    button.primary:hover {
      background: var(--primary-dark);
      border-color: var(--primary-dark);
    }

    /* Container principal */
    main {
      max-width: 1200px;
      margin: 0 auto;
      padding: var(--spacing-3xl) var(--spacing-xl);
    }

    /* Section Hero Score */
    .hero-section {
      text-align: center;
      margin-bottom: var(--spacing-3xl);
      padding: var(--spacing-3xl) var(--spacing-xl);
      background: linear-gradient(135deg, var(--primary-light) 0%, var(--bg) 100%);
      border-radius: var(--radius-xl);
      border: 1px solid var(--border);
    }

    .score-display {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: var(--spacing-3xl);
      margin-bottom: var(--spacing-2xl);
      flex-wrap: wrap;
    }

    @media (max-width: 768px) {
      .score-display {
        gap: var(--spacing-lg);
      }
    }

    .score-main {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--spacing-lg);
    }

    .score-main svg {
      filter: drop-shadow(var(--shadow-lg));
    }

    .score-categories {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
      gap: var(--spacing-md);
      width: 100%;
      max-width: 600px;
    }

    .category-score {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: var(--spacing-md);
      text-align: center;
    }

    .category-score svg {
      width: 60px;
      height: 60px;
      margin-bottom: var(--spacing-sm);
    }

    .category-score .label {
      font-size: var(--text-xs);
      font-weight: 600;
      color: var(--text-secondary);
      margin-bottom: var(--spacing-xs);
    }

    .category-score .value {
      font-size: var(--text-xl);
      font-weight: 700;
      color: var(--text-primary);
    }

    .verdict {
      margin-top: var(--spacing-xl);
      font-size: var(--text-lg);
      font-weight: 600;
      color: var(--text-primary);
      max-width: 600px;
      margin-left: auto;
      margin-right: auto;
    }

    .verdict-emoji {
      font-size: var(--text-2xl);
      margin-right: var(--spacing-sm);
    }

    /* Sections de contenu */
    section {
      margin-bottom: var(--spacing-3xl);
    }

    section h2 {
      font-size: var(--text-3xl);
      font-weight: 700;
      margin-bottom: var(--spacing-xl);
      padding-bottom: var(--spacing-md);
      border-bottom: 2px solid var(--border);
    }

    /* Top Problèmes */
    .problems-grid {
      display: grid;
      gap: var(--spacing-lg);
    }

    .problem-card {
      background: var(--bg);
      border-left: 4px solid var(--danger);
      border: 1px solid var(--border);
      border-left: 4px solid var(--danger);
      border-radius: var(--radius-lg);
      padding: var(--spacing-lg);
      cursor: pointer;
      transition: all var(--transition-base);
    }

    .problem-card:hover {
      box-shadow: var(--shadow-lg);
      border-color: var(--danger);
    }

    .problem-card .title {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      font-size: var(--text-lg);
      font-weight: 600;
      margin-bottom: var(--spacing-md);
    }

    .problem-card .badge {
      background: var(--danger-light);
      color: #991B1B;
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: var(--radius-full);
      font-size: var(--text-xs);
      font-weight: 600;
    }

    .problem-card .description {
      color: var(--text-secondary);
      margin-bottom: var(--spacing-md);
      line-height: 1.6;
    }

    .problem-card .impact {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      color: var(--text-secondary);
      font-size: var(--text-sm);
    }

    /* Quick Wins */
    .quick-wins-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: var(--spacing-lg);
    }

    .quick-win-card {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: var(--spacing-lg);
      position: relative;
      transition: all var(--transition-base);
      overflow: hidden;
    }

    .quick-win-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, var(--success), var(--warning));
    }

    .quick-win-card:hover {
      box-shadow: var(--shadow-lg);
      transform: translateY(-4px);
    }

    .quick-win-badge {
      display: inline-block;
      background: var(--success-light);
      color: #065F46;
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: var(--radius-full);
      font-size: var(--text-xs);
      font-weight: 600;
      margin-bottom: var(--spacing-md);
    }

    .quick-win-card h3 {
      font-size: var(--text-lg);
      font-weight: 600;
      margin-bottom: var(--spacing-md);
      margin-top: 0;
    }

    .comparison {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--spacing-md);
      margin: var(--spacing-lg) 0;
    }

    .comparison-item {
      padding: var(--spacing-md);
      border-radius: var(--radius-md);
    }

    .comparison-item.before {
      background: var(--danger-light);
      border: 1px solid var(--danger);
    }

    .comparison-item.after {
      background: var(--success-light);
      border: 1px solid var(--success);
    }

    .comparison-label {
      font-size: var(--text-xs);
      font-weight: 600;
      margin-bottom: var(--spacing-sm);
      opacity: 0.7;
    }

    .comparison-text {
      font-size: var(--text-sm);
      line-height: 1.5;
      font-weight: 500;
    }

    .metrics {
      display: flex;
      gap: var(--spacing-lg);
      margin-top: var(--spacing-lg);
      flex-wrap: wrap;
    }

    .metric {
      flex: 1;
      min-width: 100px;
      text-align: center;
    }

    .metric-label {
      font-size: var(--text-xs);
      color: var(--text-secondary);
      margin-bottom: var(--spacing-xs);
    }

    .metric-value {
      font-size: var(--text-lg);
      font-weight: 700;
      color: var(--text-primary);
    }

    /* Filtres */
    .filters {
      display: flex;
      gap: var(--spacing-md);
      margin-bottom: var(--spacing-xl);
      flex-wrap: wrap;
    }

    .filter {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
    }

    .filter label {
      font-size: var(--text-sm);
      font-weight: 600;
      color: var(--text-secondary);
    }

    select {
      padding: var(--spacing-sm) var(--spacing-md);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      background: var(--bg);
      color: var(--text-primary);
      font-family: var(--font-family);
      cursor: pointer;
      transition: border-color var(--transition-fast);
    }

    select:hover {
      border-color: var(--primary);
    }

    select:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--primary-light);
    }

    /* Copy Rewrites Table */
    .copy-table {
      overflow-x: auto;
      margin: var(--spacing-xl) 0;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--bg);
    }

    th {
      background: var(--bg-secondary);
      padding: var(--spacing-md);
      text-align: left;
      font-weight: 600;
      font-size: var(--text-sm);
      color: var(--text-secondary);
      border-bottom: 2px solid var(--border);
    }

    td {
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border);
      font-size: var(--text-sm);
    }

    td:first-child {
      font-weight: 600;
      color: var(--text-primary);
      min-width: 120px;
    }

    tr:hover {
      background: var(--bg-secondary);
    }

    .copy-cell {
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      color: var(--text-secondary);
    }

    .copy-button {
      background: var(--primary);
      color: white;
      border: none;
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: var(--radius-md);
      font-size: var(--text-xs);
      cursor: pointer;
      transition: all var(--transition-fast);
    }

    .copy-button:hover {
      background: var(--primary-dark);
    }

    /* Timeline */
    .timeline {
      position: relative;
      padding: var(--spacing-lg) 0;
    }

    .timeline::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 2px;
      background: var(--border);
    }

    .timeline-item {
      margin-left: var(--spacing-3xl);
      margin-bottom: var(--spacing-xl);
      position: relative;
    }

    .timeline-item::before {
      content: '';
      position: absolute;
      left: -2.75rem;
      top: 0.5rem;
      width: 20px;
      height: 20px;
      background: var(--primary);
      border: 3px solid var(--bg);
      border-radius: var(--radius-full);
    }

    .timeline-item h4 {
      font-size: var(--text-lg);
      font-weight: 600;
      margin: 0 0 var(--spacing-sm) 0;
    }

    .timeline-item p {
      margin: 0;
      color: var(--text-secondary);
      font-size: var(--text-sm);
    }

    /* Footer */
    footer {
      margin-top: var(--spacing-3xl);
      padding: var(--spacing-3xl) var(--spacing-xl);
      background: var(--bg-secondary);
      border-top: 1px solid var(--border);
      text-align: center;
      color: var(--text-secondary);
      font-size: var(--text-sm);
    }

    /* Responsive */
    @media (max-width: 768px) {
      .header-container {
        flex-direction: column;
        align-items: flex-start;
      }

      .header-actions {
        width: 100%;
        justify-content: space-between;
      }

      main {
        padding: var(--spacing-xl) var(--spacing-md);
      }

      section h2 {
        font-size: var(--text-2xl);
      }

      .score-display {
        flex-direction: column;
        gap: var(--spacing-2xl);
      }

      .quick-wins-grid {
        grid-template-columns: 1fr;
      }

      .comparison {
        grid-template-columns: 1fr;
      }

      table {
        font-size: var(--text-xs);
      }

      td, th {
        padding: var(--spacing-sm);
      }
    }

    @media print {
      header, .header-actions button:not(.print-only) {
        display: none;
      }

      main {
        max-width: 100%;
        padding: 0;
      }

      section {
        break-inside: avoid;
        page-break-inside: avoid;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="header-container">
      <div class="header-left">
        <div class="logo">GS</div>
        <div class="header-title">
          <h1>Growth Audit — {{CLIENT_NAME}}</h1>
          <div class="header-meta">
            <span>📅 {{AUDIT_DATE}}</span>
            <span>👤 {{AUDITOR_NAME}}</span>
            <span>🌐 {{AUDIT_URL}}</span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <button onclick="toggleDarkMode()">🌙 Sombre</button>
        <button class="primary" onclick="window.print()">📥 PDF</button>
      </div>
    </div>
  </header>

  <main>
    <!-- Hero Score -->
    <section class="hero-section">
      <div class="score-display">
        <div class="score-main">
          <svg width="200" height="200" viewBox="0 0 200 200">
            <circle cx="100" cy="100" r="90" fill="none" stroke="#E5E7EB" stroke-width="8"/>
            <circle cx="100" cy="100" r="90" fill="none" stroke="#10B981" stroke-width="8"
                    stroke-dasharray="{{SCORE_PERCENTAGE}} 100" stroke-linecap="round"
                    style="transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dasharray 1.2s ease-out;"/>
            <text x="100" y="110" text-anchor="middle" font-size="48" font-weight="700" fill="#111827">{{SCORE}}</text>
            <text x="100" y="135" text-anchor="middle" font-size="20" fill="#6B7280">/108</text>
          </svg>
          <div class="verdict">
            <span class="verdict-emoji">{{VERDICT_EMOJI}}</span>
            {{VERDICT_TEXT}}
          </div>
        </div>

        <div class="score-categories">
          {{CATEGORY_SCORES_HTML}}
        </div>
      </div>
    </section>

    <!-- Top Problèmes -->
    <section id="problems">
      <h2>🔴 Top Problèmes</h2>
      <div class="problems-grid">
        {{PROBLEMS_HTML}}
      </div>
    </section>

    <!-- Quick Wins -->
    <section id="quick-wins">
      <h2>⚡ Quick Wins</h2>
      <div class="quick-wins-grid">
        {{QUICK_WINS_HTML}}
      </div>
    </section>

    <!-- Recommandations Détaillées -->
    <section id="recommendations">
      <h2>📋 Recommandations Détaillées</h2>

      <div class="filters">
        <div class="filter">
          <label>Catégorie</label>
          <select onchange="filterRecommendations()">
            <option value="">Toutes</option>
            <option value="strategy">Cohérence Stratégique</option>
            <option value="hero">Hero / Above the fold</option>
            <option value="persuasion">Persuasion & Copy</option>
            <option value="ux">Structure & UX</option>
            <option value="technical">Qualité Technique</option>
            <option value="psychology">Psychologie</option>
          </select>
        </div>
        <div class="filter">
          <label>Priorité</label>
          <select onchange="filterRecommendations()">
            <option value="">Tous</option>
            <option value="P1">P1 - Critique</option>
            <option value="P2">P2 - Important</option>
            <option value="P3">P3 - Amélioration</option>
          </select>
        </div>
        <div class="filter">
          <label>Effort</label>
          <select onchange="filterRecommendations()">
            <option value="">Tous</option>
            <option value="low">Faible</option>
            <option value="medium">Moyen</option>
            <option value="high">Élevé</option>
          </select>
        </div>
        <div class="filter">
          <label>Impact</label>
          <select onchange="filterRecommendations()">
            <option value="">Tous</option>
            <option value="high">Élevé</option>
            <option value="medium">Moyen</option>
            <option value="low">Faible</option>
          </select>
        </div>
      </div>

      <div id="recommendations-container">
        {{RECOMMENDATIONS_HTML}}
      </div>
    </section>

    <!-- Copy Rewrites -->
    <section id="copy">
      <h2>✏️ Copy Rewrites</h2>
      <p style="color: var(--text-secondary); margin-bottom: var(--spacing-lg);">
        Alternatives de copy testées et optimisées psychologiquement pour chaque élément clé.
      </p>
      <div class="copy-table">
        <table>
          <thead>
            <tr>
              <th>Élément</th>
              <th>Actuel</th>
              <th>Alternative 1</th>
              <th>Alternative 2</th>
              <th>Alternative 3</th>
            </tr>
          </thead>
          <tbody>
            {{COPY_REWRITES_HTML}}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Plan d'Action -->
    <section id="action-plan">
      <h2>🎯 Plan d'Action — 3 Vagues</h2>
      <div class="timeline">
        {{ACTION_PLAN_HTML}}
      </div>
    </section>

    <!-- Wireframe Optimisé (si Deep Dive) -->
    {{WIREFRAME_SECTION_IF_DEEP_DIVE}}
  </main>

  <footer>
    <p>Growth Audit réalisé par <strong>Growth Society</strong> — {{AUDIT_DATE}}</p>
    <p style="margin-top: var(--spacing-md);">Pour questions ou approfondissement : contact@growthsociety.io</p>
    <button class="primary" style="margin-top: var(--spacing-lg); margin-left: auto; margin-right: auto; display: block;"
            onclick="launchGSGGenerator()">
      🚀 Générer la page optimisée via GSG
    </button>
  </footer>

  <script>
    // Dark Mode
    function toggleDarkMode() {
      const html = document.documentElement;
      const isDark = html.style.colorScheme === 'dark';
      html.style.colorScheme = isDark ? 'light' : 'dark';
      localStorage.setItem('audit-theme', isDark ? 'light' : 'dark');
    }

    // Charger thème sauvegardé
    const savedTheme = localStorage.getItem('audit-theme');
    if (savedTheme) {
      document.documentElement.style.colorScheme = savedTheme;
    }

    // Filtres Recommandations
    function filterRecommendations() {
      const category = document.querySelector('select[onchange="filterRecommendations()"]').value;
      const items = document.querySelectorAll('[data-reco]');

      items.forEach(item => {
        const match = !category || item.dataset.reco === category;
        item.style.display = match ? 'block' : 'none';
      });
    }

    // Animation scores au scroll
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animated');
        }
      });
    });

    document.querySelectorAll('gauge-circle').forEach(gauge => {
      observer.observe(gauge);
    });

    // Copier au clipboard
    function copyToClipboard(text, button) {
      navigator.clipboard.writeText(text).then(() => {
        const original = button.textContent;
        button.textContent = '✓ Copié!';
        setTimeout(() => {
          button.textContent = original;
        }, 2000);
      });
    }

    // Lancer GSG (stub à adapter)
    function launchGSGGenerator() {
      const briefData = {
        clientName: '{{CLIENT_NAME}}',
        auditScore: {{SCORE}},
        keyRecommendations: {{BRIEF_JSON}},
        briefGSG: {{BRIEF_GSG_JSON}}
      };

      // Sera implémenté selon intégration réelle GSG
      console.log('Launching GSG with brief:', briefData);
      alert('Transition vers Growth Site Generator en préparation...');
    }

    // Print-friendly
    window.addEventListener('beforeprint', () => {
      document.body.classList.add('printing');
    });

    window.addEventListener('afterprint', () => {
      document.body.classList.remove('printing');
    });
  </script>
</body>
</html>
```

---

## FORMAT 2 — EXPORT PDF/DOCX

### 2.1 Structure du document

Le document d'export reprend la structure du dashboard mais dans un format **imprimable et shareable** (PDF via print du HTML, ou export DOCX via outils tiers).

**Avantages:**
- Peut être émailé, hébergé en PDF statique
- Lisible offline
- Ressemble à un rapport pro classique
- Peut être annoté/commenté

**Structure:**

```
[PAGE 1 - COUVERTURE]
┌─────────────────────────────────────┐
│  📊 GROWTH AUDIT REPORT             │
│                                     │
│  {{CLIENT_NAME}}                    │
│                                     │
│  Score: {{SCORE}}/108               │
│  Date: {{DATE}}                     │
│  Auditeur: {{AUDITOR}}              │
│                                     │
│  Growth Society                     │
└─────────────────────────────────────┘

[PAGE 2 - EXECUTIVE SUMMARY]
- Score global + verdict
- Top 3 problèmes
- Top 3 quick wins
- ROI estimé des optimisations

[PAGES 3-8 - DÉTAIL PAR CATÉGORIE]
Pour chaque catégorie:
- Score catégorie (jauge)
- Tableau critères scorés
- Recommandations priorisées

[PAGE 9 - COPY REWRITES]
- Tableau avant/après
- Justifications

[PAGE 10 - WIREFRAME] (si Deep Dive)

[PAGE 11 - PLAN D'ACTION]
- Timeline 3 vagues
- Responsables

[PAGE 12 - NEXT STEPS]
- Options: auto vs Growth Society vs GSG
- Contact
```

### 2.2 Styles pour export

```css
/* Print-specific styles */
@media print {
  /* Couverture */
  .cover {
    page-break-after: always;
    text-align: center;
    padding: 4cm;
    background: linear-gradient(135deg, #4F46E5, #312E81);
    color: white;
  }

  .cover h1 {
    font-size: 48pt;
    margin-bottom: 2cm;
  }

  .cover .score-big {
    font-size: 72pt;
    font-weight: 700;
    margin: 2cm 0;
  }

  /* Summary */
  .summary {
    page-break-after: always;
  }

  /* Sections */
  section {
    page-break-inside: avoid;
  }

  .problem-card, .quick-win-card {
    page-break-inside: avoid;
    break-inside: avoid;
  }

  /* Tables */
  table {
    page-break-inside: avoid;
    width: 100%;
  }

  /* Enlever interactivité */
  button, select, input[type="checkbox"] {
    display: none !important;
  }

  /* Optimiser pour papier */
  body {
    color: #000;
    background: white;
  }

  a {
    color: #0066cc;
  }
}
```

### 2.3 Générateur DOCX

Via `python-docx` ou équivalent :

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def generate_audit_docx(audit_data):
    doc = Document()

    # Couverture
    title = doc.add_heading('GROWTH AUDIT REPORT', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    client_name = doc.add_paragraph(audit_data['client_name'])
    client_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    client_name.runs[0].font.size = Pt(28)

    doc.add_paragraph()  # Space

    score_text = f"Score: {audit_data['score']}/108"
    score_p = doc.add_paragraph(score_text)
    score_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_p.runs[0].font.size = Pt(48)
    score_p.runs[0].font.bold = True

    # Executive Summary
    doc.add_page_break()
    doc.add_heading('Executive Summary', level=1)

    verdict = doc.add_paragraph(audit_data['verdict'])
    verdict.style = 'List Bullet'

    # Top problèmes
    doc.add_heading('🔴 Top Problèmes', level=2)
    for problem in audit_data['top_problems']:
        doc.add_paragraph(problem['title'], style='List Bullet')
        doc.add_paragraph(problem['impact'], style='List Bullet 2')

    # Quick wins
    doc.add_heading('⚡ Quick Wins', level=2)
    for quick_win in audit_data['quick_wins']:
        doc.add_paragraph(f"{quick_win['title']} — Effort: {quick_win['effort']}",
                         style='List Bullet')

    # Détail par catégorie
    for category in audit_data['categories']:
        doc.add_page_break()
        doc.add_heading(category['name'], level=1)

        # Score jauge (texte)
        doc.add_paragraph(f"Score: {category['score']}/{{max_category_points}}")

        # Critères
        table = doc.add_table(rows=1, cols=3)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Critère'
        hdr_cells[1].text = 'Statut'
        hdr_cells[2].text = 'Note'

        for criterion in category['criteria']:
            row_cells = table.add_row().cells
            row_cells[0].text = criterion['name']
            row_cells[1].text = criterion['status']
            row_cells[2].text = str(criterion['score'])

    # Copy rewrites
    doc.add_page_break()
    doc.add_heading('✏️ Copy Rewrites', level=1)

    table = doc.add_table(rows=1, cols=5)
    hdr_cells = table.rows[0].cells
    headers = ['Élément', 'Actuel', 'Alt 1', 'Alt 2', 'Alt 3']
    for i, header in enumerate(headers):
        hdr_cells[i].text = header

    for rewrite in audit_data['copy_rewrites']:
        row_cells = table.add_row().cells
        row_cells[0].text = rewrite['element']
        row_cells[1].text = rewrite['current']
        row_cells[2].text = rewrite['alt1']
        row_cells[3].text = rewrite['alt2']
        row_cells[4].text = rewrite['alt3']

    # Plan d'action
    doc.add_page_break()
    doc.add_heading('🎯 Plan d'Action', level=1)

    for wave_idx, wave in enumerate(audit_data['action_plan'], 1):
        doc.add_heading(f"Vague {wave_idx}: {wave['name']}", level=2)
        for action in wave['actions']:
            p = doc.add_paragraph(f"{action['title']} (Effort: {action['effort']})",
                                 style='List Bullet')

    # Next steps
    doc.add_page_break()
    doc.add_heading('Next Steps', level=1)
    doc.add_paragraph(
        'Vous avez 3 options pour mettre en œuvre ces recommandations:\n'
        '1. Implémenter vous-même (ressources internes)\n'
        '2. Nous confier les optimisations (Growth Society)\n'
        '3. Générer la page optimisée via Growth Site Generator',
        style='List Number'
    )

    return doc

# Export
doc = generate_audit_docx(audit_data)
doc.save(f'{client_name}_growth_audit.docx')
```

---

## FORMAT 3 — BRIEF GSG (TRANSMISSION AU GROWTH SITE GENERATOR)

### 3.1 Structure du brief

Le brief est un **JSON structuré** qui alimente le skill Growth Site Generator (GSG) pour créer la page optimisée basée sur les insights de l'audit.

```json
{
  "audit_metadata": {
    "audit_id": "{{AUDIT_ID}}",
    "client_name": "{{CLIENT_NAME}}",
    "audit_date": "{{ISO_DATE}}",
    "audit_score": {{SCORE}},
    "audit_depth": "{{quick-scan|standard|deep-dive}}",
    "auditor": "{{AUDITOR_NAME}}",
    "url_audited": "{{URL}}"
  },

  "brief_gsg": {
    "page_type": "{{landing_page|product_page|home_page|etc}}",
    "business_context": {
      "industry": "{{INDUSTRY}}",
      "target_audience": "{{PERSONA}}",
      "primary_goal": "{{GOAL: lead|sale|signup}}",
      "traffic_source": "{{TRAFFIC_SOURCE}}",
      "estimated_monthly_traffic": {{TRAFFIC_NUMBER}}
    },

    "insights_from_audit": {
      "strengths": [
        {
          "insight": "{{Strength identifiée}}",
          "source_criterion": "{{Critère audit}}",
          "priority_preserve": true,
          "psychological_principle": "{{Principle activée}}"
        }
      ],
      "weaknesses": [
        {
          "issue": "{{Weakness identifiée}}",
          "source_criterion": "{{Critère audit}}",
          "impact_on_conversion": "{{high|medium|low}}",
          "recommended_fix": "{{Fix court}}"
        }
      ],
      "copy_that_works": [
        {
          "element": "{{Élément (headline, CTA, etc)}}",
          "current_copy": "{{Copy fonctionnelle}}",
          "why_works": "{{Psychologie derrière}}"
        }
      ],
      "copy_to_rewrite": [
        {
          "element": "{{Élément à réécrire}}",
          "current_copy": "{{Copy actuelle}}",
          "problem": "{{Pourquoi ça ne fonctionne pas}}",
          "suggested_alternatives": [
            {"copy": "{{Alt 1}}", "psychological_angle": "{{Angle psy}}"},
            {"copy": "{{Alt 2}}", "psychological_angle": "{{Angle psy}}"},
            {"copy": "{{Alt 3}}", "psychological_angle": "{{Angle psy}}"}
          ]
        }
      ]
    },

    "design_system": {
      "colors": {
        "primary": "{{HEX}}",
        "secondary": "{{HEX}}",
        "accent": "{{HEX}}",
        "text": "{{HEX}}",
        "background": "{{HEX}}",
        "extracted_from": "{{Actuel site ou analysé de DA existante}}"
      },
      "typography": {
        "headline_font": "{{Font name}}",
        "body_font": "{{Font name}}",
        "sizes": {
          "h1": "{{Size}}",
          "h2": "{{Size}}",
          "body": "{{Size}}"
        }
      },
      "tone_of_voice": "{{formal|casual|urgency|emotional|data-driven}}",
      "visual_style": "{{minimalist|maximalist|playful|professional}}"
    },

    "recommended_page_architecture": {
      "sections": [
        {
          "section_name": "{{Hero|Value Props|Social Proof|Objections|CTA|etc}}",
          "current_state": "{{Description actuelle}}",
          "recommended_change": "{{Changement recommandé}}",
          "wireframe_description": "{{Description textuelle du wireframe}}",
          "copy_focus": "{{Copy strategy pour section}}",
          "psychological_strategy": "{{Stratégie psycho}}"
        }
      ],
      "flow_diagram": "{{ASCII ou description du flow de persuasion}}"
    },

    "psychological_framework": {
      "primary_sequence": "{{PAS|AIDA|BAB|Doctor's Creed|etc}}",
      "cialdini_principles_to_activate": [
        "{{reciprocity|commitment|social_proof|authority|liking|scarcity}}"
      ],
      "cognitive_biases_to_leverage": [
        "{{loss_aversion|anchoring|scarcity|social_proof|bandwagon}}"
      ],
      "schwartz_consciousness_levels": "{{Conscious|Semi-conscious|Subconscious}}",
      "objection_handling": [
        {
          "objection": "{{Objection courante}}",
          "handling_strategy": "{{Comment l'adresser}}"
        }
      ]
    },

    "conversion_optimization": {
      "current_conversion_metrics": {
        "estimated_ctr": "{{%}}",
        "estimated_cpc": "{{$}}",
        "estimated_conversion_rate": "{{%}}"
      },
      "target_metrics_after_optimization": {
        "target_ctr": "{{%}}",
        "target_conversion_rate": "{{%}}",
        "estimated_uplift": "{{%}}"
      },
      "critical_optimization_points": [
        {
          "element": "{{Élément critique}}",
          "current_performance": "{{Perf actuelle}}",
          "optimization_potential": "{{Potential}}",
          "ab_test_hypothesis": "{{Hypothèse test}}"
        }
      ]
    },

    "next_steps_for_gsg": {
      "recommended_variations_to_generate": "{{Nombres de variations}}",
      "testing_priority": "{{hero|cta|social_proof|copy|flow}}",
      "estimated_impact": {
        "expected_score_improvement": "{{/153 selon grille GSG}}",
        "estimated_conversion_improvement": "{{%}}"
      },
      "quick_wins_to_prioritize": [
        "{{Action 1}}", "{{Action 2}}", "{{Action 3}}"
      ]
    }
  }
}
```

### 3.2 Mapping Score Audit → Brief GSG

Comment les 6 catégories d'audit se traduisent en instructions GSG :

| Catégorie Audit | Mapping GSG | Section Brief |
|---|---|---|
| **Cohérence Stratégique** (Score 1.1-1.6) | Alignement ad → page, objectif unique, prop. valeur claire | `insights_from_audit.copy_that_works` + `business_context` |
| **Hero / ATF** (Score 2.1-2.5) | Impactful hero, value prop visible, CTA prominent | `recommended_page_architecture[Hero]` + `psychological_framework` |
| **Persuasion & Copy** (Score 3.1-3.7) | Arguments solides, objections traitées, CTA copy | `copy_to_rewrite` + `cialdini_principles_to_activate` |
| **Structure & UX** (Score 4.1-4.7) | Flow logique, mobile-friendly, formulaires optimisés | `recommended_page_architecture.flow_diagram` |
| **Qualité Technique** (Score 5.1-5.5) | Performance, accessibilité (GSG gère auto) | Noté mais délégué à GSG builder |
| **Psychologie** (Score 6.1-6.6) | Séquence persuasion, biais, frictions, éthique | `psychological_framework` complet |

### 3.3 Exemple de brief GSG minimal

```json
{
  "audit_metadata": {
    "audit_id": "audit_2026_04_acme",
    "client_name": "ACME Corp",
    "audit_score": 62,
    "url_audited": "https://acme.com/product-x"
  },

  "brief_gsg": {
    "page_type": "product_page",
    "business_context": {
      "industry": "SaaS — Project Management",
      "target_audience": "CTOs, Engineering Managers",
      "primary_goal": "lead",
      "traffic_source": "Google Ads (brand keywords)"
    },

    "insights_from_audit": {
      "strengths": [
        {
          "insight": "Feature list est détaillée et pertinente",
          "source_criterion": "3.2 — Argumentation produit",
          "priority_preserve": true,
          "psychological_principle": "Authority, Competence"
        }
      ],
      "weaknesses": [
        {
          "issue": "Aucun testimonial ou cas d'usage visible",
          "source_criterion": "3.4 — Social Proof",
          "impact_on_conversion": "high",
          "recommended_fix": "Ajouter 3-5 testimonials vidéo ou citations côté hero"
        }
      ],
      "copy_that_works": [
        {
          "element": "Headline",
          "current_copy": "Gestion de projets en temps réel pour les équipes modernes",
          "why_works": "Specifique, bénéfice immédiat, parle à persona"
        }
      ],
      "copy_to_rewrite": [
        {
          "element": "CTA principal (button)",
          "current_copy": "Learn More",
          "problem": "Générique, pas d'urgence, pas de bénéfice",
          "suggested_alternatives": [
            {
              "copy": "Commencer gratuitement en 2 min",
              "psychological_angle": "Scarcité temporelle + facilité d'action"
            },
            {
              "copy": "Voir la démo (5 min)",
              "psychological_angle": "Réciprocité + démonctration de compétence"
            }
          ]
        }
      ]
    },

    "design_system": {
      "colors": {
        "primary": "#3B82F6",
        "secondary": "#10B981",
        "text": "#1F2937",
        "background": "#F9FAFB"
      },
      "tone_of_voice": "professional_friendly"
    },

    "recommended_page_architecture": {
      "sections": [
        {
          "section_name": "Hero",
          "recommended_change": "Ajouter vidéo démo hero ou image produit animée",
          "psychological_strategy": "Demonstrability + Authority"
        },
        {
          "section_name": "Social Proof",
          "current_state": "Absente",
          "recommended_change": "Ajouter section 3-5 testimonials avec logos clients",
          "psychological_strategy": "Social proof + Consensus"
        }
      ]
    },

    "psychological_framework": {
      "primary_sequence": "AIDA",
      "cialdini_principles_to_activate": ["social_proof", "authority", "scarcity"],
      "cognitive_biases_to_leverage": ["social_proof", "authority_bias"]
    }
  }
}
```

---

## FORMAT 4 — RÈGLES DE GÉNÉRATION DES LIVRABLES

### 4.1 Adaptation au niveau client

```
Client Tech (CTO, Product Manager)
├── Montrer: métriques détaillées, benchmarks, données
├── Tone: analytique, fact-based
├── Profondeur: technique (Core Web Vitals, accessibility scores, etc)
└── Templates: Avec données brutes JSON disponibles

Client Marketing (CMO, Head of Growth)
├── Montrer: KPIs, ROI estimé, impact business
├── Tone: business-focused, orienté action
├── Profondeur: psychology, funnel, copy
└── Templates: Avec métriques de conversion, benchmarks industrie

Client Fondateur / Non-tech
├── Montrer: actions concrètes, résultats estimés, coût
├── Tone: simple, accessible, orienté résultat
├── Profondeur: pas de jargon tech, focus sur "quoi faire"
└── Templates: Avec plan d'action clair, timeline simple
```

### 4.2 Adaptation au niveau de profondeur

```
Quick Scan (5 min)
├── Livrables:
│   ├── Score seul (/108)
│   ├── Top 5 problèmes (liste simple)
│   └── Top 3 quick wins
├── Pas de: Dashboard HTML, Wireframe, Copy rewrites détaillés
└── Format: Message texte + JSON simple

Audit Standard (15 min)
├── Livrables:
│   ├── Dashboard HTML complet
│   ├── Recommandations structurées (40-60)
│   ├── Copy rewrites (5-10)
│   ├── Plan d'action 3 vagues
│   └── Export PDF possible
├── Pas de: Wireframe, Brief GSG complet, Benchmark concurrentiel
└── Temps réaction: < 20 min après audit

Deep Dive (30 min)
├── Livrables:
│   ├── Dashboard HTML complet + avancé
│   ├── Wireframe optimisé (ASCII + description)
│   ├── Copy rewrites détaillés (10-15)
│   ├── Brief GSG structuré
│   ├── Benchmark concurrentiel (5 sites)
│   ├── Plan d'action 3 vagues détaillé
│   ├── Export PDF professionnel
│   └── Video walkthrough (optionnel, lien Loom)
└── Temps réaction: 30-45 min après audit complet
```

### 4.3 Personnalisation

```
Élément à personnaliser          | Comment injecter
──────────────────────────────────────────────────────────
Nom du client                     | {{CLIENT_NAME}} dans tous les templates
Logo du client                    | Remplacer logo Growth Society (si fourni)
Couleurs (optionnel)             | --primary, --secondary CSS vars
Benchmarks industrie             | {{INDUSTRY_BENCHMARKS}} contextualisés
Plan d'action responsables       | {{PERSON}} assigné en fonction contexte
Score cible post-recos           | {{SCORE_TARGET}} prédictif
Timeline du client               | {{TIMELINE}} adapté capacités
Langue                           | Templates en FR par défaut, possible EN
```

---

## CHECKLIST DE GÉNÉRATION DES LIVRABLES

- [ ] **Avant génération:**
  - [ ] Audit complété et scoré (36 critères)
  - [ ] Top 5 problèmes identifiés et classés
  - [ ] Quick wins (3-5) validés
  - [ ] Recommandations (40-100) structurées
  - [ ] Copy rewrites (5-15) rédigées avec justifications
  - [ ] Plan d'action 3 vagues défini

- [ ] **Dashboard HTML:**
  - [ ] Tous les scores injectés (global + 6 catégories)
  - [ ] Verdict et émojis corrects
  - [ ] Problèmes cards remplies (expandable)
  - [ ] Quick wins cards avec avant/après
  - [ ] Recommandations filtrables
  - [ ] Matrice Impact × Effort interactive
  - [ ] Copy table avec boutons "copier"
  - [ ] Timeline plan d'action
  - [ ] Responsive testé (375px, 768px, 1024px)
  - [ ] Dark mode fonctionnnel
  - [ ] Print-friendly CSS
  - [ ] Bouton "Export PDF" opérationnel

- [ ] **Export PDF:**
  - [ ] Couverture avec logo + score
  - [ ] Executive summary (1 page)
  - [ ] Détail 6 catégories (6 pages)
  - [ ] Copy rewrites table
  - [ ] Wireframe (si Deep Dive)
  - [ ] Plan d'action
  - [ ] Next steps + contact
  - [ ] Numérotation pages
  - [ ] No pagination breaks bizarres

- [ ] **Brief GSG:**
  - [ ] JSON valide et complet
  - [ ] Audit metadata remplie
  - [ ] Insights from audit détaillés
  - [ ] Design system exact
  - [ ] Recommended architecture claire
  - [ ] Psychological framework complet
  - [ ] Conversion optimization metrics
  - [ ] Next steps pour GSG exploitable

- [ ] **Textes:**
  - [ ] Pas de jargon incompréhensible pour le client
  - [ ] Chiffres et visuels > paragraphes
  - [ ] Tone cohérent avec niveau client
  - [ ] Actions concrètes et non "pensez à..."
  - [ ] Justifications courtes mais complètes

---

## VARIABLES TEMPLATE À SUBSTITUER

| Variable | Exemple | Où injecter |
|----------|---------|-------------|
| `{{CLIENT_NAME}}` | "ACME Corp" | Tous formats |
| `{{SCORE}}` | "78" | Dashboard + PDF |
| `{{SCORE_PERCENTAGE}}` | "72.2" | Jauges |
| `{{AUDIT_DATE}}` | "2026-04-04" | Header + Footer |
| `{{AUDITOR_NAME}}` | "Mathis Fronty" | Métadonnées |
| `{{AUDIT_URL}}` | "https://example.com" | Métadonnées |
| `{{AUDIT_ID}}` | "audit_2026_04_xxx" | Brief GSG |
| `{{VERDICT_TEXT}}` | "Page performante..." | Hero Score |
| `{{VERDICT_EMOJI}}` | "🟢" | Hero Score |
| `{{CATEGORY_SCORES_HTML}}` | Boucle 6 catégories | Dashboard |
| `{{PROBLEMS_HTML}}` | Cards problèmes | Dashboard |
| `{{QUICK_WINS_HTML}}` | Cards quick wins | Dashboard |
| `{{RECOMMENDATIONS_HTML}}` | Cards recos | Dashboard |
| `{{COPY_REWRITES_HTML}}` | Table rows | Dashboard + PDF |
| `{{ACTION_PLAN_HTML}}` | Timeline items | Dashboard + PDF |
| `{{WIREFRAME_SECTION_IF_DEEP_DIVE}}` | Section entière ou vide | Dashboard si Deep Dive |
| `{{BRIEF_JSON}}` | JSON complet | Stub GSG |
| `{{INDUSTRY}}` | "SaaS" | Brief GSG |
| `{{TRAFFIC_SOURCE}}` | "Google Ads" | Brief GSG |
| `{{SCORE_TARGET}}` | "95" | Plan d'action |

---

## NOTES DÉVELOPPEUR

- **Composants Web réutilisables** : `<gauge-circle>`, `<reco-card>`, `<impact-effort-matrix>` — considérer les utiliser ou en créer de nouveaux
- **CSS Variables** : Toutes les couleurs/spacing via variables pour faciliter la personnalisation
- **Single-file HTML** : Dashboard = 1 fichier HTML (CSS + JS inline) pour portabilité max
- **No external deps** : Utiliser système-fonts, pas de jQuery/Vue/React pour perf
- **JSON pour Brief GSG** : Serializable et documenté pour intégration GSG fluide
- **Print-friendly** : Tous formats doivent imprimer proprement
- **Accessibility** : WCAG 2.1 AA minimum (contrast, alt text, keyboard nav)
- **Localisation** : Templates par défaut en français, facile à adapter pour EN

---

**Fin du fichier**

Last updated: 2026-04-04
Version: 1.0
Maintainer: Growth Society — CRO Team
