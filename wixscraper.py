# WixScraper - Convert Wix websites to offline files
# Based on https://github.com/timlg07/WixScraper

import json
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import asyncio
import os
import requests
from PIL import Image

# Scroll to the bottom to load all content
async def scroll_to_bottom(page):
    pageHeight = await page.evaluate('document.body.scrollHeight')
    for i in range(0, pageHeight, 100):
        await page.evaluate(f'window.scrollTo(0, {i})')
        await asyncio.sleep(0.1)
    await asyncio.sleep(1)

# Only use this function in compliance with Wix Terms of Service.
async def delete_wix(page):
    # Delete the wix header with id WIX_ADS
    await page.evaluate('''() => {
        const element = document.getElementById('WIX_ADS');
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }''')

    # Edit in-line CSS defined in <style> tag, remove any string "--wix-ads"
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('style');
        for (const element of elements) {
            if (element && typeof element.innerText === 'string' && element.innerText.includes('--wix-ads')) {
                element.innerText = element.innerText.replace('--wix-ads', '');
            }
        }
    }''')

    # Delete any span that includes "Made with Wix"
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('span');
        for (const element of elements) {
            if (element && typeof element.innerText === 'string' && element.innerText.includes('Made with Wix') && element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }
    }''')

    # Remove all <script> tags
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('script');
        for (const element of elements) {
            if (element && element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }
    }''')

    # Remove all <link> tags
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('link');
        for (const element of elements) {
            if (element && element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }
    }''')

async def fix_gallery(page):
    # If pro-gallery is a class on the page, then we need to fix the gallery
    gallery = await page.query_selector('.pro-gallery')

    if gallery is not None:
        print("Found gallery! Fixing..")
        
        # Import slick.carousel
        await page.add_script_tag(url='https://cdn.jsdelivr.net/npm/jquery@3.6.4/dist/jquery.min.js')
        await page.add_style_tag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick.css')
        await page.add_style_tag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick-theme.css')
        await page.add_script_tag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick.min.js')

        # Get all img links
        img_links = await page.eval_on_selector_all('img', 'nodes => nodes.map(n => n.src)')
    
        # Create the carousel
        await page.evaluate('''() => {
            const element = document.createElement('div');
            element.className = 'slick-carousel';
            document.querySelector('.pro-gallery').parentNode.parentNode.insertBefore(element, document.querySelector('.pro-gallery').parentNode);
        }''')

        # Delete all siblings of the slick carousel
        await page.evaluate('''() => {
            const element = document.querySelector('.slick-carousel');
            while (element.nextSibling) {
                element.nextSibling.parentNode.removeChild(element.nextSibling);
            }
        }''')

        # Add the images to the carousel
        for link in img_links:
            await page.evaluate(f'''() => {{
                const element = document.createElement('img');
                element.src = '{link}';
                element.alt = 'Gallery Image';
                document.querySelector('.slick-carousel').appendChild(element);
            }}''')

        # Add the above evaluation as a script tag
        await page.add_script_tag(content='''
        window.addEventListener('DOMContentLoaded', function() {
        var $jq = jQuery.noConflict();
        $jq(document).ready(function () {
            $jq('.slick-carousel').slick({
                dots: true,
                infinite: true,
                speed: 300,
                slidesToShow: 2,
                responsive: [
                    {
                    breakpoint: 1024,
                    settings: {
                        slidesToShow: 1,
                    }
                    },
                    {
                    breakpoint: 600,
                    settings: {
                        slidesToShow: 1,
                    }
                    }
                ]
            });
        });
        });''')

async def fix_googlemap(page, mapData):
    # Get the one titled = "Google Maps"
    googlemap = await page.query_selector('wix-iframe[title="Google Maps"]')

    if googlemap is not None:
        print("Found Google Maps! Fixing..")

        # Import leaflet
        await page.add_style_tag(url='https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/leaflet.css')

        await page.evaluate('''() => {
            const element = document.createElement('script');
            element.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/leaflet.js';
            document.querySelector('script').parentNode.insertBefore(element, document.querySelector('script').nextSibling);
        }''')

        # Add new style tag to the page
        await page.add_style_tag(content='''
        #map { height: 100%; }
        html, body { height: 100%; margin: 0; padding: 0; }
        :root {
        --map-tiles-filter: brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.3) brightness(0.7);
        }
        @media (prefers-color-scheme: dark) {
            .map-tiles {
                filter:var(--map-tiles-filter, none);
            }
        }''')

        # Add a new map div next to the google map
        await page.evaluate('''() => {
            const element = document.createElement('div');
            element.id = 'map';
            document.querySelector('iframe[title="Google Maps"]').parentNode.insertBefore(element, document.querySelector('iframe[title="Google Maps"]').nextSibling);
        }''')

        # Delete all siblings of the map div
        await page.evaluate('''() => {
            const element = document.querySelector('#map');
            while (element.nextSibling) {
                element.nextSibling.parentNode.removeChild(element.nextSibling);
            }
        }''')

        content = '''
        window.addEventListener('DOMContentLoaded', function() {
        var map = L.map('map').setView([''' + mapData['latitude'] + ',' + mapData['longitude'] + '],' + mapData['zoom'] + ''');
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
            className: 'map-tiles'
        }).addTo(map);
        L.marker([''' + mapData['mapMarker']['latitude'] + ',' + mapData['mapMarker']['longitude'] + ''']).addTo(map)
            .bindPopup(" ''' + mapData['mapMarker']['popup'] + ''' ")
            .openPopup();
        });'''

        await page.evaluate('''() => {
            const element = document.createElement('script');
            element.innerHTML = `''' + content + '''`;
            document.querySelector('body').appendChild(element);
        }''')

        # Delete the google map iframe
        await page.evaluate('''() => {
            const element = document.querySelector('iframe[title="Google Maps"]');
            element.parentNode.removeChild(element);
        }''')

        # Add preconnect to openstreetmap
        await page.evaluate('''() => {
            const element = document.createElement('link');
            element.rel = 'preconnect';
            element.href = 'https://a.tile.openstreetmap.org';
            document.querySelector('head').appendChild(element);
            element.href = 'https://b.tile.openstreetmap.org';
            document.querySelector('head').appendChild(element);
            element.href = 'https://c.tile.openstreetmap.org';
            document.querySelector('head').appendChild(element);
        }''')

async def fix_slideshow(page):
    gallery = await page.query_selector('.wixui-slideshow')

    if gallery is not None:
        print("Found Slideshow! Fixing..")
        
        # Import slick.carousel
        await page.add_script_tag(url='https://cdn.jsdelivr.net/npm/jquery@3.6.4/dist/jquery.min.js')
        await page.add_style_tag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick.css')
        await page.add_style_tag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick-theme.css')
        await page.add_script_tag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick.min.js')

        await page.evaluate('''() => {
            const element = document.createElement('div');
            element.className = 'slick-carousel-slides';
            document.querySelector('.wixui-slideshow').parentNode.parentNode.insertBefore(element, document.querySelector('.wixui-slideshow').parentNode);
        }''')

        # Give all images inside slideshow alt tags
        await page.evaluate('''() => {
            const elements = document.querySelectorAll('nav[aria-label="Slides"] li img');
            for (const element of elements) {   
                element.alt = 'Slideshow Image';
            }
        }''')

        slides = await page.query_selector_all('nav[aria-label="Slides"] li')

        # Ensure first slide is selected
        await asyncio.sleep(5)
        if slides:
            await slides[0].click()

            for slide in slides:
                await slide.click()
                await asyncio.sleep(5)

                slide_content = await page.query_selector('div[data-testid="slidesWrapper"] > div')
                parent = await page.evaluate('(slide_content) => slide_content.innerHTML', slide_content)

                await page.evaluate(f'''(parent) => {{
                    const element = document.createElement('div');
                    element.innerHTML = parent;
                    document.querySelector('.slick-carousel-slides').appendChild(element);
                }}''', parent)

        # Delete all children of slidesWrapper
        await page.evaluate('''() => {
            const element = document.querySelector('div[data-testid="slidesWrapper"]');
            while (element.firstChild) {
                element.removeChild(element.firstChild);
            }
        }''')

        # Move slick-carousel next to aria-label="Slideshow"
        await page.evaluate('''() => {
           const element = document.querySelector('.slick-carousel-slides');
           document.querySelector('.wixui-slideshow').parentNode.insertBefore(element, document.querySelector('.wixui-slideshow').nextSibling);
        }''')

        await page.evaluate('''() => {
           const element = document.querySelector('.wixui-slideshow');
           document.querySelector('.slick-carousel-slides').className = element.className + ' slick-carousel-slides';
           document.querySelector('.slick-carousel-slides').id = element.id;
           element.parentNode.removeChild(element);
        }''')

        await page.add_style_tag(content='''
        .slick-next {
            z-index: 100;
            right: 75px;
        }
        .slick-prev {
            z-index: 100;
            left: 75px;
        }''')

slideFix = '''<script>
        window.addEventListener('DOMContentLoaded', function() {
        var $jq = jQuery.noConflict();
        $jq(document).ready(function () {
            $jq('.slick-carousel-slides').slick({
                dots: true,
                infinite: false,
                speed: 300,
                slidesToShow: 1,
                responsive: [
                    {
                    breakpoint: 1024,
                    settings: {
                        slidesToShow: 1,
                    }
                    },
                    {
                    breakpoint: 600,
                    settings: {
                        slidesToShow: 1,
                    }
                    }
                ]
            });
        });
    });</script></body>'''

lightModeFix = '''<style>
        .slick-dots li button:before {
            font-family: 'slick';
            font-size: 6px;
            line-height: 20px;
            position: absolute;
            top: 0;
            left: 0;
            width: 20px;
            height: 20px;
            content: '•';
            text-align: center;
            opacity: .25;
            color: white;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        .slick-dots li.slick-active button:before {
            opacity: .75;
            color: white;
        }
    </style></head>'''

async def makeLocalImages(page, hostname, forceDownloadAgain):
    # Create images folder if it doesn't exist in hostname folder
    if not os.path.exists(hostname + '/images'):
        os.makedirs(hostname + '/images')

    # Download all images
    imageLinks = await page.eval_on_selector_all('img', 'nodes => nodes.map(n => n.src)')

    for link in imageLinks:
        # Skip data URIs (base64 encoded images)
        if link.startswith('data:'):
            continue

        # If a webp version of the image already exists, skip it
        if not forceDownloadAgain and os.path.exists(hostname + '/images/' + link.split('/')[-1].split('.')[0] + '.webp'):
            continue

        try:
            imageName = link.split('/')[-1]
            r = requests.get(link, allow_redirects=True)
            open(hostname + '/images/' + imageName, 'wb').write(r.content)

            # Convert each image to WebP
            im = Image.open(hostname + '/images/' + imageName)
            im.save(hostname + '/images/' + imageName.split('.')[0] + '.webp', 'webp')

            # Delete the original image
            os.remove(hostname + '/images/' + imageName)
        except Exception as e:
            print(f"Error downloading image {link}: {e}")

    # Replace all image links with the local image links
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('img');
        for (const element of elements) {
            element.src = '/images/' + element.src.split('/').slice(-1)[0].split('.')[0] + '.webp';
            element.removeAttribute('srcset');
        }
    }''')

async def makeFontsLocal(page, hostname, forceDownloadAgain):
    # Create a fonts folder if it doesn't exist in hostname folder
    if not os.path.exists(hostname + '/fonts'):
        os.makedirs(hostname + '/fonts')

    # Download all fonts, which are parastorage links
    fontLinks = await page.eval_on_selector_all(
        'style',
        '''nodes => nodes
            .map(n => typeof n.innerText === 'string' ? n.innerText.match(/url\\((.*?)\\)/g) : [])
            .flat()
            .filter(x => x)'''
    )

    # Get all url("//static.parastorage.com...") links
    fontLinks = [link for link in fontLinks if link is not None and 'static.parastorage.com' in link]

    for link in fontLinks:
        # Only get if the link is a font
        if 'woff' not in link and 'woff2' not in link and 'ttf' not in link and 'eot' not in link and 'otf' not in link and 'svg' not in link:
            continue
        
        # Remove anything before the link
        parts = link.split('static.parastorage.com')
        if len(parts) < 2:
            continue
        link = 'static.parastorage.com' + parts[1]
        # Get the font name
        fontName = link.split('/')[-1].split(')')[0]
        fontName = fontName.split('?')[0]
        fontName = fontName.split('#')[0]
        fontName = fontName.replace('"', '')
        
        # If the font already exists, skip it
        if not forceDownloadAgain and os.path.exists(hostname + '/fonts/' + fontName):
            continue
        
        try:
            r = requests.get("https://" + link, allow_redirects=True)
            open(hostname + '/fonts/' + fontName, 'wb').write(r.content)
        except Exception as e:
            print(f"Error downloading font {link}: {e}")

    # Replace all font links with the local font links
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('style');
        for (const element of elements) {
            if (element && typeof element.innerText === 'string' && element.innerText.includes('static.parastorage.com')) {
                const fontLinks = element.innerText.match(/url\\((.*?)\\)/g);
                if (Array.isArray(fontLinks)) {
                    for (const link of fontLinks) {
                        if (
                            link.includes('woff') || link.includes('woff2') ||
                            link.includes('ttf') || link.includes('eot') ||
                            link.includes('otf') || link.includes('svg')
                        ) {
                            let fontName = link.substring(link.lastIndexOf('/') + 1, link.lastIndexOf(')'))
                                .split('?')[0].split('#')[0].replace(/\"/g, '');
                            element.innerText = element.innerText.replace(link, 'url(\"/fonts/' + fontName + '\")');
                        }
                    }
                }
            }
        }
    }''')

async def fix_page(page, wait, hostname, blockPrimaryFolder, darkWebsite, forceDownloadAgain, metatags, mapData):
    # Get the current page
    url_parts = page.url.split(hostname)
    key = url_parts[1] if len(url_parts) > 1 else '/'
    if not key:
        key = '/'
    print("Current page: " + key)
    
    await asyncio.sleep(wait)
    await scroll_to_bottom(page)
    await delete_wix(page)
    await fix_gallery(page)
    await fix_googlemap(page, mapData)
    await fix_slideshow(page)

    # Defer all scripts
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('script');
        for (const element of elements) {
            element.setAttribute('defer', '');
        }
    }''')

    # In every font-face, add font-display: swap;
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('style');
        for (const element of elements) {
            if (element && typeof element.innerText === 'string' && element.innerText.includes('@font-face')) {
                element.innerText = element.innerText.replace(/@font-face {/g, '@font-face { font-display: swap;');
            }
        }
    }''')

    # Edit in-line CSS defined in <style> tag, remove any string "--wix-ads"
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('style');
        for (const element of elements) {
            if (element && typeof element.innerText === 'string' && element.innerText.includes('--wix-ads')) {
                element.innerText = element.innerText.replace('--wix-ads', '');
            }
        }
    }''')

    # Remove data-href from every style tag
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('style');
        for (const element of elements) {
            element.removeAttribute('data-href');
            element.removeAttribute('data-url');
        }
    }''')

    # Make all images local
    await makeLocalImages(page, hostname, forceDownloadAgain)

    # Make all fonts local
    await makeFontsLocal(page, hostname, forceDownloadAgain)

    # Delete all meta tags
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('meta');
        for (const element of elements) {
            element.parentNode.removeChild(element);
        }
    }''')

    if key not in metatags:
        print("Warning: No metatags defined for this page. Using default metatags.")
        key = '/'
       
    title = metatags.get(key, {}).get('title', 'Wix Website')
    description = metatags.get(key, {}).get('description', '')
    keywords = metatags.get(key, {}).get('keywords', '')
    canonical = metatags.get(key, {}).get('canonical', '')
    image = metatags.get(key, {}).get('image', '')
    author = metatags.get(key, {}).get('author', '')

    await page.evaluate(f'''() => {{
        const element = document.createElement('title');
        element.innerText = '{title}';
        document.querySelector('head').appendChild(element);
    }}''')

    # Add meta tags
    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'title';
        element.content = '{title}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.property = 'og:title';
        element.content = '{title}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'description';
        element.content = '{description}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.property = 'og:description';
        element.content = '{description}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'keywords';
        element.content = '{keywords}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('link');
        element.rel = 'canonical';
        element.href = '{canonical}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate('''() => {
        const element = document.createElement('meta');
        element.name = 'viewport';
        element.content = 'width=device-width, initial-scale=1.0';
        document.querySelector('head').appendChild(element);
    }''')

    await page.evaluate('''() => {
        const element = document.createElement('meta');
        element.name = 'robots';
        element.content = 'index, follow';
        document.querySelector('head').appendChild(element);
    }''')

    html = await page.evaluate('document.documentElement.outerHTML')

    html = html.replace('<br>', '')
    html = html.replace('</body>', slideFix)
    if darkWebsite:
        html = html.replace('</head>', lightModeFix)
    
    # Fix every href to be relative 
    html = html.replace('href="https://' + hostname, 'href="')
    html = html.replace('href="http://' + hostname, 'href="')
    html = html.replace('href="https://www.' + hostname, 'href="')
    html = html.replace('href="http://www.' + hostname, 'href="')
    html = html.replace('href="www.' + hostname, 'href="')
    html = html.replace('href="' + hostname, 'href="')

    # Remove the primaryFolder from any hrefs
    html = html.replace('href="/' + blockPrimaryFolder, 'href="')

    # Any empty hrefs are now root hrefs, replace them with /
    html = html.replace('href=""', 'href="/"')

    # Remove browser-sentry script
    html = html.replace('<script src="https://browser.sentry-cdn.com/6.18.2/bundle.min.js" defer></script>', '')
    html = html.replace('//static.parastorage.com', 'https://static.parastorage.com')

    # Add doctype HTML to start 
    html = '<!DOCTYPE html>' + html

    return html

async def scrape_wix_site(site, blockPrimaryFolder='', wait=3, recursive=False, darkWebsite=False, 
                          forceDownloadAgain=False, metatags=None, mapData=None, output_dir='output',
                          progress_callback=None):
    """
    Main function to scrape a Wix website
    """
    if metatags is None:
        metatags = {'/': {'title': 'Website', 'description': '', 'keywords': '', 'canonical': site, 'image': '', 'author': ''}}
    
    if mapData is None:
        mapData = {
            'latitude': '0',
            'longitude': '0',
            'zoom': '12',
            'mapMarker': {
                'latitude': '0',
                'longitude': '0',
                'popup': ''
            }
        }

    # Get the hostname
    hostname = urlparse(site).hostname
    
    # Create output directory
    output_path = os.path.join(output_dir, hostname)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if progress_callback:
        progress_callback(f"Starting browser...")

    # Launch browser using Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.set_default_timeout(60000)  # 60 second timeout
        
        if progress_callback:
            progress_callback(f"Navigating to {site}...")
        
        await page.goto(site, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(5)  # Wait for JS to load content
        
        if progress_callback:
            progress_callback(f"Processing main page...")

        # Fix the first page
        html = await fix_page(page, wait, output_path, blockPrimaryFolder, darkWebsite, forceDownloadAgain, metatags, mapData)

        with open(output_path + '/index.html', 'w', encoding="utf-8") as f:
            f.write(html)

        if recursive:
            seen = []
            errors = {}
            
            async def save_links(links):
                nonlocal seen, errors
                # Delete all links that are not local
                links = [link for link in links if hostname in link]
                # Delete all links with hash
                links = [link for link in links if '#' not in link]
                links = set(links)
                
                for link in links:
                    if link in seen:
                        continue

                    try:
                        if progress_callback:
                            progress_callback(f"Processing: {link}")
                        
                        await page.goto(link, wait_until='domcontentloaded', timeout=60000)
                        await asyncio.sleep(3)  # Wait for JS to load content
                        seen.append(link)

                        html = await fix_page(page, wait, output_path, blockPrimaryFolder, darkWebsite, forceDownloadAgain, metatags, mapData)

                        # Write each page as index.html to a folder named after the page
                        newlink = link.replace('https://', '').replace('http://', '')
                        link_parts = newlink.split('/')

                        if len(link_parts) > 2 and blockPrimaryFolder not in link_parts[1]:
                            page_path = '/'.join(link_parts[1:])
                            if page_path and not os.path.exists(output_path + '/' + page_path):
                                os.makedirs(output_path + '/' + page_path)
                            with open(output_path + '/' + page_path + '/index.html', 'w', encoding="utf-8") as f:
                                f.write(html)
                        else:
                            page_name = link.split('/')[-1] if link.split('/') else 'page'
                            if page_name and not os.path.exists(output_path + '/' + page_name):
                                os.makedirs(output_path + '/' + page_name)
                            with open(output_path + '/' + page_name + '/index.html', 'w', encoding="utf-8") as f:
                                f.write(html)
                    
                        await save_links(await page.eval_on_selector_all('a', 'nodes => nodes.map(n => n.href)'))

                    except Exception as e:
                        if link in errors:
                            errors[link] += 1
                        else:
                            errors[link] = 1

                        if errors[link] > 3:
                            seen.append(link)
                            print(f"Error: {link}. Giving up after 3 attempts.")
                            continue

                        print(f"Error: {link}. Try {errors[link]} of 3: {e}")
                        continue
            
            await save_links(await page.eval_on_selector_all('a', 'nodes => nodes.map(n => n.href)'))
        
        await browser.close()
    
    if progress_callback:
        progress_callback(f"Completed! Files saved to {output_path}")
    
    return output_path

# Define the main function for standalone use
async def main():
    # Load the data in from the json file
    with open('config.json') as f:
        data = json.load(f)

    site = data['site']
    blockPrimaryFolder = data['blockPrimaryFolder']
    wait = data['wait']
    recursive = data['recursive'].lower() == 'true'
    darkWebsite = data['darkWebsite'].lower() == 'true'
    forceDownloadAgain = data['forceDownloadAgain'].lower() == 'true'
    metatags = data['metatags']
    mapData = data['mapData']

    await scrape_wix_site(
        site=site,
        blockPrimaryFolder=blockPrimaryFolder,
        wait=wait,
        recursive=recursive,
        darkWebsite=darkWebsite,
        forceDownloadAgain=forceDownloadAgain,
        metatags=metatags,
        mapData=mapData
    )

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
