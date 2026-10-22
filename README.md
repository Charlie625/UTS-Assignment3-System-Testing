# UTS Assignment 3 – System Testing

## 1. Project Overview

This repository contains automated system tests for the LambdaTest eCommerce Playground website.

The project was developed for UTS Assignment 3. It uses Python, Selenium WebDriver and pytest to test three main functions: product search, product filtering and product sorting.

**Website Under Test:** https://ecommerce-playground.lambdatest.io/

## 2. Test Cases

| Test Case | Function | Test Scenarios |
|---|---|---|
| T004 | Product Search | Valid keyword, non-existent keyword, empty keyword |
| T005 | Product Filtering | Apple manufacturer, price range ($100–$200), in-stock availability |
| T006 | Product Sorting | Price low to high, price high to low, name A to Z |

Each test case includes three automated scenarios.

## 3. Testing Tools

- Python 3.13
- Selenium WebDriver
- pytest
- Google Chrome
- Visual Studio Code
- Windows 11

## 4. Source Code Files

**test_T004_search.py**

Tests product search using different search inputs and verifies the returned results.

**test_T005_filter.py**

Tests manufacturer, price range and product availability filters. It checks whether the displayed results meet the selected conditions.

**test_T006_sort.py**

Tests ascending price sorting, descending price sorting and alphabetical product name sorting. It uses Python assertions to verify the order of displayed products.

## 5. How to Run the Tests

Install the required Python packages:

`python -m pip install selenium pytest`

Ensure Google Chrome is installed and the Selenium WebDriver environment is configured.

Run each test file separately:

`python -m pytest test_T004_search.py -v`

`python -m pytest test_T005_filter.py -v`

`python -m pytest test_T006_sort.py -v`

Run all test files together:

`python -m pytest -v`

## 6. Test Results

All nine automated scenarios passed during the recorded test executions.

| Test Case | Passed | Failed |
|---|---|---|
| T004 | 3 | 0 |
| T005 | 3 | 0 |
| T006 | 3 | 0 |
| **Total** | **9** | **0** |

The automated tests verify the selected scenarios and their specified conditions. Some manual tests cover additional product listings and pages.

## 7. Evidence and Validation

Selenium WebDriver was used to interact with the website. Python assertions were used to compare actual results with expected outcomes.

pytest generated test execution results, and screenshots were captured during testing. The automated testing evidence is documented in the Assignment 3 report.

## 8. AI Assistance

AI assistance was used to support test script development, debugging and code review. The suggested code was reviewed, adjusted and executed in the local testing environment. The test outcomes were verified using pytest results and manual observations.
