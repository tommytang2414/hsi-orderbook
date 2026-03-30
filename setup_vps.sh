#!/bin/bash
# Run this on your DigitalOcean Ubuntu droplet (as root or with sudo)
# Usage: bash setup_vps.sh

set -e

echo "=== HSI Order Book Collector — VPS Setup ==="

# 1. System packages
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv git wget unzip screen

# 2. Download Futu OpenD for Linux
# Check latest version at: https://www.futunn.com/download/openAPI
FUTU_VERSION="9.2.5108"
FUTU_URL="https://openapi.futunn.com/futu-api-doc/assets/files/FutuOpenD_${FUTU_VERSION}_Ubuntu18.tar.gz"

echo "Downloading Futu OpenD ${FUTU_VERSION}..."
mkdir -p /opt/futud
cd /opt/futud
wget -q "$FUTU_URL" -O futud.tar.gz
tar -xzf futud.tar.gz
rm futud.tar.gz
echo "Futu OpenD extracted to /opt/futud"

# 3. Create Futu OpenD config
mkdir -p /opt/futud/config
cat > /opt/futud/FutuOpenD.xml << 'FUTU_CONFIG'
<?xml version="1.0" encoding="UTF-8"?>
<config>
  <!-- Fill in your Futu account details -->
  <login_account>YOUR_FUTU_PHONE_NUMBER</login_account>
  <login_pwd_md5>YOUR_PASSWORD_MD5</login_pwd_md5>
  <trade_pwd_md5></trade_pwd_md5>
  <lang>2052</lang>
  <api_ip>127.0.0.1</api_ip>
  <api_port>11111</api_port>
  <push_proto_type>0</push_proto_type>
  <log_level>1</log_level>
</config>
FUTU_CONFIG
echo "Edit /opt/futud/FutuOpenD.xml with your Futu credentials before starting."

# 4. Clone project
cd /opt
if [ -d "HSIOrderBook" ]; then
  cd HSIOrderBook && git pull
else
  git clone https://github.com/YOUR_GITHUB_USERNAME/HSIOrderBook.git
  cd HSIOrderBook
fi

# 5. Python venv + dependencies
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit /opt/futud/FutuOpenD.xml with your Futu credentials"
echo "  2. Edit /opt/HSIOrderBook/.env with your DATABASE_URL"
echo "  3. Run: bash start.sh"
