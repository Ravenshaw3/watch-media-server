# Docker Image Setup for Unraid

## 🐳 **Why You Need a Docker Image**

For Unraid users to automatically download and run your Watch Media Server, you need to build and push a Docker image to a container registry. Unraid will then pull this image when users install your template.

## 📋 **Current Status**

- ✅ **Template**: Configured to use `ravenshaw3/watch-media-server:latest`
- ❌ **Docker Image**: Not yet built/pushed to registry
- ❌ **Registry**: Needs to be set up

## 🚀 **Setup Options**

### **Option 1: Docker Hub (Recommended for Unraid)**

Docker Hub is the most compatible with Unraid and easiest for users.

#### **Step 1: Create Docker Hub Repository**

1. Go to [hub.docker.com](https://hub.docker.com)
2. Sign up/Login with username `ravenshaw3`
3. Click "Create Repository"
4. Repository name: `watch-media-server`
5. Description: "Web-based media library management system"
6. Set to **Public**
7. Click "Create"

#### **Step 2: Build and Push Image**

**Windows:**
```bash
build-and-push.bat
```

**Linux/macOS:**
```bash
chmod +x build-and-push.sh
./build-and-push.sh
```

**Manual Commands:**
```bash
# Build the image
docker build -t ravenshaw3/watch-media-server:latest .

# Tag for version
docker tag ravenshaw3/watch-media-server:latest ravenshaw3/watch-media-server:1.0.0

# Login to Docker Hub
docker login

# Push images
docker push ravenshaw3/watch-media-server:latest
docker push ravenshaw3/watch-media-server:1.0.0
```

#### **Step 3: Verify Upload**

- Visit: `https://hub.docker.com/r/ravenshaw3/watch-media-server`
- Verify both `latest` and `1.0.0` tags are available
- Test pulling the image: `docker pull ravenshaw3/watch-media-server:latest`

### **Option 2: GitHub Container Registry**

Alternative option using GitHub's container registry.

#### **Step 1: Create GitHub Personal Access Token**

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes: `write:packages`, `read:packages`, `delete:packages`
4. Generate and copy the token

#### **Step 2: Build and Push to GitHub Registry**

**Windows:**
```bash
build-github-registry.bat
```

**Manual Commands:**
```bash
# Build for GitHub Container Registry
docker build -t ghcr.io/ravenshaw3/watch-media-server:latest .

# Tag for version
docker tag ghcr.io/ravenshaw3/watch-media-server:latest ghcr.io/ravenshaw3/watch-media-server:1.0.0

# Login to GitHub Container Registry
docker login ghcr.io
# Username: ravenshaw3
# Password: your_github_token

# Push images
docker push ghcr.io/ravenshaw3/watch-media-server:latest
docker push ghcr.io/ravenshaw3/watch-media-server:1.0.0
```

#### **Step 3: Update Template (if using GitHub Registry)**

If you choose GitHub Container Registry, update the template:

```xml
<Repository>ghcr.io/ravenshaw3/watch-media-server:latest</Repository>
<Registry>https://ghcr.io/</Registry>
```

## 🔧 **Template Configuration**

Your current template is configured for Docker Hub:

```xml
<Repository>ravenshaw3/watch-media-server:latest</Repository>
<Registry>https://hub.docker.com/</Registry>
```

This is perfect for Unraid users!

## ✅ **Verification Steps**

### **1. Test Local Build**
```bash
docker build -t watch-media-server:test .
docker run -d -p 8080:8080 --name watch-test watch-media-server:test
```

### **2. Test Registry Pull**
```bash
docker pull ravenshaw3/watch-media-server:latest
docker run -d -p 8080:8080 --name watch-registry-test ravenshaw3/watch-media-server:latest
```

### **3. Test Unraid Template**
1. Import `watch-template.xml` into Unraid
2. Start the container
3. Verify it pulls the image automatically
4. Access the web interface

## 🚨 **Common Issues**

### **Issue: Image Not Found**
- **Cause**: Image not pushed to registry
- **Solution**: Run the build and push script

### **Issue: Permission Denied**
- **Cause**: Not logged into Docker Hub
- **Solution**: Run `docker login` first

### **Issue: Build Fails**
- **Cause**: Dockerfile issues or missing files
- **Solution**: Check Dockerfile and ensure all files are present

### **Issue: Unraid Can't Pull Image**
- **Cause**: Wrong repository name or registry
- **Solution**: Verify template configuration matches your registry

## 📊 **Image Size Optimization**

Your current Dockerfile is optimized for size:
- Uses Python 3.11-slim base image
- Multi-stage build (if implemented)
- Minimal dependencies
- Non-root user for security

## 🔄 **Automated Builds**

### **GitHub Actions (Recommended)**

Your project already has GitHub Actions configured in `.github/workflows/ci.yml` that will:
- Build the Docker image on every push
- Push to Docker Hub automatically
- Run security scans
- Create releases

### **Docker Hub Automated Builds**

1. Connect your GitHub repository to Docker Hub
2. Enable automated builds
3. Images will build automatically on code changes

## 🎯 **Next Steps After Setup**

1. **Build and push** your Docker image
2. **Test** the image locally
3. **Update** your GitHub repository with the new files
4. **Create a release** with the template
5. **Share** with the Unraid community

## 📈 **Monitoring**

- **Docker Hub**: Monitor downloads and usage
- **GitHub**: Track issues and contributions
- **Unraid Forums**: Get user feedback

---

**Once you've built and pushed your Docker image, Unraid users will be able to automatically download and run your Watch Media Server!** 🎬
