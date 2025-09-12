# PWA (Progressive Web App) Service for Watch Media Server
import os
import json
from typing import Dict, List
from datetime import datetime

class PWAService:
    def __init__(self):
        self.manifest = {
            "name": "Watch Media Server",
            "short_name": "Watch",
            "description": "Personal media library management and streaming",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#1a1a2e",
            "theme_color": "#667eea",
            "orientation": "portrait-primary",
            "scope": "/",
            "lang": "en",
            "categories": ["entertainment", "multimedia"],
            "icons": [
                {
                    "src": "/static/images/icon-72x72.png",
                    "sizes": "72x72",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/images/icon-96x96.png",
                    "sizes": "96x96",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/images/icon-128x128.png",
                    "sizes": "128x128",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/images/icon-144x144.png",
                    "sizes": "144x144",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/images/icon-152x152.png",
                    "sizes": "152x152",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/images/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/images/icon-384x384.png",
                    "sizes": "384x384",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/images/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
            ],
            "screenshots": [
                {
                    "src": "/static/images/screenshot-mobile.png",
                    "sizes": "390x844",
                    "type": "image/png",
                    "form_factor": "narrow"
                },
                {
                    "src": "/static/images/screenshot-desktop.png",
                    "sizes": "1280x720",
                    "type": "image/png",
                    "form_factor": "wide"
                }
            ],
            "shortcuts": [
                {
                    "name": "Recently Added",
                    "short_name": "Recent",
                    "description": "View recently added media",
                    "url": "/?tab=recent",
                    "icons": [
                        {
                            "src": "/static/images/shortcut-recent.png",
                            "sizes": "96x96"
                        }
                    ]
                },
                {
                    "name": "Continue Watching",
                    "short_name": "Continue",
                    "description": "Resume watching your media",
                    "url": "/?tab=continue",
                    "icons": [
                        {
                            "src": "/static/images/shortcut-continue.png",
                            "sizes": "96x96"
                        }
                    ]
                },
                {
                    "name": "Search",
                    "short_name": "Search",
                    "description": "Search your media library",
                    "url": "/?tab=search",
                    "icons": [
                        {
                            "src": "/static/images/shortcut-search.png",
                            "sizes": "96x96"
                        }
                    ]
                }
            ],
            "related_applications": [],
            "prefer_related_applications": False,
            "edge_side_panel": {
                "preferred_width": 400
            },
            "launch_handler": {
                "client_mode": "navigate-existing"
            }
        }
        
        self.service_worker_script = self.generate_service_worker()
        self.offline_page = self.generate_offline_page()
    
    def get_manifest(self) -> Dict:
        """Get PWA manifest"""
        return self.manifest
    
    def generate_service_worker(self) -> str:
        """Generate service worker script for offline support"""
        return """
const CACHE_NAME = 'watch-media-v1';
const OFFLINE_URL = '/offline';

// Files to cache for offline use
const STATIC_CACHE_URLS = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/images/icon-192x192.png',
    '/static/images/icon-512x512.png',
    '/offline'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('Service Worker: Install');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                console.log('Service Worker: Skip waiting');
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activate');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker: Claiming clients');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Skip chrome-extension and other non-http requests
    if (!event.request.url.startsWith('http')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version or fetch from network
                if (response) {
                    console.log('Service Worker: Serving from cache', event.request.url);
                    return response;
                }
                
                console.log('Service Worker: Fetching from network', event.request.url);
                return fetch(event.request)
                    .then(response => {
                        // Don't cache if not a valid response
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // Clone the response
                        const responseToCache = response.clone();
                        
                        // Cache API responses and static assets
                        if (event.request.url.includes('/api/') || 
                            event.request.url.includes('/static/')) {
                            caches.open(CACHE_NAME)
                                .then(cache => {
                                    cache.put(event.request, responseToCache);
                                });
                        }
                        
                        return response;
                    })
                    .catch(() => {
                        // If offline and request is for a page, show offline page
                        if (event.request.destination === 'document') {
                            return caches.match(OFFLINE_URL);
                        }
                        
                        // For other requests, return a basic response
                        return new Response('Offline', {
                            status: 503,
                            statusText: 'Service Unavailable'
                        });
                    });
            })
    );
});

// Background sync for play history
self.addEventListener('sync', event => {
    if (event.tag === 'play-history-sync') {
        console.log('Service Worker: Background sync for play history');
        event.waitUntil(syncPlayHistory());
    }
});

// Push notifications
self.addEventListener('push', event => {
    console.log('Service Worker: Push received');
    
    const options = {
        body: event.data ? event.data.text() : 'New content available',
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'View Now',
                icon: '/static/images/action-view.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/images/action-close.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Watch Media Server', options)
    );
});

// Notification click
self.addEventListener('notificationclick', event => {
    console.log('Service Worker: Notification click');
    
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Helper function for background sync
async function syncPlayHistory() {
    try {
        // Get pending play history from IndexedDB
        const pendingHistory = await getPendingPlayHistory();
        
        for (const record of pendingHistory) {
            try {
                const response = await fetch('/api/play-history', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${record.token}`
                    },
                    body: JSON.stringify({
                        media_id: record.media_id,
                        duration_watched: record.duration_watched,
                        completed: record.completed
                    })
                });
                
                if (response.ok) {
                    // Remove from pending queue
                    await removePendingPlayHistory(record.id);
                }
            } catch (error) {
                console.error('Failed to sync play history:', error);
            }
        }
    } catch (error) {
        console.error('Background sync error:', error);
    }
}

// IndexedDB helpers for offline storage
function getPendingPlayHistory() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('WatchMediaDB', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['playHistory'], 'readonly');
            const store = transaction.objectStore('playHistory');
            const getAllRequest = store.getAll();
            
            getAllRequest.onsuccess = () => resolve(getAllRequest.result);
            getAllRequest.onerror = () => reject(getAllRequest.error);
        };
        
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains('playHistory')) {
                db.createObjectStore('playHistory', { keyPath: 'id', autoIncrement: true });
            }
        };
    });
}

function removePendingPlayHistory(id) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('WatchMediaDB', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['playHistory'], 'readwrite');
            const store = transaction.objectStore('playHistory');
            const deleteRequest = store.delete(id);
            
            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => reject(deleteRequest.error);
        };
    });
}
"""
    
    def generate_offline_page(self) -> str:
        """Generate offline page HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline - Watch Media Server</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .offline-container {
            max-width: 500px;
            padding: 40px 20px;
        }
        .offline-icon {
            font-size: 80px;
            margin-bottom: 20px;
            opacity: 0.7;
        }
        h1 {
            font-size: 32px;
            margin-bottom: 20px;
            color: #667eea;
        }
        p {
            font-size: 18px;
            margin-bottom: 30px;
            opacity: 0.9;
            line-height: 1.6;
        }
        .retry-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        .retry-btn:hover {
            transform: translateY(-2px);
        }
        .features {
            margin-top: 40px;
            text-align: left;
        }
        .feature {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            opacity: 0.8;
        }
        .feature i {
            margin-right: 15px;
            color: #667eea;
            width: 20px;
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="offline-container">
        <div class="offline-icon">
            <i class="fas fa-wifi-slash"></i>
        </div>
        <h1>You're Offline</h1>
        <p>It looks like you've lost your internet connection. Don't worry, you can still access some features while offline.</p>
        
        <button class="retry-btn" onclick="window.location.reload()">
            <i class="fas fa-refresh"></i> Try Again
        </button>
        
        <div class="features">
            <h3>Available Offline:</h3>
            <div class="feature">
                <i class="fas fa-check"></i>
                <span>Browse cached media</span>
            </div>
            <div class="feature">
                <i class="fas fa-check"></i>
                <span>View your watchlist</span>
            </div>
            <div class="feature">
                <i class="fas fa-check"></i>
                <span>Access settings</span>
            </div>
            <div class="feature">
                <i class="fas fa-check"></i>
                <span>Play history sync (when online)</span>
            </div>
        </div>
    </div>
    
    <script>
        // Check online status
        window.addEventListener('online', () => {
            window.location.reload();
        });
        
        // Auto-retry every 30 seconds
        setInterval(() => {
            if (navigator.onLine) {
                window.location.reload();
            }
        }, 30000);
    </script>
</body>
</html>
"""
    
    def generate_install_prompt(self) -> str:
        """Generate install prompt HTML"""
        return """
<div id="installPrompt" class="install-prompt" style="display: none;">
    <div class="install-content">
        <div class="install-icon">
            <i class="fas fa-download"></i>
        </div>
        <div class="install-text">
            <h3>Install Watch Media Server</h3>
            <p>Add to your home screen for quick access and offline viewing</p>
        </div>
        <div class="install-actions">
            <button id="installBtn" class="btn btn-primary">
                <i class="fas fa-plus"></i> Install
            </button>
            <button id="dismissInstall" class="btn btn-secondary">
                <i class="fas fa-times"></i> Not Now
            </button>
        </div>
    </div>
</div>

<style>
.install-prompt {
    position: fixed;
    bottom: 20px;
    left: 20px;
    right: 20px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    animation: slideUp 0.3s ease;
}

.dark-theme .install-prompt {
    background: #2d2d2d;
    color: #e0e0e0;
}

.install-content {
    display: flex;
    align-items: center;
    padding: 15px;
    gap: 15px;
}

.install-icon {
    font-size: 24px;
    color: #667eea;
}

.install-text {
    flex: 1;
}

.install-text h3 {
    margin: 0 0 5px 0;
    font-size: 16px;
}

.install-text p {
    margin: 0;
    font-size: 14px;
    opacity: 0.8;
}

.install-actions {
    display: flex;
    gap: 10px;
}

.install-actions .btn {
    padding: 8px 12px;
    font-size: 12px;
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (max-width: 768px) {
    .install-prompt {
        left: 10px;
        right: 10px;
        bottom: 10px;
    }
    
    .install-content {
        flex-direction: column;
        text-align: center;
    }
    
    .install-actions {
        width: 100%;
        justify-content: center;
    }
}
</style>

<script>
class InstallPrompt {
    constructor() {
        this.deferredPrompt = null;
        this.installPrompt = document.getElementById('installPrompt');
        this.installBtn = document.getElementById('installBtn');
        this.dismissBtn = document.getElementById('dismissInstall');
        
        this.init();
    }
    
    init() {
        // Listen for beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });
        
        // Listen for app installed event
        window.addEventListener('appinstalled', () => {
            this.hideInstallPrompt();
            console.log('PWA was installed');
        });
        
        // Install button click
        this.installBtn.addEventListener('click', () => {
            this.installApp();
        });
        
        // Dismiss button click
        this.dismissBtn.addEventListener('click', () => {
            this.hideInstallPrompt();
            // Don't show again for this session
            sessionStorage.setItem('installPromptDismissed', 'true');
        });
        
        // Check if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            console.log('PWA is already installed');
        }
    }
    
    showInstallPrompt() {
        // Don't show if dismissed this session
        if (sessionStorage.getItem('installPromptDismissed')) {
            return;
        }
        
        // Don't show if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            return;
        }
        
        this.installPrompt.style.display = 'block';
    }
    
    hideInstallPrompt() {
        this.installPrompt.style.display = 'none';
    }
    
    async installApp() {
        if (!this.deferredPrompt) {
            return;
        }
        
        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;
        
        if (outcome === 'accepted') {
            console.log('User accepted the install prompt');
        } else {
            console.log('User dismissed the install prompt');
        }
        
        this.deferredPrompt = null;
        this.hideInstallPrompt();
    }
}

// Initialize install prompt when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new InstallPrompt();
});
</script>
"""
    
    def get_meta_tags(self) -> str:
        """Get PWA meta tags for HTML head"""
        return """
<!-- PWA Meta Tags -->
<meta name="application-name" content="Watch">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Watch">
<meta name="description" content="Personal media library management and streaming">
<meta name="format-detection" content="telephone=no">
<meta name="mobile-web-app-capable" content="yes">
<meta name="msapplication-config" content="/static/images/browserconfig.xml">
<meta name="msapplication-TileColor" content="#667eea">
<meta name="msapplication-tap-highlight" content="no">
<meta name="theme-color" content="#667eea">

<!-- Apple Touch Icons -->
<link rel="apple-touch-icon" href="/static/images/icon-152x152.png">
<link rel="apple-touch-icon" sizes="152x152" href="/static/images/icon-152x152.png">
<link rel="apple-touch-icon" sizes="180x180" href="/static/images/icon-180x180.png">
<link rel="apple-touch-icon" sizes="167x167" href="/static/images/icon-167x167.png">

<!-- Favicon -->
<link rel="icon" type="image/png" sizes="32x32" href="/static/images/icon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/static/images/icon-16x16.png">
<link rel="shortcut icon" href="/static/images/favicon.ico">

<!-- Manifest -->
<link rel="manifest" href="/manifest.json">

<!-- Splash Screens -->
<link rel="apple-touch-startup-image" href="/static/images/splash-640x1136.png" media="(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)">
<link rel="apple-touch-startup-image" href="/static/images/splash-750x1334.png" media="(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2)">
<link rel="apple-touch-startup-image" href="/static/images/splash-1242x2208.png" media="(device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3)">
<link rel="apple-touch-startup-image" href="/static/images/splash-1125x2436.png" media="(device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3)">
"""
