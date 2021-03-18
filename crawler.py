from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By


class Crawler(webdriver.Firefox):
    """
        Modifying the existing webdriver with custom functions
    """

    options = Options()

    def __init__(self, headless=True, size=[1200, 800]):
        if headless:
            self.options.add_argument("--headless")
        if size:
            self.options.add_argument("--window-size={},{}".format(size[0], size[1]))
        super(Crawler, self).__init__(
            options=self.options
        )

    # Beautiful Soup to XPATH element
    def bsel(self, child):
        xpath = []
        for parent in child.parents:
            siblings = parent(child.name, recursive=False)
            i = '' if siblings == [child] else '[{}]'.format(siblings.index(child) + 1)
            xpath.append(child.name + i)
            child = parent
        xpath.reverse()
        target = self.find_element(By.XPATH, '/{}'.format('/'.join(xpath)) )
        return target

    def new_tab(self, url='about:blank'):
        script = '''window.open("{}", "_blank");'''.format(url)
        self.execute_script(script)

    def new_tabs(self, urls=['about:blank']):
        for u in urls:
            self.new_tab(u)

    def window_list(self):
        windows = {i: handle for i, handle in enumerate(self.window_handles)}
        return windows

    def wait_for(self, attr, name, timeout=10):
        wait = WebDriverWait(self, timeout)
        if attr == 'id':
            wait.until(EC.presence_of_element_located((By.ID, name)))
        elif attr == 'class':
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, name)))
        else:
            print('attribute {} not found.'.format(attr))

    def cleanup(self):
        self.stop_client()
        self.close()
        self.quit()


def main():
    driver = Crawler(size=[1200, 800])
    driver.get('http://www.aoe2.net')
    driver.save_screenshot('test.png')
    driver.cleanup()


if __name__ == '__main__':
    main()
