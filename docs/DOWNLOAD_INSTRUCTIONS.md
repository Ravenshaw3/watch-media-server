# How to Download Watch Media Server

## 📥 Download Options

### Option 1: Download as ZIP Archive (Recommended)

1. **Download the Complete Project**:
   - Click the **"Code"** button (green button) on the repository page
   - Select **"Download ZIP"**
   - Save the file to your computer
   - Extract the ZIP file to a folder on your computer

2. **What You'll Get**:
   ```
   Watch-main/
   ├── app.py
   ├── console.py
   ├── media_formatter.py
   ├── requirements.txt
   ├── Dockerfile
   ├── docker-compose.yml
   ├── watch-template.xml           ← This is what you need for Unraid
   ├── setup.sh
   ├── setup.bat
   ├── README.md
   ├── UNRAID_INSTALLATION.md       ← Installation guide
   ├── UNRAID_INSTALLATION_FLOW.md  ← Quick reference
   ├── templates/
   │   └── index.html
   └── static/
       ├── css/
       ├── js/
       └── images/
   ```

### Option 2: Clone with Git (For Developers)

If you have Git installed:

```bash
git clone https://github.com/your-username/watch-media-server.git
cd watch-media-server
```

### Option 3: Download Individual Files

If you only need specific files for Unraid:

1. **Essential Files for Unraid**:
   - `watch-template.xml` - Unraid Docker template
   - `UNRAID_INSTALLATION.md` - Installation guide
   - `README.md` - General documentation

2. **How to Download Individual Files**:
   - Navigate to the file in the repository
   - Click on the file name
   - Click the **"Raw"** button
   - Right-click and **"Save As"** to download

## 🎯 For Unraid Users - Quick Download

### Step 1: Download the Template
1. Go to the repository page
2. Click on `watch-template.xml`
3. Click the **"Raw"** button
4. Right-click and **"Save As"**
5. Save as `watch-template.xml` to your computer

### Step 2: Download the Installation Guide
1. Click on `UNRAID_INSTALLATION.md`
2. Click the **"Raw"** button
3. Right-click and **"Save As"**
4. Save as `UNRAID_INSTALLATION.md` to your computer

### Step 3: You're Ready!
- You now have everything needed for Unraid installation
- Follow the instructions in `UNRAID_INSTALLATION.md`

## 📋 What You Need for Unraid

### Minimum Required Files:
- ✅ `watch-template.xml` - Docker template
- ✅ `UNRAID_INSTALLATION.md` - Installation guide

### Optional but Helpful:
- 📖 `README.md` - General project information
- 📖 `UNRAID_INSTALLATION_FLOW.md` - Quick reference guide
- 📖 `PROJECT_OVERVIEW.md` - Feature overview

## 🚀 After Download - Next Steps

### For Unraid Installation:
1. **Extract the ZIP file** (if downloaded as ZIP)
2. **Locate `watch-template.xml`**
3. **Follow the Unraid installation guide**:
   - Open `UNRAID_INSTALLATION.md`
   - Follow the step-by-step instructions
   - Import the template into Unraid

### For Docker Compose Installation:
1. **Extract the ZIP file**
2. **Run the setup script**:
   - Windows: Double-click `setup.bat`
   - Linux/macOS: Run `./setup.sh`

## 🔗 Repository Information

### If This is a GitHub Repository:
- **Repository URL**: `https://github.com/your-username/watch-media-server`
- **Latest Release**: Check the "Releases" section for stable versions
- **Issues**: Report problems in the "Issues" section

### If This is a Local Project:
- All files are already in your `P:\Watch` directory
- You can copy the files to another location
- Or use them directly from the current location

## 📁 File Structure After Download

```
Your Download Location/
├── watch-template.xml           ← Import this into Unraid
├── UNRAID_INSTALLATION.md       ← Follow this guide
├── UNRAID_INSTALLATION_FLOW.md  ← Quick reference
├── README.md                    ← General documentation
├── PROJECT_OVERVIEW.md          ← Feature overview
├── app.py                       ← Main application (for Docker)
├── console.py                   ← Console interface
├── media_formatter.py           ← File organization
├── requirements.txt             ← Python dependencies
├── Dockerfile                   ← Docker configuration
├── docker-compose.yml           ← Docker Compose setup
├── setup.sh                     ← Linux/macOS setup script
├── setup.bat                    ← Windows setup script
├── templates/
│   └── index.html               ← Web interface
└── static/
    ├── css/
    │   └── style.css            ← Styling
    ├── js/
    │   └── app.js               ← Frontend JavaScript
    └── images/                  ← Static assets
```

## ⚡ Quick Start for Unraid

1. **Download** the project (ZIP or individual files)
2. **Extract** if downloaded as ZIP
3. **Import** `watch-template.xml` into Unraid
4. **Configure** your media paths
5. **Start** the container
6. **Access** at `http://YOUR_UNRAID_IP:8080`

## 🆘 Need Help?

- **Installation Issues**: Check `UNRAID_INSTALLATION.md`
- **General Questions**: Check `README.md`
- **Feature Overview**: Check `PROJECT_OVERVIEW.md`
- **Quick Reference**: Check `UNRAID_INSTALLATION_FLOW.md`

---

**Ready to install?** Follow the Unraid installation guide and you'll have your media server running in minutes!
