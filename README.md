# 🌐 Wix Scraper - Convert Wix Websites to Offline HTML

A powerful web application that converts Wix websites to fully offline HTML sites. Download your Wix website as static files that work without an internet connection.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Platform](https://img.shields.io/badge/platform-Ubuntu%2020.04%20%7C%2022.04%20%7C%2024.04-orange.svg)

---

## ✨ Features

- 🖥️ **User-friendly Web Interface** - Easy-to-use web UI for converting Wix websites
- 📥 **Complete Download** - Downloads HTML, CSS, images, and fonts
- 🔄 **Recursive Scraping** - Option to scrape all linked pages
- 🎨 **Dark Theme Support** - Fixes dark mode styling issues
- 🗺️ **Map Support** - Replaces Google Maps with OpenStreetMap/Leaflet
- 🖼️ **Gallery Support** - Converts Wix galleries to Slick carousel
- 📱 **Responsive** - Works on desktop and mobile
- 🚀 **One-Click Install** - Deploy to any VPS with a single command

---

## 🚀 One-Click VPS Installation

Deploy to any Ubuntu VPS (20.04, 22.04, or 24.04) with a single command:

```bash
curl -sSL https://raw.githubusercontent.com/moha-aamir/Wix-Scraper/main/install.sh | sudo bash
```

**That's it!** After 3-5 minutes, your Wix Scraper will be ready at `http://YOUR-SERVER-IP`

### What the installer does:
1. ✅ Updates system packages
2. ✅ Installs Python and dependencies
3. ✅ Installs Chromium browser for rendering
4. ✅ Sets up the Flask web application
5. ✅ Configures Nginx as reverse proxy
6. ✅ Creates a systemd service (auto-starts on reboot)
7. ✅ Shows you the final URL

---

## 📋 Management Commands

After installation, use these commands to manage your app:

| Command | Description |
|---------|-------------|
| `wixscraper status` | Check if the app is running |
| `wixscraper start` | Start the application |
| `wixscraper stop` | Stop the application |
| `wixscraper restart` | Restart the application |
| `wixscraper logs` | View live logs (Ctrl+C to exit) |
| `wixscraper update` | Update to the latest version |
| `wixscraper uninstall` | Completely remove the app |

---

## 💻 Local Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/moha-aamir/Wix-Scraper.git
   cd Wix-Scraper
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browser**
   ```bash
   playwright install chromium
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   ```
   http://localhost:5000
   ```

---

## 📖 How to Use

### Step 1: Enter URL
Enter the full URL of your Wix website (e.g., `https://username.wixsite.com/mysite`)

### Step 2: Configure Options

| Option | Description |
|--------|-------------|
| **Primary Folder** | The folder path after wixsite.com (if any) |
| **Wait Time** | Seconds to wait for page to load (default: 3) |
| **Scrape All Pages** | Recursively download all linked pages |
| **Dark Theme** | Apply dark mode styling fixes |
| **Force Re-download** | Re-download all assets even if they exist |

### Step 3: Advanced Options (Optional)

**SEO & Meta Tags:**
- Page Title
- Description
- Keywords
- Author
- Social Image URL

**Map Configuration (if your site has maps):**
- Latitude/Longitude
- Zoom Level
- Marker Popup Text

### Step 4: Start Conversion
Click "Start Conversion" and wait for the process to complete.

### Step 5: Download
Once complete, click the download button to get your offline website as a ZIP file.

---

## 📁 Output Structure

```
website.zip
├── index.html          # Main page
├── images/             # All images (converted to WebP)
├── fonts/              # Local font files
├── page1/              # Additional pages (if recursive)
│   └── index.html
└── page2/
    └── index.html
```

---

## 🐳 Docker Deployment

You can also deploy using Docker:

```bash
docker build -t wix-scraper .
docker run -d -p 8080:8080 --name wix-scraper wix-scraper
```

Access at `http://localhost:8080`

---

## ☁️ Digital Ocean App Platform

1. Fork this repository
2. Create a new App in Digital Ocean App Platform
3. Connect your GitHub repository
4. Select **Dockerfile** as the build method
5. Set HTTP Port to **8080**
6. Deploy!

---

## 🔧 Troubleshooting

### "Job not found" error
This usually means the browser isn't installed. Run:
```bash
cd /opt/wix-scraper
source venv/bin/activate
playwright install chromium
sudo systemctl restart wixscraper
```

### Browser crashes on server
Make sure you have enough RAM (minimum 1GB recommended). Also check:
```bash
wixscraper logs
```

### Conversion takes too long
- Increase the "Wait Time" setting
- Large sites with many images take longer
- Check server resources with `htop`

### Permission denied errors
Make sure you're running as root or with sudo:
```bash
sudo wixscraper restart
```

---

## 🛡️ Security Notes

- Only convert websites you own or have permission to download
- The app doesn't store any credentials
- Consider adding authentication if deploying publicly
- Use HTTPS in production (see SSL setup below)

---

## 🔒 Adding SSL (HTTPS)

After installation, add free SSL with Let's Encrypt:

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d yourdomain.com
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## ⚠️ Important Notice

**Only use this tool for websites you own or have permission to download.**

This tool should only be used by those who have paid for Wix. Your Wix website might not belong to you under [Wix Terms of Service](https://www.wix.com/about/terms-of-use) if you haven't paid for it.

---

## 📜 License

This project is provided as-is for educational purposes. Please respect Wix's Terms of Service.

---

## 🙏 Credits

- Based on [WixScraper](https://github.com/timlg07/WixScraper) by timlg07
- [Playwright](https://playwright.dev/) for browser automation
- [Flask](https://flask.palletsprojects.com/) for the web framework

---

## 📞 Support

If you encounter any issues:
1. Check the [Troubleshooting](#-troubleshooting) section
2. View logs with `wixscraper logs`
3. Open an issue on GitHub

---

**Made with ❤️ by [moha-aamir](https://github.com/moha-aamir)**
