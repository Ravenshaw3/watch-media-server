# Watch Media Server - Refactoring Guide

## New Directory Structure

The application has been refactored into a more organized, modular structure:

```
Watch/
├── src/                          # Source code
│   ├── app/                      # Application factory and configuration
│   │   └── __init__.py          # App factory function
│   ├── api/                      # API route modules
│   │   ├── __init__.py
│   │   ├── auth_routes.py       # Authentication endpoints
│   │   └── media_routes.py      # Media management endpoints
│   ├── models/                   # Data models and business logic
│   │   ├── __init__.py
│   │   └── media_manager.py     # Media file management
│   ├── services/                 # External service integrations
│   │   ├── __init__.py
│   │   ├── auth_service.py      # User authentication
│   │   ├── cache_service.py     # Caching layer
│   │   ├── database_service.py  # Database operations
│   │   └── ...                  # Other services
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       ├── config.py            # Configuration management
│       └── media_formatter.py   # Media formatting utilities
├── docs/                         # Documentation
│   ├── README.md
│   ├── REFACTORING_GUIDE.md
│   └── ...                      # Other documentation
├── scripts/                      # Build and deployment scripts
│   ├── build-and-push.bat
│   ├── build-and-push.sh
│   └── ...                      # Other scripts
├── static/                       # Static web assets
├── templates/                    # HTML templates
├── tests/                        # Test files
├── main.py                       # New application entry point
├── app_backup.py                 # Backup of original app.py
└── requirements.txt              # Python dependencies
```

## Key Changes

### 1. Modular Architecture
- **Separation of Concerns**: Each module has a single responsibility
- **API Routes**: Authentication and media routes are now in separate modules
- **Models**: Business logic is separated from API logic
- **Services**: External integrations are organized in the services directory

### 2. Application Factory Pattern
- The main application is now created using a factory function in `src/app/__init__.py`
- This allows for better testing and configuration management
- Services are initialized once and shared across the application

### 3. Blueprint-based Routing
- API routes are organized using Flask Blueprints
- Each blueprint handles a specific domain (auth, media, etc.)
- Routes are registered with the main application

### 4. Improved Import Structure
- All imports are relative to the `src` package
- Clear separation between internal and external dependencies
- Better organization of imports

## Migration Notes

### For Developers
1. **New Entry Point**: Use `main.py` instead of `app.py`
2. **Import Changes**: Update imports to use the new structure
3. **Service Access**: Services are now accessed through the app context

### For Deployment
1. **Docker**: The Dockerfile has been updated to use `main.py`
2. **Scripts**: Build scripts have been moved to the `scripts/` directory
3. **Documentation**: All documentation is now in the `docs/` directory

## Benefits

1. **Maintainability**: Easier to find and modify specific functionality
2. **Testability**: Each module can be tested independently
3. **Scalability**: New features can be added as separate modules
4. **Code Reuse**: Common functionality is centralized in utils
5. **Documentation**: Better organization of project documentation

## Next Steps

1. **Testing**: Update test files to work with the new structure
2. **Documentation**: Update API documentation to reflect new routes
3. **Performance**: Monitor performance after refactoring
4. **Features**: Add new features using the modular structure
