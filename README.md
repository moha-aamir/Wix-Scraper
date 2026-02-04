# Wix to Offline Converter

A simple web application that converts Wix websites to offline files using the [WixScraper](https://github.com/timlg07/WixScraper) tool.

## Features

- **User-friendly Web Interface**: Easy-to-use web interface to convert Wix websites
- **Optimized Performance**: Removes Wix JavaScript and replaces with lightweight alternatives
- **Local Assets**: Downloads and converts images to WebP format, localizes all fonts
- **SEO Ready**: Adds proper meta tags, Open Graph data, and Twitter cards
- **Map Support**: Replaces Google Maps with OpenStreetMap/Leaflet
- **Gallery/Slideshow Support**: Replaces Wix galleries with Slick carousel

## Prerequisites

- Python 3.8 or higher
- Microsoft Edge browser (or modify the browser path in the code)

## Installation

1. Clone or download this repository

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Web Interface (Recommended)

1. Start the web server:
   ```bash
   python app.py
   ```

2. Open your browser and go to: `http://localhost:5000`

3. Enter your Wix website URL and configure options

4. Click "Start Conversion" and wait for the process to complete

5. Download the ZIP file containing your offline website

### Command Line (Original WixScraper)

1. Edit `config.json` with your website details

2. Run:
   ```bash
   python wixscraper.py
   ```

## Configuration Options

| Option | Description |
|--------|-------------|
| **Website URL** | The full URL of your Wix website |
| **Primary Folder** | The folder after wixsite.com (if any) |
| **Wait Time** | Seconds to wait before processing each page |
| **Scrape All Pages** | Recursively scrape all linked pages |
| **Dark Theme** | Apply dark mode styling fixes |
| **Force Re-download** | Re-download all assets even if they exist |

### SEO Options

- **Page Title**: Title for meta tags
- **Description**: Meta description for SEO
- **Keywords**: Comma-separated keywords
- **Author**: Author name for meta tags
- **Social Image URL**: Image URL for Open Graph/Twitter cards

### Map Configuration

If your site uses Google Maps, you can configure the replacement OpenStreetMap:
- **Latitude/Longitude**: Map center coordinates
- **Zoom Level**: Default zoom level (1-20)
- **Marker Popup**: HTML content for the map marker popup

## Output

The converted website will be saved as a ZIP file containing:
- `index.html` - Main page
- `images/` - Converted WebP images
- `fonts/` - Local font files
- Additional page folders (if recursive scraping is enabled)

## Important Notice

⚠️ **Only use this tool for websites you own or have permission to download.** 

This tool should only be used by those who have paid for Wix. Your Wix website might not belong to you under [Wix Terms of Service](https://www.wix.com/about/terms-of-use) if you haven't paid for it.

## Credits

Based on [WixScraper](https://github.com/timlg07/WixScraper) by timlg07

## License

This project is provided as-is for educational purposes. Please respect Wix's Terms of Service.
