// Netflix-style Watch Media Server - Frontend JavaScript
class WatchApp {
    constructor() {
        try {
            this.socket = io();
        } catch (error) {
            console.error('Socket.IO not available:', error);
            this.socket = null;
        }
        this.currentTab = 'all';
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.searchQuery = '';
        this.mediaData = [];
        this.searchFilters = {};
        this.selectedMedia = new Set();
        this.viewMode = 'grid';
        this.isAuthenticated = false;
        this.currentUser = null;
        
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
        this.loadVersion();
        this.checkAuth();
        this.loadMedia();
        this.setupHeaderScroll();
    }
    
    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
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
            this.showSettings();
        });
        
        // Auth
        document.getElementById('authBtn').addEventListener('click', () => {
            this.showAuth();
        });
        
        // User menu
        const userBtn = document.getElementById('userBtn');
        if (userBtn) {
            userBtn.addEventListener('click', () => {
                this.toggleUserMenu();
            });
        }
        
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }
        
        // Modals
        this.setupModalListeners();
        
        // Hero actions
        const playHeroBtn = document.getElementById('playHeroBtn');
        if (playHeroBtn) {
            playHeroBtn.addEventListener('click', () => {
                this.playRandomMedia();
            });
        }
        
        const infoHeroBtn = document.getElementById('infoHeroBtn');
        if (infoHeroBtn) {
            infoHeroBtn.addEventListener('click', () => {
                this.showRandomMediaInfo();
            });
        }
    }
    
    setupSocketListeners() {
        if (!this.socket) {
            console.log('Socket.IO not available, skipping socket listeners');
            return;
        }
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });
        
        this.socket.on('scan_status', (data) => {
            this.updateScanStatus(data);
        });
        
        this.socket.on('scan_complete', (data) => {
            this.handleScanComplete(data);
        });
        
        this.socket.on('scan_error', (data) => {
            this.handleScanError(data);
        });
        
        this.socket.on('library_path_changed', (data) => {
            this.showStatus(`Library path changed to: ${data.new_path}`, 'info');
            this.loadLibraryInfo();
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'k':
                        e.preventDefault();
                        document.getElementById('searchInput').focus();
                        break;
                    case 's':
                        e.preventDefault();
                        this.scanLibrary();
                        break;
                }
            }
            
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }
    
    setupTheme() {
        // Netflix theme is already applied via CSS class
        this.createThemeToggle();
    }
    
    createThemeToggle() {
        // Netflix theme is dark by default, so we'll keep it simple
        const existingToggle = document.querySelector('.theme-toggle');
        if (existingToggle) return;
        
        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle action-btn';
        toggle.innerHTML = '<i class="fas fa-moon"></i>';
        toggle.title = 'Toggle Theme';
        toggle.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            const icon = toggle.querySelector('i');
            if (document.body.classList.contains('light-theme')) {
                icon.className = 'fas fa-sun';
            } else {
                icon.className = 'fas fa-moon';
            }
        });
        
        document.body.appendChild(toggle);
    }
    
    setupResumePlayback() {
        // Resume playback functionality
        this.resumeData = JSON.parse(localStorage.getItem('resumePlayback') || '{}');
    }
    
    setupHeaderScroll() {
        const header = document.querySelector('.netflix-header');
        let lastScrollY = window.scrollY;
        
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            
            if (currentScrollY > 100) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
            
            lastScrollY = currentScrollY;
        });
    }
    
    setupModalListeners() {
        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeAllModals();
            }
        });
        
        // Close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeAllModals();
            });
        });
        
        // Settings form
        const settingsForm = document.getElementById('settingsForm');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSettings();
            });
        }
        
        // Auth forms
        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                this.login();
            });
        }
        
        const registerBtn = document.getElementById('registerBtn');
        if (registerBtn) {
            registerBtn.addEventListener('click', () => {
                this.register();
            });
        }
        
        const showRegister = document.getElementById('showRegister');
        if (showRegister) {
            showRegister.addEventListener('click', () => {
                this.showRegisterForm();
            });
        }
        
        const showLogin = document.getElementById('showLogin');
        if (showLogin) {
            showLogin.addEventListener('click', () => {
                this.showLoginForm();
            });
        }
    }
    
    switchTab(tab) {
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
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
            
            if (this.searchQuery) {
                params.append('search', this.searchQuery);
            }
            
            console.log('Loading media with params:', params.toString());
            const response = await fetch(`/api/media?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Media data received:', data);
            
            this.mediaData = data;
            this.renderMediaGrid();
            this.updateHeroBanner();
            
            // Update library info after loading media
            this.loadLibraryInfo();
            
        } catch (error) {
            console.error('Error loading media:', error);
            this.showStatus(`Error loading media: ${error.message}`, 'error');
        }
    }
    
    renderMediaGrid() {
        // Render different grids based on current tab
        this.renderFeaturedGrid();
        this.renderMoviesGrid();
        this.renderTVShowsGrid();
        this.renderKidsGrid();
        this.renderMusicVideosGrid();
        this.renderRecentGrid();
    }
    
    renderFeaturedGrid() {
        const grid = document.getElementById('featuredGrid');
        if (!grid) return;
        
        // Get featured content (first few items)
        const featured = this.mediaData.slice(0, 6);
        
        if (featured.length === 0) {
            grid.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading featured content...</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = featured.map(media => this.createFeaturedCard(media)).join('');
        this.addCardEventListeners(grid);
    }
    
    renderMoviesGrid() {
        const grid = document.getElementById('moviesGrid');
        if (!grid) return;
        
        const movies = this.mediaData.filter(media => media.media_type === 'movie');
        
        if (movies.length === 0) {
            grid.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading movies...</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = movies.map(media => this.createMediaCard(media)).join('');
        this.addCardEventListeners(grid);
    }
    
    renderTVShowsGrid() {
        const grid = document.getElementById('tvShowsGrid');
        if (!grid) return;
        
        const tvShows = this.mediaData.filter(media => media.media_type === 'tv_show');
        
        if (tvShows.length === 0) {
            grid.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading TV shows...</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = tvShows.map(media => this.createMediaCard(media)).join('');
        this.addCardEventListeners(grid);
    }
    
    renderKidsGrid() {
        const grid = document.getElementById('kidsCategoryGrid');
        if (!grid) return;
        
        const kids = this.mediaData.filter(media => media.media_type === 'kids' || media.category === 'kids');
        
        if (kids.length === 0) {
            grid.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading kids content...</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = kids.map(media => this.createMediaCard(media)).join('');
        this.addCardEventListeners(grid);
    }
    
    renderMusicVideosGrid() {
        const grid = document.getElementById('musicVideosCategoryGrid');
        if (!grid) return;
        
        const musicVideos = this.mediaData.filter(media => media.media_type === 'music_video' || media.category === 'music_videos');
        
        if (musicVideos.length === 0) {
            grid.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading music videos...</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = musicVideos.map(media => this.createMediaCard(media)).join('');
        this.addCardEventListeners(grid);
    }
    
    renderRecentGrid() {
        const grid = document.getElementById('recentGrid');
        if (!grid) return;
        
        // Get recent content (last 20 items)
        const recent = this.mediaData.slice(-20).reverse();
        
        if (recent.length === 0) {
            grid.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading recent content...</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = recent.map(media => this.createMediaCard(media)).join('');
        this.addCardEventListeners(grid);
    }
    
    addCardEventListeners(grid) {
        grid.querySelectorAll('.media-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.overlay-btn')) {
                    const mediaId = card.dataset.mediaId;
                    this.playMedia(mediaId);
                }
            });
        });
        
        grid.querySelectorAll('.overlay-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const mediaId = btn.dataset.mediaId;
                const action = btn.dataset.action;
                
                if (action === 'play') {
                    this.playMedia(mediaId);
                } else if (action === 'info') {
                    this.showMediaInfo(mediaId);
                }
            });
        });
    }
    
    createFeaturedCard(media) {
        const typeClass = media.media_type === 'movie' ? 'movie' : 'tv_show';
        const typeIcon = media.media_type === 'movie' ? 'fas fa-film' : 'fas fa-tv';
        const hasPoster = media.poster_url && media.poster_url.trim() !== '';
        const rating = media.rating ? media.rating.toFixed(1) : 'N/A';
        
        return `
            <div class="media-card featured" data-media-id="${media.id}">
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
                    <div class="media-overlay">
                        <button class="overlay-btn" data-media-id="${media.id}" data-action="play">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="overlay-btn secondary" data-media-id="${media.id}" data-action="info">
                            <i class="fas fa-info-circle"></i>
                        </button>
                    </div>
                </div>
                <div class="media-info">
                    <h3 class="media-title">${media.title}</h3>
                    <div class="media-meta">
                        <span class="media-type ${typeClass}">
                            <i class="${typeIcon}"></i>
                            ${media.media_type === 'movie' ? 'Movie' : 'TV Show'}
                        </span>
                        <span class="media-rating">
                            <i class="fas fa-star"></i>
                            ${rating}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }
    
    createMediaCard(media) {
        let typeClass, typeIcon, typeLabel;
        
        switch(media.media_type) {
            case 'tv_show':
                typeClass = 'tv_show';
                typeIcon = 'fas fa-tv';
                typeLabel = 'TV Show';
                break;
            case 'kids':
                typeClass = 'kids';
                typeIcon = 'fas fa-child';
                typeLabel = 'Kids';
                break;
            case 'music_video':
                typeClass = 'music_video';
                typeIcon = 'fas fa-music';
                typeLabel = 'Music Video';
                break;
            default:
                typeClass = 'movie';
                typeIcon = 'fas fa-film';
                typeLabel = 'Movie';
        }
        
        const rating = media.rating ? media.rating.toFixed(1) : 'N/A';
        const posterUrl = `/api/media/${media.id}/poster`;
        
        return `
            <div class="media-card" data-media-id="${media.id}">
                <div class="media-poster">
                    <img src="${posterUrl}" alt="${media.title}" class="poster-image" 
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                    <div class="poster-fallback" style="display: none;">
                        <i class="${typeIcon}"></i>
                    </div>
                    <div class="media-overlay">
                        <button class="overlay-btn" data-media-id="${media.id}" data-action="play">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="overlay-btn secondary" data-media-id="${media.id}" data-action="info">
                            <i class="fas fa-info-circle"></i>
                        </button>
                    </div>
                </div>
                <div class="media-info">
                    <h3 class="media-title">${media.title}</h3>
                    <div class="media-meta">
                        <span class="media-type ${typeClass}">
                            <i class="${typeIcon}"></i>
                            ${typeLabel}
                        </span>
                        <span class="media-rating">
                            <i class="fas fa-star"></i>
                            ${rating}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }
    
    updateHeroBanner() {
        if (this.mediaData.length === 0) return;
        
        // Get a random featured item
        const featured = this.mediaData[Math.floor(Math.random() * Math.min(this.mediaData.length, 10))];
        
        const heroTitle = document.getElementById('heroTitle');
        const heroDescription = document.getElementById('heroDescription');
        const heroBackdrop = document.getElementById('heroBackdrop');
        
        if (heroTitle) {
            heroTitle.textContent = featured.title;
        }
        
        if (heroDescription) {
            const description = featured.overview || 
                `${featured.media_type === 'movie' ? 'Movie' : 'TV Show'} • ${featured.resolution || 'HD'} • ${featured.duration ? Math.floor(featured.duration / 60) + ' min' : 'Unknown duration'}`;
            heroDescription.textContent = description;
        }
        
        if (heroBackdrop && featured.backdrop_url) {
            heroBackdrop.style.backgroundImage = `url(${featured.backdrop_url})`;
            heroBackdrop.style.backgroundSize = 'cover';
            heroBackdrop.style.backgroundPosition = 'center';
        }
        
        // Update hero action buttons
        const playHeroBtn = document.getElementById('playHeroBtn');
        const infoHeroBtn = document.getElementById('infoHeroBtn');
        
        if (playHeroBtn) {
            playHeroBtn.onclick = () => this.playMedia(featured.id);
        }
        
        if (infoHeroBtn) {
            infoHeroBtn.onclick = () => this.showMediaInfo(featured.id);
        }
    }
    
    playRandomMedia() {
        if (this.mediaData.length === 0) return;
        const randomMedia = this.mediaData[Math.floor(Math.random() * this.mediaData.length)];
        this.playMedia(randomMedia.id);
    }
    
    showRandomMediaInfo() {
        if (this.mediaData.length === 0) return;
        const randomMedia = this.mediaData[Math.floor(Math.random() * this.mediaData.length)];
        this.showMediaInfo(randomMedia.id);
    }
    
    async playMedia(mediaId) {
        try {
            const response = await fetch(`/api/stream/${mediaId}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                
                const player = document.getElementById('mediaPlayer');
                const modal = document.getElementById('playerModal');
                const title = document.getElementById('playerTitle');
                
                if (player && modal && title) {
                    const media = this.mediaData.find(m => m.id == mediaId);
                    if (media) {
                        title.textContent = media.title;
                    }
                    
                    player.src = url;
                    modal.classList.add('active');
                    player.play();
                }
            } else {
                throw new Error('Failed to load media');
            }
        } catch (error) {
            console.error('Error playing media:', error);
            this.showStatus(`Error playing media: ${error.message}`, 'error');
        }
    }
    
    showMediaInfo(mediaId) {
        const media = this.mediaData.find(m => m.id == mediaId);
        if (media) {
            alert(`Media Details:\nTitle: ${media.title}\nType: ${media.media_type}\nRating: ${media.rating || 'N/A'}\nOverview: ${media.overview || 'No overview available'}`);
        }
    }
    
    async scanLibrary() {
        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    scan_type: 'incremental'
                })
            });
            
            if (response.ok) {
                this.showStatus('Library scan started', 'info');
            } else {
                throw new Error('Failed to start scan');
            }
        } catch (error) {
            console.error('Error starting scan:', error);
            this.showStatus(`Error starting scan: ${error.message}`, 'error');
        }
    }
    
    updateScanStatus(data) {
        const scanStatus = document.getElementById('scanStatus');
        const scanDirectory = document.getElementById('scanDirectory');
        
        if (scanStatus && scanDirectory) {
            scanStatus.style.display = 'block';
            scanDirectory.textContent = data.current_directory || data.scan_directory || 'Scanning...';
        }
        
        this.showStatus(data.message, 'info');
    }
    
    handleScanComplete(data) {
        const scanStatus = document.getElementById('scanStatus');
        if (scanStatus) {
            scanStatus.style.display = 'none';
        }
        
        this.showStatus(data.message, 'success');
        this.loadMedia(); // Refresh media after scan
        this.loadLibraryInfo(); // Refresh library info
    }
    
    handleScanError(data) {
        const scanStatus = document.getElementById('scanStatus');
        if (scanStatus) {
            scanStatus.style.display = 'none';
        }
        
        this.showStatus(data.message, 'error');
    }
    
    async loadLibraryInfo() {
        try {
            const response = await fetch('/api/library/info');
            if (response.ok) {
                const data = await response.json();
                
                document.getElementById('moviesCount').textContent = data.movies_count || 0;
                document.getElementById('tvShowsCount').textContent = data.tv_shows_count || 0;
                document.getElementById('totalFiles').textContent = data.total_files || 0;
                document.getElementById('librarySize').textContent = data.total_size_gb ? `${data.total_size_gb} GB` : '0 GB';
                
                // Update additional counters if they exist
                const kidsCount = document.getElementById('kidsCount');
                if (kidsCount) {
                    kidsCount.textContent = data.kids_count || 0;
                }
                
                const musicVideosCount = document.getElementById('musicVideosCount');
                if (musicVideosCount) {
                    musicVideosCount.textContent = data.music_videos_count || 0;
                }
                
                // Update last scan time
                const lastScan = document.getElementById('lastScan');
                if (lastScan) {
                    lastScan.textContent = new Date().toLocaleString();
                }
            }
        } catch (error) {
            console.error('Error loading library info:', error);
        }
    }
    
    async loadVersion() {
        try {
            const response = await fetch('/api/version');
            if (response.ok) {
                const data = await response.json();
                const versionInfo = document.getElementById('versionInfo');
                if (versionInfo) {
                    versionInfo.textContent = `v${data.version}`;
                }
            }
        } catch (error) {
            console.error('Error loading version:', error);
        }
    }
    
    async checkAuth() {
        try {
            const response = await fetch('/api/auth/me');
            if (response.ok) {
                const user = await response.json();
                this.isAuthenticated = true;
                this.currentUser = user;
                this.updateAuthUI();
            } else {
                this.isAuthenticated = false;
                this.currentUser = null;
                this.updateAuthUI();
            }
        } catch (error) {
            console.error('Error checking auth:', error);
            this.isAuthenticated = false;
            this.currentUser = null;
            this.updateAuthUI();
        }
    }
    
    updateAuthUI() {
        const authBtn = document.getElementById('authBtn');
        const userMenu = document.getElementById('userMenu');
        const username = document.getElementById('username');
        
        if (this.isAuthenticated) {
            if (authBtn) authBtn.style.display = 'none';
            if (userMenu) userMenu.style.display = 'block';
            if (username && this.currentUser) {
                username.textContent = this.currentUser.username;
            }
        } else {
            if (authBtn) authBtn.style.display = 'block';
            if (userMenu) userMenu.style.display = 'none';
        }
    }
    
    showAuth() {
        const modal = document.getElementById('authModal');
        if (modal) {
            modal.classList.add('active');
            this.showLoginForm();
        }
    }
    
    showLoginForm() {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const authTitle = document.getElementById('authTitle');
        
        if (loginForm) loginForm.style.display = 'block';
        if (registerForm) registerForm.style.display = 'none';
        if (authTitle) authTitle.textContent = 'Login';
    }
    
    showRegisterForm() {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const authTitle = document.getElementById('authTitle');
        
        if (loginForm) loginForm.style.display = 'none';
        if (registerForm) registerForm.style.display = 'block';
        if (authTitle) authTitle.textContent = 'Register';
    }
    
    async login() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        if (!username || !password) {
            this.showStatus('Please enter username and password', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.token);
                this.showStatus('Login successful', 'success');
                this.closeAllModals();
                this.checkAuth();
            } else {
                throw new Error('Login failed');
            }
        } catch (error) {
            console.error('Error logging in:', error);
            this.showStatus('Login failed', 'error');
        }
    }
    
    async register() {
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        if (!username || !email || !password || !confirmPassword) {
            this.showStatus('Please fill in all fields', 'error');
            return;
        }
        
        if (password !== confirmPassword) {
            this.showStatus('Passwords do not match', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, email, password })
            });
            
            if (response.ok) {
                this.showStatus('Registration successful', 'success');
                this.showLoginForm();
            } else {
                throw new Error('Registration failed');
            }
        } catch (error) {
            console.error('Error registering:', error);
            this.showStatus('Registration failed', 'error');
        }
    }
    
    async logout() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            localStorage.removeItem('token');
            this.isAuthenticated = false;
            this.currentUser = null;
            this.updateAuthUI();
            this.showStatus('Logged out successfully', 'success');
        } catch (error) {
            console.error('Error logging out:', error);
        }
    }
    
    toggleUserMenu() {
        const dropdown = document.querySelector('.user-dropdown');
        if (dropdown) {
            dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
        }
    }
    
    showSettings() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.add('active');
            this.loadSettings();
        }
    }
    
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            if (response.ok) {
                const settings = await response.json();
                
                // Populate form fields
                Object.keys(settings).forEach(key => {
                    const element = document.getElementById(key);
                    if (element) {
                        element.value = settings[key];
                    }
                });
            }
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
                this.closeAllModals();
            } else {
                throw new Error('Failed to save settings');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showStatus('Error saving settings', 'error');
        }
    }
    
    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }
    
    showStatus(message, type = 'info') {
        const statusEl = document.getElementById('statusMessage');
        if (!statusEl) return;
        
        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;
        statusEl.classList.add('show');
        
        setTimeout(() => {
            statusEl.classList.remove('show');
        }, 3000);
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WatchApp();
    
    // Settings modal functionality
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeSettings = document.getElementById('closeSettings');
    const cancelSettings = document.getElementById('cancelSettings');
    const body = document.body;
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    body.classList.add(savedTheme);
    updateThemeDisplay(savedTheme);
    
    // Settings modal toggle
    if (settingsBtn && settingsModal) {
        settingsBtn.addEventListener('click', function() {
            settingsModal.classList.add('active');
            window.app.loadSettings();
        });
    }
    
    // Close settings modal
    if (closeSettings && settingsModal) {
        closeSettings.addEventListener('click', function() {
            settingsModal.classList.remove('active');
        });
    }
    
    if (cancelSettings && settingsModal) {
        cancelSettings.addEventListener('click', function() {
            settingsModal.classList.remove('active');
        });
    }
    
    // Settings tabs functionality
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            // Remove active class from all tabs and contents
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            this.classList.add('active');
            document.getElementById(targetTab + 'Tab').classList.add('active');
        });
    });
    
    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('change', function() {
            const selectedTheme = this.value;
            body.className = selectedTheme;
            localStorage.setItem('theme', selectedTheme);
            updateThemeDisplay(selectedTheme);
        });
    }
    
    
    // Audio-only playback functionality
    const audioOnlyBtn = document.getElementById('audioOnlyBtn');
    const mediaPlayer = document.getElementById('mediaPlayer');
    
    if (audioOnlyBtn && mediaPlayer) {
        audioOnlyBtn.addEventListener('click', function() {
            const isAudioOnly = audioOnlyBtn.classList.contains('active');
            
            if (isAudioOnly) {
                // Switch to video mode
                audioOnlyBtn.classList.remove('active');
                audioOnlyBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
                audioOnlyBtn.title = 'Audio Only';
                mediaPlayer.style.display = 'block';
            } else {
                // Switch to audio-only mode
                audioOnlyBtn.classList.add('active');
                audioOnlyBtn.innerHTML = '<i class="fas fa-video"></i>';
                audioOnlyBtn.title = 'Video Mode';
                mediaPlayer.style.display = 'none';
            }
        });
    }
    
    function updateThemeDisplay(theme) {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.value = theme;
        }
    }
});