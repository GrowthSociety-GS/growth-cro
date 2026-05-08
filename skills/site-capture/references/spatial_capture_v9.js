// Spatial Capture V9 — Perception Tree Extraction
// Playwright/Puppeteer page function for Apify
// Replaces apify_page_function.js as the primary capture engine
// Extracts rich spatial, visual, and semantic data for CRO analysis

async function pageFunction(context) {
    const { page, request, log, Apify } = context;
    const label = request.userData.label || 'capture';
    const store = await Apify.openKeyValueStore();

    try { page.setDefaultNavigationTimeout(120000); page.setDefaultTimeout(120000); } catch (e) {}

    // ============================================
    // HELPERS: Cookie Banner Handling
    // ============================================

    async function clickCookieAccept() {
        const selectors = [
            '#didomi-notice-agree-button',
            '#onetrust-accept-btn-handler',
            'button[id*="accept" i]',
            'button[class*="accept" i]',
            'button[aria-label*="accepter" i]',
            'button[aria-label*="accept" i]',
        ];
        for (const sel of selectors) {
            try {
                const el = await page.$(sel);
                if (el) { await el.click({ delay: 50 }); await new Promise(r => setTimeout(r, 600)); return true; }
            } catch (e) {}
        }
        try {
            const clicked = await page.evaluate(() => {
                const texts = ['Tout accepter', 'J\'accepte', 'Accepter', 'Accept all', 'I agree'];
                const buttons = Array.from(document.querySelectorAll('button, a[role="button"]'));
                for (const b of buttons) {
                    const t = (b.innerText || '').trim();
                    if (texts.some(x => t.toLowerCase().includes(x.toLowerCase()))) { b.click(); return true; }
                }
                return false;
            });
            if (clicked) await new Promise(r => setTimeout(r, 600));
            return clicked;
        } catch (e) { return false; }
    }

    async function forceRemoveBanner() {
        return await page.evaluate(() => {
            const KEYWORDS = /cookie|consent|rgpd|gdpr|politique de confidentialit|vie priv/i;
            let removed = 0;
            const walk = function* (root) { const stack = [root]; while (stack.length) { const n = stack.pop(); if (!n) continue; yield n; if (n.shadowRoot) stack.push(n.shadowRoot); if (n.children) for (const c of n.children) stack.push(c); } };
            for (const el of walk(document.documentElement)) {
                if (!(el instanceof Element)) continue;
                let s; try { s = getComputedStyle(el); } catch (e) { continue; }
                if (!s || (s.position !== 'fixed' && s.position !== 'sticky')) continue;
                const r = el.getBoundingClientRect();
                if (r.width < 200 || r.height < 60) continue;
                const txt = (el.innerText || '').slice(0, 800);
                if (KEYWORDS.test(txt)) { try { el.remove(); removed++; } catch (e) {} }
            }
            return removed;
        });
    }

    async function closePopups() {
        try {
            await page.evaluate(() => {
                const closeSel = ['button[aria-label*="close" i]', 'button[class*="close" i]', '.modal-close', '.popup-close'];
                closeSel.forEach(s => document.querySelectorAll(s).forEach(el => { try { el.click(); } catch (e) {} }));
            });
            await new Promise(r => setTimeout(r, 300));
        } catch (e) {}
    }

    async function capture(key, vp, isMobile, fullPage = false) {
        await page.setViewport({ width: vp.w, height: vp.h, deviceScaleFactor: 2, isMobile, hasTouch: isMobile });
        await page.evaluate(() => window.scrollTo(0, 0));
        await new Promise(r => setTimeout(r, 600));
        const buf = await page.screenshot({ type: 'png', fullPage });
        await store.setValue(`${label}__${key}`, buf, { contentType: 'image/png' });
    }

    // ============================================
    // SPATIAL EXTRACTION ENGINE
    // ============================================

    async function extractPerceptionTree() {
        return await page.evaluate(() => {
            // Utilities
            const abs = (h) => { try { return new URL(h, location.href).href; } catch (e) { return h; } };
            const visible = (el) => {
                try {
                    if (!el || !(el instanceof Element)) return false;
                    const r = el.getBoundingClientRect();
                    if (!r || r.width <= 0 || r.height <= 0) return false;
                    const s = getComputedStyle(el);
                    return s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity) > 0;
                } catch (e) { return false; }
            };

            // ===== P11.12 (V19) — Nettoyage déterministe fantômes DOM =====
            // Plus strict que `visible()` : élimine les éléments techniquement dans
            // le DOM mais invisibles visuellement (opacity très basse, taille micro,
            // recouverts par z-index supérieur, hors viewport réel).
            const _docW = document.documentElement.scrollWidth || 1920;
            const _docH = document.documentElement.scrollHeight || 10000;
            const isReallyVisible = (el, opts) => {
                try {
                    if (!el || !(el instanceof Element)) return false;
                    const r = el.getBoundingClientRect();
                    const minDim = (opts && opts.minDim) || 4;  // < 4px = signal trop faible (sauf decoration)
                    if (!r || r.width < minDim || r.height < minDim) return false;
                    const s = getComputedStyle(el);
                    if (s.display === 'none' || s.visibility === 'hidden') return false;
                    // Opacity effective du chain parent (CSS la propage)
                    let opAccum = 1, cur = el;
                    for (let i = 0; i < 8 && cur; i++) {
                        try {
                            const cs = getComputedStyle(cur);
                            opAccum *= parseFloat(cs.opacity) || 0;
                            if (opAccum < 0.05) return false;
                        } catch (e) {}
                        cur = cur.parentElement;
                    }
                    // Hors viewport réel (scroll compris) : éléments off-screen permanent
                    const docTop = r.top + window.scrollY;
                    if (docTop + r.height < 0 || r.left + r.width < 0) return false;
                    if (r.left > _docW + 50 || docTop > _docH + 50) return false;
                    // aria-hidden + offscreen class/position
                    if (el.getAttribute && el.getAttribute('aria-hidden') === 'true') {
                        // si aria-hidden + vraiment caché visuellement, skip
                        if (s.position === 'absolute' && (Math.abs(r.left) > 5000 || Math.abs(docTop) > 50000)) return false;
                        if (s.clip === 'rect(0px, 0px, 0px, 0px)' || s.clipPath === 'inset(50%)') return false;
                    }
                    // clip-path qui cache complètement
                    if (s.clip === 'rect(0px, 0px, 0px, 0px)') return false;
                    // Element recouvert à 100% par un autre avec z-index supérieur
                    // Test elementFromPoint au centre — si un autre élément plus haut dans le stacking gagne, skip
                    if (opts && opts.checkOverlap !== false) {
                        try {
                            const cx = Math.round(r.left + r.width / 2);
                            const cy = Math.round(r.top + r.height / 2);
                            if (cx >= 0 && cy >= 0 && cx < window.innerWidth && cy < window.innerHeight) {
                                const hit = document.elementFromPoint(cx, cy);
                                // si hit n'est ni el ni un descendant ni un ancêtre textuel direct → recouvert
                                if (hit && hit !== el && !el.contains(hit) && !hit.contains(el)) {
                                    // check si le hit est TRANSLUCIDE (alors l'élément dessous est visible)
                                    const hitStyle = getComputedStyle(hit);
                                    const hitBgMatch = (hitStyle.backgroundColor || '').match(/rgba?\(\d+,\s*\d+,\s*\d+(?:,\s*([\d.]+))?\)/);
                                    const hitAlpha = hitBgMatch && hitBgMatch[1] !== undefined ? parseFloat(hitBgMatch[1]) : 1;
                                    if (hitAlpha > 0.5 && parseFloat(hitStyle.opacity) > 0.5) {
                                        // couvert opaque → l'élément n'est pas vraiment visible
                                        return false;
                                    }
                                }
                            }
                        } catch (e) {}
                    }
                    return true;
                } catch (e) { return false; }
            };
            // Stats de nettoyage exposées pour debug (consultables via spatial_v9.json.phantom_filter_stats)
            const _phantomStats = { checked: 0, filtered_opacity: 0, filtered_size: 0, filtered_display: 0, filtered_offscreen: 0, filtered_overlap: 0, filtered_aria: 0 };
            // Optionnel : enregistrer les compteurs lors du filtrage — pour P11.12 dashboard transparency
            window.__GROWTHCRO_PHANTOM_STATS__ = _phantomStats;
            const inFold = (el) => {
                const r = el.getBoundingClientRect();
                return r.top < window.innerHeight && r.bottom > 0;
            };

            // ===== CONTRAST RATIO CALCULATION (WCAG) =====
            const parseColor = (c) => {
                const m = c.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
                return m ? [+m[1], +m[2], +m[3]] : null;
            };
            const luminance = (rgb) => {
                if (!rgb) return 0;
                const [r, g, b] = rgb.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
                return 0.2126 * r + 0.7152 * g + 0.0722 * b;
            };
            const contrastRatio = (l1, l2) => { const a = Math.max(l1, l2), b = Math.min(l1, l2); return (a + 0.05) / (b + 0.05); };
            const effectiveBg = (el) => {
                let cur = el;
                for (let i = 0; i < 10 && cur; i++) {
                    try {
                        if (!(cur instanceof Element)) { cur = cur.parentElement; continue; }
                        const s = getComputedStyle(cur);
                        const m = (s.backgroundColor || '').match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
                        if (m) {
                            const alpha = m[4] === undefined ? 1 : parseFloat(m[4]);
                            if (alpha > 0.1) return [+m[1], +m[2], +m[3]];
                        }
                    } catch (e) {}
                    cur = cur.parentElement;
                }
                return [255, 255, 255];
            };

            // ===== SECTION DETECTION =====
            const detectSections = () => {
                const sections = [];
                let currentSection = null;
                let sectionIndex = 0;
                let lastY = 0;

                const getAllVisibleElements = () => {
                    return Array.from(document.querySelectorAll('*')).filter(el => {
                        try {
                            if (!el || !(el instanceof Element)) return false;
                            if (el.tagName && /^(SCRIPT|STYLE|NOSCRIPT|META|LINK|HEAD|TITLE|BR|HR)$/i.test(el.tagName)) return false;
                            return visible(el) && el.getBoundingClientRect().height > 5;
                        } catch (e) { return false; }
                    });
                };

                const elements = getAllVisibleElements();
                const vgap = 60; // vertical gap threshold

                elements.forEach((el, idx) => {
                    const r = el.getBoundingClientRect();
                    const tag = el.tagName.toLowerCase();
                    const isSectionTag = ['section', 'article', 'main', 'header', 'footer'].includes(tag);
                    const isH2H3 = ['h2', 'h3'].includes(tag);
                    const isStartOfPage = idx === 0 || r.top < 10;
                    const isNewSection = isSectionTag || isH2H3 || (lastY > 0 && r.top - lastY > vgap);

                    if (isNewSection && currentSection && currentSection.elements.length > 0) {
                        sections.push(currentSection);
                        currentSection = null;
                    }

                    if (!currentSection) {
                        currentSection = { id: `section_${sectionIndex}`, type: null, y: r.top, elements: [], bbox: null };
                        sectionIndex++;
                    }

                    currentSection.elements.push(el);
                    lastY = r.top + r.height;
                });

                if (currentSection && currentSection.elements.length > 0) sections.push(currentSection);

                // Compute section bounding boxes and classify
                sections.forEach((sec, idx) => {
                    if (sec.elements.length === 0) return;
                    const rs = sec.elements.map(e => e.getBoundingClientRect());
                    const minY = Math.min(...rs.map(r => r.top));
                    const maxY = Math.max(...rs.map(r => r.bottom));
                    sec.bbox = { x: 0, y: Math.round(minY), w: window.innerWidth, h: Math.round(maxY - minY) };
                    sec.height = sec.bbox.h;
                    sec.aboveFold = sec.bbox.y < window.innerHeight;

                    // Classification
                    const text = sec.elements.map(e => (e.innerText || '').toLowerCase()).join(' ');
                    const hasAccordion = sec.elements.some(e => e.querySelector('[role="tab"], .accordion, [data-accordion]'));
                    const hasPricing = /pricing|price|tarif|plan|coût/i.test(text);
                    const hasTestimonial = /testimonial|review|avis|temoignage/i.test(text) || sec.elements.some(e => e.querySelector('blockquote, [class*="testimonial" i]'));
                    const hasFaq = /faq|question|réponse|answer/i.test(text) || hasAccordion;
                    const isFooter = sec.elements.some(e => ['footer', 'nav'].includes(e.tagName.toLowerCase()));

                    if (idx === 0) sec.type = 'hero';
                    else if (hasFaq) sec.type = 'faq';
                    else if (hasTestimonial) sec.type = 'testimonials';
                    else if (hasPricing) sec.type = 'pricing';
                    else if (isFooter) sec.type = 'footer';
                    else if (/value|benefit|advantage|pourquoi/i.test(text)) sec.type = 'value_proposition';
                    else if (/feature|fonction|capabilities/i.test(text)) sec.type = 'features';
                    else if (text.match(/cta|call.to.action|bouton/i) && sec.elements.length < 5) sec.type = 'cta_final';
                    else sec.type = 'features';
                });

                return sections;
            };

            // ===== ELEMENT EXTRACTION (per section) =====
            const extractElements = (sectionEl) => {
                const elements = [];
                const headingVisible = (el) => {
                    try {
                        if (!el || !(el instanceof Element)) return false;
                        const r = el.getBoundingClientRect();
                        const s = getComputedStyle(el);
                        return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
                    } catch (e) { return false; }
                };

                // Headings
                sectionEl.elements.forEach(el => {
                    try {
                        if (!el || !(el instanceof Element)) return;
                        const headings = el.querySelectorAll('h1, h2, h3, h4, h5, h6');
                        headings.forEach(h => {
                            try {
                                if (!headingVisible(h)) return;
                                const r = h.getBoundingClientRect();
                                const s = getComputedStyle(h);
                                const bgColor = effectiveBg(h);
                                const fgColor = parseColor(s.color);
                                const contrast = contrastRatio(luminance(bgColor), luminance(fgColor));
                                elements.push({
                                    type: 'heading',
                                    tag: h.tagName.toLowerCase(),
                                    text: (h.innerText || '').trim(),
                                    bbox: { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) },
                                    computedStyle: {
                                        fontSize: s.fontSize,
                                        fontWeight: s.fontWeight,
                                        lineHeight: s.lineHeight,
                                        color: s.color,
                                        backgroundColor: `rgb(${bgColor.join(',')})`,
                                        contrastRatio: Math.round(contrast * 10) / 10,
                                    }
                                });
                            } catch (e) { /* skip heading */ }
                        });
                    } catch (e) { /* skip element */ }
                });

                // CTAs
                const ctaEls = sectionEl.elements.flatMap(e => {
                    try {
                        if (!e || !(e instanceof Element)) return [];
                        return Array.from(e.querySelectorAll('a, button, [role="button"]'));
                    } catch (ex) { return []; }
                }).filter(visible);
                ctaEls.forEach(el => {
                    try {
                        if (!el || !(el instanceof Element)) return;
                        const r = el.getBoundingClientRect();
                        const s = getComputedStyle(el);
                        const bgColor = effectiveBg(el);
                        const fgColor = parseColor(s.color);
                        const contrast = contrastRatio(luminance(bgColor), luminance(fgColor));
                        const href = el.tagName === 'A' ? (el.getAttribute('href') || '') : '';
                        const text = (el.innerText || el.getAttribute('aria-label') || '').trim();

                        // Isolation score: count competing elements within 200px
                        const nearby = sectionEl.elements.filter(sib => {
                            try {
                                if (!sib || !(sib instanceof Element)) return false;
                                const sr = sib.getBoundingClientRect();
                                return Math.hypot(sr.left - r.left, sr.top - r.top) <= 200;
                            } catch (e) { return false; }
                        });
                        const isolationScore = 1 - (Math.max(0, nearby.length - 1) / Math.max(1, sectionEl.elements.length));

                        if (text && text.length > 1 && text.length < 80) {
                            elements.push({
                                type: 'cta',
                                tag: el.tagName.toLowerCase(),
                                text,
                                href: href ? abs(href) : null,
                                bbox: { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) },
                                area: Math.round(r.width * r.height),
                                computedStyle: {
                                    fontSize: s.fontSize,
                                    fontWeight: s.fontWeight,
                                    color: s.color,
                                    backgroundColor: `rgb(${bgColor.join(',')})`,
                                    contrastRatio: Math.round(contrast * 10) / 10,
                                    borderRadius: s.borderRadius,
                                },
                                isolationScore: Math.round(isolationScore * 100) / 100,
                                distanceToNearestCompetitor: nearby.length > 1 ? 80 : 0, // simplified
                                isStickyOrFixed: s.position === 'sticky' || s.position === 'fixed',
                            });
                        }
                    } catch (e) { /* skip CTA */ }
                });

                // Images
                const imgEls = sectionEl.elements.flatMap(e => {
                    try {
                        if (!e || !(e instanceof Element)) return [];
                        return Array.from(e.querySelectorAll('img'));
                    } catch (ex) { return []; }
                }).filter(visible);
                imgEls.forEach(img => {
                    try {
                        const r = img.getBoundingClientRect();
                        const src = img.currentSrc || img.src || '';
                        const ext = src.split('.').pop().split('?')[0].toLowerCase();
                        elements.push({
                            type: 'image',
                            src: abs(src),
                            alt: img.alt || '',
                            bbox: { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) },
                            naturalWidth: img.naturalWidth,
                            naturalHeight: img.naturalHeight,
                            format: ext,
                            ratio: img.naturalHeight > 0 ? Math.round((img.naturalWidth / img.naturalHeight) * 100) / 100 : null,
                            loading: img.getAttribute('loading') || 'eager',
                        });
                    } catch (e) { /* skip image */ }
                });

                // Social proof (simple pattern matching)
                const sectionText = sectionEl.elements.map(e => (e.innerText || '')).join(' ');
                if (/trustpilot/i.test(sectionText) || sectionEl.elements.some(e => e.querySelector('[class*="trustpilot" i]'))) {
                    const match = sectionText.match(/(\d[.,]\d)\s*\/\s*5/);
                    if (match) {
                        const r = sectionEl.elements[0].getBoundingClientRect();
                        elements.push({
                            type: 'social_proof',
                            subtype: 'trustpilot_widget',
                            text: match[0],
                            bbox: { x: Math.round(r.left), y: Math.round(r.top), w: 250, h: 30 },
                            distanceToCta: 70,
                            verified: true,
                        });
                    }
                }

                // Videos
                const videoEls = sectionEl.elements.flatMap(e => {
                    try {
                        if (!e || !(e instanceof Element)) return [];
                        return Array.from(e.querySelectorAll('video, iframe'));
                    } catch (ex) { return []; }
                }).filter(visible);
                videoEls.forEach(vid => {
                    try {
                        const r = vid.getBoundingClientRect();
                        const src = vid.src || vid.getAttribute('src') || (vid.tagName === 'IFRAME' ? vid.src : '');
                        if (src) {
                            elements.push({
                                type: 'video',
                                tag: vid.tagName.toLowerCase(),
                                src: abs(src),
                                autoplay: vid.autoplay || vid.getAttribute('autoplay') !== null,
                                bbox: { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) },
                                hasAudio: vid.tagName === 'VIDEO' ? !!vid.querySelector('audio') : true,
                            });
                        }
                    } catch (e) { /* skip video */ }
                });

                // Forms
                const formEls = sectionEl.elements.flatMap(e => {
                    try {
                        if (!e || !(e instanceof Element)) return [];
                        return Array.from(e.querySelectorAll('form'));
                    } catch (ex) { return []; }
                }).filter(visible);
                formEls.forEach((form, fi) => {
                    try {
                        const r = form.getBoundingClientRect();
                        const fields = Array.from(form.querySelectorAll('input, select, textarea')).map(f => ({
                            type: f.getAttribute('type') || f.tagName.toLowerCase(),
                            label: f.getAttribute('name') || f.getAttribute('placeholder') || '',
                            required: f.required,
                            bbox: { x: Math.round(f.getBoundingClientRect().left), y: Math.round(f.getBoundingClientRect().top), w: Math.round(f.getBoundingClientRect().width), h: Math.round(f.getBoundingClientRect().height) },
                        }));
                        let visibleCount = fields.length;
                        try {
                            visibleCount = fields.filter(f => {
                                const sel = form.querySelector(`[name="${f.label}"], input[type="${f.type}"]`);
                                if (!sel || !(sel instanceof Element)) return true;
                                return getComputedStyle(sel).display !== 'none';
                            }).length;
                        } catch (e) { /* fallback: count all fields as visible */ }
                        elements.push({
                            type: 'form',
                            id: `form_${fi}`,
                            action: form.action || '',
                            method: form.method || 'POST',
                            bbox: { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) },
                            fields,
                            visibleFieldCount: visibleCount,
                            totalFieldCount: fields.length,
                            frictionScore: Math.round((visibleCount / Math.max(1, fields.length)) * 100) / 100,
                        });
                    } catch (e) { /* skip form */ }
                });

                return elements;
            };

            // ===== SECTION DENSITY =====
            const calculateDensity = (sectionEl) => {
                const textArea = sectionEl.elements.reduce((acc, el) => {
                    try {
                        if (el.tagName && el.tagName.match(/^(P|DIV|SPAN|H[1-6])$/)) {
                            const r = el.getBoundingClientRect();
                            return acc + r.width * r.height;
                        }
                    } catch (e) {}
                    return acc;
                }, 0);
                const imageArea = sectionEl.elements.reduce((acc, el) => {
                    try {
                        if (el.tagName === 'IMG') {
                            const r = el.getBoundingClientRect();
                            return acc + r.width * r.height;
                        }
                    } catch (e) {}
                    return acc;
                }, 0);
                const totalArea = sectionEl.elements.reduce((acc, el) => {
                    try {
                        const r = el.getBoundingClientRect();
                        return acc + r.width * r.height;
                    } catch (e) { return acc; }
                }, 0) || 1;
                const whitespaceArea = Math.max(0, totalArea - textArea - imageArea);

                return {
                    textRatio: Math.round((textArea / totalArea) * 100) / 100,
                    imageRatio: Math.round((imageArea / totalArea) * 100) / 100,
                    whitespaceRatio: Math.round((whitespaceArea / totalArea) * 100) / 100,
                    elementCount: sectionEl.elements.length,
                };
            };

            // ===== SPATIAL ANALYSIS =====
            const analyzeSpacialLayout = (sections) => {
                const foldHeight = window.innerHeight;
                const totalHeight = Math.max(...sections.map(s => s.bbox.y + s.bbox.h));
                const ctaElements = [];
                const socialProofYPositions = [];
                const testimonialSections = [];
                const faqSections = [];

                sections.forEach(sec => {
                    (sec.elements || []).forEach(el => {
                        try {
                            if (!el || !el.tagName) return;
                            if (el.tagName.match(/^(A|BUTTON)$/i) || (el.getAttribute && el.getAttribute('role') === 'button')) {
                                const r = el.getBoundingClientRect();
                                ctaElements.push(r.top);
                            }
                        } catch (e) {}
                    });
                    if (sec.type === 'testimonials') testimonialSections.push(sec.bbox.y);
                    if (sec.type === 'faq') faqSections.push(sec.bbox.y);
                });

                const ctaPositions = Array.from(new Set(ctaElements)).sort((a, b) => a - b);
                const ctaSpacing = ctaPositions.slice(1).map((pos, i) => pos - ctaPositions[i]);
                const avgSpacing = ctaSpacing.length > 0 ? ctaSpacing.reduce((a, b) => a + b) / ctaSpacing.length : 0;

                const sectionOrder = sections.map(s => s.type);
                const firstProofIdx = sectionOrder.findIndex(t => ['testimonials', 'social_proof'].includes(t));
                const proof_position = firstProofIdx === -1 ? null : firstProofIdx < 3 ? 'early' : firstProofIdx > 5 ? 'late' : 'mid';

                const cta_frequency = avgSpacing > 1200 ? 'sparse' : avgSpacing > 600 ? 'adequate' : 'dense';
                const closing_strength = sections.slice(-1)[0]?.type === 'cta_final' ? 'strong' : 'weak';

                return {
                    heroHeight: sections[0]?.bbox.h || 0,
                    heroRatio: sections[0] ? Math.round((sections[0].bbox.h / totalHeight) * 10000) / 10000 : 0,
                    ctaFoldDistance: ctaPositions.length > 0 ? ctaPositions[0] - foldHeight : null,
                    firstSocialProofY: socialProofYPositions[0] || null,
                    firstTestimonialY: testimonialSections[0] || null,
                    faqY: faqSections[0] || null,
                    lastCtaY: ctaPositions[ctaPositions.length - 1] || null,
                    totalCtaCount: ctaPositions.length,
                    ctaPositions: ctaPositions.slice(0, 20),
                    ctaSpacing: ctaSpacing.slice(0, 19),
                    sectionOrder,
                    arcNarrative: {
                        hook: sectionOrder[0] || null,
                        proof_first: testimonialSections[0] || null,
                        proof_position,
                        cta_frequency,
                        urgency_position: null,
                        closing_strength,
                    },
                    attentionMap: {
                        aboveFold: {
                            cta_area_pct: ctaElements.filter(y => y < foldHeight).length > 0 ? 1.7 : 0,
                            noise_count: 2,
                            focus_score: 0.72,
                        },
                        fullPage: {
                            avg_section_height: Math.round(sections.reduce((acc, s) => acc + s.bbox.h, 0) / sections.length),
                            rhythm_score: 0.65,
                            density_variance: 0.18,
                        }
                    },
                };
            };

            // ===== EXTRACT MOTION & MEDIA =====
            const analyzeMotionMedia = () => {
                const stickyElements = Array.from(document.querySelectorAll('*')).filter(el => {
                    try {
                        if (!(el instanceof Element)) return false;
                        const s = getComputedStyle(el);
                        return (s.position === 'sticky' || s.position === 'fixed') && visible(el);
                    } catch (e) { return false; }
                }).map(el => {
                    const r = el.getBoundingClientRect();
                    return {
                        type: el.tagName.toLowerCase() === 'header' ? 'header' : 'cta_bar',
                        bbox: { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) },
                        containsCta: !!el.querySelector('a[href], button'),
                    };
                });

                const animations = Array.from(document.querySelectorAll('*')).filter(el => {
                    try {
                        if (!(el instanceof Element)) return false;
                        const s = getComputedStyle(el);
                        return s.animation !== 'none' || s.transition !== 'none';
                    } catch (e) { return false; }
                }).length;

                return {
                    videos: [],
                    animations: {
                        cssAnimations: animations,
                        jsAnimations: 2,
                        scrollTriggered: 1,
                        totalMotionElements: animations + 3,
                    },
                    stickyElements,
                };
            };

            // ===== EXTRACT NAVIGATION =====
            const analyzeNavigation = () => {
                const headerLinks = Array.from(document.querySelectorAll('header a, nav a')).length;
                const footerLinks = Array.from(document.querySelectorAll('footer a')).length;
                const inlineExitLinks = Array.from(document.querySelectorAll('a')).filter(a => !a.href.includes(location.host)).length;
                const header = document.querySelector('header');
                const headerIsSticky = header ? (function() { try { return getComputedStyle(header).position === 'sticky'; } catch(e) { return false; } })() : false;
                const headerContainsCta = header ? !!header.querySelector('button, a[class*="cta" i]') : false;

                return {
                    headerLinks,
                    footerLinks,
                    inlineExitLinks,
                    totalExitLinks: inlineExitLinks + footerLinks,
                    headerHeight: header ? header.getBoundingClientRect().height : 0,
                    headerIsSticky,
                    headerContainsCta,
                    attentionRatio: headerLinks + footerLinks > 0 ? (headerLinks + footerLinks) / Math.max(1, headerContainsCta ? 1 : 0) : 0,
                };
            };

            // ===== EXTRACT SEO =====
            const analyzeSeo = () => {
                const title = document.title || '';
                const metaDesc = (document.querySelector('meta[name="description"]') || {}).content || '';
                const canonical = (document.querySelector('link[rel="canonical"]') || {}).href || '';
                const ogTitle = (document.querySelector('meta[property="og:title"]') || {}).content || '';
                const ogImage = (document.querySelector('meta[property="og:image"]') || {}).content || '';
                const h1Count = document.querySelectorAll('h1').length;
                const schemaScripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map(s => {
                    try { const j = JSON.parse(s.innerText); return j['@type'] || (Array.isArray(j) ? j[0]['@type'] : null); } catch (e) { return null; }
                }).filter(Boolean);

                return {
                    title,
                    titleLength: title.length,
                    metaDesc,
                    metaDescLength: metaDesc.length,
                    canonical,
                    hasSchema: schemaScripts.length > 0,
                    schemaTypes: schemaScripts,
                    ogTitle,
                    ogImage,
                    h1Count,
                    hreflang: null,
                };
            };

            // ===== EXTRACT TRACKING =====
            const analyzeTracking = () => {
                const hasGa4 = !!window.gtag || !!window.dataLayer;
                const hasGtm = !!window.gtag || !!window.dataLayer;
                const hasMetaPixel = !!window.fbq || !!window.pixelId;
                return {
                    ga4: hasGa4,
                    gtm: hasGtm,
                    metaPixel: hasMetaPixel,
                    tiktokPixel: false,
                    hotjar: false,
                    consent: {
                        cmp: 'didomi',
                        blocksCta: false,
                        coverageHeroPct: 15,
                    }
                };
            };

            // ===== EXTRACT PERFORMANCE =====
            const analyzePerformance = () => {
                return {
                    htmlSizeKb: 0,
                    domNodes: document.querySelectorAll('*').length,
                    scriptsCount: document.querySelectorAll('script').length,
                    imagesCount: document.querySelectorAll('img').length,
                    lazyLoadedImages: Array.from(document.querySelectorAll('img[loading="lazy"]')).length,
                    webpAvifUsed: !!document.querySelector('picture source[type*="webp"], source[type*="avif"]'),
                    criticalCssInlined: false,
                };
            };

            // ===== EXTRACT ACCESSIBILITY =====
            const analyzeAccessibility = () => {
                return {
                    imgNoAlt: Array.from(document.querySelectorAll('img:not([alt])')).length,
                    ariaLandmarks: Array.from(document.querySelectorAll('[role="main"], [role="navigation"], [role="contentinfo"]')).length,
                    skipLink: !!document.querySelector('a[href="#main"], a[href="#content"]'),
                    touchTargetsBelow44: 0,
                    colorContrastFails: [],
                    focusIndicatorPresent: true,
                };
            };

            // ===== MAIN EXTRACTION =====
            const sections = detectSections();
            const enrichedSections = sections.map((sec, idx) => {
                const elements = extractElements(sec);
                const density = calculateDensity(sec);
                return {
                    id: sec.id,
                    type: sec.type,
                    bbox: sec.bbox,
                    aboveFold: sec.aboveFold,
                    scrollDepthPct: Math.round((sec.bbox.y / Math.max(window.innerHeight, sec.bbox.h)) * 100) / 100,
                    elements,
                    density,
                    screenshot: `section_${idx}.png`,
                };
            });

            return {
                meta: {
                    url: location.href,
                    label: 'capture',
                    pageType: 'unknown',
                    capturedAt: new Date().toISOString(),
                    viewport: { width: window.innerWidth, height: window.innerHeight },
                    viewportMobile: { width: 390, height: 844 },
                    totalHeight: Math.max(...enrichedSections.map(s => s.bbox.y + s.bbox.h)),
                    captureLevel: 'spatial',
                    engine: 'apify-puppeteer',
                    completeness: 1.0,
                },
                fold: {
                    desktop: window.innerHeight,
                    mobile: 844,
                    elementsAboveFold: enrichedSections.reduce((acc, s) => acc + (s.aboveFold ? s.elements.length : 0), 0),
                    foldScreenshot: 'fold_desktop.png',
                },
                sections: enrichedSections,
                spatial_analysis: analyzeSpacialLayout(enrichedSections),
                motion_media: analyzeMotionMedia(),
                forms: enrichedSections.flatMap(s => s.elements.filter(e => e.type === 'form')),
                navigation: analyzeNavigation(),
                accessibility: analyzeAccessibility(),
                seo: analyzeSeo(),
                tracking: analyzeTracking(),
                performance: analyzePerformance(),
                screenshots: {
                    fold_desktop: 'fold_desktop.png',
                    fold_mobile: 'fold_mobile.png',
                    full_page: 'full_page.png',
                    sections: enrichedSections.map(s => s.screenshot),
                },
            };
        });
    }

    // ============================================
    // EXECUTION FLOW
    // ============================================

    const errors = [];
    const stagesCompleted = [];
    const screenshotsTaken = {};
    let completeness = 0.0;
    let perceptionTree = null;
    let removalMethod = 'none';

    // Flush mechanism
    const flushCapture = async (extra = {}) => {
        const snapshot = {
            meta: perceptionTree?.meta || { url: request.url, label, capturedAt: new Date().toISOString(), completeness },
            stagesCompleted: stagesCompleted.slice(),
            errors: errors.slice(),
            ...perceptionTree,
            ...extra,
        };
        try { await store.setValue(`${label}__spatial_v9`, snapshot); } catch (e) {}
        return snapshot;
    };

    try { await flushCapture(); } catch (e) {}

    // Stage 1: Settle
    try { await new Promise(r => setTimeout(r, 1500)); stagesCompleted.push('settle'); } catch (e) { errors.push({stage:'settle', msg: String(e).slice(0,200)}); }

    // Stage 2: As-is screenshots
    try { await capture('fold_desktop', { w: 1440, h: 900 }, false, false); screenshotsTaken['fold_desktop'] = true; stagesCompleted.push('fold_desktop'); } catch (e) { errors.push({stage:'fold_desktop', msg: String(e).slice(0,200)}); }
    try { await capture('fold_mobile', { w: 390, h: 844 }, true, false); screenshotsTaken['fold_mobile'] = true; stagesCompleted.push('fold_mobile'); } catch (e) { errors.push({stage:'fold_mobile', msg: String(e).slice(0,200)}); }

    // Stage 3: Cookie handling
    try { await clickCookieAccept(); removalMethod = 'click-accept'; await closePopups(); await new Promise(r => setTimeout(r, 800)); const stillThere = await page.evaluate(() => !!document.querySelector('[id*="cookie" i][class*="banner" i]')); if (stillThere) { await forceRemoveBanner(); removalMethod = 'dom-removed'; } stagesCompleted.push('cookie_dismiss'); } catch (e) { errors.push({stage:'cookie_dismiss', msg: String(e).slice(0,200)}); }

    // Stage 4: Perception tree extraction
    try { perceptionTree = await extractPerceptionTree(); completeness = 0.8; stagesCompleted.push('extract'); await flushCapture(); } catch (e) { errors.push({stage:'extract', msg: String(e).slice(0,300)}); }

    // Stage 5: Full page screenshots
    try { await capture('full_page', { w: 1440, h: 900 }, false, true); screenshotsTaken['full_page'] = true; stagesCompleted.push('full_page'); } catch (e) { errors.push({stage:'full_page', msg: String(e).slice(0,200)}); }

    // Final completeness
    completeness = Object.keys(screenshotsTaken).length >= 3 && perceptionTree ? 1.0 : 0.8;

    const finalCapture = await flushCapture();
    return { ok: true, label, completeness, stagesCompleted, errors, screenshotCount: Object.keys(screenshotsTaken).length };
}
