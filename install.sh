#!/bin/bash

###########################################
#  Wix Scraper - One Click Installer      #
#  For Ubuntu/Debian VPS                  #
###########################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║          WIX SCRAPER - ONE CLICK INSTALLER                ║"
echo "║                                                           ║"
echo "║   Convert Wix websites to offline HTML sites              ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use: sudo bash install.sh)${NC}"
    exit 1
fi

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo -e "${YELLOW}[1/7] Updating system...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}[2/7] Installing dependencies...${NC}"
apt install -y python3 python3-pip python3-venv git nginx curl

# Install Playwright system dependencies
apt install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 libgtk-3-0 \
    libgdk-pixbuf2.0-0 libx11-xcb1 libxcb1 libxcursor1 libxi6 libxtst6 \
    fonts-liberation libappindicator3-1 xdg-utils wget

echo -e "${YELLOW}[3/7] Cloning Wix Scraper...${NC}"
# Remove old installation if exists
rm -rf /opt/wix-scraper
git clone https://github.com/moha-aamir/Wix-Scraper.git /opt/wix-scraper
cd /opt/wix-scraper

echo -e "${YELLOW}[4/7] Setting up Python environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

echo -e "${YELLOW}[5/7] Installing Playwright browser (this may take 2-5 minutes)...${NC}"
pip install playwright
PLAYWRIGHT_BROWSERS_PATH=/opt/wix-scraper/browsers playwright install chromium --with-deps 2>&1 | tail -5 || true

echo -e "${YELLOW}[6/7] Creating system service...${NC}"
cat > /etc/systemd/system/wixscraper.service << 'EOF'
[Unit]
Description=Wix Scraper Web Application
After=network.target

[Service]
User=root
WorkingDirectory=/opt/wix-scraper
Environment="PATH=/opt/wix-scraper/venv/bin"
Environment="PLAYWRIGHT_BROWSERS_PATH=/opt/wix-scraper/browsers"
ExecStart=/opt/wix-scraper/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8080 --timeout 300 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload and start service
systemctl daemon-reload
systemctl enable wixscraper
systemctl start wixscraper

echo -e "${YELLOW}[7/7] Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/wixscraper << EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
EOF

# Enable site
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/wixscraper /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Create useful commands script
cat > /usr/local/bin/wixscraper << 'EOF'
#!/bin/bash
case "$1" in
    status)
        systemctl status wixscraper
        ;;
    start)
        systemctl start wixscraper
        echo "Wix Scraper started"
        ;;
    stop)
        systemctl stop wixscraper
        echo "Wix Scraper stopped"
        ;;
    restart)
        systemctl restart wixscraper
        echo "Wix Scraper restarted"
        ;;
    logs)
        journalctl -u wixscraper -f
        ;;
    update)
        cd /opt/wix-scraper
        git pull
        source venv/bin/activate
        pip install -r requirements.txt
        systemctl restart wixscraper
        echo "Wix Scraper updated"
        ;;
    uninstall)
        systemctl stop wixscraper
        systemctl disable wixscraper
        rm -f /etc/systemd/system/wixscraper.service
        rm -f /etc/nginx/sites-enabled/wixscraper
        rm -f /etc/nginx/sites-available/wixscraper
        rm -rf /opt/wix-scraper
        rm -f /usr/local/bin/wixscraper
        systemctl daemon-reload
        systemctl restart nginx
        echo "Wix Scraper uninstalled"
        ;;
    *)
        echo "Wix Scraper Management Commands:"
        echo "  wixscraper status   - Check if running"
        echo "  wixscraper start    - Start the app"
        echo "  wixscraper stop     - Stop the app"
        echo "  wixscraper restart  - Restart the app"
        echo "  wixscraper logs     - View live logs"
        echo "  wixscraper update   - Update to latest version"
        echo "  wixscraper uninstall - Remove completely"
        ;;
esac
EOF
chmod +x /usr/local/bin/wixscraper

echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║          ✅ INSTALLATION COMPLETE!                        ║"
echo "║                                                           ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║                                                           ║"
echo "║  🌐 Access your Wix Scraper at:                           ║"
echo "║                                                           ║"
echo "║     http://${SERVER_IP}                                   "
echo "║                                                           ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║                                                           ║"
echo "║  📋 Useful Commands:                                      ║"
echo "║                                                           ║"
echo "║     wixscraper status   - Check status                    ║"
echo "║     wixscraper logs     - View logs                       ║"
echo "║     wixscraper restart  - Restart app                     ║"
echo "║     wixscraper update   - Update to latest                ║"
echo "║     wixscraper uninstall - Remove completely              ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
