from pathlib import Path
import json
import time

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

HOME_URL = (
    "https://ecommerce-playground.lambdatest.io/"
    "index.php?route=common/home"
)
EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"

# Read the rendered page DOM and identify the Apple control specifically
# under MANUFACTURER. Unlike an exact-text XPath, this supports "Apple 42".
APPLE_CONTROL_JS = r"""
const clean = s => (s || '').replace(/\s+/g, ' ').trim();
const visible = el => {
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return style.display !== 'none' && style.visibility !== 'hidden' &&
           rect.width > 0 && rect.height > 0;
};
const appleText = el => /^Apple(?:\s+\d+)?$/i.test(clean(el.innerText));
const priority = el => el.matches('label') ? 0 :
    el.matches('a') ? 1 : el.matches('button') ? 2 :
    el.matches('[role="checkbox"], [role="button"]') ? 3 :
    el.matches('li') ? 4 : el.matches('span') ? 5 : 6;

// Find a visible heading containing the direct text "MANUFACTURER".
const headings = [...document.querySelectorAll(
    'h2,h3,h4,h5,h6,div,span,a,strong,p'
)].filter(el => visible(el) && [...el.childNodes].some(node =>
    node.nodeType === 3 && /^MANUFACTURER$/i.test(clean(node.textContent))
));

for (const heading of headings) {
    // Walk up only far enough to reach the manufacturer's options.
    let group = heading.parentElement;
    while (group && group !== document.body) {
        const options = [...group.querySelectorAll(
            'label,a,button,[role="checkbox"],[role="button"],li,div,span'
        )].filter(el => visible(el) && appleText(el));
        if (options.length) {
            options.sort((a, b) => priority(a) - priority(b) ||
                clean(a.innerText).length - clean(b.innerText).length);
            return options[0];
        }
        group = group.parentElement;
    }
}
// Backup for different filter heading markup: restrict to left-hand
// filter containers, not unrelated product names in the results grid.
for (const root of document.querySelectorAll(
    '#column-left,aside,[class*="filter"],[id*="filter"]'
)) {
    if (!visible(root)) continue;
    const headingText = clean(root.innerText).toUpperCase();
    if (!headingText.includes('MANUFACTURER')) continue;
    const options = [...root.querySelectorAll('label,a,button,li,span')]
        .filter(el => visible(el) && appleText(el) &&
            el.getBoundingClientRect().left < window.innerWidth * 0.6);
    if (options.length) {
        options.sort((a, b) => priority(a) - priority(b));
        return options[0];
    }
}
return null;
"""


def visible_links(driver, name):
    """Find visible product-name links, excluding hidden duplicates."""
    xpath = f"//a[normalize-space(.)='{name}']"
    return [e for e in driver.find_elements(By.XPATH, xpath) if e.is_displayed()]


def save_debug(driver):
    """Save useful DOM details if a locator fails."""
    try:
        details = driver.execute_script(r"""
            return [...document.querySelectorAll('label,a,li,span,div')]
              .filter(el => /Apple|MANUFACTURER/i.test(el.innerText || '') &&
                    (el.innerText || '').length < 110)
              .slice(0, 35)
              .map(el => ({tag:el.tagName, text:el.innerText,
                            html:el.outerHTML.slice(0, 550)}));
        """)
        report = {"url": driver.current_url, "candidate_elements": details}
        file = EVIDENCE_DIR / "T005_S1_debug.json"
        file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Diagnostic file:", file)
    except Exception as exc:
        print("Could not save DOM diagnostics:", exc)


def test_T005_S1_apple_manufacturer_filter():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    driver = webdriver.Chrome()

    try:
        driver.maximize_window()
        driver.get(HOME_URL)
        wait = WebDriverWait(driver, 20)

        # Step 1: Find the visible main search field.
        search_box = wait.until(lambda d: next(
            (e for e in d.find_elements(By.NAME, "search") if e.is_displayed()),
            None,
        ))

        # Step 2: Submit the empty keyword search to load the product list.
        search_box.clear()
        search_button = wait.until(lambda d: next(
            (e for e in d.find_elements(By.CSS_SELECTOR, "button[type='submit']")
             if e.is_displayed() and "search" in e.text.lower()),
            None,
        ))
        search_button.click()
        wait.until(lambda d: "Search -" in d.find_element(By.TAG_NAME, "body").text)
        print("PASS: General search results page opened")
        print("Page URL:", driver.current_url)

        # Step 3: Confirm an unfiltered non-Apple item is initially present.
        wait.until(lambda d: len(visible_links(d, "HTC Touch HD")) > 0)
        print("PASS: HTC Touch HD was visible before applying the filter")

        # Step 4: Find Apple inside the MANUFACTURER filter section.
        apple_option = wait.until(lambda d: d.execute_script(APPLE_CONTROL_JS))
        print("Apple control:", apple_option.tag_name,
              repr(apple_option.text.strip()[:75]))
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", apple_option
        )

        # Step 5: Click Apple using ordinary Selenium interaction first.
        try:
            apple_option.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            print("Normal click was blocked; retrying the same element with JS")
            driver.execute_script("arguments[0].click();", apple_option)

        # Step 6: Wait for the filtered results, not just for the click.
        wait.until(lambda d:
                   len(visible_links(d, "iPod Touch")) > 0 and
                   len(visible_links(d, "HTC Touch HD")) == 0)

        # Step 7: Validate products observed during the manual test.
        expected_products = ["iPod Touch", "iPod Shuffle", "iPod Nano"]
        for name in expected_products:
            assert visible_links(driver, name), (
                f"Expected Apple-filtered product is missing: {name}"
            )
        assert not visible_links(driver, "HTC Touch HD"), (
            "A non-Apple HTC product is still displayed after filtering"
        )

        # Wait briefly for product pictures to render (screenshot only).
        time.sleep(2)
        image_file = EVIDENCE_DIR / "T005_S1_Automated_Result.png"
        driver.save_screenshot(str(image_file))

        print("PASS: Apple manufacturer filter changed the product listings")
        print("Verified names:", ", ".join(expected_products))
        print("Filtered URL:", driver.current_url)
        print("Screenshot:", image_file)

    except Exception:
        error_file = EVIDENCE_DIR / "T005_S1_Error.png"
        try:
            driver.save_screenshot(str(error_file))
            print("Failure screenshot:", error_file)
            save_debug(driver)
        except Exception as exc:
            print("Could not capture failure evidence:", exc)
        raise

    finally:
        driver.quit()

    

# =========================================================
# T005 - Scenario 2: Product Price Range Filtering
# Test Data: Minimum = $100, Maximum = $200
# =========================================================

def test_T005_S2_price_range_filter():
    import re
    import time
    from selenium.webdriver.common.keys import Keys

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    evidence_dir = Path("evidence")
    evidence_dir.mkdir(exist_ok=True)

    # Find the two price fields in the PRICE filter section
    price_fields_js = """
    const clean = s => (s || '').replace(/\\s+/g, ' ').trim();

    const visible = el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 &&
               s.display !== 'none' &&
               s.visibility !== 'hidden';
    };

    const headings = [...document.querySelectorAll(
        'div,span,h3,h4,h5,h6,strong,p'
    )].filter(el =>
        visible(el) &&
        [...el.childNodes].some(n =>
            n.nodeType === 3 &&
            clean(n.textContent).toUpperCase() === 'PRICE'
        )
    );

    for (const heading of headings) {
        let parent = heading.parentElement;

        while (parent && parent !== document.body) {
            const fields = [...parent.querySelectorAll('input')]
                .filter(el =>
                    visible(el) &&
                    ['text', 'number'].includes(el.type) &&
                    /^\\d+(\\.\\d+)?$/.test(el.value.trim())
                );

            if (fields.length === 2) {
                fields.sort((a, b) =>
                    a.getBoundingClientRect().left -
                    b.getBoundingClientRect().left
                );
                return fields;
            }

            parent = parent.parentElement;
        }
    }

    return [];
    """

    # Read visible product cards and their prices
    product_cards_js = """
    const visible = el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 &&
               s.display !== 'none' &&
               s.visibility !== 'hidden';
    };

    for (const selector of [
        '.product-layout',
        '.product-thumb',
        '.product-item'
    ]) {
        const cards = [...document.querySelectorAll(selector)]
            .filter(visible);

        const products = cards.map(card => {
            const name = card.querySelector(
                'h4 a, .caption a, .product-title a, a.product-name'
            );

            const price = card.querySelector(
                '.price-new, .price, .product-price'
            );

            return {
                name: (name?.textContent || '').trim(),
                price: (price?.textContent || '').trim()
            };
        }).filter(p => /\\$[\\d,.]+/.test(p.price));

        if (products.length >= 3) {
            return products;
        }
    }

    return [];
    """

    try:
        # Step 1: Open the website
        driver.maximize_window()
        driver.get(HOME_URL)

        # Step 2: Find the main search field
        search_box = wait.until(
            lambda d: next(
                (
                    e for e in d.find_elements(By.NAME, "search")
                    if e.is_displayed()
                ),
                None
            )
        )

        # Step 3: Submit an empty search
        search_box.clear()

        search_button = wait.until(
            lambda d: next(
                (
                    e for e in d.find_elements(
                        By.CSS_SELECTOR,
                        "button[type='submit']"
                    )
                    if e.is_displayed()
                    and "search" in e.text.lower()
                ),
                None
            )
        )

        search_button.click()

        wait.until(
            lambda d: "Search -" in
            d.find_element(By.TAG_NAME, "body").text
        )

        print("PASS: General product listing loaded")

        # Confirm an out-of-range product is present initially
        wait.until(
            lambda d: any(
                e.is_displayed()
                for e in d.find_elements(
                    By.XPATH,
                    "//a[normalize-space()='Palm Treo Pro']"
                )
            )
        )

        # Step 4: Set the price range without using stale elements
        from selenium.common.exceptions import StaleElementReferenceException

        # Read input values inside JavaScript to avoid stale references
        price_values_js = price_fields_js.replace(
            "return fields;",
            "return fields.map(el => el.value);"
        )

        for index, value in [(0, "100"), (1, "200")]:

            updated = False

            for attempt in range(5):
                try:
                    # Re-locate the inputs after every page update
                    fields = wait.until(
                        lambda d: (
                            elements
                            if len(elements := d.execute_script(
                                price_fields_js
                            )) == 2
                            else False
                        )
                    )

                    # Update the field in one JavaScript operation
                    driver.execute_script(
                        """
                        const input = arguments[0];
                        const value = arguments[1];

                        const setter =
                            Object.getOwnPropertyDescriptor(
                                HTMLInputElement.prototype,
                                'value'
                            ).set;

                        setter.call(input, value);

                        input.dispatchEvent(
                            new Event('input', {bubbles: true})
                        );

                        input.dispatchEvent(
                            new Event('change', {bubbles: true})
                        );

                        input.dispatchEvent(
                            new Event('blur', {bubbles: true})
                        );
                        """,
                        fields[index],
                        value
                    )

                    updated = True
                    break

                except StaleElementReferenceException:
                    print(
                        "Page refreshed; retrying price input:",
                        attempt + 1
                    )

            assert updated, (
                f"FAIL: Could not update price field {index}"
            )

            # Verify the value without caching WebElements
            wait.until(
                lambda d: (
                    len(values := d.execute_script(
                        price_values_js
                    )) == 2
                    and values[index] == value
                )
            )

            print(
                ("Minimum" if index == 0 else "Maximum"),
                "price set to:", value
            )

        # Step 5: Verify that filtering updated results
        wait.until(
            lambda d: (
                not any(
                    e.is_displayed()
                    for e in d.find_elements(
                        By.XPATH,
                        "//a[normalize-space()='Palm Treo Pro']"
                    )
                )
                and any(
                    e.is_displayed()
                    for e in d.find_elements(
                        By.XPATH,
                        "//a[normalize-space()='HTC Touch HD']"
                    )
                )
            )
        )

        print("PASS: Price filter changed the product listing")

        # Step 6: Extract and validate visible product prices
        products = wait.until(
            lambda d: (
                data if len(data := d.execute_script(
                    product_cards_js
                )) >= 3 else False
            )
        )

        checked_count = 0

        for product in products:
            price_text = product["price"]

            matches = re.findall(
                r"\$([\d,]+(?:\.\d{2})?)",
                price_text
            )

            assert matches, (
                f"Cannot read the price of {product['name']}"
            )

            price = float(matches[0].replace(",", ""))

            assert 100 <= price <= 200, (
                f"FAIL: {product['name']} costs ${price:.2f}, "
                "outside the required $100-$200 range."
            )

            checked_count += 1

            print(
                f"Verified: {product['name']} - ${price:.2f}"
            )

        assert checked_count >= 3, (
            "FAIL: Insufficient product prices were checked."
        )

        print(
            f"PASS: All {checked_count} inspected product "
            "prices are within $100-$200."
        )

        print("Filtered URL:", driver.current_url)


        # Step 7: Verify the final UI state before saving evidence
        from selenium.common.exceptions import TimeoutException

        # Return to the top of the page
        driver.execute_script("window.scrollTo(0, 0)")

        # Verify the price filter is present in the URL
        wait.until(
            lambda d: "mz_fp=100p200" in d.current_url
        )

        # Wait for product cards to finish rendering
        wait.until(
            lambda d: len(d.execute_script(product_cards_js)) >= 3
        )

        # Check the ACTUAL displayed price input values
        try:
            wait.until(
                lambda d: d.execute_script(price_values_js)
                == ["100", "200"]
            )

        except TimeoutException:
            actual_values = driver.execute_script(
                price_values_js
            )

            print(
                "WARNING: Price inputs do not match "
                "the applied filter.",
                actual_values
            )

            driver.save_screenshot(
                str(
                    evidence_dir /
                    "T005_S2_UI_Mismatch.png"
                )
            )

            raise AssertionError(
                f"Price filter URL is correct, but "
                f"displayed inputs are {actual_values}, "
                f"expected ['100', '200']."
            )

        # Save only after the UI matches the test condition
        driver.save_screenshot(
            str(evidence_dir / "T005_S2_Automated_Result.png")
        )

        print(
            "PASS: Filtered results and displayed "
            "price inputs match $100-$200."
        )


    except Exception:
        # Save evidence if the test fails
        driver.save_screenshot(
            str(evidence_dir / "T005_S2_Error.png")
        )

        print("DEBUG URL:", driver.current_url)

        try:
            fields = driver.execute_script(price_fields_js)
            print(
                "DEBUG PRICE fields:",
                [e.get_attribute("outerHTML") for e in fields]
            )
            print(
                "DEBUG product cards:",
                driver.execute_script(product_cards_js)[:5]
            )
        except Exception as error:
            print("DEBUG collection failed:", error)

        raise

    finally:
        driver.quit()



# =========================================================
# T005 - Scenario 3: Availability Filter (In Stock)
# =========================================================

def test_T005_S3_in_stock_filter():
    import re

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    evidence_dir = Path("evidence")
    evidence_dir.mkdir(exist_ok=True)

    # Find and operate the In Stock checkbox dynamically
    stock_option_js = """
    const action = arguments[0];

    const inputs = [
        ...document.querySelectorAll('input[type="checkbox"]')
    ];

    for (const input of inputs) {
        const label = input.labels && input.labels.length
            ? input.labels[0]
            : input.closest('label');

        const holder = label || input.parentElement;

        const text = (
            holder?.textContent || ''
        ).replace(/\\s+/g, ' ').trim();

        if (
            /\\bin\\s+stock\\b/i.test(text) &&
            !/\\bout\\s+of\\s+stock\\b/i.test(text)
        ) {
            if (action === 'click' && !input.checked) {
                if (label) {
                    label.click();
                } else {
                    input.click();
                }
            }

            if (action === 'scroll') {
                (label || input).scrollIntoView({
                    block: 'center'
                });
            }

            return {
                found: true,
                selected: Boolean(input.checked),
                label: text
            };
        }
    }

    return {
        found: false,
        selected: false,
        label: ''
    };
    """

    # Find a product URL without keeping stale elements
    product_url_js = """
    const target = arguments[0];

    for (const link of document.querySelectorAll('a')) {
        const name = (link.textContent || '')
            .replace(/\\s+/g, ' ')
            .trim();

        if (
            name === target &&
            link.href &&
            link.getClientRects().length > 0
        ) {
            return link.href;
        }
    }

    return null;
    """

    try:
        # Step 1: Open the website
        driver.maximize_window()
        driver.get(HOME_URL)

        # Step 2: Find the main search box
        search_box = wait.until(
            lambda d: next(
                (
                    e for e in d.find_elements(
                        By.NAME, "search"
                    )
                    if e.is_displayed()
                ),
                None
            )
        )

        # Step 3: Submit an empty search
        search_box.clear()

        search_button = wait.until(
            lambda d: next(
                (
                    e for e in d.find_elements(
                        By.CSS_SELECTOR,
                        "button[type='submit']"
                    )
                    if e.is_displayed()
                    and "search" in e.text.lower()
                ),
                None
            )
        )

        search_button.click()

        # Step 3: Wait for the search page to load
        # Use JavaScript to avoid stale element references
        wait.until(
            lambda d: d.execute_script(
                """
                return document.readyState === 'complete'
                    && document.body !== null
                    && document.body.innerText.includes('Search -');
                """
            )
        )

        print("PASS: Search page loaded successfully")


        # Step 4: Locate the Availability filter
        stock_state = wait.until(
            lambda d: (
                result
                if (result := d.execute_script(
                    stock_option_js, "status"
                ))["found"]
                else False
            )
        )

        print("Availability option found:", stock_state["label"])

        # Step 5: Apply the In Stock filter
        driver.execute_script(stock_option_js, "click")

        wait.until(
            lambda d: d.execute_script(
                stock_option_js, "status"
            )["selected"]
        )

        print("PASS: In Stock checkbox selected")

        # Step 6: Verify that product links are available
        product_names = [
            "iPod Touch",
            "HTC Touch HD"
        ]

        product_urls = {}

        for name in product_names:
            url = wait.until(
                lambda d: d.execute_script(
                    product_url_js, name
                )
            )

            assert url, (
                f"FAIL: {name} was not found in "
                "the filtered product listing."
            )

            product_urls[name] = url
            print("Filtered product found:", name)

        # Save the filtered results before opening products
        driver.execute_script(stock_option_js, "scroll")

        driver.save_screenshot(
            str(evidence_dir / "T005_S3_Automated_Result.png")
        )

        # Step 7: Verify actual availability in product details
        for name, url in product_urls.items():
            driver.get(url)

            detail_text = wait.until(
                lambda d: (
                    text if (
                        (text := d.find_element(
                            By.TAG_NAME, "body"
                        ).text)
                        and "Availability:" in text
                        and name in text
                    )
                    else False
                )
            )


            # Step 7: Extract the availability status
            # \s* matches optional whitespace, including newlines
            match = re.search(
                r"Availability\s*:\s*(In Stock|Out\s+Of\s+Stock)",
                detail_text,
                re.IGNORECASE
            )

            print(
                "Detected availability:",
                match.group(1) if match else "Not found"
            )


            assert match, (
                f"FAIL: Availability status for "
                f"{name} was not found."
            )

            status = match.group(1).strip()

            assert status.lower() == "in stock", (
                f"FAIL: {name} has availability "
                f"'{status}', expected 'In Stock'."
            )

            print(f"PASS: {name} - Availability: {status}")

            filename = name.replace(" ", "_")

            driver.save_screenshot(
                str(
                    evidence_dir /
                    f"T005_S3_{filename}_Detail.png"
                )
            )

        print(
            "PASS: In Stock filter activated and "
            "both inspected products were in stock."
        )

    except Exception:
        driver.save_screenshot(
            str(evidence_dir / "T005_S3_Error.png")
        )

        print("DEBUG URL:", driver.current_url)
        print(
            "DEBUG Stock Filter:",
            driver.execute_script(stock_option_js, "status")
        )

        raise

    finally:
        driver.quit()

