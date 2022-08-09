import scrapy
from inline_requests import inline_requests


class FoxSpider(scrapy.Spider):
    name = 'fox'
    allowed_domains = ['www.foxracing.com']
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.ridetsg.com/products-all/',
        'Connection': 'keep-alive',
        'Cookie': 'cmplz_banner-status=dismissed; _ga_K0DP6PRS4Q=GS1.1.1659435151.16.1.1659437735.0; _ga=GA1.1.48014674.1659253896; PHPSESSID=tgg3hopuh1m14l1ndsdpd7s1nm',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    custom_settings = {
        "CONCURRENT_REQUESTS": 32,
        "DOWNLOAD_DELAY": 0.4,
    }

    def start_requests(self):
        urls = ['https://www.foxracing.com/mens/mtb/?https%3A%2F%2Fwww.foxracing.com%2Fmens%2Fmtb%2F=undefined&start=0&sz=1000', 'https://www.foxracing.com/mens/moto/?https%3A%2F%2Fwww.foxracing.com%2Fmens%2Fmoto%2F=undefined&start=0&sz=1000', 'https://www.foxracing.com/mens/lifestyle/?https%3A%2F%2Fwww.foxracing.com%2Fmens%2Flifestyle%2F=undefined&start=0&sz=1000', 'https://www.foxracing.com/womens/mtb/?https%3A%2F%2Fwww.foxracing.com%2Fwomens%2Fmtb%2F=undefined&start=0&sz=1000', 'https://www.foxracing.com/womens/moto/?https%3A%2F%2Fwww.foxracing.com%2Fwomens%2Fmoto%2F=undefined&start=0&sz=1000',
                        'https://www.foxracing.com/womens/lifestyle/?https%3A%2F%2Fwww.foxracing.com%2Fwomens%2Flifestyle%2F=undefined&start=0&sz=1000', 'https://www.foxracing.com/youth/mtb/?https%3A%2F%2Fwww.foxracing.com%2Fyouth%2Fmtb%2F=undefined&start=0&sz=1000', 'https://www.foxracing.com/youth/moto/?https%3A%2F%2Fwww.foxracing.com%2Fyouth%2Fmoto%2F=undefined&start=0&sz=1000', 'https://www.foxracing.com/youth/lifestyle/?https%3A%2F%2Fwww.foxracing.com%2Fyouth%2Flifestyle%2F=undefined&start=0&sz=1000']
        for url in urls:
            yield scrapy.Request(
                url=url,
                headers=self.headers,
                callback=self.process_first_page
            )

    def process_first_page(self, response):
        product_ids = response.xpath(
            '//div[@class="row product-grid"]/div[@class="col-6 col-sm-4"]/div[@class="product"]/@data-pid').getall()
        for ids in product_ids:
            url = f"https://www.foxracing.com/on/demandware.store/Sites-FoxUS-Site/en_US/Product-ShowQuickView?pid={ids}"
            yield scrapy.Request(
                url=url,
                headers=self.headers,
                callback=self.process_api_product,
            )

    @inline_requests
    def process_api_product(self, response):
        variants = []
        for variant in response.json()['product']['variationAttributes'][0]['values']:
            url = variant['url']
            res = yield scrapy.Request(url)
            variants.append(res.json())
        product_url = response.json()['productUrl']
        resp = yield scrapy.Request(f"https://www.foxracing.com{product_url}")
        check_price = resp.xpath(
            '//div[@class="product-data col-12 col-md-6"]/div[@class="row"][2]/div[@class="col"]/div[@class="prices top-prices clearfix"]/div[@class="price"]/span/del')
        if check_price:
            sale_price = resp.xpath(
                '//div[@class="product-data col-12 col-md-6"]/div[@class="row"][2]/div[@class="col"]/div[@class="prices top-prices clearfix"]/div[@class="price"]/span/span[@class="sales"]/span/@content').get()
            price = resp.xpath(
                '//div[@class="product-data col-12 col-md-6"]/div[@class="row"][2]/div[@class="col"]/div[@class="prices top-prices clearfix"]/div[@class="price"]/span/del/span/span/@content').get()
        else:
            sale_price = resp.xpath(
                '//div[@class="product-data col-12 col-md-6"]/div[@class="row"][2]/div[@class="col"]/div[@class="prices top-prices clearfix"]/div[@class="price"]/span/span[@class="sales"]/span/@content').get()
            price = ''

        title = response.json()['product']['productName']
        vendor = response.json()['product']['brand']
        collection = response.json()['product']['gtmData']['categoryID']
        body = resp.xpath('//div[@class="product-details-tabs"]').get()
        product_number = variants[0]['product']['gtmData']['id'].split('-')[0]

        yield {
                    "Handle": f"{title}-{product_number}",
                    "Variant SKU": "",
                    "Title": title,
                    "Vendor": vendor,
                     "Body (HTML)": body,
                    "Published": True,
                    "Status": "active",
                    "Variant Price": sale_price,
                    "Variant Compare At Price": price,
                    "Image Src": variants[0]['product']['images']['large'][0]['url'],
                    "Image Position": 1,
                    "Image Alt Text": title,
                    "Collection": collection,
                    "Option1 Name": "Size",
                    'Option1 Value': 'Default title',
                    'Option2 Name': 'Color',
                    'Option2 Value': 'Default title',
                    "Variant Image": "",
                    "URL": resp.url
                    }

        variant_counter = 1
        for variant in variants:
            photos = variant['product']['images']['large']
            sizes = variant['product']['variationAttributes'][1]['values']
            color = variant['product']['variationAttributes'][0]['displayValue']
            product_handle = variant['product']['gtmData']['id'].split('-')[0]
            product_id = variant['product']['gtmData']['id']
            counter = 1
            if variant_counter == 1:
                for size in sizes:
                    if len(photos) == 1 and len(variant['product']['variationAttributes'][1]['values']) > 0:
                            yield {
                                "Handle": f"{title}-{product_number}",
                                "Variant SKU": f"{product_id}-{size['value']}",
                                "Option1 Value": size['value'],
                                'Option2 Value': color,
                                "Variant Price": sale_price,
                                "Variant Compare At Price": price,
                                "Variant Image": variant['product']['images']['large'][0]["url"]
                            }
                    elif len(photos) < len(sizes):
                        if counter <= len(sizes) and counter < len(photos):
                            yield {
                                "Handle": f"{title}-{product_number}",
                                "Variant SKU": f"{product_id}-{size['value']}",
                                "Image Src": photos[counter]['url'],
                                "Image Position": counter+1,
                                "Image Alt Text": title,
                                "Option1 Value": size['value'],
                                'Option2 Value': color,
                                "Variant Price": sale_price,
                                "Variant Compare At Price": price,
                                "Variant Image": variant['product']['images']['large'][0]["url"]
                            }
                            counter += 1
                        elif counter < len(sizes):
                            yield {
                                "Handle": f"{title}-{product_number}",
                                "Variant SKU": f"{product_id}-{size['value']}",
                                "Option1 Value": size['value'],
                                'Option2 Value': color,
                                "Variant Price": sale_price,
                                "Variant Compare At Price": price,
                                "Variant Image": variant['product']['images']['large'][0]["url"]
                            }
                            counter += 1
                    elif len(photos) > len(sizes):
                        if counter <= len(sizes):
                            yield {
                                "Handle": f"{title}-{product_number}",
                                "Variant SKU": f"{product_id}-{size['value']}",
                                "Image Src": photos[counter]['url'],
                                "Image Position": counter+1,
                                "Image Alt Text": title,
                                "Option1 Value": size['value'],
                                'Option2 Value': color,
                                "Variant Price": sale_price,
                                "Variant Compare At Price": price,
        "Variant Image": variant['product']['images']['large'][0]["url"]
                            }
                            counter += 1
                        if counter > len(sizes):
                            while counter < len(photos):
                                yield {
                                    "Handle": f"{title}-{product_number}",
"Variant SKU": f"{product_id}-{size['value']}",
                                    "Image Src": photos[counter]['url'],
                                    "Image Position": counter+1,
                                    "Image Alt Text": title,
                                }
                                counter += 1
                    else:
                        if counter < len(photos):
                            yield {
                                "Handle": f"{title}-{product_number}",
                                "Variant SKU": f"{product_id}-{size['value']}",
                                "Image Src": photos[counter]['url'],
                                "Image Position": counter+1,
                                "Image Alt Text": title,
                                "Option1 Value": size['value'],
                                'Option2 Value': color,
                                "Variant Price": sale_price,
                                "Variant Compare At Price": price,
                                "Variant Image": variant['product']['images']['large'][0]["url"]
                            }
                        counter += 1
                        if counter == len(photos):
                            yield {
                                "Handle": f"{title}-{product_number}",
                                "Variant SKU": f"{product_id}-{size['value']}",
                                "Option1 Value": size['value'],
                                'Option2 Value': color,
                                "Variant Price": sale_price,
                                "Variant Compare At Price": price,
                                "Variant Image": variant['product']['images']['large'][0]["url"]
                            }
            else:
                for size in sizes:
                        yield {
                            "Handle": f"{title}-{product_number}",
                            "Variant SKU": f"{product_id}-{size['value']}",
                            "Option1 Value": size['value'],
                            'Option2 Value': color,
                            "Variant Price": sale_price,
                            "Variant Compare At Price": price,
                            "Variant Image": variant['product']['images']['large'][0]["url"]
                        }
            variant_counter += 1
