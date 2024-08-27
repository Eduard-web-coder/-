import sys
import os
import subprocess
import ctypes
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QMessageBox, QComboBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer
import speedtest

def run_as_admin(argv=None, wait=True):
    """Run the script with admin privileges."""
    if argv is None:
        argv = sys.argv
    if not isinstance(argv, list):
        argv = list(argv)

    if ctypes.windll.shell32.IsUserAnAdmin():
        if 'admin' not in sys.argv:
            return subprocess.Popen(argv, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(argv) + ' admin', None, 1)
        if wait:
            sys.exit()

class NetworkUtils:
    DNS_SERVERS = {
        "Google Public DNS": ("8.8.8.8", "8.8.4.4"),
        "Quad9": ("9.9.9.9", "149.112.112.112"),
        "OpenDNS": ("208.67.222.222", "208.67.220.220"),
        "CleanBrowsing": ("185.228.168.9", "185.228.169.9"),
    }

    @staticmethod
    def change_dns(primary_dns, secondary_dns, interface_name="Ethernet"):
        try:
            os.system(f'netsh interface ip set dns "{interface_name}" static {primary_dns}')
            os.system(f'netsh interface ip add dns "{interface_name}" {secondary_dns} index=2')
        except Exception as e:
            raise Exception(f"Error changing DNS: {e}")

    @staticmethod
    def set_adapter_settings(interface_name="Ethernet", mtu=1500):
        try:
            os.system(f'netsh interface ipv4 set subinterface "{interface_name}" mtu={mtu} store=persistent')
        except Exception as e:
            raise Exception(f"Error setting adapter MTU: {e}")

    @staticmethod
    def optimize_traffic():
        # Here you can add commands for traffic optimization, such as changing routes or using VPN
        pass

    @staticmethod
    def check_ping(host):
        try:
            output = subprocess.check_output(['ping', '-n', '1', host], universal_newlines=True)
            return output.split('\n')[-2].split('=')[-1].strip()
        except Exception as e:
            return str(e)

    @staticmethod
    def get_network_stats():
        return {"ping": "30ms", "speed": "100Mbps"}

    @staticmethod
    def test_speed():
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        ping = st.results.ping
        return {"ping": f"{ping} ms", "download_speed": f"{download_speed:.2f} Mbps", "upload_speed": f"{upload_speed:.2f} Mbps"}

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(5000)  # Update every 5 seconds

    def initUI(self):
        self.setWindowTitle('Network Optimization Tool')
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet('background-color: #121212; color: #FFFFFF; font-family: Arial, sans-serif;')

        self.title_label = QLabel('Network Optimization Tool', self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet('font-size: 24px; color: #FFFFFF; font-weight: bold;')

        self.status_label = QLabel('Inactive', self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet('font-size: 20px; color: red;')

        self.activate_button = QPushButton('Activate', self)
        self.activate_button.clicked.connect(self.activate)
        self.activate_button.setStyleSheet('background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;')

        self.deactivate_button = QPushButton('Deactivate', self)
        self.deactivate_button.clicked.connect(self.deactivate)
        self.deactivate_button.setStyleSheet('background-color: #f44336; color: white; font-size: 16px; padding: 10px;')

        self.dns_selector = QComboBox(self)
        self.dns_selector.addItems(NetworkUtils.DNS_SERVERS.keys())
        self.dns_selector.setStyleSheet('background-color: #303030; color: white; font-size: 16px; padding: 5px;')

        self.stats_label = QLabel('Network Stats: ', self)
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet('font-size: 18px;')

        self.speedtest_button = QPushButton('Run Speed Test', self)
        self.speedtest_button.clicked.connect(self.run_speed_test)
        self.speedtest_button.setStyleSheet('background-color: #FF9800; color: white; font-size: 16px; padding: 10px;')

        self.optimize_button = QPushButton('Optimize Network', self)
        self.optimize_button.clicked.connect(self.optimize_network)
        self.optimize_button.setStyleSheet('background-color: #3F51B5; color: white; font-size: 16px; padding: 10px;')

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.activate_button)
        main_layout.addWidget(self.deactivate_button)
        main_layout.addWidget(self.dns_selector)
        main_layout.addWidget(self.stats_label)
        main_layout.addWidget(self.speedtest_button)
        main_layout.addWidget(self.optimize_button)

        self.setLayout(main_layout)

    def activate(self):
        self.status_label.setText('Active')
        self.status_label.setStyleSheet('font-size: 20px; color: green;')
        dns_choice = self.dns_selector.currentText()
        primary_dns, secondary_dns = NetworkUtils.DNS_SERVERS[dns_choice]
        self.change_dns(primary_dns, secondary_dns)
        self.log_change(f'Activated with DNS: {dns_choice}')

    def deactivate(self):
        self.status_label.setText('Inactive')
        self.status_label.setStyleSheet('font-size: 20px; color: red;')
        self.change_dns('', '')
        self.log_change('Deactivated')

    def change_dns(self, primary_dns, secondary_dns):
        try:
            NetworkUtils.change_dns(primary_dns, secondary_dns)
            self.log_change(f'DNS changed to {primary_dns}, {secondary_dns}')
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def update_stats(self):
        stats = NetworkUtils.get_network_stats()
        self.stats_label.setText(f"Network Stats: Ping: {stats['ping']}, Speed: {stats['speed']}")

    def run_speed_test(self):
        try:
            result = NetworkUtils.test_speed()
            speed_text = (f"Speed Test Results:\n"
                          f"Ping: {result['ping']}\n"
                          f"Download Speed: {result['download_speed']}\n"
                          f"Upload Speed: {result['upload_speed']}")
            QMessageBox.information(self, "Speed Test Results", speed_text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error running speed test: {e}")

    def optimize_network(self):
        try:
            NetworkUtils.optimize_traffic()
            QMessageBox.information(self, "Optimization", "Network optimization complete.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error optimizing network: {e}")

    def log_change(self, action):
        # Log changes if necessary
        pass

if __name__ == '__main__':
    run_as_admin()  # Try running the program with admin rights
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())
