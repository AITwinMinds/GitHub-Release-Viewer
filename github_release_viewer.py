import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QLineEdit, QHeaderView
from PyQt5.QtGui import QColor, QPalette, QIcon
from urllib.parse import urlparse
import requests
import configparser
import base64
from icon_data import icon_data
import os

class GitHubReleaseViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.config_file = "config.ini"
        self.load_config()

        self.init_ui()

    def load_config(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

    def save_config(self):
        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)

    def init_ui(self):
        self.setWindowTitle('GitHub Release Viewer')

        self.base_resolution = (1920, 1080)
        self.screen_resolution = QApplication.desktop().screenGeometry()

        if self.screen_resolution.width() > self.screen_resolution.height():
            self.window_width_percentage = 38
            self.window_height_percentage = 60
            self.scaling_factor_width = self.screen_resolution.width() / self.base_resolution[0]
            self.scaling_factor_height = self.screen_resolution.height() / self.base_resolution[1]
        else:
            self.window_width_percentage = 60
            self.window_height_percentage = 38
            self.scaling_factor_width = self.screen_resolution.width() / self.base_resolution[1]
            self.scaling_factor_height = self.screen_resolution.height() / self.base_resolution[0]

        self.window_width = int(self.screen_resolution.width() * (self.window_width_percentage / 100))
        self.window_height = int(self.screen_resolution.height() * (self.window_height_percentage / 100))

        self.setGeometry(100, 100, self.window_width, self.window_height)

        self.setStyleSheet(
            f"""
            background-color: #1a1d21;
            color: #c8cacc;
            QLineEdit {{
                background-color: #2b2e32;
                color: #c8cacc;
                selection-background-color: #5a90a5;
            }}
            QTreeWidget {{
                background-color: #2b2e32;
                color: #c8cacc;
                selection-background-color: #5a90a5;
                alternate-background-color: #2b2e32;
            }}
            QTreeWidget::item:selected {{
                background-color: #5a90a5;
            }}
            """
        )     

        layout = QVBoxLayout()

        title_label = QLabel("GitHub Release Information")
        title_label.setStyleSheet(
            f"""
            font-family: 'Helvetica Neue'; 
            color: #FFFFFF; 
            font-size: 11.5pt; 
            border-radius: {int(4 * self.scaling_factor_width)}px; 
            background-color: #0e303d; 
            padding-bottom: {int(10 * self.scaling_factor_height)}px; 
            padding-left: {int(5 * self.scaling_factor_height)}px; 
            padding-top: {int(10 * self.scaling_factor_height)}px;
            """
        )    
            
        layout.addWidget(title_label)

        address_layout = QHBoxLayout()

        self.link_input = QLineEdit(self)
        self.link_input.setPlaceholderText("Enter GitHub Repository Link")
        self.link_input.setFixedHeight(int(34 * self.scaling_factor_height))
        self.link_input.setStyleSheet(
            f"""
            font-size: 10.5pt; 
            background-color: #1f2834;
            border: {int(1 * self.scaling_factor_width)}px solid #1f1f1f;
            padding: {int(5 * self.scaling_factor_width)}px;
            border-radius: {int(4 * self.scaling_factor_width)}px;
            """
            )
        
        address_layout.addWidget(self.link_input)

        self.refresh_button = QPushButton('Refresh', self)
        self.refresh_button.setStyleSheet(
            f"""
            QPushButton {{
                font-size: 10.5pt;
                background-color: #00464c;
                color: #c8cacc;
                border: {int(1 * self.scaling_factor_width)}px solid #1f1f1f;
                padding: {int(5 * self.scaling_factor_width)}px;
                border-radius: {int(4 * self.scaling_factor_width)}px;
            }}
            QPushButton:hover{{
                background-color: #003535;
                border-radius: {int(4 * self.scaling_factor_width)}px;
            }}
            """
        )

        self.refresh_button.setFixedWidth(int(125 * self.scaling_factor_width))
        self.refresh_button.setFixedHeight(int(34 * self.scaling_factor_height))
        self.refresh_button.clicked.connect(self.refresh_data)
        address_layout.addWidget(self.refresh_button)

        layout.addLayout(address_layout)

        self.tree_widget = QTreeWidget(self)
        self.tree_widget.setStyleSheet("font-size: 10pt;")
        self.tree_widget.setHeaderLabels(["Release", "Details"])
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree_widget.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        layout.addWidget(self.tree_widget)

        self.setLayout(layout)

        if self.config.has_section("GitHub"):
            link = self.config.get("GitHub", "Link", fallback="")
            self.link_input.setText(link)


    def refresh_data(self):
        self.refresh_button.setText("Refreshing...")
        QApplication.processEvents()
        github_link = self.link_input.text()

        parsed_url = urlparse(github_link)
        path_segments = parsed_url.path.strip('/').split('/')
        if len(path_segments) >= 2:
            owner, repo = path_segments[:2]
            self.config["GitHub"] = {"Link": github_link}
            self.save_config()
        else:
            self.tree_widget.clear()
            error_item = QTreeWidgetItem(self.tree_widget, ["Error", "Invalid GitHub link"])
            return

        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        response = requests.get(api_url, headers={"Accept": "application/vnd.github.manifold-preview+json"})

        self.tree_widget.clear()

        if response.status_code == 200:
            releases = response.json()

            for release in releases:
                release_item = QTreeWidgetItem(self.tree_widget, [release['name'], ""])
                release_item.setExpanded(True)

                details_item = QTreeWidgetItem(release_item, ["Tag Name", release['tag_name']])
                details_item = QTreeWidgetItem(release_item, ["Author", release['author']['login']])
                details_item = QTreeWidgetItem(release_item, ["Published At", release['published_at']])

                assets_item = QTreeWidgetItem(release_item, ["Assets", ""])
                for asset in release['assets']:
                    asset_item = QTreeWidgetItem(assets_item, [asset['name'], f"Download Count: {asset['download_count']}"])

                reactions_item = QTreeWidgetItem(release_item, ["Reactions", ""])
                reactions = release.get('reactions', {})
                for reaction, count in reactions.items():
                    if reaction.lower() == 'url':
                        continue
                    reaction_item = QTreeWidgetItem(reactions_item, [reaction, f"Count: {count}"])

        else:
            error_item = QTreeWidgetItem(self.tree_widget, ["Error", f"Failed to fetch data. Status Code: {response.status_code}"])
            
        self.refresh_button.setText("Refresh")
        QApplication.processEvents()

def main():
    app = QApplication(sys.argv)

    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(26, 29, 33))  # #1a1d21
    palette.setColor(QPalette.WindowText, QColor(200, 202, 204))  # #c8cacc
    palette.setColor(QPalette.Button, QColor(0, 58, 63))  # #003a3f
    palette.setColor(QPalette.ButtonText, QColor(200, 202, 204))  # #c8cacc
    palette.setColor(QPalette.Base, QColor(27, 30, 34))  # #1b1e22
    palette.setColor(QPalette.AlternateBase, QColor(27, 30, 34))  # #1b1e22
    palette.setColor(QPalette.ToolTipBase, QColor(42, 58, 66))  # #2a3a42
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))  # #000000
    palette.setColor(QPalette.Text, QColor(200, 202, 204))  # #c8cacc
    palette.setColor(QPalette.Highlight, QColor(90, 144, 165))  # #5a90a5
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))  # #000000
    app.setPalette(palette)

    icon_path = 'icon.ico'

    if not os.path.isfile(icon_path):
        decoded_icon_data = base64.b64decode(icon_data)
        with open(icon_path, 'wb') as f:
            f.write(decoded_icon_data)
    
    app.setWindowIcon(QIcon(icon_path))
    
    viewer = GitHubReleaseViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
