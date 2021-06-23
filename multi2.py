from airtest.core.api import *
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from loguru import logger
import json
import adbutils
from multiprocessing import Process

OUTPUT_FOLDER = 'movie'


class Controller(object):

    def __init__(self, device_uri, package_name, apk_path,  need_reinstall=False, need_restart=False):
        self.device_uri = device_uri
        self.package_name = package_name
        self.apk_path = apk_path
        self.need_reintall = need_reinstall
        self.need_restart = need_restart

    def connect_device(self):
        self.device = connect_device(self.device_uri)

    def install_app(self):
        if self.device.check_app(self.package_name) and not self.need_reintall:
            return
        self.device.uninstall_app(self.package_name)
        self.device.install_app(self.apk_path)

    def start_app(self):
        if self.need_restart:
            self.device.stop_app(self.package_name)
        self.device.start_app(self.package_name)

    def init_device(self):
        self.connect_device()
        self.poco = AndroidUiautomationPoco(self.device)
        self.window_width, self.window_height = self.poco.get_screen_size()
        self.install_app()
        self.start_app()

    def scroll_up(self):
        self.device.swipe((self.window_width * 0.5, self.window_height * 0.8),
                          (self.window_width * 0.5, self.window_height * 0.3), duration=1)

    def save_data(self, element_data):
        with open(f'{self.output_folder}/{element_data.get("title")}.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(element_data, ensure_ascii=False, indent=2))
            logger.debug(f'saved as file {element_data.get("title")}.json')

    def scrape_index(self):
        elements = self.poco(f'{self.package_name}:id/item')
        elements.wait_for_appearance()
        return elements

    def scrape_detail(self, element):
        element.click()
        panel = self.poco(f'{self.package_name}:id/content')
        panel.wait_for_appearance(5)
        title = self.poco(f'{self.package_name}:id/title').attr('text')
        categories = self.poco(
            f'{self.package_name}:id/categories_value').attr('text')
        score = self.poco(f'{self.package_name}:id/score_value').attr('text')
        published_at = self.poco(
            f'{self.package_name}:id/published_at_value').attr('text')
        drama = self.poco(f'{self.package_name}:id/drama_value').attr('text')
        self.device.keyevent('BACK')
        return {
            'title': title,
            'categories': categories,
            'score': score,
            'published_at': published_at,
            'drama': drama
        }

    def scroll_up(self):
        print('scroll up')
        self.device.swipe((self.window_width * 0.5, self.window_height * 0.8),
                          (self.window_width * 0.5, self.window_height * 0.3), duration=1)

    def run(self):
        while len(self.scraped_titles) < self.total_number:
            elements = self.scrape_index()
            for element in elements:
                element_title = element.offspring(
                    f'{self.package_name}:id/tv_title')
                if not element_title.exists():
                    continue
                title = element_title.attr('text')
                logger.debug(f'get title {title}')
                if title in self.scraped_titles:
                    continue
                _, element_y = element.get_position()
                if element_y > 0.7:
                    self.scroll_up()
                element_data = self.scrape_detail(element)
                logger.debug(f'scraped data {element_data}')
                self.save_data(element_data)
                self.scraped_titles.append(title)


PACKAGE_NAME = 'com.goldze.mvvmhabit'
APK_PATH = 'scrape-app5.apk'


def run(device_uri):
    controller = Controller(device_uri=device_uri,
                            package_name=PACKAGE_NAME,
                            apk_path=APK_PATH,
                            need_reinstall=False,
                            need_restart=True)
    controller.init_device()
    controller.run()


if __name__ == '__main__':
    processes = []
    adb = adbutils.AdbClient(host="127.0.0.1", port=5037)
    for device in adb.devices():
        device_name = device.serial
        device_uri = f'Android:///{device_name}'
        p = Process(target=run, args=[device_uri])
        processes.append(p)
        p.start()
    for p in processes:
        p.join()
