import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
from time import sleep
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"


def get_pages(max_pages=1):
    return [BASE_URL.format(page) for page in range(1, max_pages + 1)]


def fetch_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except requests.exceptions.RequestException as e:
        print(f"Network error at {url}: {e}")
        return None


def extract_links(page_url):
    soup = fetch_soup(page_url)
    if soup is None:
        return []

    links = []
    for art in soup.select("article.product_pod"):
        link = urljoin(page_url, art.a["href"])
        links.append(link)

    return links


def extract_products(page_url):
    soup = fetch_soup(page_url)
    if soup is None:
        return []

    rate_map = {"One":1,"Two":2,"Three":3,"Four":4,"Five":5}

    data = []
    for article in soup.select("article.product_pod"):

        title = article.h3.a["title"]
        price = article.find("p",class_="price_color").text
        rate_class = article.find("p",class_="star-rating")["class"][1]
        rate = rate_map.get(rate_class,0)
        link = urljoin(page_url,article.a["href"])

        data.append({
            "Title":title,
            "Price":price,
            "Rate":rate,
            "Product Link":link
        })

    return data


def scrape_product(link):
    soup = fetch_soup(link)

    if soup is None:
        return "Unknown"

    th_tag = soup.find("th",string="Availability")

    if not th_tag:
        return "Unknown"

    td_value = th_tag.find_next_sibling("td")

    if not td_value:
        return "Unknown"

    return td_value.text.strip()


def collect_data(max_pages=1):

    pages = get_pages(max_pages)
    data = []

    for page_url in pages:

        products = extract_products(page_url)
        links = extract_links(page_url)

        for i, link in enumerate(links):

            availability = scrape_product(link)
            products[i]["Availability"] = availability

            sleep(random.uniform(1,2))

        data.extend(products)

    return pd.DataFrame(data)


def clean_dataframe(df):

    df = df.drop_duplicates()

    df["Price"] = (
        df["Price"]
        .str.replace("Â£","",regex=False)
        .str.strip()
        .astype(float)
    )

    df = df.fillna({
        "Title":"Unknown",
        "Price":0,
        "Rate":0,
        "Product Link":"Unknown",
        "Availability":"Unknown"
    })

    df = df.sort_values(by="Price",ascending=False).reset_index(drop=True)

    df["Price Category"] = pd.cut(
        df["Price"],
        bins=[-float("inf"),20,35,float("inf")],
        labels=["Cheap","Medium","Expensive"]
    )

    return df


def save_data(df):

    df.to_csv("books_cleaned.csv",index=False)
    df.to_excel("books_cleaned.xlsx",index=False)


def main():

    df_raw = collect_data(max_pages=3)
    df_clean = clean_dataframe(df_raw)
    save_data(df_clean)


if __name__ == "__main__":
    main()