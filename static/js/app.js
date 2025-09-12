// Watch Media Server - Frontend JavaScript
class WatchApp {
    constructor() {
        this.socket = io();
        this.currentTab = 'all';
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.searchQuery = '';
        this.mediaData = [];
        this.searchFilters = {};
        this.selectedMedia = new Set();
        this.viewMode = 'grid'; // 'grid' or 'list'
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupSocketListeners();
        this.setupKeyboardShortcuts();
        this.setupTheme();
        this.setupResumePlayback();
        this.loadSettings();
        this.loadLibraryInfo();
        this.loadMedia();
    }
    
    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Search
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.searchQuery = e.target.value;
            this.currentPage = 1;
            this.loadMedia();
        });
        
        document.getElementById('searchBtn').addEventListener('click', () => {
            this.loadMedia();
        });
        
        // Scan library
        document.getElementById('scanBtn').addEventListener('click', () => {
            this.scanLibrary();
        });
        
        // Settings
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.openSettings();
        });
        
        document.getElementById('closeSettings').addEventListener('click', () => {
            this.closeModal('settingsModal');
        });
        
        document.getElementById('cancelSettings').addEventListener('click', () => {
            this.closeModal('settingsModal');
        });
        
        document.getElementById('settingsForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSettings();
        });
        
        // Player modal
        document.getElementById('closePlayer').addEventListener('click', () => {
            this.closeModal('playerModal');
        });
        
        // Pagination
        document.getElementById('prevBtn').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadMedia();
            }
        });
        
        document.getElementById('nextBtn').addEventListener('click', () => {
            this.currentPage++;
            this.loadMedia();
        });
        
        // Close modals on outside click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }
    
    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.showStatus('Connected to server', 'success');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.showStatus('Disconnected from server', 'error');
        });
        
        this.socket.on('scan_status', (data) => {
            this.updateScanProgress(data);
        });
        
        this.socket.on('scan_complete', (data) => {
            this.showScanComplete(data);
            this.loadMedia();
            this.loadLibraryInfo();
        });
        
        this.socket.on('scan_error', (data) => {
            this.showScanError(data);
        });
        
        this.socket.on('library_path_changed', (data) => {
            this.showStatus(data.message, 'info');
            this.loadLibraryInfo();
        });
        
        this.socket.on('status', (data) => {
            if (data.scan_in_progress) {
                this.showStatus('Library scan in progress...', 'info');
            }
        });
    }
    
    switchTab(tab) {
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
        
        this.currentTab = tab;
        this.currentPage = 1;
        this.loadMedia();
    }
    
    async loadMedia() {
        try {
            // Show loading spinner
            const grid = document.getElementById('mediaGrid');
            this.showLoading(grid, 'Loading media...');
            
            const params = new URLSearchParams({
                limit: this.itemsPerPage,
                offset: (this.currentPage - 1) * this.itemsPerPage
            });
            
            if (this.currentTab !== 'all') {
                params.append('type', this.currentTab === 'movies' ? 'movie' : 'tv_show');
            }
            
            const response = await fetch(`/api/media?${params}`);
            const data = await response.json();
            
            this.mediaData = data;
            this.renderMediaGrid();
            this.updatePagination();
            
        } catch (error) {
            console.error('Error loading media:', error);
            this.showStatus('Error loading media', 'error');
            // Show error in grid
            const grid = document.getElementById('mediaGrid');
            grid.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading media. Please try again.</p>
                </div>
            `;
        }
    }
    
    renderMediaGrid() {
        const grid = document.getElementById('mediaGrid');
        
        if (this.mediaData.length === 0) {
            grid.innerHTML = `
                <div class="loading">
                    <i class="fas fa-film"></i>
                    <p>No media files found</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = this.mediaData.map(media => this.createMediaCard(media)).join('');
        
        // Add click listeners to media cards
        grid.querySelectorAll('.media-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.media-actions')) {
                    const mediaId = card.dataset.mediaId;
                    this.playMedia(mediaId);
                }
            });
        });
    }
    
    createMediaCard(media) {
        const typeClass = media.media_type === 'movie' ? 'movie' : 'tv_show';
        const typeIcon = media.media_type === 'movie' ? 'fas fa-film' : 'fas fa-tv';
        const fileSize = this.formatFileSize(media.file_size);
        const resumePosition = this.getResumePosition(media.id);
        const hasResume = resumePosition > 0;
        
        return `
            <div class="media-card" data-media-id="${media.id}">
                <div class="media-poster">
                    <i class="${typeIcon}"></i>
                    ${hasResume ? '<div class="resume-indicator"><i class="fas fa-play-circle"></i></div>' : ''}
                </div>
                <div class="media-info">
                    <h3 class="media-title">${this.escapeHtml(media.title || media.file_name)}</h3>
                    <div class="media-meta">
                        <span class="media-type ${typeClass}">${media.media_type}</span>
                        <span class="file-size">${fileSize}</span>
                        ${hasResume ? `<span class="resume-text">Resume at ${Math.floor(resumePosition / 60)}:${(resumePosition % 60).toString().padStart(2, '0')}</span>` : ''}
                    </div>
                    <div class="media-actions">
                        <button class="btn btn-primary" onclick="app.playMedia(${media.id})">
                            <i class="fas fa-${hasResume ? 'play-circle' : 'play'}"></i> 
                            ${hasResume ? 'Resume' : 'Play'}
                        </button>
                        <button class="btn btn-secondary" onclick="app.streamMedia(${media.id})">
                            <i class="fas fa-download"></i> Stream
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    updatePagination() {
        const totalPages = Math.ceil(this.mediaData.length / this.itemsPerPage);
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const pageInfo = document.getElementById('pageInfo');
        
        prevBtn.disabled = this.currentPage <= 1;
        nextBtn.disabled = this.currentPage >= totalPages;
        
        pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
    }
    
    async playMedia(mediaId) {
        try {
            const media = this.mediaData.find(m => m.id === mediaId);
            if (!media) return;
            
            const playerModal = document.getElementById('playerModal');
            const playerTitle = document.getElementById('playerTitle');
            const mediaPlayer = document.getElementById('mediaPlayer');
            
            playerTitle.textContent = media.title || media.file_name;
            mediaPlayer.src = `/api/stream/${mediaId}`;
            
            // Set resume position if available
            const resumePosition = this.getResumePosition(mediaId);
            if (resumePosition > 0) {
                mediaPlayer.addEventListener('loadedmetadata', () => {
                    mediaPlayer.currentTime = resumePosition;
                }, { once: true });
            }
            
            // Save current position every 5 seconds
            mediaPlayer.addEventListener('timeupdate', () => {
                if (mediaPlayer.currentTime > 5) { // Only save if watched for more than 5 seconds
                    this.saveResumePosition(mediaId, mediaPlayer.currentTime);
                }
            });
            
            this.openModal('playerModal');
            
            // Update play count
            await fetch(`/api/play/${mediaId}`);
            
        } catch (error) {
            console.error('Error playing media:', error);
            this.showStatus('Error playing media', 'error');
        }
    }
    
    async streamMedia(mediaId) {
        try {
            const media = this.mediaData.find(m => m.id === mediaId);
            if (!media) return;
            
            // Open stream in new tab
            window.open(`/api/stream/${mediaId}`, '_blank');
            
        } catch (error) {
            console.error('Error streaming media:', error);
            this.showStatus('Error streaming media', 'error');
        }
    }
    
    async scanLibrary() {
        try {
            const response = await fetch('/api/scan', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'started') {
                this.showStatus('Library scan started', 'info');
            } else if (data.status === 'already_running') {
                this.showStatus('Library scan already in progress', 'info');
            }
            
        } catch (error) {
            console.error('Error starting scan:', error);
            this.showStatus('Error starting scan', 'error');
        }
    }
    
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const settings = await response.json();
            
            // Populate settings form
            Object.keys(settings).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.value = settings[key];
                }
            });
            
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
    
    async saveSettings() {
        try {
            const formData = new FormData(document.getElementById('settingsForm'));
            const settings = Object.fromEntries(formData.entries());
            
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            
            if (response.ok) {
                this.showStatus('Settings saved successfully', 'success');
                this.closeModal('settingsModal');
            } else {
                throw new Error('Failed to save settings');
            }
            
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showStatus('Error saving settings', 'error');
        }
    }
    
    openSettings() {
        this.openModal('settingsModal');
    }
    
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        
        // Stop video if player modal is closed
        if (modalId === 'playerModal') {
            const player = document.getElementById('mediaPlayer');
            player.pause();
            player.src = '';
        }
    }
    
    showStatus(message, type = 'info') {
        const statusEl = document.getElementById('statusMessage');
        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;
        statusEl.classList.add('show');
        
        setTimeout(() => {
            statusEl.classList.remove('show');
        }, 3000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    updateScanProgress(data) {
        // Create or update progress bar
        let progressContainer = document.getElementById('scanProgress');
        if (!progressContainer) {
            progressContainer = document.createElement('div');
            progressContainer.id = 'scanProgress';
            progressContainer.className = 'scan-progress';
            document.querySelector('.stats-bar').appendChild(progressContainer);
        }
        
        progressContainer.innerHTML = `
            <div class="progress-info">
                <h4>Library Scan Progress</h4>
                <p>${data.message}</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${data.progress}%"></div>
                </div>
                <div class="progress-details">
                    ${data.processed_files ? `${data.processed_files}/${data.total_files} files` : ''}
                    ${data.current_file ? ` - Processing: ${data.current_file}` : ''}
                </div>
            </div>
        `;
        
        // Update scan button
        const scanBtn = document.getElementById('scanBtn');
        if (data.status === 'scanning' || data.status === 'counting') {
            scanBtn.disabled = true;
            scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
        }
    }
    
    showScanComplete(data) {
        // Remove progress bar
        const progressContainer = document.getElementById('scanProgress');
        if (progressContainer) {
            progressContainer.remove();
        }
        
        // Reset scan button
        const scanBtn = document.getElementById('scanBtn');
        scanBtn.disabled = false;
        scanBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Scan Library';
        
        // Show completion message
        this.showStatus(data.message, 'success');
        
        // Update stats
        this.loadLibraryInfo();
    }
    
    showScanError(data) {
        // Remove progress bar
        const progressContainer = document.getElementById('scanProgress');
        if (progressContainer) {
            progressContainer.remove();
        }
        
        // Reset scan button
        const scanBtn = document.getElementById('scanBtn');
        scanBtn.disabled = false;
        scanBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Scan Library';
        
        // Show error message
        this.showStatus(data.message, 'error');
    }
    
    async loadLibraryInfo() {
        try {
            const response = await fetch('/api/library/info');
            const info = await response.json();
            
            // Update stats bar
            document.getElementById('totalFiles').textContent = info.total_files;
            document.getElementById('librarySize').textContent = `${info.total_size_gb} GB`;
            
            // Update library path in settings if needed
            const libraryPathInput = document.getElementById('libraryPath');
            if (libraryPathInput && libraryPathInput.value !== info.library_path) {
                libraryPathInput.value = info.library_path;
            }
            
            // Show warning if path doesn't exist
            if (!info.exists) {
                this.showStatus(`Warning: Library path does not exist: ${info.library_path}`, 'error');
            }
            
        } catch (error) {
            console.error('Error loading library info:', error);
        }
    }
    
    // ===== QUICK WINS IMPLEMENTATION =====
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            switch(e.code) {
                case 'Space':
                    e.preventDefault();
                    this.togglePlayPause();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.seekVideo(-10);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.seekVideo(10);
                    break;
                case 'KeyF':
                    e.preventDefault();
                    this.toggleFullscreen();
                    break;
                case 'KeyM':
                    e.preventDefault();
                    this.toggleMute();
                    break;
                case 'Escape':
                    this.closeAllModals();
                    break;
                case 'KeyS':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.openSettings();
                    }
                    break;
                case 'Slash':
                    if (e.shiftKey) {
                        e.preventDefault();
                        this.toggleKeyboardHelp();
                    }
                    break;
            }
        });
    }
    
    setupTheme() {
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('watch-theme') || 'light';
        this.applyTheme(savedTheme);
        
        // Create theme toggle button
        this.createThemeToggle();
    }
    
    createThemeToggle() {
        const header = document.querySelector('.header');
        const themeToggle = document.createElement('button');
        themeToggle.id = 'themeToggle';
        themeToggle.className = 'btn btn-secondary theme-toggle';
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        themeToggle.title = 'Toggle Dark/Light Theme';
        themeToggle.addEventListener('click', () => this.toggleTheme());
        
        header.appendChild(themeToggle);
    }
    
    toggleTheme() {
        const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        localStorage.setItem('watch-theme', newTheme);
    }
    
    applyTheme(theme) {
        document.body.classList.remove('light-theme', 'dark-theme');
        document.body.classList.add(`${theme}-theme`);
        
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        }
    }
    
    setupResumePlayback() {
        // Load resume positions from localStorage
        this.resumePositions = JSON.parse(localStorage.getItem('watch-resume-positions') || '{}');
    }
    
    saveResumePosition(mediaId, position) {
        this.resumePositions[mediaId] = position;
        localStorage.setItem('watch-resume-positions', JSON.stringify(this.resumePositions));
    }
    
    getResumePosition(mediaId) {
        return this.resumePositions[mediaId] || 0;
    }
    
    // Video player controls
    togglePlayPause() {
        const player = document.getElementById('mediaPlayer');
        if (player) {
            if (player.paused) {
                player.play();
            } else {
                player.pause();
            }
        }
    }
    
    toggleKeyboardHelp() {
        const help = document.getElementById('keyboardShortcuts');
        help.classList.toggle('show');
    }
    
    seekVideo(seconds) {
        const player = document.getElementById('mediaPlayer');
        if (player) {
            player.currentTime += seconds;
        }
    }
    
    toggleFullscreen() {
        const player = document.getElementById('mediaPlayer');
        if (player) {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                player.requestFullscreen();
            }
        }
    }
    
    toggleMute() {
        const player = document.getElementById('mediaPlayer');
        if (player) {
            player.muted = !player.muted;
        }
    }
    
    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
        document.body.style.overflow = 'auto';
    }
    
    // Enhanced media card with file size formatting
    formatFileSize(bytes) {
        if (!bytes) return 'Unknown';
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    // Loading spinner utility
    showLoading(element, message = 'Loading...') {
        element.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
                <p>${message}</p>
            </div>
        `;
    }
    
    // ===== HIGH-IMPACT FEATURES =====
    
    async loadRecentlyAdded() {
        try {
            const response = await fetch('/api/recently-added?limit=20');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error loading recently added:', error);
            return [];
        }
    }
    
    async loadTrending() {
        try {
            const response = await fetch('/api/trending?limit=20');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error loading trending:', error);
            return [];
        }
    }
    
    async loadContinueWatching() {
        try {
            const response = await fetch('/api/continue-watching?limit=20');
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error loading continue watching:', error);
            return [];
        }
    }
    
    async performAdvancedSearch(searchTerm = '', filters = {}) {
        try {
            const params = new URLSearchParams();
            if (searchTerm) params.append('q', searchTerm);
            
            // Add filters to params
            Object.keys(filters).forEach(key => {
                if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
                    if (Array.isArray(filters[key])) {
                        params.append(key, filters[key].join(','));
                    } else {
                        params.append(key, filters[key]);
                    }
                }
            });
            
            const response = await fetch(`/api/search?${params}`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error performing advanced search:', error);
            return [];
        }
    }
    
    async getSearchSuggestions(query) {
        try {
            const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}&limit=10`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error getting search suggestions:', error);
            return [];
        }
    }
    
    async getSubtitles(mediaId) {
        try {
            const response = await fetch(`/api/subtitles/${mediaId}`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error getting subtitles:', error);
            return [];
        }
    }
    
    async updateMetadata(mediaId, refresh = false) {
        try {
            const url = refresh ? `/api/metadata/${mediaId}?refresh=true` : `/api/metadata/${mediaId}`;
            const response = await fetch(url);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error updating metadata:', error);
            return null;
        }
    }
    
    async bulkUpdateMetadata(mediaIds) {
        try {
            const response = await fetch('/api/bulk/update-metadata', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ media_ids: mediaIds })
            });
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error bulk updating metadata:', error);
            return { updated_count: 0, errors: [error.message] };
        }
    }
    
    async bulkDelete(mediaIds, deleteFiles = false) {
        try {
            const response = await fetch('/api/bulk/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    media_ids: mediaIds,
                    delete_files: deleteFiles
                })
            });
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error bulk deleting:', error);
            return { deleted_count: 0, errors: [error.message] };
        }
    }
    
    // Enhanced media card with poster support
    createEnhancedMediaCard(media) {
        const typeClass = media.media_type === 'movie' ? 'movie' : 'tv_show';
        const typeIcon = media.media_type === 'movie' ? 'fas fa-film' : 'fas fa-tv';
        const fileSize = this.formatFileSize(media.file_size);
        const resumePosition = this.getResumePosition(media.id);
        const hasResume = resumePosition > 0;
        const hasPoster = media.poster_url && media.poster_url.trim() !== '';
        const rating = media.rating ? media.rating.toFixed(1) : 'N/A';
        const genres = media.genres ? (Array.isArray(media.genres) ? media.genres : JSON.parse(media.genres)) : [];
        
        return `
            <div class="media-card enhanced" data-media-id="${media.id}">
                <div class="media-poster">
                    ${hasPoster ? 
                        `<img src="${media.poster_url}" alt="${media.title}" class="poster-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                         <div class="poster-fallback" style="display: none;">
                             <i class="${typeIcon}"></i>
                         </div>` :
                        `<div class="poster-fallback">
                             <i class="${typeIcon}"></i>
                         </div>`
                    }
                    ${hasResume ? '<div class="resume-indicator"><i class="fas fa-play-circle"></i></div>' : ''}
                    ${media.rating ? `<div class="rating-badge">${rating}</div>` : ''}
                    <div class="media-overlay">
                        <button class="btn btn-primary btn-sm" onclick="app.playMedia(${media.id})">
                            <i class="fas fa-${hasResume ? 'play-circle' : 'play'}"></i>
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="app.showMediaDetails(${media.id})">
                            <i class="fas fa-info-circle"></i>
                        </button>
                    </div>
                </div>
                <div class="media-info">
                    <h3 class="media-title">${this.escapeHtml(media.title || media.file_name)}</h3>
                    <div class="media-meta">
                        <span class="media-type ${typeClass}">${media.media_type}</span>
                        <span class="file-size">${fileSize}</span>
                        ${media.year ? `<span class="year">${media.year}</span>` : ''}
                    </div>
                    ${genres.length > 0 ? `<div class="genres">${genres.slice(0, 3).map(g => `<span class="genre-tag">${g}</span>`).join('')}</div>` : ''}
                    ${hasResume ? `<div class="resume-text">Resume at ${Math.floor(resumePosition / 60)}:${(resumePosition % 60).toString().padStart(2, '0')}</div>` : ''}
                    <div class="media-actions">
                        <button class="btn btn-primary" onclick="app.playMedia(${media.id})">
                            <i class="fas fa-${hasResume ? 'play-circle' : 'play'}"></i> 
                            ${hasResume ? 'Resume' : 'Play'}
                        </button>
                        <button class="btn btn-secondary" onclick="app.streamMedia(${media.id})">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="btn btn-secondary" onclick="app.toggleMediaSelection(${media.id})">
                            <i class="fas fa-check"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    toggleMediaSelection(mediaId) {
        if (this.selectedMedia.has(mediaId)) {
            this.selectedMedia.delete(mediaId);
        } else {
            this.selectedMedia.add(mediaId);
        }
        this.updateSelectionUI();
    }
    
    updateSelectionUI() {
        const selectedCount = this.selectedMedia.size;
        const bulkActions = document.getElementById('bulkActions');
        
        if (selectedCount > 0) {
            if (!bulkActions) {
                this.createBulkActionsPanel();
            }
            document.getElementById('selectedCount').textContent = selectedCount;
        } else {
            if (bulkActions) {
                bulkActions.remove();
            }
        }
    }
    
    createBulkActionsPanel() {
        const bulkActions = document.createElement('div');
        bulkActions.id = 'bulkActions';
        bulkActions.className = 'bulk-actions';
        bulkActions.innerHTML = `
            <div class="bulk-actions-content">
                <span id="selectedCount">0</span> items selected
                <div class="bulk-buttons">
                    <button class="btn btn-primary" onclick="app.bulkUpdateMetadataSelected()">
                        <i class="fas fa-sync"></i> Update Metadata
                    </button>
                    <button class="btn btn-warning" onclick="app.bulkDeleteSelected(false)">
                        <i class="fas fa-trash"></i> Remove from Library
                    </button>
                    <button class="btn btn-danger" onclick="app.bulkDeleteSelected(true)">
                        <i class="fas fa-trash-alt"></i> Delete Files
                    </button>
                    <button class="btn btn-secondary" onclick="app.clearSelection()">
                        <i class="fas fa-times"></i> Clear
                    </button>
                </div>
            </div>
        `;
        
        document.querySelector('.main').insertBefore(bulkActions, document.getElementById('mediaGrid'));
    }
    
    clearSelection() {
        this.selectedMedia.clear();
        this.updateSelectionUI();
        // Remove selection styling from cards
        document.querySelectorAll('.media-card.selected').forEach(card => {
            card.classList.remove('selected');
        });
    }
    
    async bulkUpdateMetadataSelected() {
        if (this.selectedMedia.size === 0) return;
        
        const mediaIds = Array.from(this.selectedMedia);
        this.showStatus('Updating metadata...', 'info');
        
        const result = await this.bulkUpdateMetadata(mediaIds);
        
        if (result.updated_count > 0) {
            this.showStatus(`Updated metadata for ${result.updated_count} items`, 'success');
            this.loadMedia(); // Refresh the view
        }
        
        if (result.errors.length > 0) {
            this.showStatus(`Errors: ${result.errors.join(', ')}`, 'error');
        }
        
        this.clearSelection();
    }
    
    async bulkDeleteSelected(deleteFiles = false) {
        if (this.selectedMedia.size === 0) return;
        
        const action = deleteFiles ? 'delete files' : 'remove from library';
        if (!confirm(`Are you sure you want to ${action} for ${this.selectedMedia.size} items?`)) {
            return;
        }
        
        const mediaIds = Array.from(this.selectedMedia);
        this.showStatus(`${deleteFiles ? 'Deleting' : 'Removing'} items...`, 'info');
        
        const result = await this.bulkDelete(mediaIds, deleteFiles);
        
        if (result.deleted_count > 0) {
            this.showStatus(`${deleteFiles ? 'Deleted' : 'Removed'} ${result.deleted_count} items`, 'success');
            this.loadMedia(); // Refresh the view
        }
        
        if (result.errors.length > 0) {
            this.showStatus(`Errors: ${result.errors.join(', ')}`, 'error');
        }
        
        this.clearSelection();
    }
    
    showMediaDetails(mediaId) {
        // This would open a detailed modal with full metadata
        // For now, just show a simple alert
        const media = this.mediaData.find(m => m.id === mediaId);
        if (media) {
            alert(`Media Details:\nTitle: ${media.title}\nType: ${media.media_type}\nRating: ${media.rating || 'N/A'}\nOverview: ${media.overview || 'No overview available'}`);
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WatchApp();
});
