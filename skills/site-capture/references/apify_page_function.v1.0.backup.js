// pageFunction pour apify~puppeteer-scraper
// Appelée par scripts/run_capture.py via l'input Apify.
// Retourne un SiteCapture JSON + stocke 6 PNG dans le Key-Value Store.

async function pageFunction(context) {
    const { page, request, log, Apify } = context;
    const label = request.userData.label || 'capture';
    const store = await Apify.openKeyValueStore();
    // Avoid 30s Puppeteer default — setViewport can trigger implicit nav wait
    try { page.setDefaultNavigationTimeout(120000); page.setDefaultTimeout(120000); } catch (e) {}

    // --- Helpers ---
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
        // Fallback text-based
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

    async function detectCookieBannerBeforeClick() {
        // Runs BEFORE clicking accept. Captures the as-is state: presence, selector hit,
        // dimensions, coverage of hero, competing CTAs introduced, CMP detected, CNIL compliance.
        return await page.evaluate(() => {
            // Known CMP fingerprints — ordered by specificity
            const CMPs = [
                { name: 'didomi',    test: () => !!(window.Didomi || document.querySelector('#didomi-host, #didomi-popup, .didomi-popup-container')) },
                { name: 'onetrust',  test: () => !!(window.OneTrust || document.querySelector('#onetrust-banner-sdk, #onetrust-consent-sdk')) },
                { name: 'cookiebot', test: () => !!(window.Cookiebot || document.querySelector('#CybotCookiebotDialog')) },
                { name: 'axeptio',   test: () => !!(window.axeptioSDK || document.querySelector('#axeptio_overlay, #axeptio_main_button')) },
                { name: 'tarteaucitron', test: () => !!(window.tarteaucitron || document.querySelector('#tarteaucitronRoot')) },
                { name: 'osano',     test: () => !!(window.Osano || document.querySelector('.osano-cm-window')) },
                { name: 'quantcast', test: () => !!document.querySelector('#qc-cmp2-container') },
                { name: 'iubenda',   test: () => !!document.querySelector('#iubenda-cs-banner') },
                { name: 'cookieyes', test: () => !!document.querySelector('#cookie-law-info-bar, .cky-consent-container') },
            ];
            let cmpDetected = 'custom';
            for (const cmp of CMPs) { try { if (cmp.test()) { cmpDetected = cmp.name; break; } } catch (e) {} }

            const KEYWORDS = /cookie|consent|rgpd|gdpr|politique de confidentialit|vie priv|traceurs?/i;
            const ACCEPT_PATTERNS = /^(tout accepter|accepter tout|j['’]accepte|j['’]accepte tout|accepter|accept all|i agree|agree|ok pour moi|ok|got it|jai compris|i understand|allow all|enable all|continue|autoriser tout)$/i;
            const REJECT_PATTERNS = /^(tout refuser|refuser tout|je refuse|refuser|reject all|reject|decline|disagree|continue without|refuse all|non merci|disallow)$/i;
            const CUSTOMIZE_PATTERNS = /(personnaliser|paramétrer|gérer|manage|customize|options|préférences|je choisis|settings|mes choix)/i;

            // Selector short list (for fast path) — but we ALSO do a deep walk that finds the real container
            const SELECTORS = [
                '#didomi-host', '#didomi-popup', '.didomi-popup-container',
                '#onetrust-banner-sdk', '#onetrust-consent-sdk',
                '#CybotCookiebotDialog', '#axeptio_overlay', '#tarteaucitronRoot',
                '.osano-cm-window', '#qc-cmp2-container', '#iubenda-cs-banner',
                '#cookie-law-info-bar', '.cky-consent-container',
                '[id*="cookie" i][class*="banner" i]', '[class*="cookie-consent" i]',
                '[class*="cookie-notice" i]', '[class*="cookie-banner" i]',
                '[class*="cookiebar" i]', '[class*="gdpr" i]',
                '[role="dialog"][aria-label*="cookie" i]',
                '[data-testid*="cookie" i]',
            ];
            // Walk DOM including Shadow DOMs (open shadows only)
            const walkAll = function* (root) {
                const stack = [root];
                while (stack.length) {
                    const node = stack.pop();
                    if (!node) continue;
                    yield node;
                    if (node.shadowRoot) stack.push(node.shadowRoot);
                    if (node.children) for (const c of node.children) stack.push(c);
                }
            };
            const isVisible = (el) => {
                try {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 50 && r.height > 20 && s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity) > 0;
                } catch (e) { return false; }
            };

            // STEP 1 — Find every "candidate button" (text = accept/reject/customize)
            const allButtons = [];
            for (const node of walkAll(document.documentElement)) {
                if (!(node instanceof Element)) continue;
                const tag = node.tagName;
                if (tag !== 'BUTTON' && tag !== 'A' && node.getAttribute('role') !== 'button') continue;
                if (!isVisible(node)) continue;
                const txt = (node.innerText || node.textContent || node.getAttribute('aria-label') || '').trim();
                if (!txt || txt.length > 60) continue;
                const kind = ACCEPT_PATTERNS.test(txt) ? 'accept'
                           : REJECT_PATTERNS.test(txt) ? 'reject'
                           : CUSTOMIZE_PATTERNS.test(txt) ? 'customize'
                           : null;
                if (kind) allButtons.push({ el: node, kind, label: txt });
            }

            // STEP 2 — For each accept button, walk up ancestors looking for the smallest container
            // whose innerText also contains the cookie keyword. That container is the real banner.
            let banner = null, hit = null, bannerButtons = [];
            const acceptBtns = allButtons.filter(b => b.kind === 'accept');
            for (const btn of acceptBtns) {
                let cur = btn.el.parentElement;
                let depth = 0;
                while (cur && depth < 12) {
                    const txt = (cur.innerText || cur.textContent || '').slice(0, 1500);
                    if (KEYWORDS.test(txt) && isVisible(cur)) {
                        const r = cur.getBoundingClientRect();
                        // Container must be reasonably large to be a banner (not just the button wrapper)
                        if (r.width > 200 && r.height > 60) {
                            banner = cur;
                            hit = `ancestor-of-accept[${depth}]`;
                            break;
                        }
                    }
                    cur = cur.parentElement;
                    depth++;
                }
                if (banner) break;
            }

            // STEP 3 — Fallback: try known CMP selectors (deep)
            if (!banner) {
                for (const sel of SELECTORS) {
                    for (const node of walkAll(document.documentElement)) {
                        try {
                            if (node.matches && node.matches(sel) && isVisible(node)) {
                                const r = node.getBoundingClientRect();
                                if (r.width > 200 && r.height > 60) { banner = node; hit = `selector:${sel}`; break; }
                            }
                        } catch (e) {}
                    }
                    if (banner) break;
                }
            }

            // STEP 4 — Fallback: any visible fixed/sticky element with cookie text
            if (!banner) {
                for (const el of walkAll(document.documentElement)) {
                    if (!(el instanceof Element)) continue;
                    let s; try { s = getComputedStyle(el); } catch (e) { continue; }
                    if (!s || (s.position !== 'fixed' && s.position !== 'sticky')) continue;
                    const r = el.getBoundingClientRect();
                    if (r.width < 200 || r.height < 60) continue;
                    const txt = (el.innerText || el.textContent || '').slice(0, 800);
                    if (KEYWORDS.test(txt)) { banner = el; hit = 'text-based-fixed'; break; }
                }
            }

            // STEP 5 — If we found a banner, collect the buttons inside it
            if (banner) {
                for (const b of allButtons) {
                    if (banner.contains(b.el)) bannerButtons.push({ kind: b.kind, label: b.label });
                }
            }
            if (!banner) return { present: false, cmpDetected };

            const r = banner.getBoundingClientRect();
            const vw = window.innerWidth, vh = window.innerHeight;
            const coversHero = (r.top < vh * 0.6) && (r.width * r.height) > (vw * vh * 0.15);
            const position = getComputedStyle(banner).position;
            const blocksCTA = (position === 'fixed' || position === 'sticky') && r.height > vh * 0.4;
            const coveragePct = Math.round(((r.width * r.height) / (vw * vh)) * 100);

            const hasAcceptAll = bannerButtons.some(b => b.kind === 'accept');
            const hasRejectAll = bannerButtons.some(b => b.kind === 'reject');
            const hasGranular  = bannerButtons.some(b => b.kind === 'customize');

            // CRO / legal issues
            const croIssues = [];
            if (hasAcceptAll && !hasRejectAll) croIssues.push('no-reject-all-button-cnil-risk');
            if (coversHero) croIssues.push('covers-hero-atf');
            if (coveragePct > 30) croIssues.push('large-coverage');
            if (blocksCTA) croIssues.push('blocks-interaction');
            if (bannerButtons.length > 3) croIssues.push('too-many-competing-ctas');

            return {
                present: true,
                cmpDetected,
                selectorHit: hit,
                position,
                boundingBox: { top: Math.round(r.top), left: Math.round(r.left), width: Math.round(r.width), height: Math.round(r.height) },
                coveragePct,
                coversHero,
                blocksCTA,
                hasAcceptAll,
                hasRejectAllButton: hasRejectAll,
                hasGranularChoice: hasGranular,
                competingCtas: bannerButtons,
                innerTextSnippet: (banner.innerText || '').trim().slice(0, 250),
                croIssues,
            };
        });
    }

    async function forceRemoveBanner() {
        // Last-resort fallback: remove any banner-like element from DOM so the clean capture is truly clean
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

    // --- Extract structured data (runs in the clean state) ---
    async function extract() {
        return await page.evaluate(() => {
            const abs = (h) => { try { return new URL(h, location.href).href; } catch (e) { return h; } };
            const visible = (el) => {
                const r = el.getBoundingClientRect();
                const s = getComputedStyle(el);
                return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity) > 0;
            };
            const inFold = (el) => {
                const r = el.getBoundingClientRect();
                return r.top < window.innerHeight && r.bottom > 0;
            };

            const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4'))
                .filter(visible)
                .map((h, i) => ({ level: +h.tagName[1], text: (h.innerText || '').trim(), order: i + 1 }));

            const h1s = headings.filter(h => h.level === 1);
            const h1 = h1s.length ? h1s[0].text : '';

            // subtitle = plus gros texte sous le premier h1 dans le fold
            let subtitle = '';
            const firstH1El = document.querySelector('h1');
            if (firstH1El) {
                const sib = firstH1El.parentElement ? Array.from(firstH1El.parentElement.querySelectorAll('p,h2,h3,div')).filter(visible).filter(inFold) : [];
                const cand = sib.find(e => (e.innerText || '').trim().length > 10);
                if (cand) subtitle = (cand.innerText || '').trim().slice(0, 240);
            }

            // CTAs — extraction enrichie + scoring multi-signaux
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
            const pageBgColor = parseColor(getComputedStyle(document.body).backgroundColor) || [255, 255, 255];
            const pageBgLum = luminance(pageBgColor);
            // Get effective background: walk up parents until a non-transparent bg is found
            const effectiveBg = (el) => {
                let cur = el;
                for (let i = 0; i < 10 && cur; i++) {
                    const s = getComputedStyle(cur);
                    const m = (s.backgroundColor || '').match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
                    if (m) {
                        const alpha = m[4] === undefined ? 1 : parseFloat(m[4]);
                        if (alpha > 0.1) return [+m[1], +m[2], +m[3]];
                    }
                    cur = cur.parentElement;
                }
                return pageBgColor;
            };

            const ctaEls = Array.from(document.querySelectorAll('a,button,[role="button"]')).filter(visible);
            const ctas = ctaEls.map(el => {
                const r = el.getBoundingClientRect();
                const s = getComputedStyle(el);
                const bg = effectiveBg(el);
                const fg = parseColor(s.color);
                const contrastVsPage = contrastRatio(luminance(bg), pageBgLum);
                const contrastText = fg ? contrastRatio(luminance(bg), luminance(fg)) : 1;
                const cls = (el.className || '').toString().toLowerCase();
                const href = el.tagName === 'A' ? (el.getAttribute('href') || '') : '';
                return {
                    label: (el.innerText || el.getAttribute('aria-label') || '').trim(),
                    href: href ? abs(href) : null,
                    rawHref: href,
                    tag: el.tagName.toLowerCase(),
                    classes: cls.slice(0, 120),
                    surface: Math.round(r.width * r.height),
                    width: Math.round(r.width),
                    height: Math.round(r.height),
                    inFold: inFold(el),
                    top: Math.round(r.top),
                    bgColor: `rgb(${bg.join(',')})`,
                    contrastVsPage: Math.round(contrastVsPage * 10) / 10,
                    contrastText: Math.round(contrastText * 10) / 10,
                };
            }).filter(c => c.label && c.label.length < 80 && c.label.length > 1);

            // Multi-signal CTA scoring (0-100)
            // Apostrophes droites et courbes + "j'" collé
            const actionVerbs = /(^|[\s'’])(je |j['’]|créer|créez|commencer|commence|démarrer|démarre|découvrir|découvre|essaie|essayer|essaye|obtenir|obtenez|lancer|tester|teste|choisir|choisis|configurer|configure|calculer|calcule|réserver|réserve|télécharger|recevoir|m['’]inscrire|inscris|s['’]inscrire|rejoindre|voir|get |start |try |create |begin |claim |book |join |download |sign up|build |make |choose |discover |launch )/i;
            const weakVerbs = /^(en savoir plus|en savoir|lire|learn more|read more|→|>|plus|more)$/i;
            const promoPatterns = /(-\d+\s*%|offre|promo|gratuit|free|\d+\s*%\s*off|solde)/i;
            const actionHrefs = /(signup|sign-up|register|profile-builder|onboard|checkout|trial|devis|quote|contact|inscription|reserver|book|start|demo|get-started|\/#form|#form|\/app)/i;
            const primaryClasses = /(btn-primary|button-primary|cta-primary|main-cta|primary-button|btn--primary)/;

            const foldCtas = ctas.filter(c => c.inFold);
            const maxFoldSurface = Math.max(1, ...foldCtas.map(c => c.surface));
            const foldWidth = window.innerWidth;

            foldCtas.forEach(c => {
                let score = 0;
                const reasons = [];
                // inFold is a prerequisite (already filtered)
                score += 30; reasons.push('inFold+30');
                if (actionVerbs.test(c.label)) { score += 20; reasons.push('actionVerb+20'); }
                if (weakVerbs.test(c.label.trim())) { score -= 15; reasons.push('weakVerb-15'); }
                if (c.contrastVsPage >= 2.0) { score += 15; reasons.push('contrast+15'); }
                if (c.surface >= maxFoldSurface * 0.5) { score += 15; reasons.push('bigSize+15'); }
                if (c.rawHref && actionHrefs.test(c.rawHref)) { score += 10; reasons.push('actionHref+10'); }
                if (primaryClasses.test(c.classes)) { score += 10; reasons.push('primaryClass+10'); }
                if (c.tag === 'button') { score += 3; reasons.push('button+3'); }
                // Disqualifiants
                if (promoPatterns.test(c.label)) { score = Math.round(score * 0.3); reasons.push('promo×0.3'); }
                if (c.width > foldWidth * 0.8) { score = Math.round(score * 0.5); reasons.push('fullWidth×0.5'); }
                if (c.label.length < 3) { score = 0; reasons.push('tooShort=0'); }
                c.primaryScore = score;
                c.primaryScoreReasons = reasons;
            });

            foldCtas.sort((a, b) => b.primaryScore - a.primaryScore);
            const primary = foldCtas[0] || null;
            if (primary) primary.isPrimary = true;
            const secondary = foldCtas[1] || null;
            if (secondary) secondary.isSecondary = true;

            // Social proof in fold
            const foldText = (document.body.innerText || '').slice(0, 3000);
            const trustpilot = !!document.querySelector('[class*="trustpilot" i], iframe[src*="trustpilot" i]');
            const judgeme = !!document.querySelector('[class*="jdgm" i], [class*="judgeme" i]');
            const starsMatch = foldText.match(/(\d[.,]\d)\s*\/\s*5/);
            const countMatch = foldText.match(/(\d[\d\s]{1,6})\s*(avis|reviews|clients|customers|utilisateurs|users)/i);
            const socialProofInFold = {
                present: !!(trustpilot || judgeme || starsMatch || countMatch),
                type: trustpilot ? 'trustpilot_widget' : judgeme ? 'judgeme_widget' : starsMatch ? 'stars_text' : countMatch ? 'count_text' : null,
                snippet: [trustpilot && 'Trustpilot', judgeme && 'Judge.me', starsMatch && starsMatch[0], countMatch && countMatch[0]].filter(Boolean).join(' | '),
            };

            // Trust widgets details
            const reviewCounts = Array.from(foldText.matchAll(/\d[\d\s]{1,6}\s*(?:avis|reviews)/gi)).map(m => m[0]).slice(0, 5);

            // Testimonials (basique)
            const testimonials = Array.from(document.querySelectorAll('[class*="testimonial" i], [class*="review" i], blockquote')).slice(0, 10).map(el => ({
                text: (el.innerText || '').trim().slice(0, 240),
                hasPhoto: !!el.querySelector('img'),
            })).filter(t => t.text.length > 20);

            // Overlays
            const cookieBanner = !!document.querySelector('#didomi-host, #onetrust-banner-sdk, [id*="cookie" i][class*="banner" i], [class*="cookie-consent" i]');
            const chatWidgets = [];
            if (document.querySelector('iframe[src*="intercom" i], .intercom-launcher')) chatWidgets.push({ type: 'intercom' });
            if (document.querySelector('#hubspot-messages-iframe-container')) chatWidgets.push({ type: 'hubspot' });
            if (document.querySelector('#crisp-chatbox')) chatWidgets.push({ type: 'crisp' });

            // Forms
            const forms = Array.from(document.querySelectorAll('form')).slice(0, 10).map(f => ({
                fields: Array.from(f.querySelectorAll('input,select,textarea')).map(i => i.getAttribute('name') || i.getAttribute('type')).filter(Boolean),
                submitLabel: ((f.querySelector('button[type="submit"], input[type="submit"]') || {}).innerText || '').trim(),
            }));

            // Meta / tech
            const meta = {
                title: document.title,
                metaDescription: (document.querySelector('meta[name="description"]') || {}).content || '',
                lang: document.documentElement.lang,
                viewport: (document.querySelector('meta[name="viewport"]') || {}).content || '',
                ogTitle: (document.querySelector('meta[property="og:title"]') || {}).content || '',
                ogImage: (document.querySelector('meta[property="og:image"]') || {}).content || '',
                schemaOrg: Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map(s => { try { const j = JSON.parse(s.innerText); return j['@type'] || (Array.isArray(j) ? j[0] && j[0]['@type'] : null); } catch (e) { return null; } }).filter(Boolean),
                domNodes: document.querySelectorAll('*').length,
            };

            // Hero images
            const heroImgs = Array.from(document.querySelectorAll('img')).filter(visible).filter(inFold).slice(0, 5).map(i => ({
                src: abs(i.currentSrc || i.src || ''),
                alt: i.alt || '',
                width: i.naturalWidth, height: i.naturalHeight,
            }));

            return {
                hero: { h1, h1Count: h1s.length, subtitle, ctas: foldCtas.slice(0, 8), primaryCta: primary, heroImages: heroImgs, socialProofInFold },
                structure: { headings, ctas: ctas.slice(0, 60), forms },
                socialProof: { trustWidgets: [trustpilot && { type: 'trustpilot' }, judgeme && { type: 'judgeme' }].filter(Boolean), testimonials, reviewCounts },
                overlays: { cookieBanner: { present: cookieBanner }, chatWidgets },
                technical: meta,
            };
        });
    }

    // --- Flow ---
    await new Promise(r => setTimeout(r, 1500));

    // AS-IS captures
    await capture('desktop_asis_fold', { w: 1440, h: 900 }, false, false);
    await capture('mobile_asis_fold',  { w: 390, h: 844 },  true,  false);

    // Detect cookie banner BEFORE clicking accept (so we keep the as-is signal)
    await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2, isMobile: false });
    await page.evaluate(() => window.scrollTo(0, 0));
    const cookieBannerAsIs = await detectCookieBannerBeforeClick();

    // Try to dismiss: click accept → fallback DOM removal
    let removalMethod = 'none';
    const cookieAccepted = await clickCookieAccept();
    if (cookieAccepted) removalMethod = 'click-accept';
    await closePopups();
    await new Promise(r => setTimeout(r, 800));
    // Verify banner is gone; if not, force-remove from DOM
    const stillThere = await detectCookieBannerBeforeClick();
    if (stillThere && stillThere.present) {
        const removed = await forceRemoveBanner();
        if (removed > 0) removalMethod = 'dom-removed';
    }
    await new Promise(r => setTimeout(r, 400));

    const data = await extract();
    // Override the (post-click) cookie banner detection with the as-is one + removal metadata
    data.overlays.cookieBanner = { ...cookieBannerAsIs, removalMethod };

    await capture('desktop_clean_fold', { w: 1440, h: 900 }, false, false);
    await capture('desktop_clean_full', { w: 1440, h: 900 }, false, true);
    await capture('mobile_clean_fold',  { w: 390, h: 844 },  true,  false);
    await capture('mobile_clean_full',  { w: 390, h: 844 },  true,  true);

    // Raw HTML
    const html = await page.content();
    await store.setValue(`${label}__html`, html, { contentType: 'text/html' });

    const capture_json = {
        meta: {
            url: request.url,
            label,
            capturedAt: new Date().toISOString(),
            finalUrl: page.url(),
            title: data.technical.title,
            metaDescription: data.technical.metaDescription,
        },
        hero: data.hero,
        structure: data.structure,
        socialProof: data.socialProof,
        overlays: data.overlays,
        technical: data.technical,
        screenshots: {
            desktop_asis_fold: `${label}__desktop_asis_fold`,
            desktop_clean_fold: `${label}__desktop_clean_fold`,
            desktop_clean_full: `${label}__desktop_clean_full`,
            mobile_asis_fold: `${label}__mobile_asis_fold`,
            mobile_clean_fold: `${label}__mobile_clean_fold`,
            mobile_clean_full: `${label}__mobile_clean_full`,
        },
        rawHtml: `${label}__html`,
    };

    await store.setValue(`${label}__capture`, capture_json);
    return { ok: true, label, keys: Object.keys(capture_json.screenshots) };
}
