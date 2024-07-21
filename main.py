import json
import requests
from bs4 import BeautifulSoup
import time

# Variable to store the last sent statuss
last_sent_status = None

# Function to fetch URL content with retries 3
def fetch_url_with_retry(url, max_retries=7, delay=1):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
            else:
                print(f"Failed to fetch URL: {url}. Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
        retries += 1
        time.sleep(delay)
    print(f"Max retries reached for URL: {url}")
    return None

# Function to extract product details and image URL
def extract_product_details(product_url):
    try:
        response = requests.get(product_url)
        html_content = response.content
        soup = BeautifulSoup(html_content, "html.parser")
        product_name = soup.find("span", class_="base", itemprop="name").text.strip()
        # Check for "متوفر" status first
        product_status_element = soup.find("div", class_="stock available")
        if product_status_element:
            product_status = product_status_element.span.text.strip()
        else:
            raise ValueError("Status 'متوفر' not found")
        # Extract all image URLs and find the one containing the desired pattern
        images = soup.find_all("img")
        pattern = "https://assets.dzrt.com/media/catalog/product/cache/bd08de51ffb7051e85ef6e224cd8b890/"
        image_url = None
        for img in images:
            src = img.get('data-src') or img.get('src')
            if src and pattern in src:
                image_url = src
                break
        return product_name, product_status, image_url
    except Exception as e:
        try:
            # Try to find "سيتم توفيرها في المخزون قريباً" status if "متوفر" is not found
            product_status_element = soup.find("div", class_="stock unavailable")
            if product_status_element:
                product_status = product_status_element.span.text.strip()
            else:
                product_status = None
            # Extract all image URLs and find the one containing the desired pattern
            images = soup.find_all("img")
            pattern = "https://assets.dzrt.com/media/catalog/product/cache/bd08de51ffb7051e85ef6e224cd8b890/"
            image_url = None
            for img in images:
                src = img.get('data-src') or img.get('src')
                if src and pattern in src:
                    image_url = src
                    break
            return product_name, product_status, image_url
        except Exception as inner_e:
            print(f"Error extracting product details for {product_url}: {str(inner_e)}")
            return None, None, None

# Function to send product data to Telegram
def send_product_data_to_telegram(product_name, product_status, image_url, product_link):
    bot_token = "7288675008:AAEuvumaPpNNbnHMJfVEPYTBVKxFjLPJwl8"
    chat_id = "-1002201592907"
    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
       # Update the message text with emojis, user-friendly language, and bold text
    if product_status == "متوفر":
        message_text = f"✅ **المنتج متاح** ✅: {product_name}"
        reply_markup = {
            "inline_keyboard": [
                [{"text": "🔍 عرض المنتج", "url": product_link}, {"text": "🛒 عرض السلة", "url": "https://www.dzrt.com/ar/checkout/cart"}],
                [{"text": "🔐 تسجيل الدخول", "url": "https://www.dzrt.com/ar/customer/account/login/"}, {"text": "💳 الانتقال إلى رابط الدفع النهائي", "url": "https://www.dzrt.com/ar/onestepcheckout.html"}]
            ]
        }
    else:
        message_text = f"❌ **نفذ من المخزون** ❌: {product_name}"
        reply_markup = {
            "inline_keyboard": [
                [{"text": "🔐 تسجيل الدخول", "url": "https://www.dzrt.com/ar/customer/account/login/"}]
            ]
        }

    params = {
        "chat_id": chat_id,
        "photo": image_url,
        "caption": message_text,
        "parse_mode": "Markdown",  # Specify Markdown to enable bold text
        "reply_markup": json.dumps(reply_markup)
    }
    
    response = requests.post(telegram_api_url, params=params)
    if response.status_code == 200:
        print(f"Product data sent successfully for {product_name}")
    else:
        print(f"Failed to send product data for {product_name}. Status code: {response.status_code}")

# Main function to run the code
def main():
    global last_sent_status
    url = "https://www.dzrt.com/ar/tamra.html"
    while True:
        html_content = fetch_url_with_retry(url)
        if html_content:
            product_name, product_status, image_url = extract_product_details(url)
            if product_name and product_name == "تمرة":
                if product_status in ["متوفر", "سيتم توفيرها في المخزون قريباً"]:
                    if product_status != last_sent_status:
                        send_product_data_to_telegram(product_name, product_status, image_url, url)
                        last_sent_status = product_status
        # Wait for 20 seconds before checking again
        time.sleep(5)

if __name__ == "__main__":
    main()
