from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re
import time
from pynput.keyboard import Listener, KeyCode
import threading
import os
import csv

def load_patients_from_csv(csv_path):
    patients = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not any(row.values()):
                continue
            patient = {(k or '').strip(): (v or '').strip() for k, v in row.items() if k}
            patients.append(patient)
    return patients

def take_screenshot(page, filename):
    try:
        page.screenshot(path=filename)
        print(f"Screenshot saved: {filename}")
    except Exception as e:
        print(f"Failed to take screenshot: {e}")

form_data = {
    "user_id": "fake_user",
    "password": "FakePassword123!",
    "patients": load_patients_from_csv("patients.csv")
}

ADDRESS_MAP = {
  "cc": {
      "address": "123 MAIN ST",
      "city": "CITYNAME",
      "zip": "11111",
      "state": "ST",
      "fax": "1112223333"
  },
  "rv": {
      "address": "456 BROADWAY AVE",
      "city": "TOWNVILLE",
      "zip": "22222",
      "state": "ST",
      "fax": "4445556666"
  }
}

def run_login():
    stop_event = threading.Event()
    diag_error_occurred = False

    def on_press(key):
        if key == KeyCode.from_char('='):
            print("Exit key (=) pressed. Closing browser...")
            stop_event.set()
            return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(accept_downloads=True)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        def inject_scroll_center():
            try:
                page.evaluate("""
                    () => {
                        window.scrollTo({ top: document.body.scrollHeight / 2 - window.innerHeight / 2, behavior: 'smooth' });
                        document.body.style.overflow = 'auto';
                    }
                """)
            except Exception as e:
                print(f"Scroll injection failed: {e}")

        page.goto("https://www.example.com/", wait_until="domcontentloaded")
        page.wait_for_selector('#asPrimary_ctl00_txtLoginId', timeout=30000)
        inject_scroll_center()
        page.fill('#asPrimary_ctl00_txtLoginId', form_data["user_id"])
        page.click('#asPrimary_ctl00_btnLookup')
        password_input = page.wait_for_selector('#asPrimary_ctl00_txtPassWord', timeout=15000)
        inject_scroll_center()
        password_input.click()
        password_input.type(form_data["password"], delay=100)
        page.wait_for_selector('#asPrimary_ctl00_btnSubmit', timeout=15000)
        inject_scroll_center()
        page.click('#asPrimary_ctl00_btnSubmit')
        page.wait_for_timeout(7000)
        page.wait_for_selector('#asPrimary_ctl00_cmdAgreeContinue', timeout=15000)
        inject_scroll_center()
        page.click('#asPrimary_ctl00_cmdAgreeContinue')
        page.wait_for_timeout(7000)

        for i, patient in enumerate(form_data["patients"]):
            print(f"Processing patient {i + 1}/{len(form_data['patients'])}...")
            retry_attempt = 0
            max_retries = 2
            while retry_attempt < max_retries:
                try:
                    page.fill('#asPrimary_ctl00_txtDateOfService', patient['date_of_service'])
                    time.sleep(1)
                    page.fill('#asPrimary_ctl00_TxbFirstName', patient['first_name'])
                    time.sleep(1)
                    page.fill('#asPrimary_ctl00_TxbLastName', patient['last_name'])
                    time.sleep(1)
                    page.fill('#asPrimary_ctl00_TxbMemberNumber', patient['member_id'])
                    time.sleep(1)
                    page.fill('#asPrimary_ctl00_TxbDateOfBirth', patient['dob'])
                    time.sleep(1)
                    inject_scroll_center()
                    diag_card = page.locator('div[data-contact-display="Phone"] h3.card-title', has_text="Diagnostic Imaging")
                    if diag_card.is_visible(timeout=5000):
                        diag_card.click()
                        time.sleep(3)
                        break
                    else:
                        print("Diagnostic Imaging not found. Proceeding with member search logic.")
                    member_selected = False
                    page.click('#asPrimary_ctl00_BtnSearch', no_wait_after=True)
                    try:
                        page.wait_for_selector('#asPrimary_ctl00_gvSearchMembers_ctl02_cmdSelectMember', timeout=15000)
                        row_index = retry_attempt + 2
                        select_member_id = f'#asPrimary_ctl00_gvSearchMembers_ctl0{row_index}_cmdSelectMember'
                        patient_link = page.locator(select_member_id)
                        if patient_link.is_visible(timeout=5000):
                            patient_link.click()
                            time.sleep(5)
                            member_selected = True
                    except PlaywrightTimeoutError:
                        print("Member search timed out.")
                    diag_card = page.locator('div[data-contact-display="Phone"] h3.card-title', has_text="Diagnostic Imaging")
                    if diag_card.is_visible(timeout=5000):
                        diag_card.click()
                        time.sleep(3)
                        break
                    else:
                        print("Diagnostic Imaging not found.")
                    take_screenshot(page, f"diag_error_{patient['first_name']}_{patient['last_name']}_try{retry_attempt+1}.png")
                    home_button = page.locator('#asNavigation_ctl00_hlHome')
                    if home_button.is_visible(timeout=5000):
                        home_button.click()
                        page.wait_for_timeout(5000)
                    retry_attempt += 1
                except Exception as e:
                    print(f"Error during patient retry {retry_attempt + 1}: {e}")
                    retry_attempt += 1
                    continue
            if retry_attempt == max_retries:
                print(f"Skipping patient {patient['first_name']} {patient['last_name']} after {max_retries} failed attempts.")
                continue
            try:
                phone_input = page.locator("#txbPhone")
                if phone_input.is_visible(timeout=5000):
                    page.fill('#txbPhone', patient['phone'])
                    page.select_option('#ddlPhoneType', value=patient['phone_type'])
            except Exception:
                pass
            time.sleep(2)
            try:
                page.wait_for_selector('#cmdContinue', timeout=15000)
                page.click('#cmdContinue')
            except Exception as e:
                print(f"Failed to click Start Order Request button: {e}")
            time.sleep(7)
            try:
                next_button = page.locator('#asPrimary_ctl00_cmdNext')
                if next_button.is_visible(timeout=15000):
                    next_button.click()
            except Exception as e:
                print(f"Failed to click Next button: {e}")
            time.sleep(7)
            try:
                provider_type_code = patient.get("provider_type", "").lower()
                page.check('#asSearch_ctl00_rbSearchType_2')
                if provider_type_code in ADDRESS_MAP:
                    address_info = ADDRESS_MAP[provider_type_code]
                    page.fill('#asSearch_ctl00_tbAddress', address_info['address'])
                    page.fill('#asSearch_ctl00_tbCity', address_info['city'])
                    page.fill('#asSearch_ctl00_tbZip', address_info['zip'])
                page.click('#asSearch_ctl00_btnSearch')
            except Exception as e:
                print(f"Failed in address search step: {e}")
            time.sleep(7)
            try:
                page.wait_for_selector('#asPrimary_ctl00_gvRecentProviders_ddlPageSizeList', timeout=10000)
                page.select_option('#asPrimary_ctl00_gvRecentProviders_ddlPageSizeList', '50')
                time.sleep(7)
            except PlaywrightTimeoutError:
                print("Page size dropdown not found.")
            def find_provider_across_pages():
                try:
                    locator = page.locator("a", has_text=re.compile(re.escape(patient['provider_name']), re.IGNORECASE))
                    if locator.count() > 0:
                        locator.first.click()
                        return True
                except Exception as e:
                    print(f"Error locating provider: {e}")
                for page_number in range(1, 6):
                    try:
                        next_button = page.get_by_role("link", name=">", exact=True)
                        if not next_button.is_visible():
                            break
                        next_button.click()
                        page.wait_for_timeout(7000)
                        locator = page.locator("a", has_text=re.compile(re.escape(patient['provider_name']), re.IGNORECASE))
                        if locator.count() > 0:
                            locator.first.click()
                            return True
                    except Exception as e:
                        print(f"Error navigating page {page_number + 1}: {e}")
                        break
                return False
            provider_found = find_provider_across_pages()
            if provider_found:
                try:
                    provider_type = patient.get("provider_type", "").lower()
                    fax_number = ADDRESS_MAP.get(provider_type, {}).get("fax", "")
                    if fax_number:
                        fax_input = page.locator('#asPrimary_ctl00_txbFax')
                        fax_input.fill('')
                        for digit in fax_number:
                            fax_input.type(digit)
                            time.sleep(0.2)
                        fax_input.focus()
                        page.keyboard.press("Tab")
                    save_btn = page.locator('#save')
                    if save_btn.is_enabled(timeout=5000):
                        save_btn.click()
                except Exception as e:
                    print(f"Error during Save step: {e}")
            time.sleep(7)
            try:
                cpt_code = patient.get("cpt_code", "")
                if cpt_code:
                    page.fill('#examSelection\\.cptCode__formControl', cpt_code)
                    page.click('svg.cl-search-icon')
                    page.wait_for_timeout(5000)
                    page.click('#addExam\\(\\)__button')
            except Exception as e:
                print(f"Error during CPT code step: {e}")
            time.sleep(7)
            try:
                next_button = page.locator('button#applyPostClaimsForm__next\\(\\)__button')
                next_button.wait_for(timeout=17000)
                if next_button.is_visible():
                    next_button.click()
                    page.wait_for_timeout(7000)
            except PlaywrightTimeoutError:
                print("Timed out waiting for Next button after Add Exam.")
            time.sleep(7)

        print("All patients processed. Press '=' to exit browser.")
        listener = Listener(on_press=on_press)
        listener.start()
        stop_event.wait()
        context.close()
        browser.close()
        listener.stop()

if __name__ == "__main__":
    run_login()
