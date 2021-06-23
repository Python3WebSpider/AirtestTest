from re import T
from main import PACKAGE_NAME
from airtest.core.api import *
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
import adbutils
from multiprocessing import Process


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

    def run(self):
        for _ in range(10):
            self.scroll_up()


PACKAGE_NAME = 'com.goldze.mvvmhabit'
APK_PATH = 'app-debug.apk'


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
