import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Assignment 3 - Member B
# T004: Product Search
# Scenario 1: Search with a valid keyword

HOME_URL = (
    "https://ecommerce-playground.lambdatest.io/"
    "index.php?route=common/home"
)


def test_T004_S1_valid_product_search():

    driver = webdriver.Chrome()

    try:
        driver.maximize_window()
        driver.get(HOME_URL)

        wait = WebDriverWait(driver, 20)

        # Step 1: Find the visible search input
        search_box = wait.until(
            lambda d: next(
                (e for e in d.find_elements(By.NAME, "search")
                 if e.is_displayed()),
                None
            )
        )

        # Step 2: Enter the valid keyword
        search_box.clear()
        search_box.send_keys("iMac")

        # Step 3: Find and click the Search button
        search_button = wait.until(
            lambda d: next(
                (e for e in d.find_elements(
                    By.CSS_SELECTOR, "button[type='submit']")
                 if e.is_displayed()
                 and "search" in e.text.lower()),
                None
            )
        )
        search_button.click()

        # Step 4: Wait until the search results heading appears
        wait.until(
            lambda d: "Search - iMac"
            in d.find_element(By.TAG_NAME, "body").text
        )

        # Record the actual URL for debugging and test evidence
        print("Search results URL:", driver.current_url)


        # Step 5: Locate product links named "iMac"
        product_titles = wait.until(
            lambda d: [
                e for e in d.find_elements(
                    By.XPATH,
                    "//a[normalize-space()='iMac']"
                )
                if e.is_displayed()
            ]
        )

        # Display the number of matching products
        print("Matching product links:", len(product_titles))


        # Step 6: Compare results with expectation
        assert any(
            e.text.strip().lower() == "imac"
            for e in product_titles
        ), "FAIL: No matching iMac product was found."

        print("PASS: iMac products were found.")

    finally:
        # Save screenshot even if an assertion fails
        Path("evidence").mkdir(exist_ok=True)
        time.sleep(4)
        driver.save_screenshot(
            "evidence/T004_S1_Automated_Result.png"
        )

        driver.quit()



# ==========================================================
# T004 - Scenario 2: Search with a non-existent keyword
# Expected: The website displays a no-results message.
# ==========================================================

def test_T004_S2_nonexistent_keyword():

    driver = webdriver.Chrome()

    try:
        driver.maximize_window()
        driver.get(HOME_URL)

        wait = WebDriverWait(driver, 20)

        # Step 1: Locate the main search input
        search_box = wait.until(
            lambda d: next(
                (e for e in d.find_elements(By.NAME, "search")
                 if e.is_displayed()),
                None
            )
        )

        # Step 2: Enter a keyword that should not match
        search_box.clear()
        search_box.send_keys("zzzxxyy998877")

        # Step 3: Submit the search
        search_button = wait.until(
            lambda d: next(
                (e for e in d.find_elements(
                    By.CSS_SELECTOR,
                    "button[type='submit']")
                 if e.is_displayed()
                 and "search" in e.text.lower()),
                None
            )
        )

        search_button.click()

        # Step 4: Wait until the results page is displayed
        wait.until(
            lambda d: "Search - zzzxxyy998877"
            in d.find_element(By.TAG_NAME, "body").text
        )

        # Step 5: Verify the no-results message
        expected_message = (
            "There is no product that matches "
            "the search criteria."
        )

        actual_text = wait.until(
            lambda d: d.find_element(
                By.TAG_NAME, "body"
            ).text
            if expected_message in d.find_element(
                By.TAG_NAME, "body"
            ).text
            else False
        )

        assert expected_message in actual_text, (
            "FAIL: The expected no-results "
            "message was not displayed."
        )

        print("PASS: No matching products were found.")
        print("Expected message:", expected_message)
        print("Search results URL:", driver.current_url)

    finally:
        # Save screenshot as evidence
        Path("evidence").mkdir(exist_ok=True)

        driver.save_screenshot(
            "evidence/T004_S2_Automated_Result.png"
        )

        driver.quit()


    
# ==========================================================
# T004 - Scenario 3: Search with an empty keyword
# Expected: The website responds without an application
# error and displays a valid product listing.
# ==========================================================

def test_T004_S3_empty_keyword():

    driver = webdriver.Chrome()

    try:
        driver.maximize_window()
        driver.get(HOME_URL)

        wait = WebDriverWait(driver, 20)

        # Step 1: Locate the main product search field
        search_box = wait.until(
            lambda d: next(
                (e for e in d.find_elements(By.NAME, "search")
                 if e.is_displayed()),
                None
            )
        )

        # Step 2: Leave the keyword empty
        search_box.clear()

        # Confirm that no keyword has been entered
        assert search_box.get_attribute("value") == "", (
            "FAIL: The search field is not empty."
        )

        # Step 3: Find and click the Search button
        search_button = wait.until(
            lambda d: next(
                (e for e in d.find_elements(
                    By.CSS_SELECTOR,
                    "button[type='submit']")
                 if e.is_displayed()
                 and "search" in e.text.lower()),
                None
            )
        )

        search_button.click()

        # Step 4: Wait for the search results heading
        wait.until(
            lambda d: "Search -"
            in d.find_element(By.TAG_NAME, "body").text
        )

        # Step 5: Verify a product listing is displayed
        # HTC Touch HD was observed in the manual test
        product_links = wait.until(
            lambda d: [
                e for e in d.find_elements(
                    By.XPATH,
                    "//a[normalize-space()='HTC Touch HD']"
                )
                if e.is_displayed()
            ]
        )

        assert len(product_links) > 0, (
            "FAIL: No expected product listing was found."
        )

        # Step 6: Report the actual behaviour
        print("PASS: Empty search was handled successfully.")
        print("Visible HTC Touch HD links:", len(product_links))
        print("Search results URL:", driver.current_url)

    finally:
        # Save evidence even if the test fails
        Path("evidence").mkdir(exist_ok=True)
        
        driver.save_screenshot(
            "evidence/T004_S3_Automated_Result.png"
        )

        driver.quit()
    
