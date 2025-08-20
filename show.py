import sys
import requests
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QWidget,
    QMessageBox
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from picamera2 import Picamera2
from io import BytesIO
from PIL import Image


class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Raspberry Pi Camera + OCR + Translation")
        self.resize(800, 600)

        # Initialize camera (RGB)
        self.picam2 = Picamera2()
        camera_config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
        self.picam2.configure(camera_config)
        self.picam2.start()

        # UI
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Timer to update preview
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def mousePressEvent(self, event):
        """On mouse click -> capture and translate"""
        if event.button() == Qt.LeftButton:
            self.capture_and_translate()

    def update_frame(self):
        frame = self.picam2.capture_array()
        if frame is not None:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg).scaled(
                self.label.width(), self.label.height(), Qt.KeepAspectRatio
            )
            self.label.setPixmap(pixmap)

    def capture_and_translate(self):
        try:
            # 1. Capture and call OCR service
            frame = self.picam2.capture_array()
            pil_image = Image.fromarray(frame)
            img_buffer = BytesIO()
            pil_image.save(img_buffer, format="JPEG")
            img_buffer.seek(0)

            ocr_url = "http://localhost:8001/ocr"  # OCR service endpoint
            ocr_response = requests.post(
                ocr_url,
                files={"image": ("capture.jpg", img_buffer, "image/jpeg")}
            )

            if ocr_response.status_code != 200:
                raise Exception(f"OCR service error: {ocr_response.text}")

            ocr_text = ocr_response.json()["result"][0]  # take first line

            # 2. Call llama.cpp translation via OpenAI-compatible API
            translate_url = "http://localhost:8000/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer sk-dummy"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a translation assistant. Convert Chinese input to English."
                    },
                    {
                        "role": "user",
                        "content": f"Please translate the following: {ocr_text}"
                    }
                ]
            }

            translate_response = requests.post(
                translate_url,
                headers=headers,
                json=data
            )

            if translate_response.status_code != 200:
                raise Exception(f"Translation service error: {translate_response.text}")

            # 3. Parse translation
            translation = translate_response.json()["choices"][0]["message"]["content"]

            # 4. Show original and translated text
            result_text = f"【Original】{ocr_text}\n\n【Translation】{translation}"
            QMessageBox.information(self, "Translation Result", result_text)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Processing failed: {str(e)}")

    def closeEvent(self, event):
        self.timer.stop()
        self.picam2.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec())