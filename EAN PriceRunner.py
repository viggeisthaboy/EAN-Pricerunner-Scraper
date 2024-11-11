import requests
import csv
import time
import random

# URLs for API endpoints
search_url = "https://www.pricerunner.se/se/api/search-compare-gateway/public/search/v5/SE?q={EAN}"
product_detail_url = "https://www.pricerunner.se/se/api/search-compare-gateway/public/product-detail/v0/offers/SE/{ID}?af_ORIGIN=NATIONAL&af_ITEM_CONDITION=NEW,UNKNOWN&sortByPreset=PRICE"

# Headers for requests
headers = {
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
}

def fetch_product_id(ean):
    """Fetch product ID from EAN."""
    response = requests.get(search_url.format(EAN=ean), headers=headers)

    if response.status_code == 200:
        data = response.json()
        products = data.get("products", [])
        if products:
            return products[0]["id"]  # Return the first product ID found
    else:
        print(f"Failed to retrieve product ID for EAN: {ean}. Status code: {response.status_code}")
    return None

def fetch_price_and_merchant_info(product_id):
    """Fetch unique offers (price and merchant) for a given product ID, only if available and in stock."""
    url = product_detail_url.format(ID=product_id)
    response = requests.get(url, headers=headers)

    unique_offers = set()  # Use a set to track unique (merchant, price) combinations
    offers_list = []

    if response.status_code == 200:
        data = response.json()
        offers = data.get("offers", [])
        if offers:
            for offer in offers:
                # Check if the offer is available and in stock
                if offer.get("availability") == "AVAILABLE" and offer.get("stockStatus") == "IN_STOCK":
                    price_str = offer["price"]["amount"]
                    price = float(price_str)

                    # Check if the price is a whole number and convert to integer if so
                    if price.is_integer():
                        price = int(price)

                    merchant_name = data["merchants"].get(str(offer["merchantId"]), {}).get("name", "Unknown Merchant")
                    # Only add if this (merchant, price) combination is unique
                    if (merchant_name, price) not in unique_offers:
                        unique_offers.add((merchant_name, price))
                        offers_list.append({"price": price, "merchantName": merchant_name})
    else:
        print(f"Failed to retrieve details for Product ID {product_id}. Status code: {response.status_code}")

    return offers_list

def main():
    # Load input CSV with EAN, Price exc VAT, and Rec Price
    input_filename = "inputmargin.csv"  # Input CSV with headers 'EAN', 'Price exc VAT', and 'Rec Price'
    output_filename = "outputmargin.csv"  # Output CSV with additional headers

    with open(input_filename, mode="r", encoding="utf-8") as infile, open(output_filename, mode="w", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(infile)
        # Adding new columns to existing input columns for output
        fieldnames = reader.fieldnames + ["BrandName", "Sell Price"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            ean = row["EAN"]
            print(f"\nFetching offers for EAN: {ean}")
            product_id = fetch_product_id(ean)

            if product_id:
                offers = fetch_price_and_merchant_info(product_id)
                if offers:
                    # Collect unique brand names and prices as comma-separated strings
                    brand_names = ", ".join(sorted(set(offer["merchantName"] for offer in offers)))
                    prices = ", ".join(str(offer["price"]) for offer in offers)

                    # Update row with new information
                    row.update({
                        "BrandName": brand_names,
                        "Sell Price": prices
                    })
                else:
                    # No offers found for this product
                    row.update({
                        "BrandName": "No Product Found",
                        "Sell Price": ""
                    })
            else:
                # No product ID found for this EAN
                row.update({
                    "BrandName": "No Product Found",
                    "Sell Price": ""
                })

            # Write updated row to CSV
            writer.writerow(row)

            # Random delay to avoid detection
            delay = random.randint(1, 6)
            print(f"Sleeping for {delay} seconds to avoid detection as a bot.")
            time.sleep(delay)

if __name__ == "__main__":
    main()