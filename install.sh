#!/bin/bash

###########################################
#  Wix Scraper - One Click Installer      #
#  For Ubuntu 22.04/24.04 VPS             #
###########################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║           🌐 WIX SCRAPER - ONE CLICK INSTALLER 🌐             ║"
echo "║                                                               ║"
echo "║       Convert Wix websites to offline HTML sites              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root: sudo bash install.sh${NC}"
    exit 1
fi

# Get server IP
echo -e "${YELLOW}⏳ Detecting server IP...${NC}"
SERVER_IP=$(curl -s -4 ifconfig.me 2>/dev/null || curl -s -4 icanhazip.com 2>/dev/null || hostname -I | awk '{print $1}')
echo -e "${GREEN}✓ Server IP: ${SERVER_IP}${NC}"
echo ""

# Step 1: Update system
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}[1/8] 📦 Updating system packages...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
echo -e "${GREEN}✓ System updated${NC}"
echo ""

# Step 2: Install system dependencies
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}[2/8] 🔧 Installing system dependencies...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
apt-get install -y python3 python3-pip python3-venv git nginx curl wget unzip \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2t64 libpango-1.0-0 libcairo2 libatspi2.0-0 \
    libgtk-3-0 libx11-xcb1 libxcb1 libxcursor1 \
    libxi6 libxtst6 fonts-liberation xdg-utils 2>/dev/null || \
apt-get install -y python3 python3-pip python3-venv git nginx curl wget unzip \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 \
    libgtk-3-0 libx11-xcb1 libxcb1 libxcursor1 \
    libxi6 libxtst6 fonts-liberation xdg-utils
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 3: Clean up old installation
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}[3/8] 🧹 Preparing installation directory...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
systemctl stop wixscraper 2>/dev/null || true
rm -rf /opt/wix-scraper
echo -e "${GREEN}✓ Directory ready${NC}"
echo ""

# Step 4: Clone repository
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}[4/8] 📥 Downloading Wix Scraper...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
git clone --depth 1 https://github.com/moha-aamir/Wix-Scraper.git /opt/wix-scraper > /dev/null 2>&1
cd /opt/wix-scraper
echo -e "${GREEN}✓ Downloaded${NC}"
echo ""

# Step 5: Setup Python environment
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}[5/8] 🐍 Setting up Python environment...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install gunicorn -q
echo -e "${GREEN}✓ Python environment ready${NC}"
echo ""

# Step 6: Install Playwright
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}[6/8] 🌐 Installing browser (this takes 2-5 minutes)...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
pip install playwright -q
playwright install chromium 2>&1 | grep -E "(Downloading|chromium)" || true
playwright install-deps chromium > /dev/null 2>&1 || true
echo -e "${GREEN}✓ Browser installed${NC}"
echo ""

# Step 7: Create systemd service
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}[7/8] ⚙️  Creating system service...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat > /etc/systemd/system/wixscraper.service << 'SERVICEEOF'
[Unit]
Description=Wix Scraper Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wix-scraper
Environment="PATH=/opt/wix-scraper/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright"
ExecStart=/opt/wix-scraper/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8080 --timeout 300 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable wixscraper > /dev/null 2>&1
systemctl start wixscraper
echo -e "${GREEN}✓ Service created and started${NC}"
echo ""

# Step 8: Configure Nginx
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}[8/8] 🔀 Configuring web server...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat > /etc/nginx/sites-available/wixscraper << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 100M;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINXEOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/wixscraper /etc/nginx/sites-enabled/
nginx -t > /dev/null 2>&1
systemctl restart nginx
echo -e "${GREEN}✓ Web server configured${NC}"
echo ""

# Create management command
cat > /usr/local/bin/wixscraper << 'CMDEOF'
#!/bin/bash
case "$1" in
    status)
        systemctl status wixscraper
        ;;
    start)
        systemctl start wixscraper
        echo "✓ Wix Scraper started"
        ;;
    stop)
        systemctl stop wixscraper
        echo "✓ Wix Scraper stopped"
        ;;
    restart)
        systemctl restart wixscraper
        echo "✓ Wix Scraper restarted"
        ;;
    logs)
        journalctl -u wixscraper -f
        ;;
    update)
        echo "Updating Wix Scraper..."
        cd /opt/wix-scraper
        git pull
        source venv/bin/activate
        pip install -r requirements.txt -q
        systemctl restart wixscraper
        echo "✓ Wix Scraper updated!"
        ;;
    uninstall)
        echo "Uninstalling Wix Scraper..."
        systemctl stop wixscraper
        systemctl disable wixscraper
        rm -f /etc/systemd/system/wixscraper.service
        rm -f /etc/nginx/sites-enabled/wixscraper
        rm -f /etc/nginx/sites-available/wixscraper
        rm -rf /opt/wix-scraper
        rm -f /usr/local/bin/wixscraper
        systemctl daemon-reload
        systemctl restart nginx
        echo "✓ Wix Scraper uninstalled"
        ;;
    *)
        echo ""
        echo "🔧 Wix Scraper Management Commands:"
        echo ""
        echo "   wixscraper status    - Check if app is running"
        echo "   wixscraper start     - Start the app"
        echo "   wixscraper stop      - Stop the app"
        echo "   wixscraper restart   - Restart the app"
        echo "   wixscraper logs      - View live logs"
        echo "   wixscraper update    - Update to latest version"
        echo "   wixscraper uninstall - Remove completely"
        echo ""
        ;;
esac
CMDEOF
chmod +x /usr/local/bin/wixscraper

# Wait for service to start
sleep 3

# Check if service is running
SERVICE_STATUS=$(systemctl is-active wixscraper 2>/dev/null || echo "failed")

echo ""
echo ""
if [ "$SERVICE_STATUS" = "active" ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║          ✅ INSTALLATION SUCCESSFUL!                          ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╠═══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║  🌐 Your Wix Scraper is ready at:                             ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${CYAN}║     👉  http://${SERVER_IP}${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╠═══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║  📋 Management Commands:                                      ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║     wixscraper status   - Check status                        ║${NC}"
    echo -e "${GREEN}║     wixscraper logs     - View logs                           ║${NC}"
    echo -e "${GREEN}║     wixscraper restart  - Restart app                         ║${NC}"
    echo -e "${GREEN}║     wixscraper update   - Update to latest                    ║${NC}"
    echo -e "${GREEN}║     wixscraper uninstall - Remove app                         ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ Service failed to start. Checking logs...                 ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    journalctl -u wixscraper -n 20 --no-pager
    echo ""
    echo -e "${YELLOW}Try running: wixscraper logs${NC}"
fi
echo ""
