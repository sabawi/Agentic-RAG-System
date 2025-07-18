from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import time
import tempfile 

USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

class SeleniumCrawler:
    def __init__(self, base_url, max_depth=2, max_url_count=2,timeout_response=30):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        self.url_count = 0
        self.max_url_count = max_url_count
        self.visited = set()
        self.results = []
        self.timeout = timeout_response #in seconds
        self.check_robot = False

        temp_dir = tempfile.mkdtemp(prefix='chrome_user_data_')
        
        # Set up headless Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument(f'--user-data-dir={temp_dir}')
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument(f"--timeout 40000")
        chrome_options.add_argument(f"user-agent={USER_AGENT}")

        # seleniumwire_options = {'verify_ssl':False, 'connection_timeout':timeout_response, 'read_timeout':timeout_response}
        
        # Set page load timeout
        chrome_options.page_load_strategy = 'normal'
        
        service = Service()  # Remove timeout from here as it's not the right place
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set various timeouts
        self.driver.set_page_load_timeout(self.timeout)  # Page load timeout
        self.driver.set_script_timeout(self.timeout)     # Async script timeout
        self.driver.implicitly_wait(5)        # Implicit wait for finding elements
        
        self.robot_parser = self.setup_robot_parser()
        
    def setCheckRobot(self,check):
        self.check_robot = check
        
    def setup_robot_parser(self):
        robots_url = urljoin(self.base_url, "/robots.txt")
        robot_parser = RobotFileParser()
        robot_parser.set_url(robots_url)
        robot_parser.read()
        return robot_parser
    
    def is_allowed_to_crawl(self, url):
        if self.check_robot:
            # Check whether the site allows crawling or not
            return self.robot_parser.can_fetch("*", url)
        else:
            # print("\nSkipping robot.txt Check!!\n")
            # Skip whether what the site say and crawl anyway
            return True
    
    def crawl(self, url, depth=0):
        if depth > self.max_depth or url in self.visited or not self.is_allowed_to_crawl(url):
            return
        
        if self.url_count > self.max_url_count:
            # print(f"\n\n################ Reached max url_count = {self.url_count}",flush=True)
            return 
        
        # Mark the page as visited
        self.visited.add(url)
        print(f"Crawling {self.url_count}: {url}",flush=True)
        
        try:
            # Use Selenium to load the page
            self.driver.get(url)
            time.sleep(2)  # Wait for the page to load

            # Parse the rendered HTML
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            title = soup.title.string if soup.title else 'No Title'
            readable_text = self.extract_readable_text(soup)
            # print("Text : "+readable_text)

            # Store the title, URL, and readable text
            self.results.append({
                "title": title,
                "url": url,
                "content": readable_text
            })
             
            self.url_count +=1

            # Find all links and crawl them recursively
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                if self.is_valid_url(full_url):
                    self.crawl(full_url, depth + 1)

        except TimeoutException as e:
                print(f"An error occurred while waiting for the element: {str(e)}")
                self.driver.execute_script("window.stop();")  # Stop page loading
        except Exception as e:
            print(f"An error occurred. Error: {e}")

        
    def extract_readable_text(self, soup):
        # Extract text from paragraphs and headers
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3'])
        readable_text = "\n".join(element.get_text().strip() for element in text_elements if element.get_text().strip())
        return readable_text

    def is_valid_url(self, url):
        # Only crawl URLs within the same domain
        parsed_url = urlparse(url)
        return parsed_url.netloc == self.domain and url not in self.visited

    def close(self):
        # Close the Selenium browser
        self.driver.quit()

# ##########################################################################################################################
if __name__== "__main__":
    # Usage
    start_url = "https://www.wsj.com/news/latest-headlines"
    
    start_url = input("Enter URL: ")
    crawler = SeleniumCrawler(start_url, max_depth=1,max_url_count=3)
    crawler.crawl(start_url)
    crawler.close()

    if len(crawler.results) == 0:
        print ("NO Results")

    # Print results
    for result in crawler.results:
        print(f"Title: {result['title']}, URL: {result['url']}")
        print("Content:", result['content'])
        print("-" * 80)

