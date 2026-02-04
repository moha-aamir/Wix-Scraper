#!/bin/bash

###########################################
#  Wix Scraper - One Click Installer      #
#  For Ubuntu 20.04/22.04/24.04 VPS       #
###########################################

# DO NOT use set -e - we handle errors manually

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
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
}

print_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Start
print_header

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root: sudo bash install.sh"
    exit 1
fi

# Get server IP
echo -e "${YELLOW}⏳ Detecting server IP...${NC}"
SERVER_IP=$(curl -s -4 --max-time 10 ifconfig.me 2>/dev/null)
if [ -z "$SERVER_IP" ]; then
    SERVER_IP=$(curl -s -4 --max-time 10 icanhazip.com 2>/dev/null)
fi
if [ -z "$SERVER_IP" ]; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
fi
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="YOUR_SERVER_IP"
fi
print_success "Server IP: ${SERVER_IP}"

###########################################
# STEP 1: Update system
###########################################
print_step "[1/8] 📦 Updating system packages..."

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
if [ $? -eq 0 ]; then
    print_success "System updated"
else
    print_error "Failed to update system, continuing anyway..."
fi

###########################################
# STEP 2: Install basic packages
###########################################
print_step "[2/8] 🔧 Installing basic packages..."

apt-get install -y python3 python3-pip python3-venv git nginx curl wget unzip
if [ $? -eq 0 ]; then
    print_success "Basic packages installed"
else
    print_error "Some packages failed, trying alternatives..."
fi

###########################################
# STEP 3: Install Playwright dependencies
###########################################
print_step "[3/8] 🔧 Installing browser dependencies..."

# Try to install common dependencies - ignore errors for missing packages
apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libx11-xcb1 \
    libxcb1 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    fonts-liberation \
    xdg-utils \
    2>/dev/null || true

# Try libasound2 (Ubuntu 22.04 and earlier)
apt-get install -y libasound2 2>/dev/null || true

# Try libasound2t64 (Ubuntu 24.04)
apt-get install -y libasound2t64 2>/dev/null || true

# Try libgtk packages
apt-get install -y libgtk-3-0 2>/dev/null || true
apt-get install -y libgtk-3-0t64 2>/dev/null || true

print_success "Browser dependencies installed"

###########################################
# STEP 4: Clean up old installation
###########################################
print_step "[4/8] 🧹 Preparing installation directory..."

systemctl stop wixscraper 2>/dev/null || true
systemctl disable wixscraper 2>/dev/null || true
rm -rf /opt/wix-scraper 2>/dev/null || true

print_success "Directory ready"

###########################################
# STEP 5: Clone repository
###########################################
print_step "[5/8] 📥 Downloading Wix Scraper..."

git clone --depth 1 https://github.com/moha-aamir/Wix-Scraper.git /opt/wix-scraper
if [ $? -ne 0 ]; then
    print_error "Failed to clone repository"
    exit 1
fi
cd /opt/wix-scraper
print_success "Downloaded"

###########################################
# STEP 6: Setup Python environment
###########################################
print_step "[6/8] 🐍 Setting up Python environment..."

python3 -m venv venv
if [ $? -ne 0 ]; then
    print_error "Failed to create virtual environment"
    exit 1
fi

source venv/bin/activate

pip install --upgrade pip
pip install wheel setuptools

echo "Installing Flask and dependencies..."
pip install flask werkzeug requests pillow gunicorn

echo "Installing Playwright..."
pip install playwright

print_success "Python environment ready"

###########################################
# STEP 7: Install Playwright browser
###########################################
print_step "[7/8] 🌐 Installing Chromium browser (this takes 2-5 minutes)..."

# Install playwright browsers with full output
echo "Downloading Chromium browser..."
playwright install chromium

# Verify installation
if [ -d "/root/.cache/ms-playwright" ]; then
    print_success "Browser installed"
else
    print_error "Browser installation may have failed, trying again..."
    playwright install chromium
fi

# Install system deps for playwright
playwright install-deps chromium 2>/dev/null || true

print_success "Browser setup complete"

###########################################
# STEP 8: Create systemd service
###########################################
print_step "[8/8] ⚙️  Creating system service and configuring Nginx..."

# Create systemd service file
cat > /etc/systemd/system/wixscraper.service << 'EOF'
[Unit]
Description=Wix Scraper Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wix-scraper
Environment="PATH=/opt/wix-scraper/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/wix-scraper/venv/bin/gunicorn --workers 1 --threads 4 --bind 127.0.0.1:8080 --timeout 300 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable wixscraper
systemctl start wixscraper

print_success "Service created"

# Configure Nginx
cat > /etc/nginx/sites-available/wixscraper << 'EOF'
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
EOF

# Enable Nginx site
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
ln -sf /etc/nginx/sites-available/wixscraper /etc/nginx/sites-enabled/

# Test and restart Nginx
nginx -t
if [ $? -eq 0 ]; then
    systemctl restart nginx
    print_success "Nginx configured"
else
    print_error "Nginx configuration error"
fi

###########################################
# Create management command
###########################################
cat > /usr/local/bin/wixscraper << 'EOF'
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
        pip install -r requirements.txt
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
EOF
chmod +x /usr/local/bin/wixscraper

###########################################
# Final check and display result
###########################################
echo ""
echo ""
sleep 3

SERVICE_STATUS=$(systemctl is-active wixscraper 2>/dev/null || echo "inactive")

if [ "$SERVICE_STATUS" = "active" ]; then
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║          ✅ INSTALLATION SUCCESSFUL!                          ║"
    echo "║                                                               ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║                                                               ║"
    echo "║  🌐 Your Wix Scraper is ready at:                             ║"
    echo "║                                                               ║"
    echo -e "║     👉  ${CYAN}http://${SERVER_IP}${GREEN}                                     "
    echo "║                                                               ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║                                                               ║"
    echo "║  📋 Management Commands:                                      ║"
    echo "║                                                               ║"
    echo "║     wixscraper status   - Check status                        ║"
    echo "║     wixscraper logs     - View logs                           ║"
    echo "║     wixscraper restart  - Restart app                         ║"
    echo "║     wixscraper update   - Update to latest                    ║"
    echo "║     wixscraper uninstall - Remove app                         ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
else
    echo -e "${RED}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  ⚠️  Service may not have started properly                    ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo "Checking service status..."
    systemctl status wixscraper --no-pager -l
    echo ""
    echo "Recent logs:"
    journalctl -u wixscraper -n 30 --no-pager
    echo ""
    echo -e "${YELLOW}Try these commands to debug:${NC}"
    echo "  wixscraper logs"
    echo "  wixscraper restart"
    echo ""
    echo -e "${CYAN}Your app might still work at: http://${SERVER_IP}${NC}"
fi

echo ""
