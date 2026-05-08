// apify_discover_function.js — pageFunction pour apify~puppeteer-scraper
// Objectif : découvrir TOUTES les pages navigables d'un site.
// Légère : pas de screenshots, pas d'extraction CRO. Juste les liens.
//
// Stratégie :
// 1. Charger la home (JS exécuté)
// 2. Trouver tous les éléments de navigation (header, nav, footer)
// 3. Pour chaque lien avec dropdown/submenu : hover → attendre le menu → extraire les liens enfants
// 4. Collecter TOUS les liens internes avec contexte (anchorText, region, depth)
// 5. Retourner la liste structurée

async function pageFunction(context) {
    const { page, request, log } = context;
    const label = request.userData.label || 'discover';

    try { page.setDefaultNavigationTimeout(60000); page.setDefaultTimeout(30000); } catch (e) {}

    // Wait for page to be reasonably loaded
    await new Promise(r => setTimeout(r, 3000));

    // --- Cookie dismiss (same logic as main capture, keep it simple) ---
    try {
        const cookieSelectors = [
            '#didomi-notice-agree-button',
            '#onetrust-accept-btn-handler',
            'button[id*="accept" i]',
            'button[class*="accept" i]',
            'button[aria-label*="accepter" i]',
            'button[aria-label*="accept" i]',
        ];
        for (const sel of cookieSelectors) {
            const el = await page.$(sel);
            if (el) { await el.click({ delay: 50 }); await new Promise(r => setTimeout(r, 800)); break; }
        }
    } catch (e) { log.info('Cookie dismiss failed (non-blocking): ' + e.message); }

    // === PHASE 1 : Extraire tous les liens visibles AVANT interaction ===
    const staticLinks = await page.evaluate(() => {
        const results = [];
        const seen = new Set();
        const rootHost = location.hostname.replace(/^www\./, '');

        function isInternal(href) {
            try {
                const u = new URL(href, location.origin);
                return u.hostname.replace(/^www\./, '') === rootHost;
            } catch { return false; }
        }

        function cleanUrl(href) {
            try {
                const u = new URL(href, location.origin);
                // Strip query params and hash for dedup
                return u.origin + u.pathname.replace(/\/$/, '') || '/';
            } catch { return null; }
        }

        function getRegion(el) {
            let node = el;
            for (let i = 0; i < 10 && node; i++) {
                const tag = (node.tagName || '').toLowerCase();
                if (tag === 'header' || tag === 'nav') return 'header';
                if (tag === 'footer') return 'footer';
                const role = (node.getAttribute('role') || '').toLowerCase();
                if (role === 'navigation') return 'header';
                if (role === 'contentinfo') return 'footer';
                // Common class patterns
                const cls = (node.className || '').toString().toLowerCase();
                if (cls.includes('header') || cls.includes('navbar') || cls.includes('nav-main') || cls.includes('main-nav')) return 'header';
                if (cls.includes('footer')) return 'footer';
                node = node.parentElement;
            }
            return 'body';
        }

        document.querySelectorAll('a[href]').forEach(a => {
            const href = a.getAttribute('href');
            if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) return;
            const absoluteHref = new URL(href, location.origin).href;
            if (!isInternal(absoluteHref)) return;
            const clean = cleanUrl(absoluteHref);
            if (!clean || seen.has(clean)) return;
            seen.add(clean);

            const text = (a.innerText || a.textContent || '').trim().substring(0, 100);
            const region = getRegion(a);
            const ariaLabel = a.getAttribute('aria-label') || '';

            results.push({
                url: clean,
                anchorText: text || ariaLabel,
                region: region,
                phase: 'static',
            });
        });

        return results;
    });

    log.info(`Phase 1 (static): ${staticLinks.length} internal links found`);

    // === PHASE 2 : Interagir avec les menus dropdown ===
    // Trouver tous les éléments de navigation qui ont des sous-menus (hover ou click)
    const dropdownLinks = await page.evaluate(async () => {
        const results = [];
        const seen = new Set();
        const rootHost = location.hostname.replace(/^www\./, '');

        function isInternal(href) {
            try { return new URL(href, location.origin).hostname.replace(/^www\./, '') === rootHost; }
            catch { return false; }
        }
        function cleanUrl(href) {
            try { const u = new URL(href, location.origin); return u.origin + (u.pathname.replace(/\/$/, '') || '/'); }
            catch { return null; }
        }

        // Find nav trigger elements: buttons/links in header/nav with aria-expanded, dropdown indicators
        const navRegion = document.querySelector('header, nav, [role="navigation"]');
        if (!navRegion) return results;

        // Strategy: find all interactive elements that might trigger dropdowns
        const triggers = navRegion.querySelectorAll([
            'button[aria-expanded]',
            'a[aria-expanded]',
            '[class*="dropdown" i] > a',
            '[class*="dropdown" i] > button',
            '[class*="menu" i] > li > a',
            '[class*="nav" i] > li > a',
            'li[class*="has-sub" i] > a',
            'li[class*="has-children" i] > a',
            'li[class*="dropdown" i] > a',
            // Generic: any direct child link of a nav list item
            'nav li > a',
            'header li > a',
        ].join(', '));

        return { triggerCount: triggers.length };
    });

    log.info(`Found ${dropdownLinks.triggerCount || 0} potential dropdown triggers`);

    // Phase 2b: Hover each nav item to reveal dropdowns, then extract new links
    const hoverLinks = await page.evaluate(async () => {
        const results = [];
        const seenBefore = new Set();
        const rootHost = location.hostname.replace(/^www\./, '');

        function isInternal(href) {
            try { return new URL(href, location.origin).hostname.replace(/^www\./, '') === rootHost; }
            catch { return false; }
        }
        function cleanUrl(href) {
            try { const u = new URL(href, location.origin); return u.origin + (u.pathname.replace(/\/$/, '') || '/'); }
            catch { return null; }
        }

        // Snapshot current links
        document.querySelectorAll('a[href]').forEach(a => {
            const clean = cleanUrl(a.getAttribute('href'));
            if (clean) seenBefore.add(clean);
        });

        // Find top-level nav items in header
        const navRegion = document.querySelector('header') || document.querySelector('nav') || document.querySelector('[role="navigation"]');
        if (!navRegion) return results;

        // Get all top-level list items that might have submenus
        const topItems = navRegion.querySelectorAll('li, [class*="nav-item" i], [class*="menu-item" i]');

        for (const item of topItems) {
            // Simulate hover by dispatching mouseenter/mouseover
            item.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
            item.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));

            // Also try click on buttons with aria-expanded="false"
            const expandBtn = item.querySelector('button[aria-expanded="false"], a[aria-expanded="false"]');
            if (expandBtn) {
                try { expandBtn.click(); } catch (e) {}
            }

            // Small wait for CSS transitions / JS to reveal submenu
            await new Promise(r => setTimeout(r, 300));

            // Check for newly visible links
            const subLinks = item.querySelectorAll('a[href]');
            for (const a of subLinks) {
                const href = a.getAttribute('href');
                if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) continue;
                if (!isInternal(new URL(href, location.origin).href)) continue;
                const clean = cleanUrl(href);
                if (!clean || seenBefore.has(clean)) continue;
                seenBefore.add(clean);

                const text = (a.innerText || a.textContent || '').trim().substring(0, 100);
                // Check if this link is actually visible now
                const rect = a.getBoundingClientRect();
                const visible = rect.width > 0 && rect.height > 0;

                if (visible || text) {
                    results.push({
                        url: clean,
                        anchorText: text,
                        region: 'header_dropdown',
                        phase: 'hover',
                        parentText: (item.querySelector(':scope > a, :scope > button') || {}).innerText?.trim()?.substring(0, 50) || '',
                    });
                }
            }

            // Reset hover
            item.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true }));

            // Close any expanded
            if (expandBtn) {
                const expanded = item.querySelector('button[aria-expanded="true"], a[aria-expanded="true"]');
                if (expanded) try { expanded.click(); } catch (e) {}
            }

            await new Promise(r => setTimeout(r, 100));
        }

        return results;
    });

    log.info(`Phase 2 (hover): ${hoverLinks.length} additional links from dropdowns`);

    // === PHASE 3 : Fetch sitemap.xml ===
    let sitemapLinks = [];
    try {
        const sitemapUrl = new URL('/sitemap.xml', request.url).href;
        const sitemapResp = await page.evaluate(async (url) => {
            try {
                const resp = await fetch(url, { redirect: 'follow' });
                if (!resp.ok) return null;
                const text = await resp.text();
                // Extract <loc> tags
                const locs = [];
                const regex = /<loc>\s*(.*?)\s*<\/loc>/gi;
                let m;
                while ((m = regex.exec(text)) !== null) {
                    const loc = m[1].trim();
                    if (!loc.endsWith('.xml')) locs.push(loc); // Skip sub-sitemaps
                }
                return locs;
            } catch { return null; }
        }, sitemapUrl);

        if (sitemapResp && sitemapResp.length > 0) {
            const rootHost = new URL(request.url).hostname.replace(/^www\./, '');
            const seenAll = new Set([...staticLinks.map(l => l.url), ...hoverLinks.map(l => l.url)]);

            for (const loc of sitemapResp) {
                try {
                    const u = new URL(loc);
                    if (u.hostname.replace(/^www\./, '') !== rootHost) continue;
                    const clean = u.origin + (u.pathname.replace(/\/$/, '') || '/');
                    if (seenAll.has(clean)) continue;
                    seenAll.add(clean);
                    sitemapLinks.push({
                        url: clean,
                        anchorText: '',
                        region: 'sitemap',
                        phase: 'sitemap',
                    });
                } catch {}
            }
            log.info(`Phase 3 (sitemap): ${sitemapLinks.length} additional unique URLs`);
        } else {
            log.info('Phase 3 (sitemap): not found or empty');
        }
    } catch (e) {
        log.info('Phase 3 (sitemap): fetch failed — ' + e.message);
    }

    // === MERGE & RETURN ===
    const allLinks = [...staticLinks, ...hoverLinks, ...sitemapLinks];

    // Deduplicate by URL (keep first occurrence = highest priority source)
    const deduped = [];
    const seenFinal = new Set();
    for (const link of allLinks) {
        if (!seenFinal.has(link.url)) {
            seenFinal.add(link.url);
            deduped.push(link);
        }
    }

    log.info(`TOTAL: ${deduped.length} unique internal links (static: ${staticLinks.length}, hover: ${hoverLinks.length}, sitemap: ${sitemapLinks.length})`);

    return {
        label,
        url: request.url,
        discoveredAt: new Date().toISOString(),
        stats: {
            staticLinks: staticLinks.length,
            hoverLinks: hoverLinks.length,
            sitemapLinks: sitemapLinks.length,
            total: deduped.length,
        },
        links: deduped,
    };
}
