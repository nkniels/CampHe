document.addEventListener('DOMContentLoaded', () => {

    const grid = document.getElementById('campaign-grid');

    // ── Detail Drawer ──────────────────────────────────────
    const detailOverlay  = document.getElementById('detail-overlay');
    const detailDrawer   = document.getElementById('detail-drawer');
    const detailCloseBtn = document.getElementById('detail-close-btn');

    function openDetail(campaign) {
        const status   = campaign.status   || 'unknown';
        const category = campaign.category || 'general';
        const link     = (campaign.link || '').startsWith('http') ? campaign.link : null;

        document.getElementById('detail-title').textContent        = campaign.title || '—';
        document.getElementById('detail-location').textContent     = campaign.location || '—';
        document.getElementById('detail-date').textContent         = campaign.date || 'Date TBC';
        document.getElementById('detail-status').textContent       = status.charAt(0).toUpperCase() + status.slice(1);
        document.getElementById('detail-description').textContent  = campaign.description || 'No description available.';
        document.getElementById('detail-category-tag').textContent = category.charAt(0).toUpperCase() + category.slice(1);

        const badge = document.getElementById('detail-badge');
        badge.className   = `badge ${status}`;
        badge.textContent = status;

        const participateEl = document.getElementById('detail-participate');
        participateEl.innerHTML = `
            <strong>Comment participer / s'inscrire ?</strong><br>
            Les modalités de participation (lieux exacts, contacts, documents requis) sont spécifiques à chaque campagne. 
            Veuillez lire la description ci-dessus ou cliquer sur le bouton <b>"Source Originale"</b> ci-dessous pour accéder aux instructions officielles.
        `;

        const sourceEl     = document.getElementById('detail-source');
        const sourceNameEl = document.getElementById('detail-source-name');
        if (campaign.source_name) {
            sourceNameEl.textContent = `Source: ${campaign.source_name}`;
            sourceEl.style.display   = 'flex';
        } else {
            sourceEl.style.display   = 'none';
        }

        const linkBtn = document.getElementById('detail-link-btn');
        if (link) {
            linkBtn.href          = link;
            linkBtn.style.display = 'flex';
        } else {
            linkBtn.style.display = 'none';
        }

        detailOverlay.style.display = 'block';
        setTimeout(() => detailOverlay.classList.add('show'), 10);
        detailDrawer.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function closeDetail() {
        detailOverlay.classList.remove('show');
        detailDrawer.classList.remove('open');
        setTimeout(() => {
            detailOverlay.style.display = 'none';
            document.body.style.overflow = '';
        }, 380);
    }

    detailCloseBtn.addEventListener('click', closeDetail);
    detailOverlay.addEventListener('click', closeDetail);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDetail(); });

    // ── Campaign Fetch & Render ────────────────────────────
    async function fetchCampaigns() {
        try {
            await new Promise(r => setTimeout(r, 800));
            // Use local path so Firebase instant deploy makes it immediately available, 
            // bypassing the 5-minute GitHub raw CDN cache.
            const response = await fetch('./data/campaigns.json?t=' + Date.now());
            if (!response.ok) throw new Error('Network response was not ok');
            renderCampaigns(await response.json());
        } catch (error) {
            console.error('Failed to fetch campaigns:', error);
            grid.innerHTML = `
                <div style="grid-column:1/-1;text-align:center;color:var(--cam-red);padding:3rem;">
                    Failed to load campaigns. Please try again later.
                </div>`;
        }
    }

    function renderCampaigns(campaigns) {
        grid.innerHTML = '';

        if (!campaigns.length) {
            grid.innerHTML = `
                <div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:3rem;">
                    No health campaigns currently available.
                </div>`;
            return;
        }

        const locIcon  = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`;
        const calIcon  = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`;
        const arrIcon  = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>`;

        campaigns.forEach(campaign => {
            const card       = document.createElement('div');
            card.className   = 'glass-card';
            const status     = campaign.status || 'unknown';
            const sourceName = campaign.source_name || '';
            const date       = campaign.date || 'Date TBC';

            card.innerHTML = `
                <div class="card-header">
                    <h4 class="card-title">${campaign.title}</h4>
                    <span class="badge ${status}">${status}</span>
                </div>
                <div class="card-meta">
                    <span>${locIcon} ${campaign.location || 'Cameroun'}</span>
                    <span>${calIcon} ${date}</span>
                </div>
                <p class="card-desc">${campaign.description || ''}</p>
                <div class="card-footer">
                    ${sourceName ? `<div class="source-tag"><span>📡 ${sourceName}</span></div>` : '<div></div>'}
                    <span class="read-more">Details ${arrIcon}</span>
                </div>`;

            card.addEventListener('click', () => openDetail(campaign));
            grid.appendChild(card);
        });
    }

    fetchCampaigns();
});
