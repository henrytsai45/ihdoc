from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def write_to_google_sheets(transaction_total, gross_sales):
    # Google Sheets API 設定
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('shop-line.json', scope)
    client = gspread.authorize(creds)

    # 開啟 Google Sheet
    sheet = client.open_by_key("").sheet1

    # 插入資料到第 2 行，舊數據下移
    now = datetime.now().strftime("最近更新時間：%Y年%m月%d日 %H：%M：%S")
    new_row = [now, transaction_total, gross_sales]
    sheet.insert_row(new_row, 2)

def main():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 進到後台登入頁
        driver.get("")

        # 顯式等待
        wait = WebDriverWait(driver, 20)

        # 登入流程
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, "staff_email"))
        )
        password_field = wait.until(
            EC.presence_of_element_located((By.ID, "staff_password"))
        )
        login_button = wait.until(
            EC.element_to_be_clickable((By.ID, "reg-submit-button"))
        )

        username_field.send_keys("")
        password_field.send_keys("")
        login_button.click()

        # 等待後台頁面加載完成
        wait.until(EC.url_contains("/admin"))
        time.sleep(5)  # 額外延遲

        # 點擊「更多數據」按鈕
        try:
            more_data_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'sc-eHgmQL') and .//span[text()='更多數據']]"))
            )
            more_data_button.click()
        except Exception as e:
            print("無法點擊「更多數據」按鈕: ", e)

        # 選擇今天的數據
        try:
            parent_element = driver.find_element(By.XPATH, "//div[contains(@class, 'DateRange__StyledCurrentDateRange')]")
            parent_element.click()

            today_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='tab' and contains(@class, 'DateMultiRangePickerModal__ToolkitsOption') and text()='今天']"))
            )
            today_button.click()

            apply_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(@class, 'Button__Container') and text()='套用']"))
            )
            apply_button.click()
        except Exception as e:
            print("無法選擇今天的數據: ", e)

        time.sleep(3)

        # 提取成交總額 (order='0')
        transaction_total = "N/A"
        try:
            transaction_total_element = wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@order='0']//div[@data-test-type='number']/div[@class='PanelSummaryValue__StyledValue-vmxipn-1 eudrua']"))
            )
            transaction_total = transaction_total_element.text
        except Exception as e:
            print("無法提取成交總額: ", e)

        # 提取總營業額 (order='2')
        gross_sales = "N/A"
        try:
            gross_sales_element = wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@order='2']//div[@data-test-type='number']/div[@class='PanelSummaryValue__StyledValue-vmxipn-1 eudrua']"))
            )
            gross_sales = gross_sales_element.text
        except Exception as e:
            print("無法提取總營業額: ", e)

        # 將數據寫入 Google Sheets
        write_to_google_sheets(transaction_total, gross_sales)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
