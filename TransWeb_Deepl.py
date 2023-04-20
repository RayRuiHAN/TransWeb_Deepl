# -*- coding: utf-8 -*-
import os
import time
import tkinter as tk
import unicodedata as ucd

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from retrying import retry


def read_text_file(input_path):
    """从指定的文本文件中读取文本并返回文本列表"""
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text.splitlines()


def split_text(text_list):
    """将文本列表中的长文本按照指定长度分割成多个段落"""
    max_len = 2500
    paragraphs = []
    current_len = 0
    current_paragraph = ''

    for text in text_list:
        text = ucd.normalize('NFKC', text).replace(' ', ' ').replace('\t', ' ')
        if text == '':
            continue

        text_len = len(text)
        if current_len + text_len > max_len:
            paragraphs.append(current_paragraph.strip())
            current_len = 0
            current_paragraph = ''

        current_paragraph += text + '\n'
        current_len += text_len

    if current_paragraph:
        paragraphs.append(current_paragraph.strip())

    return paragraphs


def wait_for_translation_result(driver):
    """等待翻译结果出现并返回结果元素"""
    @retry(stop_max_delay=30000)
    def copy_button_appears(driver):
        driver.find_element(By.XPATH, xpath_copy_button)

    copy_button_appears(driver)
    result_div = driver.find_element(By.XPATH, xpath_result)
    return result_div


def translate_text(text, driver):
    """将指定的文本翻译为中文，并返回翻译结果"""
    # 输入翻译文本
    textarea = driver.find_element(By.XPATH, xpath_textarea)
    textarea.send_keys(text)

    try:
        # 等待翻译结果出现
        result_div = wait_for_translation_result(driver)
    except NoSuchElementException as error:
        print(f"Error translating: {text[:20]}...")
        return ''

    # 获取翻译结果
    output = result_div.get_attribute('textContent')

    # 将翻译结果写入文件
    with open(output_path, 'a+', encoding='utf-8') as file1:
        file1.write(output + '\n')

    return output


def translate_text_list(text_list, driver):
    """将指定的文本列表翻译为中文"""
    total = len(text_list)
    count = 0

    for i, text in enumerate(text_list):
        # 翻译文本
        output = translate_text(text, driver)

        # 输出翻译进度
        count += 1
        print(f'{count}/{total}: {text[:20]}... -> {output[:20]}...')

        # 清空文本框
        textarea = driver.find_element(By.XPATH, xpath_textarea)
        textarea.clear()

    print(total, " All Done. Quit in 3 Seconds...")
    time.sleep(3)


def main():
    # 初始化 tkinter，以隐藏窗
    root = tk.Tk()
    root.withdraw()

    # 获取当前工作目录
    current_dir = os.getcwd()

    # 获取输入文件名
    raw = input("The name of raw txt: ")

    # 构建输入文件路径
    input_path = os.path.join(current_dir, raw + '.txt')

    # 构建输出文件路径
    global output_path
    output_path = os.path.join(current_dir, raw + '_zh.txt')

    # 获取起始页码
    page = int(input("Continued Page (default 1): ") or '1')

    # 打开谷歌浏览器并访问翻译网站
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.deepl.com/translator#en/zh/")
    driver.minimize_window()
    time.sleep(2)

    # 读取并分割文本
    text_list = read_text_file(input_path)
    paragraphs = split_text(text_list)

    # 从指定页码开始翻译文本
    translate_text_list(paragraphs[page-1:], driver)

    # 退出浏览器
    driver.quit()
    os.system('''taskkill /F /im chromedriver.exe''')

    # 输出总用时
    end_time = time.time()
    total_time = end_time - start_time
    print(f"time cost {total_time:.2f} seconds")


start_time = time.time()
web_link = 'https://www.deepl.com/translator#en/zh/'
xpath_textarea = '//*[@id="panelTranslateText"]/div[1]/div[2]/section[1]/div[3]/div[2]/d-textarea/div'
xpath_result = '//*[@id="target-dummydiv"]'
xpath_copy_button = '//*[@id="panelTranslateText"]/div[1]/div[2]/section[2]/div[3]/div[6]/div/div/div[2]/span[2]/span/span/button'
main()
