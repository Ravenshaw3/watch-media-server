// Watch Media Server - Frontend JavaScript
class WatchApp {
    constructor() {
        this.socket = io();
        this.currentTab = 'all';
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.searchQuery = '';
        this.mediaData = [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupSocketListeners();
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
        const sizeMB = media.file_size ? (media.file_size / (1024 * 1024)).toFixed(1) : 'Unknown';
        
        return `
            <div class="media-card" data-media-id="${media.id}">
                <div class="media-poster">
                    <i class="${typeIcon}"></i>
                </div>
                <div class="media-info">
                    <h3 class="media-title">${this.escapeHtml(media.title || media.file_name)}</h3>
                    <div class="media-meta">
                        <span class="media-type ${typeClass}">${media.media_type}</span>
                        <span>${sizeMB} MB</span>
                    </div>
                    <div class="media-actions">
                        <button class="btn btn-primary" onclick="app.playMedia(${media.id})">
                            <i class="fas fa-play"></i> Play
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
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WatchApp();
});
