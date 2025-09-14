# API Documentation Service for Watch Media Server
import os
import json
from typing import Dict, List, Any
from datetime import datetime

class APIDocsService:
    def __init__(self):
        self.api_spec = self._generate_openapi_spec()
    
    def _generate_openapi_spec(self) -> Dict:
        """Generate OpenAPI 3.0 specification"""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Watch Media Server API",
                "description": "A comprehensive media library management and streaming API",
                "version": "1.0.0",
                "contact": {
                    "name": "Watch Media Server",
                    "url": "https://github.com/your-username/watch-media-server"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:5000",
                    "description": "Development server"
                },
                {
                    "url": "https://your-domain.com",
                    "description": "Production server"
                }
            ],
            "tags": [
                {"name": "Authentication", "description": "User authentication and authorization"},
                {"name": "Media", "description": "Media library management"},
                {"name": "Search", "description": "Search and filtering"},
                {"name": "Streaming", "description": "Media streaming and transcoding"},
                {"name": "User", "description": "User-specific features"},
                {"name": "Admin", "description": "Administrative functions"},
                {"name": "PWA", "description": "Progressive Web App features"}
            ],
            "paths": self._generate_paths(),
            "components": self._generate_components()
        }
    
    def _generate_paths(self) -> Dict:
        """Generate API paths specification"""
        return {
            "/api/auth/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "User login",
                    "description": "Authenticate user and return JWT token",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/LoginRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/LoginResponse"
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Invalid credentials",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/auth/register": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "User registration",
                    "description": "Register a new user account",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/RegisterRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Registration successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/RegisterResponse"
                                    }
                                }
                            }
                        },
                        "409": {
                            "description": "Username or email already exists",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/media": {
                "get": {
                    "tags": ["Media"],
                    "summary": "Get media library",
                    "description": "Retrieve all media files with optional filtering",
                    "parameters": [
                        {
                            "name": "type",
                            "in": "query",
                            "description": "Filter by media type",
                            "schema": {
                                "type": "string",
                                "enum": ["movie", "tv_show", "episode"]
                            }
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "Number of results to return",
                            "schema": {
                                "type": "integer",
                                "default": 50
                            }
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "description": "Number of results to skip",
                            "schema": {
                                "type": "integer",
                                "default": 0
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Media library retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/MediaFile"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/search": {
                "get": {
                    "tags": ["Search"],
                    "summary": "Search media",
                    "description": "Search media files with advanced filtering",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "description": "Search query",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        },
                        {
                            "name": "type",
                            "in": "query",
                            "description": "Filter by media type",
                            "schema": {
                                "type": "string",
                                "enum": ["movie", "tv_show", "episode"]
                            }
                        },
                        {
                            "name": "year_from",
                            "in": "query",
                            "description": "Filter by year (from)",
                            "schema": {
                                "type": "integer"
                            }
                        },
                        {
                            "name": "year_to",
                            "in": "query",
                            "description": "Filter by year (to)",
                            "schema": {
                                "type": "integer"
                            }
                        },
                        {
                            "name": "genres",
                            "in": "query",
                            "description": "Filter by genres (comma-separated)",
                            "schema": {
                                "type": "string"
                            }
                        },
                        {
                            "name": "rating_min",
                            "in": "query",
                            "description": "Minimum rating",
                            "schema": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 10
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Search results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/MediaFile"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/stream/{file_id}": {
                "get": {
                    "tags": ["Streaming"],
                    "summary": "Stream media file",
                    "description": "Stream a media file with optional quality selection",
                    "parameters": [
                        {
                            "name": "file_id",
                            "in": "path",
                            "required": True,
                            "description": "Media file ID",
                            "schema": {
                                "type": "integer"
                            }
                        },
                        {
                            "name": "quality",
                            "in": "query",
                            "description": "Streaming quality",
                            "schema": {
                                "type": "string",
                                "enum": ["240p", "360p", "480p", "720p", "1080p", "4k", "original"],
                                "default": "720p"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Media file stream",
                            "content": {
                                "video/mp4": {
                                    "schema": {
                                        "type": "string",
                                        "format": "binary"
                                    }
                                }
                            }
                        },
                        "202": {
                            "description": "Transcoding in progress",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TranscodeStatus"
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "File not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    },
                    "security": [{"BearerAuth": []}]
                }
            },
            "/api/watchlist": {
                "get": {
                    "tags": ["User"],
                    "summary": "Get user watchlist",
                    "description": "Retrieve user's watchlist",
                    "responses": {
                        "200": {
                            "description": "User watchlist",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/MediaFile"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "security": [{"BearerAuth": []}]
                }
            },
            "/api/watchlist/{media_id}": {
                "post": {
                    "tags": ["User"],
                    "summary": "Add to watchlist",
                    "description": "Add media to user's watchlist",
                    "parameters": [
                        {
                            "name": "media_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "integer"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Added to watchlist",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SuccessResponse"
                                    }
                                }
                            }
                        }
                    },
                    "security": [{"BearerAuth": []}]
                },
                "delete": {
                    "tags": ["User"],
                    "summary": "Remove from watchlist",
                    "description": "Remove media from user's watchlist",
                    "parameters": [
                        {
                            "name": "media_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "integer"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Removed from watchlist",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SuccessResponse"
                                    }
                                }
                            }
                        }
                    },
                    "security": [{"BearerAuth": []}]
                }
            },
            "/api/recommendations": {
                "get": {
                    "tags": ["User"],
                    "summary": "Get recommendations",
                    "description": "Get personalized media recommendations",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "Number of recommendations",
                            "schema": {
                                "type": "integer",
                                "default": 20
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Personalized recommendations",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/MediaFile"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "security": [{"BearerAuth": []}]
                }
            },
            "/api/transcode/{media_id}": {
                "get": {
                    "tags": ["Streaming"],
                    "summary": "Start transcoding",
                    "description": "Start transcoding a media file to specified quality",
                    "parameters": [
                        {
                            "name": "media_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "integer"
                            }
                        },
                        {
                            "name": "quality",
                            "in": "query",
                            "description": "Target quality",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": ["240p", "360p", "480p", "720p", "1080p", "4k"]
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Transcoding started",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TranscodeResponse"
                                    }
                                }
                            }
                        }
                    },
                    "security": [{"BearerAuth": []}]
                }
            },
            "/api/transcode/status/{job_id}": {
                "get": {
                    "tags": ["Streaming"],
                    "summary": "Get transcoding status",
                    "description": "Get status of a transcoding job",
                    "parameters": [
                        {
                            "name": "job_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "integer"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Transcoding status",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TranscodeStatus"
                                    }
                                }
                            }
                        }
                    },
                    "security": [{"BearerAuth": []}]
                }
            },
            "/api/admin/users": {
                "get": {
                    "tags": ["Admin"],
                    "summary": "Get all users",
                    "description": "Get list of all users (admin only)",
                    "responses": {
                        "200": {
                            "description": "List of users",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/User"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "security": [{"BearerAuth": []}]
                }
            },
            "/manifest.json": {
                "get": {
                    "tags": ["PWA"],
                    "summary": "PWA Manifest",
                    "description": "Get Progressive Web App manifest",
                    "responses": {
                        "200": {
                            "description": "PWA manifest",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/PWAManifest"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/sw.js": {
                "get": {
                    "tags": ["PWA"],
                    "summary": "Service Worker",
                    "description": "Get service worker script",
                    "responses": {
                        "200": {
                            "description": "Service worker script",
                            "content": {
                                "application/javascript": {
                                    "schema": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _generate_components(self) -> Dict:
        """Generate OpenAPI components"""
        return {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            },
            "schemas": {
                "LoginRequest": {
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Username or email"
                        },
                        "password": {
                            "type": "string",
                            "format": "password",
                            "description": "User password"
                        }
                    }
                },
                "LoginResponse": {
                    "type": "object",
                    "properties": {
                        "token": {
                            "type": "string",
                            "description": "JWT access token"
                        },
                        "user": {
                            "$ref": "#/components/schemas/User"
                        }
                    }
                },
                "RegisterRequest": {
                    "type": "object",
                    "required": ["username", "email", "password"],
                    "properties": {
                        "username": {
                            "type": "string",
                            "minLength": 3,
                            "description": "Username"
                        },
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address"
                        },
                        "password": {
                            "type": "string",
                            "minLength": 6,
                            "format": "password",
                            "description": "Password"
                        }
                    }
                },
                "RegisterResponse": {
                    "type": "object",
                    "properties": {
                        "token": {
                            "type": "string",
                            "description": "JWT access token"
                        },
                        "user": {
                            "$ref": "#/components/schemas/User"
                        }
                    }
                },
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "User ID"
                        },
                        "username": {
                            "type": "string",
                            "description": "Username"
                        },
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address"
                        },
                        "role": {
                            "type": "string",
                            "enum": ["user", "admin"],
                            "description": "User role"
                        },
                        "preferences": {
                            "type": "object",
                            "description": "User preferences"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Account creation date"
                        },
                        "last_login": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Last login date"
                        }
                    }
                },
                "MediaFile": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "Media file ID"
                        },
                        "filename": {
                            "type": "string",
                            "description": "File name"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File path"
                        },
                        "media_type": {
                            "type": "string",
                            "enum": ["movie", "tv_show", "episode"],
                            "description": "Media type"
                        },
                        "file_size": {
                            "type": "integer",
                            "description": "File size in bytes"
                        },
                        "duration": {
                            "type": "number",
                            "description": "Duration in seconds"
                        },
                        "title": {
                            "type": "string",
                            "description": "Media title"
                        },
                        "year": {
                            "type": "integer",
                            "description": "Release year"
                        },
                        "rating": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 10,
                            "description": "Rating"
                        },
                        "genres": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Genres"
                        },
                        "poster_url": {
                            "type": "string",
                            "format": "uri",
                            "description": "Poster image URL"
                        },
                        "backdrop_url": {
                            "type": "string",
                            "format": "uri",
                            "description": "Backdrop image URL"
                        },
                        "overview": {
                            "type": "string",
                            "description": "Media overview"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Added to library date"
                        }
                    }
                },
                "TranscodeResponse": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "integer",
                            "description": "Transcoding job ID"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["queued", "processing", "completed", "failed"],
                            "description": "Job status"
                        },
                        "message": {
                            "type": "string",
                            "description": "Status message"
                        }
                    }
                },
                "TranscodeStatus": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "integer",
                            "description": "Transcoding job ID"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["queued", "processing", "completed", "failed"],
                            "description": "Job status"
                        },
                        "progress": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Progress percentage"
                        },
                        "error_message": {
                            "type": "string",
                            "description": "Error message if failed"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Output file path"
                        },
                        "started_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Job start time"
                        },
                        "completed_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Job completion time"
                        }
                    }
                },
                "SuccessResponse": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Success message"
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "string",
                            "description": "Error message"
                        }
                    }
                },
                "PWAManifest": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "App name"
                        },
                        "short_name": {
                            "type": "string",
                            "description": "Short app name"
                        },
                        "description": {
                            "type": "string",
                            "description": "App description"
                        },
                        "start_url": {
                            "type": "string",
                            "description": "Start URL"
                        },
                        "display": {
                            "type": "string",
                            "enum": ["fullscreen", "standalone", "minimal-ui", "browser"],
                            "description": "Display mode"
                        },
                        "theme_color": {
                            "type": "string",
                            "description": "Theme color"
                        },
                        "background_color": {
                            "type": "string",
                            "description": "Background color"
                        },
                        "icons": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "src": {
                                        "type": "string",
                                        "description": "Icon source"
                                    },
                                    "sizes": {
                                        "type": "string",
                                        "description": "Icon sizes"
                                    },
                                    "type": {
                                        "type": "string",
                                        "description": "Icon type"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def get_openapi_spec(self) -> Dict:
        """Get OpenAPI specification"""
        return self.api_spec
    
    def get_api_docs_html(self) -> str:
        """Generate HTML documentation page"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watch Media Server API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
        .swagger-ui .topbar {{
            display: none;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: '/api/docs/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                tryItOutEnabled: true,
                requestInterceptor: function(request) {{
                    // Add authentication token if available
                    const token = localStorage.getItem('access_token');
                    if (token) {{
                        request.headers.Authorization = 'Bearer ' + token;
                    }}
                    return request;
                }}
            }});
        }};
    </script>
</body>
</html>
        """

# API docs service instance
api_docs_service = APIDocsService()
