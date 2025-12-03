# Scripts Directory

This directory contains various scripts used for development, testing, and maintenance purposes. These scripts are primarily intended for developers and maintainers of the VabHub project, not for regular end users.

## Directory Structure

```
scripts/
├── windows/          # Windows-specific scripts (.bat, .ps1)
├── python/           # Python utility and test scripts
└── tools/            # Repository maintenance and management scripts
```

## Usage Guidelines

### For Developers

These scripts are provided as convenience tools for development and testing. They are not part of the official deployment process.

### For End Users

**Important**: The official recommended deployment method for VabHub is Docker/docker-compose, as described in:
- [README.md](../../README.md)
- [GETTING_STARTED.md](../../docs/user/GETTING_STARTED.md)
- [DEPLOY_WITH_DOCKER.md](../../docs/user/DEPLOY_WITH_DOCKER.md)

You do not need to use these scripts for normal deployment or usage of VabHub.

## Script Categories

### windows/
- **Purpose**: Development and debugging scripts for Windows environments
- **Examples**:
  - `start_backend.bat`: Start backend service locally (development only)
  - `启动前端.bat`: Start frontend service locally (development only)
  - Various test and diagnostic scripts

### python/
- **Purpose**: Test scripts and utility tools written in Python
- **Examples**:
  - `test_video_autoloop.py`: Test script for video auto-loop functionality
  - `test_recommendation_and_upload.py`: Test script for recommendation settings and file uploads

### tools/
- **Purpose**: Repository maintenance and management scripts
- **Examples**:
  - `backup_and_remove_root_md.ps1`: Script for cleaning up root-level Markdown files
  - `move_scripts.ps1`: Script used to organize the scripts directory itself

## Important Notes

1. These scripts are not officially supported for production use
2. They may require specific development dependencies to be installed
3. Some scripts may modify your development environment
4. Always read the script content before executing to understand its effects
5. Use at your own risk

## Contributing

When adding new scripts, please follow these guidelines:

1. Place the script in the appropriate subdirectory based on its type and purpose
2. Ensure the script has a clear, descriptive name
3. Add comments to explain the script's purpose and usage
4. Avoid hardcoding paths or environment-specific settings
5. Test the script to ensure it works correctly

If you're unsure where to place a new script, please ask the development team for guidance.