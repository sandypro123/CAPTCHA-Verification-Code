from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import random
import requests
from ultralytics import YOLO
from markdownify import markdownify as md
import mysql.connector
from mysql.connector import Error
import re
import logging
import sys
# 配置日志记录器
logging.basicConfig(
    level=logging.ERROR,  # 记录错误级别的日志
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='error.log',  # 指定日志文件名
    filemode='a'  # 追加模式
)

#异常情况资源清理
def auto_clean(driver):
    driver.quit()
    #sys.exit()
#通过模型获取缺口位置
def get_pos(imageSrc):
    model = YOLO('best.onnx',task='detect')
    results = model.predict(imageSrc)
    # 处理预测结果
    for result in results:
        result.save()
        boxes = result.boxes
        box=boxes.xyxy.tolist()
        return box[0][0]

#自动化登录操作
def auto_login(driver):
    # 等待密码登录按钮出现并点击
    try:
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@id='root']/div/main/div/div/div/div/div[2]/div/div/div/div/form/div/div[2]"))
        )
        # 使用 ActionChains 模拟鼠标点击
        actions = ActionChains(driver)
        actions.move_to_element(login_button).click().perform()
    except Exception as e:
        logging.error("无法找到密码登录按钮: %s", e)
        auto_clean(driver) 
    # 等待用户名输入框出现
    try:
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))
        )
        # 使用 ActionChains 模拟键盘输入
        actions = ActionChains(driver)
        actions.move_to_element(username_input).click().perform()
        actions.send_keys("18017441060").perform()
    except Exception as e:
        logging.error("无法找到用户名输入框: %s", e)
        auto_clean(driver)
    time.sleep(random.uniform(2, 4))  # 随机等待时间
    # 等待密码输入框出现
    try:
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))
        )
        # 使用 ActionChains 模拟键盘输入
        actions = ActionChains(driver)
        actions.move_to_element(password_input).click().perform()
        password = "256131719xsl"
        for char in password:
            actions.send_keys(char).perform()
            # 在每个字符之间添加随机延迟
            time.sleep(random.uniform(0.1, 0.3))  # 随机延迟0.1到0.3秒
    except Exception as e:
        logging.error("无法找到密码输入框: %s", e)
        auto_clean(driver)
    time.sleep(random.uniform(2, 4))  # 随机等待时间
    # 等待登录按钮出现并点击
    try:
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        # 使用 ActionChains 模拟鼠标点击
        actions = ActionChains(driver)
        actions.move_to_element(login_button).click().perform()
    except Exception as e:
        logging.error("无法找到登录按钮: %s", e)
        auto_clean(driver)
    # 等待一段时间，以便登录完成
    time.sleep(random.uniform(2, 4))  # 随机等待时间
    bigImage = driver.find_element(By.CLASS_NAME, "yidun_bg-img")
    image_url = bigImage.get_attribute('src')
    response = requests.get(image_url)
    if response.status_code == 200:
        # 指定保存图片的路径和文件名
        directory = r'D:\zhihu-answers-catch'  # 替换为你的目录路径
        filename = 'result.jpg'    # 替换为你想要的文件名
        filepath = os.path.join(directory, filename)
        
        # 将图片内容写入指定路径的文件
        with open(filepath, 'wb') as f:
            f.write(response.content)
        distance=get_pos(filepath)
        print(f"图片已保存到: {filepath}")
    else:
        logging.error("图片下载失败，状态码：%s", response.status_code)
        auto_clean(driver)
    # 执行滑动操作
    actions = ActionChains(driver)
    actions.click_and_hold(driver.find_element(By.XPATH,'//div[2]/div/div/div[2]/div/div[2]/div[2]')).perform()
    actions.move_by_offset(distance+10, 0).perform()
    time.sleep(random.uniform(1, 2))
    actions.release().perform()
    time.sleep(random.uniform(2, 4))
    try:
        driver.find_element(By.XPATH,"/html/body/div[1]/div/main/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/a")
    except Exception as e:
        logging.error("登录失败: %s", e)
        auto_clean(driver)

#自动化抓取数据
def auto_getData(driver):
    print(driver.current_url)
    if driver.current_url !="https://www.zhihu.com/" :
        driver.get("https://www.zhihu.com/");  
    # 解析页面，获取热门问题列表
    time.sleep(2)  # 等待页面加载
    hot_questions = driver.find_elements(By.CLASS_NAME, "ContentItem-title")
    question_links = [question.find_element(By.TAG_NAME, "a").get_attribute("href") for question in hot_questions]
    connection=get_connect()
    # 抓取选中问题的答案
    for question_link in question_links:
        driver.get(question_link)
        time.sleep(2)  # 等待页面加载
        try:
            h1_element= driver.find_elements(By.XPATH, "//h1[@class='QuestionHeader-title']")
            if len(h1_element)==0 :
                h1_element= driver.find_elements(By.XPATH, "//h1[@class='post-title']")
            title=h1_element[1].text
            answers = driver.find_elements(By.XPATH, "//div[@class='RichContent-inner']")
            url=question_link
            content=""
            for answer in answers:
                markdown_content = "😀答："+md(answer.get_attribute('outerHTML'))
                content=markdown_content+content
            content = re.sub(r'\n\s*\n', '\n', content)
            cursor = connection.cursor()
            insert_query = "INSERT INTO spider_cnblognews (content, title, url) VALUES (%s, %s, %s)"
            data = (content, title, url)
        except Exception as e:
            logging.error("Failed to get data: %s", e)
        try:
            cursor.execute(insert_query, data)
            connection.commit()  # 提交事务
            print("Data inserted successfully")
        except Error as e:
            logging.error("Failed to insert data into MySQL table: %s", e)
    connection.close()

#连接数据库
def get_connect():
    try:
        connection = mysql.connector.connect(
            host='54.169.143.126',       # 数据库主机地址
            port='13306', #数据库端口
            user='sandy',       # 数据库用户名
            password='256131719xsl',   # 数据库密码
            database='mysql',  # 数据库名
            charset='utf8'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        logging.error("Error while connecting to MySQL: %s", e)

#主函数
if __name__ == "__main__":
    driver = None
    print("start")
    while True:
        try:
            # 创建选项对象
            edge_options = Options()
            # 设置选项，例如无头模式
            #edge_options.add_argument('--headless')
            # 设置自定义User-Agent
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            edge_options.add_argument(f'user-agent={user_agent}')
            # 使用本地用户资料
            edge_options.add_argument(r'--user-data-dir=C:\Users\songlin.xu\AppData\Local\Microsoft\Edge\User Data')
            # 排除自动化操作检测
            edge_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            # 使用webdriver_manager自动管理EdgeDriver
            service = Service(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=edge_options)
            # 修改webdriver属性防止被检测自动化操作
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                """
            })
            print("step1")
            # 访问登录页面
            driver.get("https://www.zhihu.com/signin")  
            # 判断是否登录过
            try:
                driver.find_element(By.XPATH,"/html/body/div[1]/div/main/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/a")
            except Exception as e:
                auto_login(driver)
            auto_getData(driver)
            print("step2")
            logging.error("Success")
        except Exception as e:
            logging.error("An error occurred: %s", e)
        finally:
            if driver is not None:
                auto_clean(driver)
            driver = None
        time.sleep(3600)