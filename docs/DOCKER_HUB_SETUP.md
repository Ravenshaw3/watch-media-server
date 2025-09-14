# Docker Hub Setup Without Docker Desktop

## 🚀 **Easy Solution: Use GitHub Actions**

Since you don't have Docker Desktop, we'll use GitHub Actions to automatically build and push your Docker image to Docker Hub. This is actually better because it's automated!

## 📋 **Step-by-Step Setup**

### **Step 1: Create Docker Hub Account**

1. Go to [hub.docker.com](https://hub.docker.com)
2. Sign up with username `ravenshaw3` (or your preferred username)
3. Verify your email address

### **Step 2: Create Docker Hub Repository**

1. Login to Docker Hub
2. Click **"Create Repository"**
3. Repository name: `watch-media-server`
4. Description: `Web-based media library management system for movies and TV shows`
5. Set to **Public**
6. Click **"Create"**

### **Step 3: Get Docker Hub Access Token**

1. Go to Docker Hub → Account Settings → Security
2. Click **"New Access Token"**
3. Access Token Description: `GitHub Actions - Watch Media Server`
4. Access permissions: **Read, Write, Delete**
5. Click **"Generate"**
6. **Copy the token** (you won't see it again!)

### **Step 4: Add Secrets to GitHub**

1. Go to your GitHub repository: `https://github.com/Ravenshaw3/watch-media-server`
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **"New repository secret"**
5. Add these two secrets:

   **Secret 1:**
   - Name: `DOCKER_USERNAME`
   - Value: `ravenshaw3` (your Docker Hub username)

   **Secret 2:**
   - Name: `DOCKER_PASSWORD`
   - Value: `your_docker_hub_access_token` (the token you copied)

### **Step 5: Trigger the Build**

1. Make a small change to any file (like adding a comment)
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Trigger Docker build"
   git push origin main
   ```

3. Go to your GitHub repository → **Actions** tab
4. Watch the workflow run and build your Docker image
5. It will automatically push to Docker Hub!

## ✅ **What Happens Automatically**

Once you push to GitHub, the workflow will:

1. **Build** your Docker image using the Dockerfile
2. **Test** the image to make sure it works
3. **Push** to Docker Hub as:
   - `ravenshaw3/watch-media-server:latest`
   - `ravenshaw3/watch-media-server:1.0.0`
   - `ravenshaw3/watch-media-server:commit-hash`

## 🎯 **Verify It Worked**

1. Go to [hub.docker.com/r/ravenshaw3/watch-media-server](https://hub.docker.com/r/ravenshaw3/watch-media-server)
2. You should see your image with multiple tags
3. Unraid users can now use your template!

## 🔄 **Future Updates**

Every time you push changes to the `main` branch:
- GitHub Actions automatically builds a new image
- Pushes it to Docker Hub
- Unraid users get the latest version

## 🆘 **Troubleshooting**

### **Issue: Workflow Fails**
- Check the **Actions** tab in GitHub for error details
- Make sure Docker Hub secrets are set correctly
- Verify Docker Hub repository exists and is public

### **Issue: Image Not Found**
- Wait a few minutes for the build to complete
- Check Docker Hub repository for the image
- Verify the repository name matches your template

### **Issue: Permission Denied**
- Check Docker Hub access token permissions
- Make sure the token has Read, Write, Delete access
- Verify the username in secrets matches your Docker Hub username

## 🎉 **Benefits of This Approach**

- ✅ **No local Docker needed**
- ✅ **Automatic builds** on every code change
- ✅ **Consistent builds** in clean environment
- ✅ **Version tagging** for releases
- ✅ **Free** (GitHub Actions free tier)
- ✅ **Secure** (secrets are encrypted)

## 📊 **Monitoring**

- **GitHub Actions**: Monitor build status and logs
- **Docker Hub**: Track downloads and usage
- **Unraid Community**: Get user feedback

---

**Once you complete these steps, your Watch Media Server will be automatically built and available for Unraid users!** 🎬

The GitHub Actions workflow will handle everything - you just need to set up the Docker Hub account and GitHub secrets!
