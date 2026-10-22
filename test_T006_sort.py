import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import StaleElementReferenceException


# Assignment 3 - Member B
# T006: Product Sorting
# Scenario 1: Price (Low > High)

SEARCH_URL = (
    "https://ecommerce-playground.lambdatest.io/"
    "index.php?route=product/search&search="
)

EVIDENCE_DIR = Path(__file__).parent / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)


# Extract visible products in their displayed order
def get_products(driver):

    return driver.execute_script("""
        const root =
            document.querySelector('#entry_212408')
            || document;

        let cards = [
            ...root.querySelectorAll('.product-grid')
        ];

        if (cards.length === 0) {
            cards = [
                ...root.querySelectorAll('.product-layout')
            ];
        }

        const products = [];

        for (const card of cards) {

            const nameElement = card.querySelector(
                'h4, h3, h5, .product-title, .title'
            );

            const priceElement = card.querySelector(
                '.price-new, .price'
            );

            if (nameElement && priceElement) {
                products.push({
                    name: nameElement.innerText.trim(),
                    price: priceElement.innerText.trim()
                });
            }
        }

        return products;
    """)


# Locate the sorting dropdown
def get_sort_dropdown(driver):

    elements = driver.find_elements(
        By.XPATH,
        "//select[option[contains(., 'Price (Low > High)')]]"
    )

    for element in elements:
        if element.is_displayed():
            return element

    return None


def test_T006_S1_price_low_to_high():

    driver = webdriver.Chrome()
    driver.maximize_window()

    wait = WebDriverWait(driver, 25)

    try:

        # Step 1: Open the product listing
        driver.get(SEARCH_URL)

        wait.until(
            lambda d: len(get_products(d)) >= 6
        )

        original_products = get_products(driver)

        print("PASS: Product listing loaded.")

        # Step 2: Locate sorting dropdown
        sort_dropdown = wait.until(
            get_sort_dropdown
        )

        # Step 3: Apply ascending price sorting
        Select(sort_dropdown).select_by_visible_text(
            "Price (Low > High)"
        )

        # Step 4: Wait for the updated listing
        def sorting_updated(d):
            try:
                dropdown = get_sort_dropdown(d)

                if dropdown is None:
                    return False

                selected = Select(
                    dropdown
                ).first_selected_option.text.strip()

                products = get_products(d)

                return (
                    selected == "Price (Low > High)"
                    and len(products) >= 6
                    and products != original_products
                )

            except StaleElementReferenceException:
                return False

        wait.until(sorting_updated)

        print("PASS: Ascending sorting selected.")

        # Step 5: Extract product prices
        products = get_products(driver)

        prices = []

        for product in products:

            match = re.search(
                r"\$\s*([\d,]+(?:\.\d{1,2})?)",
                product["price"]
            )

            assert match, (
                f"FAIL: Cannot read price for "
                f"{product['name']}"
            )

            price = float(
                match.group(1).replace(",", "")
            )

            prices.append(price)

            print(
                f"Verified: {product['name']} - "
                f"${price:.2f}"
            )

        # Step 6: Verify price order
        assert len(prices) == 15, (
            f"FAIL: Expected 15 products, "
            f"found {len(prices)}."
        )

        assert all(
            prices[i] <= prices[i + 1]
            for i in range(len(prices) - 1)
        ), (
            "FAIL: Products are not sorted "
            f"in ascending price order: {prices}"
        )

        print(
            "PASS: All 15 displayed products "
            "are sorted from low to high."
        )

        print("Sorted prices:", prices)
        print("Sorted URL:", driver.current_url)

        # Step 7: Save screenshot
        driver.execute_script(
            "window.scrollTo(0, 0);"
        )

        time.sleep(1)

        screenshot_path = (
            EVIDENCE_DIR /
            "T006_S1_Automated_Result.png"
        )

        driver.save_screenshot(
            str(screenshot_path)
        )

        print("Screenshot:", screenshot_path)
        print("PASS: T006-S1 completed.")

    except Exception:

        driver.save_screenshot(
            str(
                EVIDENCE_DIR /
                "T006_S1_Error.png"
            )
        )

        raise

    finally:
        driver.quit()


# =========================================================
# T006 - Scenario 2
# Sort Products by Price (High to Low)
# =========================================================

def test_T006_S2_price_high_to_low():

    driver = webdriver.Chrome()
    driver.maximize_window()

    wait = WebDriverWait(driver, 25)

    try:
        # Step 1: Open the general product listing
        driver.get(SEARCH_URL)

        wait.until(
            lambda d: len(get_products(d)) >= 6
        )

        original_products = get_products(driver)

        print("PASS: Product listing loaded.")

        # Step 2: Locate the Sort By dropdown
        sort_dropdown = wait.until(
            get_sort_dropdown
        )

        # Step 3: Select Price (High > Low)
        Select(sort_dropdown).select_by_visible_text(
            "Price (High > Low)"
        )

        # Step 4: Wait for the sorted listing to load
        def sorting_updated(d):
            try:
                dropdown = get_sort_dropdown(d)

                if dropdown is None:
                    return False

                selected = Select(
                    dropdown
                ).first_selected_option.text.strip()

                products = get_products(d)

                return (
                    selected == "Price (High > Low)"
                    and len(products) == 15
                    and products != original_products
                )

            except StaleElementReferenceException:
                return False

        wait.until(sorting_updated)

        print("PASS: Descending sorting selected.")

        # Step 5: Extract displayed product prices
        products = get_products(driver)

        prices = []

        for product in products:

            match = re.search(
                r"\$\s*([\d,]+(?:\.\d{1,2})?)",
                product["price"]
            )

            assert match, (
                f"FAIL: Cannot read price for "
                f"{product['name']}"
            )

            price = float(
                match.group(1).replace(",", "")
            )

            prices.append(price)

            print(
                f"Verified: {product['name']} - "
                f"${price:.2f}"
            )

        # Step 6: Verify descending price order
        assert len(prices) == 15, (
            f"FAIL: Expected 15 products, "
            f"found {len(prices)}."
        )

        assert all(
            prices[i] >= prices[i + 1]
            for i in range(len(prices) - 1)
        ), (
            "FAIL: Products are not sorted "
            f"in descending price order: {prices}"
        )

        print(
            "PASS: All 15 displayed products "
            "are sorted from high to low."
        )

        print("Sorted prices:", prices)
        print("Sorted URL:", driver.current_url)

        # Step 7: Save automated screenshot
        driver.execute_script(
            "window.scrollTo(0, 0);"
        )

        time.sleep(2)

        screenshot_path = (
            EVIDENCE_DIR /
            "T006_S2_Automated_Result.png"
        )

        driver.save_screenshot(
            str(screenshot_path)
        )

        print("Screenshot:", screenshot_path)
        print("PASS: T006-S2 completed.")

    except Exception:

        driver.save_screenshot(
            str(
                EVIDENCE_DIR /
                "T006_S2_Error.png"
            )
        )

        raise

    finally:
        driver.quit()


# =========================================================
# T006 - Scenario 3
# Sort Products by Name (A to Z)
# =========================================================

def test_T006_S3_name_a_to_z():

    driver = webdriver.Chrome()
    driver.maximize_window()

    wait = WebDriverWait(driver, 25)

    try:
        # Step 1: Open the general product listing
        driver.get(SEARCH_URL)

        wait.until(
            lambda d: len(get_products(d)) >= 6
        )

        original_products = get_products(driver)

        print("PASS: Product listing loaded.")

        # Step 2: Locate the Sort By dropdown
        sort_dropdown = wait.until(
            get_sort_dropdown
        )

        # Step 3: Select Name (A - Z)
        Select(sort_dropdown).select_by_visible_text(
            "Name (A - Z)"
        )

        # Step 4: Wait for the sorted products
        def sorting_updated(d):
            try:
                dropdown = get_sort_dropdown(d)

                if dropdown is None:
                    return False

                selected = Select(
                    dropdown
                ).first_selected_option.text.strip()

                products = get_products(d)

                return (
                    selected == "Name (A - Z)"
                    and len(products) == 15
                    and products != original_products
                )

            except StaleElementReferenceException:
                return False

        wait.until(sorting_updated)

        print("PASS: Alphabetical sorting selected.")

        # Step 5: Extract the displayed product names
        products = get_products(driver)

        product_names = []

        for product in products:

            name = product["name"].strip()

            assert name, (
                "FAIL: An empty product name was found."
            )

            product_names.append(name)

            print(f"Verified product: {name}")

        # Step 6: Verify alphabetical order
        assert len(product_names) == 15, (
            f"FAIL: Expected 15 products, "
            f"found {len(product_names)}."
        )

        assert len(set(product_names)) >= 2, (
            "FAIL: Insufficient distinct product "
            "names to verify alphabetical order."
        )

        normalized_names = [
            name.casefold()
            for name in product_names
        ]

        assert all(
            normalized_names[i] <= normalized_names[i + 1]
            for i in range(len(normalized_names) - 1)
        ), (
            "FAIL: Products are not sorted "
            f"alphabetically: {product_names}"
        )

        print(
            "PASS: All 15 displayed products "
            "are sorted alphabetically from A to Z."
        )

        print("Sorted product names:", product_names)
        print("Sorted URL:", driver.current_url)

        # Step 7: Save automated result screenshot
        driver.execute_script(
            "window.scrollTo(0, 0);"
        )

        time.sleep(2)

        screenshot_path = (
            EVIDENCE_DIR /
            "T006_S3_Automated_Result.png"
        )

        driver.save_screenshot(
            str(screenshot_path)
        )

        print("Screenshot:", screenshot_path)
        print("PASS: T006-S3 completed.")

    except Exception:

        try:
            driver.save_screenshot(
                str(
                    EVIDENCE_DIR /
                    "T006_S3_Error.png"
                )
            )
        except Exception:
            pass

        raise

    finally:
        driver.quit()
