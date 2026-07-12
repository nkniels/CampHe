document.addEventListener('DOMContentLoaded', () => {
    // Register Service Worker
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('./sw.js').then(registration => {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
            }, err => {
                console.log('ServiceWorker registration failed: ', err);
            });
        });
    }

    const grid = document.getElementById('campaign-grid');

    // Fetch campaign data
    async function fetchCampaigns() {
        try {
            // Give a slight delay to show off the skeleton loading animation
            await new Promise(r => setTimeout(r, 800));
            
            // Generate a random query parameter to prevent caching for dev purpose
            const noCacheUrl = './data/campaigns.json?t=' + new Date().getTime();
            const response = await fetch(noCacheUrl);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            renderCampaigns(data);
        } catch (error) {
            console.error('Failed to fetch campaigns:', error);
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; color: var(--cam-red);">
                    Failed to load campaigns. Please try again later.
                </div>
            `;
        }
    }

    function renderCampaigns(campaigns) {
        grid.innerHTML = ''; // Clear skeletons

        if (campaigns.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted);">
                    No health campaigns currently available.
                </div>
            `;
            return;
        }

        campaigns.forEach(campaign => {
            const card = document.createElement('div');
            card.className = 'glass-card';

            // SVG icon strings
            const locationIcon = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`;
            const calendarIcon = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`;
            const arrowIcon = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>`;

            const status = campaign.status || 'unknown';
            const sourceName = campaign.source_name || '';
            const rawLink = campaign.link || '';
            const date = campaign.date || 'Date TBC';

            // Only show "Read More" for valid absolute URLs (http/https)
            const isValidLink = rawLink.startsWith('http://') || rawLink.startsWith('https://');
            const link = isValidLink ? rawLink : '';

            // Build card footer — show source tag and a "Read More" link if available
            const footerHTML = `
                <div class="card-footer">
                    ${sourceName ? `<div class="source-tag"><span>📡 ${sourceName}</span></div>` : '<div></div>'}
                    ${link
                        ? `<a class="read-more" href="${link}" target="_blank" rel="noopener noreferrer">
                               Read more ${arrowIcon}
                           </a>`
                        : ''}
                </div>
            `;

            card.innerHTML = `
                <div class="card-header">
                    <h4 class="card-title">${campaign.title}</h4>
                    <span class="badge ${status}">${status}</span>
                </div>
                <div class="card-meta">
                    <span>${locationIcon} ${campaign.location || 'Cameroun'}</span>
                    <span>${calendarIcon} ${date}</span>
                </div>
                <p class="card-desc">${campaign.description || ''}</p>
                ${footerHTML}
            `;

            grid.appendChild(card);
        });
    }

    fetchCampaigns();
});
