from playwright.sync_api import Playwright, sync_playwright
import json
import time

def get_case_pages(browser):
    
    page = browser.new_page()
    page.goto("https://knowit.dk/cases")

    case_pages = []

    # Accept cookies
    consent_button = page.get_by_role("button").and_(page.get_by_text("Accepter alle")).click()

   
    while True:
        page.get_by_role("button").and_(page.get_by_text("Flere cases")).click()
        page.wait_for_timeout(1000)
        if page.get_by_role("button").and_(page.get_by_text("Flere cases")).is_hidden():
            break


    for link in page.get_by_role("link").all():
        url = link.get_attribute('href')
        if "cases" in url and "knowit" in url:
            case_pages.append(url)

    return case_pages

def get_case(browser, url):
    page = browser.new_page()
    page.goto(url)

    # second last item because all mined case urls end on /
    name = url.split("/")[-2]
    json_dom = []

    case = page.locator("div.CasePage")
    wrap = case.locator("div").nth(0)
    content_divs = wrap.locator(">div")

    el = {
        "el": "h1",
        "text":case.locator("h1").inner_text()
    }

    json_dom.append(el)

    for i, div in enumerate(content_divs.all()):

        # we do not want the contact page. That is too much logic right now
        if i == content_divs.count()-1:    
            break

        # we try to maintain h2, p and image order by collecting them all at once
        all_in_one = div.locator("h2").or_(div.locator("p").or_(div.locator("img")))
        
        for element in all_in_one.all():
            # We evaluate a bit of javascript here giving us the element HTML type
            element_type  = element.evaluate("el => el.tagName")

            if element_type == "IMG":
                srcset = element.get_attribute("srcset")
                src = srcset.split(",")[0]
            
                el = {
                    "el": "img",
                    "src": "https://www.knowit.dk" + srcset.split(",")[0],
                    "alt": element.get_attribute("alt")
                }
                json_dom.append(el)

            else:
                el = {
                    "el": element_type.lower(),
                    "text":element.inner_text()
                }
                json_dom.append(el)
    
    return {
        "case": name, 
        "url": url,
        "dom": json_dom
    }

def save_case(case):
    path = "./cases/" + case["case"] + ".json"
    with open(path, "w", encoding='utf8') as casefile:
        json.dump(case, casefile, indent=4, ensure_ascii=False)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
   
    case_pages = get_case_pages(browser)

    
    for url in case_pages:
        print("Fetching data from " + url)
        case = get_case(browser, url)
        save_case(case)
        # Does it matter, maybe?
        time.sleep(1)
    
    browser.close()
    

