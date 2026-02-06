document.addEventListener('DOMContentLoaded', () => {
    // --- Local Dev Delete Button ---
    const isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    if (isLocal) {
        document.body.classList.add('local-dev');

        const modal = document.getElementById('deleteModal');
        const modalFile = document.getElementById('deleteModalFile');
        const cancelBtn = document.getElementById('deleteCancelBtn');
        const confirmBtn = document.getElementById('deleteConfirmBtn');
        let pendingFile = '';

        function openDeleteModal(file) {
            pendingFile = file;
            if (modalFile) modalFile.textContent = file ? `File: ${file}` : '';
            if (modal) {
                modal.classList.add('visible');
                modal.setAttribute('aria-hidden', 'false');
                document.body.style.overflow = 'hidden';
            }
        }

        function closeDeleteModal() {
            pendingFile = '';
            if (modal) {
                modal.classList.remove('visible');
                modal.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
            }
        }

        async function confirmDelete() {
            const file = pendingFile;
            if (!file) return;

            try {
                const res = await fetch('/__delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file })
                });

                if (!res.ok) {
                    const text = await res.text();
                    alert(`Delete failed: ${text}`);
                    closeDeleteModal();
                    return;
                }

                window.location.reload();
            } catch (err) {
                alert(`Delete failed: ${err}`);
                closeDeleteModal();
            }
        }

        document.querySelectorAll('.tweet-delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const file = btn.getAttribute('data-file');
                if (!file) return;
                openDeleteModal(file);
            });
        });

        if (cancelBtn) cancelBtn.addEventListener('click', closeDeleteModal);
        if (confirmBtn) confirmBtn.addEventListener('click', confirmDelete);

        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeDeleteModal();
            });
        }

        document.addEventListener('keydown', (e) => {
            if (!modal || !modal.classList.contains('visible')) return;
            if (e.key === 'Escape') closeDeleteModal();
        });
    }

    // --- Modal Logic ---
    const tagsToggle = document.getElementById('tagsToggle');
    const archiveToggle = document.getElementById('archiveToggle');
    const modelStatusToggle = document.getElementById('modelStatusToggle');

    const tagsModal = document.getElementById('tagsModal');
    const archiveModal = document.getElementById('archiveModal');
    const modelStatusModal = document.getElementById('modelStatusModal');

    const closeBtns = document.querySelectorAll('.close-modal');

    function openModal(modal) {
        if (!modal) return;
        modal.classList.add('visible');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        document.querySelectorAll('.modal').forEach(m => m.classList.remove('visible'));
        document.body.style.overflow = '';
    }

    if (tagsToggle) tagsToggle.addEventListener('click', () => openModal(tagsModal));
    if (archiveToggle) archiveToggle.addEventListener('click', () => openModal(archiveModal));
    if (modelStatusToggle) modelStatusToggle.addEventListener('click', () => {
        openModal(modelStatusModal);
        loadModelStatus();
    });

    closeBtns.forEach(btn => btn.addEventListener('click', closeModal));
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) closeModal();
    });

    // --- Model Status ---
    const modelStatusIndicator = document.getElementById('modelStatusIndicator');
    const modelStatusMeta = document.getElementById('modelStatusMeta');
    const modelStatusTable = document.getElementById('modelStatusTable');

    async function loadModelStatus() {
        if (!modelStatusMeta || !modelStatusTable) return;
        modelStatusMeta.textContent = 'Loading...';
        try {
            // Detect if we're on a date page (in /date/ subdirectory)
            const isDatePage = window.location.pathname.includes('/date/');
            const jsonPath = isDatePage ? '../model-status.json' : 'model-status.json';
            const res = await fetch(jsonPath, { cache: 'no-store' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const summary = data.summary || {};
            modelStatusMeta.textContent = `Last updated: ${data.generated_at || 'unknown'} | Total: ${summary.total || 0} | Passed: ${summary.passed || 0} | Failed: ${summary.failed || 0}`;

            const rows = (data.results || []).map(r => {
                const badgeClass = r.success ? 'ok' : 'fail';
                const badgeText = r.success ? 'OK' : 'FAIL';
                return `
                    <tr>
                        <td>${r.provider}</td>
                        <td>${r.model}</td>
                        <td><span class="model-status-badge ${badgeClass}">${badgeText}</span></td>
                        <td>${r.status}</td>
                        <td>${r.response || ''}</td>
                    </tr>
                `;
            }).join('');

            modelStatusTable.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Provider</th>
                            <th>Model</th>
                            <th>Status</th>
                            <th>Detail</th>
                            <th>Response</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows || '<tr><td colspan="5">No data</td></tr>'}
                    </tbody>
                </table>
            `;

            updateModelIndicator(summary);
        } catch (err) {
            modelStatusMeta.textContent = `Failed to load model status: ${err.message}`;
            if (modelStatusTable) modelStatusTable.innerHTML = '';
            updateModelIndicator({ failed: 1, total: 1, passed: 0 });
        }
    }

    function updateModelIndicator(summary) {
        if (!modelStatusIndicator) return;
        const total = summary.total || 0;
        const failed = summary.failed || 0;
        modelStatusIndicator.classList.remove('ok', 'warn', 'fail');
        if (total === 0) {
            modelStatusIndicator.classList.add('warn');
        } else if (failed === 0) {
            modelStatusIndicator.classList.add('ok');
        } else if (failed < total) {
            modelStatusIndicator.classList.add('warn');
        } else {
            modelStatusIndicator.classList.add('fail');
        }
    }

    // Prefetch status for indicator on load
    (async () => {
        try {
            const res = await fetch('model-status.json', { cache: 'no-store' });
            if (!res.ok) return;
            const data = await res.json();
            updateModelIndicator(data.summary || {});
        } catch (_) {
            updateModelIndicator({ failed: 1, total: 1, passed: 0 });
        }
    })();

    // --- Filtering Logic (Tags, Search, Archive) ---
    const filterStatus = document.getElementById('filterStatus');
    const currentTagSpan = document.getElementById('currentTag');
    const clearFilterBtn = document.getElementById('clearFilter');
    const tweets = document.querySelectorAll('.tweet');
    const tags = document.querySelectorAll('.tag');

    const searchInput = document.getElementById('searchInput');

    function filterByTag(tagName) {
        const targetTag = tagName.toLowerCase();
        let count = 0;
        tweets.forEach(tweet => {
            const tweetTags = (tweet.getAttribute('data-tags') || "").split(',');
            if (tweetTags.includes(targetTag)) {
                tweet.style.display = 'block';
                count++;
            } else {
                tweet.style.display = 'none';
            }
        });
        updateFilterUI(`#${tagName} (${count})`);
    }

    function filterByArchive(datePrefix) {
        let count = 0;
        tweets.forEach(tweet => {
            const tweetTime = tweet.querySelector('.tweet-time').textContent;
            if (tweetTime.includes(datePrefix)) {
                tweet.style.display = 'block';
                count++;
            } else {
                tweet.style.display = 'none';
            }
        });
        updateFilterUI(`${datePrefix} (${count} posts)`);
    }

    function filterByDay(dayStr) {
        let count = 0;
        tweets.forEach(tweet => {
            const tweetTime = tweet.querySelector('.tweet-time').textContent;
            if (tweetTime.includes(dayStr)) {
                tweet.style.display = 'block';
                count++;
            } else {
                tweet.style.display = 'none';
            }
        });
        updateFilterUI(`${dayStr} (${count} posts)`);
    }

    function filterBySearch(term) {
        let count = 0;
        tweets.forEach(tweet => {
            const content = tweet.innerText.toLowerCase();
            if (content.includes(term)) {
                tweet.style.display = 'block';
                count++;
            } else {
                tweet.style.display = 'none';
            }
        });
        updateFilterUI(`Search: "${term}" (${count})`);
    }

    function updateFilterUI(statusText) {
        if (filterStatus) filterStatus.classList.add('visible');
        if (currentTagSpan) currentTagSpan.textContent = statusText;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function clearFilter() {
        tweets.forEach(tweet => tweet.style.display = 'block');
        if (filterStatus) filterStatus.classList.remove('visible');
        if (searchInput) searchInput.value = '';
        tags.forEach(t => t.classList.remove('active'));
    }

    // --- Event Listeners ---
    // Tags
    tags.forEach(tag => {
        tag.addEventListener('click', (e) => {
            e.stopPropagation();
            const tagName = tag.getAttribute('data-tag');
            filterByTag(tagName);
            closeModal();
            // Highlight active tag
            tags.forEach(t => t.classList.toggle('active', t.getAttribute('data-tag') === tagName));
        });
    });

    // Archive (Calendar)
    const archiveDays = window.__archiveDays || {};
    const calendarGrid = document.getElementById('calendarGrid');
    const calendarTitle = document.getElementById('calendarTitle');
    const calendarMonthFilter = document.getElementById('calendarMonthFilter');
    let currentMonthKey = '';
    let selectedDay = '';

    function getLatestMonthKey() {
        const keys = Object.keys(archiveDays).sort();
        return keys.length ? keys[keys.length - 1] : '';
    }

    function renderCalendar(monthKey) {
        if (!calendarGrid) return;
        if (!monthKey) {
            calendarGrid.innerHTML = '<div class="calendar-empty">No data</div>';
            return;
        }

        currentMonthKey = monthKey;
        const [yearStr, monthStr] = monthKey.split('-');
        const year = Number(yearStr);
        const month = Number(monthStr);

        if (calendarTitle) calendarTitle.textContent = `${year}-${monthStr}`;

        const firstDay = new Date(year, month - 1, 1).getDay();
        const daysInMonth = new Date(year, month, 0).getDate();
        const daysWithPosts = new Set(archiveDays[monthKey] || []);

        const cells = [];
        for (let i = 0; i < firstDay; i++) {
            cells.push('<div class="calendar-day empty"></div>');
        }
        for (let day = 1; day <= daysInMonth; day++) {
            const dd = String(day).padStart(2, '0');
            const dayStr = `${monthKey}-${dd}`;
            const hasPost = daysWithPosts.has(dayStr);
            const isSelected = dayStr === selectedDay;
            cells.push(
                `<div class="calendar-day ${hasPost ? 'has-post' : 'empty'} ${isSelected ? 'selected' : ''}" data-date="${hasPost ? dayStr : ''}">${day}</div>`
            );
        }
        calendarGrid.innerHTML = cells.join('');
    }

    if (calendarGrid) {
        calendarGrid.addEventListener('click', (e) => {
            const target = e.target.closest('.calendar-day.has-post');
            if (!target) return;
            const dateStr = target.getAttribute('data-date');
            if (!dateStr) return;
            selectedDay = dateStr;
            closeModal();
            
            // Navigate to the date page instead of filtering on current page
            const isHome = window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/');
            const datePageUrl = isHome ? `date/${dateStr}.html` : `${dateStr}.html`;
            window.location.href = datePageUrl;
        });
    }

    if (calendarMonthFilter) {
        calendarMonthFilter.addEventListener('click', () => {
            if (!currentMonthKey) return;
            filterByArchive(currentMonthKey);
            closeModal();
        });
    }

    document.querySelectorAll('.archive-month').forEach(item => {
        item.addEventListener('click', () => {
            const monthKey = item.getAttribute('data-date');
            renderCalendar(monthKey);
        });
    });

    if (archiveToggle) {
        archiveToggle.addEventListener('click', () => {
            const latest = getLatestMonthKey();
            renderCalendar(latest);
        });
    }

    // Search
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase().trim();
            if (term.length === 0) {
                clearFilter();
            } else {
                filterBySearch(term);
            }
        });
    }

    // Clear
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', clearFilter);
    }

    // --- Type Filtering ---
    // --- Type Filtering (Dropdown) ---
    const filterTrigger = document.getElementById('filterDropdownTrigger');
    const filterDropdown = document.getElementById('typeFilterDropdown');
    const filterItems = document.querySelectorAll('.dropdown-item');
    const currentFilterIcon = document.getElementById('currentFilterIcon');

    if (filterTrigger && filterDropdown) {
        filterTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            filterDropdown.classList.toggle('visible');
        });

        filterItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const type = item.getAttribute('data-type');

                // Update active state
                filterItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');

                // Update Icon
                if (type === 'all') currentFilterIcon.textContent = '📑';
                if (type === 'original') currentFilterIcon.textContent = '📝';
                if (type === 'repost') currentFilterIcon.textContent = '🔄';

                // Do Filter
                let count = 0;
                tweets.forEach(tweet => {
                    const tweetType = tweet.getAttribute('data-type'); // original or repost
                    if (type === 'all' || tweetType === type) {
                        tweet.style.display = 'block';
                        count++;
                    } else {
                        tweet.style.display = 'none';
                    }
                });

                // Update UI Status bar
                if (type === 'all') {
                    clearFilter();
                } else {
                    const label = type.charAt(0).toUpperCase() + type.slice(1);
                    updateFilterUI(`${label} (${count})`);
                }

                filterDropdown.classList.remove('visible');
            });
        });

        // Close dropdown when clicking outside
        window.addEventListener('click', () => {
            filterDropdown.classList.remove('visible');
        });
    }

    // --- Back to Top Button ---
    const backToTopBtn = document.getElementById('backToTop');

    if (backToTopBtn) {
        // Show/hide button based on scroll position
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        });

        // Scroll to top when clicked
        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // --- Post-process Links (Open External Links in New Tab) ---
    function processExternalLinks() {
        const links = document.querySelectorAll('.tweet-text a');
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('http')) {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
            }
        });
    }

    processExternalLinks();

    // --- Lightbox / Image Gallery Logic ---
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightboxImg');
    const lightboxClose = document.querySelector('.lightbox-close');
    const lightboxPrev = document.getElementById('lightboxPrev');
    const lightboxNext = document.getElementById('lightboxNext');

    let currentGallery = [];
    let currentIndex = 0;

    function openLightbox(src, gallery) {
        currentGallery = gallery;
        currentIndex = gallery.indexOf(src);

        lightboxImg.src = src;
        lightbox.classList.add('visible');
        document.body.style.overflow = 'hidden';

        updateNavButtons();
    }

    function closeLightbox() {
        lightbox.classList.remove('visible');
        document.body.style.overflow = '';
    }

    function updateNavButtons() {
        if (currentGallery.length <= 1) {
            lightboxPrev.style.display = 'none';
            lightboxNext.style.display = 'none';
        } else {
            lightboxPrev.style.display = 'block';
            lightboxNext.style.display = 'block';
        }
    }

    function navigate(direction) {
        currentIndex = (currentIndex + direction + currentGallery.length) % currentGallery.length;
        lightboxImg.src = currentGallery[currentIndex];
    }

    // Initialize all tweet images
    function initGallery() {
        const tweets = document.querySelectorAll('.tweet');

        tweets.forEach(tweet => {
            const images = tweet.querySelectorAll('.tweet-text img');
            const gallerySources = Array.from(images).map(img => img.src);

            images.forEach(img => {
                img.addEventListener('click', (e) => {
                    e.stopPropagation();
                    openLightbox(img.src, gallerySources);
                });
            });
        });
    }

    if (lightbox) {
        lightboxClose.addEventListener('click', closeLightbox);
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox || e.target.classList.contains('lightbox-content')) {
                closeLightbox();
            }
        });

        lightboxPrev.addEventListener('click', (e) => {
            e.stopPropagation();
            navigate(-1);
        });

        lightboxNext.addEventListener('click', (e) => {
            e.stopPropagation();
            navigate(1);
        });

        // Keyboard Support
        document.addEventListener('keydown', (e) => {
            if (!lightbox.classList.contains('visible')) return;

            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowLeft') navigate(-1);
            if (e.key === 'ArrowRight') navigate(1);
        });
    }

    initGallery();
});
