import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QComboBox,QSplashScreen,QGridLayout,QTextEdit,QLineEdit,QMenu, QProgressBar,QHBoxLayout, QInputDialog, QColorDialog, QFontDialog, QScrollArea,QDoubleSpinBox, QMainWindow, QSlider,QAction, QFileDialog, QLabel, QDialogButtonBox, QVBoxLayout, QWidget, QMessageBox, QDialog, QFormLayout, QSpinBox, QPushButton
from PyQt5.QtGui import QPixmap, QImage, QPainter,QColor,QPen,QFont,QPolygon,QIntValidator
from PyQt5.QtCore import Qt,QTimer,QRect,QPoint,QSize
from mydesign2or import Ui_AuraEdit  # Replace with your generated UI class
from PIL import Image, ImageFilter
from PyQt5.QtGui import QTransform
import torch
from torchvision import transforms
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter
import math
from PIL import Image, ImageQt



class AuraEdit(QMainWindow):

     

    def __init__(self):
        super().__init__()

        # Set up the UI
        self.ui = Ui_AuraEdit()
        self.ui.setupUi(self)
        # Example filters and their default parameters
        self.current_filter = None
        
        # Initialize current file path (empty at the start)
        self.current_file = None
          # Initialize original_pixmap to None
        self.current_pixmap = None
        self.rotation_angle = 0
        self.translation_popup = None
        self.drawing = False  # Attribute to track if drawing is in progress
        self.eraser_active = False  # Attribute to track if eraser is active
        self.brush_active = False  # Attribute to track if brush is active
        self.brush_pixmap = None  # Store brush strokes
        self.brush_color = QColor("black")  # Default brush color
        self.last_point = None
        self.selected_shape = None
        self.shape_drawn = False
        self.original_pixmap = None  # Store original image for erasing

    



        self.stroke_history = []  # Track brush strokes
   

        self.text_tool_active = False
        self.text_color = QColor(Qt.black)  # Default text color is black
        self.text_font = QFont("Arial", 14)
        self.last_point = QPoint()  # Tr
      # Create and customize the status bar
        self.init_status_bar()
 

         # Initialize filter parameters as an empty dictionary
        self.filter_parameters = {}
        self.image_position = QPoint(0, 0)
        self.dragging = False 
        self.last_position = QPoint(0, 0)

       
        self.ui.tools_widget.setHidden(True)

        self.ui.frame_2.setHidden(True)
        # self.ui.size_dropdown.setHidden(True)
        self.ui.adjust_dropdown.setVisible(False)
        # self.ui.select_dropdown.setVisible(False)
        self.ui.retouch_dropdown.setVisible(False)
        self.ui.quickaction_dropdown.setVisible(False)
        self.ui.transform_dropdown.setVisible(False)
        self.ui.paint_dropdown.setVisible(False)
          # Set window properties
        self.setWindowTitle("AuraEdit")
        self.setMinimumSize(1480, 649)
        self.showMaximized()


               # Connect actions
        self.ui.actionOpen.triggered.connect(self.open_file)
        self.ui.actionNew.triggered.connect(self.new_file)
        self.ui.actionSave.triggered.connect(self.save_file)
     
        self.ui.actionSave_as.triggered.connect(self.save_as_file)
        self.ui.actionClose.triggered.connect(self.close_app)
        self.ui.actionCut.triggered.connect(self.cut_item)
        self.ui.actionCopy.triggered.connect(self.copy_item)
        self.ui.actionPaste.triggered.connect(self.paste_item)
        self.ui.actionAbout.triggered.connect(self.grayscale_filter)
        self.ui.actionGuassian_blur.triggered.connect(self.show_gaussian_blur_dialog)
        self.ui.actionNoise.triggered.connect(self.show_noise_dialog)
        self.ui.actionDistort.triggered.connect(self.show_distortion_dialog)
        self.ui.actionSharpen.triggered.connect(self.show_sharpen_dialog)
        self.ui.actionSketch.triggered.connect(self.sketch_filter)
        self.ui.actionMean_Filter.triggered.connect(self.show_mean_filter_dialog)
        self.ui.actionEdge_Detection.triggered.connect(self.show_edge_detection_dialog)
        self.ui.sobel_Filter.triggered.connect(self.show_sobel_dialog)
        self.ui.linear_Filter.triggered.connect(self.show_box_filter_dialog)
        self.ui.actionAbout_3.triggered.connect(self.show_about_dialog)
 
     
         # Connect the brightness button
        self.ui.brightness.clicked.connect(self.brightness_functionality)
        # Connect the saturation button
        self.ui.saturation.clicked.connect(self.saturation_functionality)
          # Connect the dropdown buttons
        self.ui.lighten.clicked.connect(self.lighten_action)
        self.ui.darken.clicked.connect(self.darken_action)
          # Connect dropdown buttons to their respective actions
        self.ui.remove_bg.clicked.connect(self.remove_background_action)
        self.ui.blur_bg.clicked.connect(self.blur_background_action)
        self.ui.blackwhite_bg.clicked.connect(self.blackwhite_background_action)
        self.ui.brush.clicked.connect(self.use_brush)
        self.ui.eraser.clicked.connect(self.use_eraser)
        self.ui.rotation.clicked.connect(self.apply_rotation)
        self.ui.translation.clicked.connect(self.show_translation_popup)
        self.ui.text2_PushButton.clicked.connect(self.text)
        # self.ui.shapes2_pushButton.clicked.connect(self.shapes)

              # Connect the zoom buttons to their respective functions
        self.ui.pushButton.clicked.connect(self.zoom_in)  # Zoom In
        self.ui.pushButton_2.clicked.connect(self.zoom_out)  # Zoom Out
        self.ui.pushButton_3.clicked.connect(self.reset_zoom)  # Reset Zoom
        # You might also need to store the original image (if you're using pixmap)
        self.original_pixmap = None
        self.original_image = None

    
        
    def init_status_bar(self):
        """Initialize and customize the status bar."""
        # Access the status bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("background-color: rgb(50, 50, 50); color: white;")

        # Add dynamic message label
        self.status_message = QLabel("Welcome to AuraEdit!")
        self.status_message.setStyleSheet("color: white; font-size: 14px;")
        self.status_bar.addWidget(self.status_message)

        # Add a progress bar (example usage, not currently active)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(
            "QProgressBar {background-color: rgb(70, 70, 70); color: white; border: none; height: 15px;}"
            "QProgressBar::chunk {background-color: rgb(100, 100, 250);}"
        )
        self.progress_bar.setVisible(False)  # Hide initially
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Add a tool indicator label
        self.tool_label = QLabel("Tool: None")
        self.tool_label.setStyleSheet("color: white; font-size: 14px;")
        self.status_bar.addPermanentWidget(self.tool_label)

    def update_tool_label(self, tool_name):
        """Update the tool label in the status bar."""
        self.tool_label.setText(f"Tool: {tool_name}")

    
    def brightness_functionality(self):
        """Handle brightness adjustment with a dialog and apply logic."""
        if self.current_pixmap is None:
            QMessageBox.warning(self, "No Image", "No image loaded to adjust brightness.")
            return

        # Ensure the original image is saved
        if not hasattr(self, "original_pixmap") or self.original_pixmap is None:
            self.original_pixmap = self.current_pixmap.copy()

        # Create a dialog to adjust brightness
        brightness_dialog = QDialog(self)
        brightness_dialog.setWindowTitle("Adjust Brightness")
        layout = QVBoxLayout(brightness_dialog)

        # Slider for brightness adjustment
        brightness_slider = QSlider(Qt.Horizontal, brightness_dialog)
        brightness_slider.setRange(-100, 100)  # Brightness adjustment range
        brightness_slider.setValue(0)  # Default value (no adjustment)
        brightness_slider.setTickPosition(QSlider.TicksBelow)
        brightness_slider.setTickInterval(10)
        layout.addWidget(brightness_slider)

        # Button Box (Apply / Cancel)
        button_box = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Cancel, brightness_dialog)
        layout.addWidget(button_box)

        # Real-time preview of brightness changes
        def preview_brightness(value):
            """Preview brightness adjustment in real-time."""
            temp_image = self.original_pixmap.toImage()

            # Adjust brightness for every pixel
            for x in range(temp_image.width()):
                for y in range(temp_image.height()):
                    color = temp_image.pixelColor(x, y)
                    color.setRed(max(0, min(255, color.red() + value)))
                    color.setGreen(max(0, min(255, color.green() + value)))
                    color.setBlue(max(0, min(255, color.blue() + value)))
                    temp_image.setPixelColor(x, y, color)

            # Convert the modified QImage back to QPixmap for preview
            preview_pixmap = QPixmap.fromImage(temp_image)
            self.ui.imageLabel.setPixmap(preview_pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        brightness_slider.valueChanged.connect(preview_brightness)

        # Finalize the brightness adjustment and close dialog
        def apply_brightness():
            """Apply brightness adjustment and close dialog."""
            value = brightness_slider.value()

            final_image = self.original_pixmap.toImage()

            for x in range(final_image.width()):
                for y in range(final_image.height()):
                    color = final_image.pixelColor(x, y)
                    color.setRed(max(0, min(255, color.red() + value)))
                    color.setGreen(max(0, min(255, color.green() + value)))
                    color.setBlue(max(0, min(255, color.blue() + value)))
                    final_image.setPixelColor(x, y, color)

            self.current_pixmap = QPixmap.fromImage(final_image)
            self.ui.imageLabel.setPixmap(self.current_pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

            brightness_dialog.accept()  # Close the dialog

        # Connect buttons
        button_box.button(QDialogButtonBox.Apply).clicked.connect(apply_brightness)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(brightness_dialog.reject)

        # Show the dialog
        brightness_dialog.exec_()


    def saturation_functionality(self):
        """Handle saturation adjustment with a dialog and apply logic."""
        if self.current_pixmap is None:
            QMessageBox.warning(self, "No Image", "No image loaded to adjust saturation.")
            return

        # Ensure the original image is saved
        if not hasattr(self, "original_pixmap") or self.original_pixmap is None:
            self.original_pixmap = self.current_pixmap.copy()

        # Create a dialog to adjust saturation
        saturation_dialog = QDialog(self)
        saturation_dialog.setWindowTitle("Adjust Saturation")
        layout = QVBoxLayout(saturation_dialog)

        # Slider for saturation adjustment
        saturation_slider = QSlider(Qt.Horizontal, saturation_dialog)
        saturation_slider.setRange(-100, 100)  # Saturation adjustment range (-100 to 100)
        saturation_slider.setValue(0)  # Default value (no adjustment)
        saturation_slider.setTickPosition(QSlider.TicksBelow)
        saturation_slider.setTickInterval(10)
        layout.addWidget(saturation_slider)

        # Button Box (Apply / Cancel)
        button_box = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Cancel, saturation_dialog)
        layout.addWidget(button_box)

        # Real-time preview of saturation changes
        def preview_saturation(value):
            """Preview saturation adjustment in real-time."""
            temp_image = self.original_pixmap.toImage()

            # Adjust saturation for every pixel
            for x in range(temp_image.width()):
                for y in range(temp_image.height()):
                    color = temp_image.pixelColor(x, y)

                    # Convert RGB to HSV
                    hsv_color = color.toHsv()  # Convert color to HSV

                    # Adjust saturation
                    hsv_color.setHsv(hsv_color.hue(), max(0, min(255, hsv_color.saturation() + value)), hsv_color.value())

                    # Convert back to RGB and apply the modified color
                    color.setRed(hsv_color.toRgb().red())
                    color.setGreen(hsv_color.toRgb().green())
                    color.setBlue(hsv_color.toRgb().blue())
                    temp_image.setPixelColor(x, y, color)

            # Convert the modified QImage back to QPixmap for preview
            preview_pixmap = QPixmap.fromImage(temp_image)
            self.ui.imageLabel.setPixmap(preview_pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        saturation_slider.valueChanged.connect(preview_saturation)

        # Finalize the saturation adjustment and close dialog
        def apply_saturation():
            """Apply saturation adjustment and close dialog."""
            value = saturation_slider.value()

            final_image = self.original_pixmap.toImage()

            for x in range(final_image.width()):
                for y in range(final_image.height()):
                    color = final_image.pixelColor(x, y)

                    # Convert RGB to HSV
                    hsv_color = color.toHsv()  # Convert color to HSV

                    # Adjust saturation
                    hsv_color.setHsv(hsv_color.hue(), max(0, min(255, hsv_color.saturation() + value)), hsv_color.value())

                    # Convert back to RGB and apply the modified color
                    color.setRed(hsv_color.toRgb().red())
                    color.setGreen(hsv_color.toRgb().green())
                    color.setBlue(hsv_color.toRgb().blue())
                    final_image.setPixelColor(x, y, color)

            self.current_pixmap = QPixmap.fromImage(final_image)
            self.ui.imageLabel.setPixmap(self.current_pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

            saturation_dialog.accept()  # Close the dialog

        # Connect buttons
        button_box.button(QDialogButtonBox.Apply).clicked.connect(apply_saturation)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(saturation_dialog.reject)

        # Show the dialog
        saturation_dialog.exec_()


    def lighten_action(self):
        if not hasattr(self, 'original_pixmap') or self.original_pixmap.isNull():
            print("No image loaded!")
            return

        print("Lighten action triggered")
        # Use the original pixmap to avoid cumulative effects
        original_image = self.original_pixmap.toImage()
        current_image = self.current_pixmap.toImage()

        for x in range(current_image.width()):
            for y in range(current_image.height()):
                color = current_image.pixelColor(x, y)

                # Increase brightness
                r = min(color.red() + 20, 255)
                g = min(color.green() + 20, 255)
                b = min(color.blue() + 20, 255)

                current_image.setPixelColor(x, y, QColor(r, g, b))

        # Update the pixmap and display the lightened image
        self.current_pixmap = QPixmap.fromImage(current_image)
        self.ui.imageLabel.setPixmap(self.current_pixmap)


    def darken_action(self):
        if not hasattr(self, 'original_pixmap') or self.original_pixmap.isNull():
            print("No image loaded!")
            return

        print("Darken action triggered")
        # Use the original pixmap to avoid cumulative effects
        original_image = self.original_pixmap.toImage()
        current_image = self.current_pixmap.toImage()

        for x in range(current_image.width()):
            for y in range(current_image.height()):
                color = current_image.pixelColor(x, y)

                # Decrease brightness
                r = max(color.red() - 20, 0)
                g = max(color.green() - 20, 0)
                b = max(color.blue() - 20, 0)

                current_image.setPixelColor(x, y, QColor(r, g, b))

        # Update the pixmap and display the darkened image
        self.current_pixmap = QPixmap.fromImage(current_image)
        self.ui.imageLabel.setPixmap(self.current_pixmap)


    def remove_background_action(self):
        """Remove the background from the image using color thresholding."""
        print("Remove background action triggered")

        if self.current_pixmap is None:
            QMessageBox.warning(self, "No Image", "No image loaded to remove background.")
            return

        # Convert QPixmap to QImage for manipulation
        image = self.current_pixmap.toImage()

        # Define the background color and threshold for detection
        background_color = QColor(255, 255, 255)  # White background color
        threshold = 100  # Sensitivity for detecting background pixels

        # Create a new image to store the result (with transparency)
        result_image = QImage(image.size(), QImage.Format_ARGB32_Premultiplied)

        # Process each pixel in the image
        for x in range(image.width()):
            for y in range(image.height()):
                color = image.pixelColor(x, y)

                # Calculate the color difference with the background color
                diff = abs(color.red() - background_color.red()) + abs(color.green() - background_color.green()) + abs(color.blue() - background_color.blue())

                # If the difference is less than the threshold, consider it as the background
                if diff < threshold:
                    # Set the background pixel to transparent
                    result_image.setPixelColor(x, y, QColor(0, 0, 0, 0))  # Transparent pixel
                else:
                    # Keep the original color for non-background pixels
                    result_image.setPixelColor(x, y, color)

        # Convert the result image back to QPixmap
        self.current_pixmap = QPixmap.fromImage(result_image)

        # Update the QLabel to display the image with the background removed
        self.ui.imageLabel.setPixmap(self.current_pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        print("Background removed successfully.")    

  
    def blur_background_action(self):
        """Apply a blur effect to the background of the image while keeping the foreground intact."""
        print("Blur background action triggered")

        if self.current_pixmap is None:
            QMessageBox.warning(self, "No Image", "No image loaded to blur background.")
            return

        # Convert QPixmap to QImage for manipulation
        image = self.current_pixmap.toImage()

        # Convert QImage to OpenCV format (numpy array)
        width = image.width()
        height = image.height()
        ptr = image.bits()
        ptr.setsize(image.byteCount())
        img_array = np.array(ptr).reshape(height, width, 4)  # 4 channels (RGBA)

        # Convert to RGB format (OpenCV uses BGR by default)
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)

        # Convert to grayscale (needed for background detection)
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

        # Apply a binary threshold or use edge detection to identify the background
        _, binary_mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

        # Invert the mask (background becomes white, foreground becomes black)
        background_mask = cv2.bitwise_not(binary_mask)

        # Create a blurred version of the entire image
        blurred_img = cv2.GaussianBlur(img_rgb, (21, 21), 0)

        # Mask the blurred image (keep the background blurred)
        blurred_background = cv2.bitwise_and(blurred_img, blurred_img, mask=background_mask)

        # Mask the original image to keep the foreground intact
        foreground = cv2.bitwise_and(img_rgb, img_rgb, mask=binary_mask)

        # Combine the foreground and blurred background
        final_img = cv2.add(foreground, blurred_background)

        # Convert the resulting image back to QImage
        final_img = cv2.cvtColor(final_img, cv2.COLOR_RGB2RGBA)
        result_image = QImage(final_img.data, final_img.shape[1], final_img.shape[0], QImage.Format_RGBA8888)

        # Convert the QImage back to QPixmap
        self.current_pixmap = QPixmap.fromImage(result_image)

        # Update the QLabel to display the image with the blurred background
        self.ui.imageLabel.setPixmap(self.current_pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        

    def blackwhite_background_action(self):
        """Convert the background to black & white while keeping the foreground intact."""
        print("Black & White background action triggered")

        if self.current_pixmap is None:
            QMessageBox.warning(self, "No Image", "No image loaded to apply black & white background.")
            return

        # Convert QPixmap to QImage for manipulation
        image = self.current_pixmap.toImage()

        # Convert QImage to OpenCV format (numpy array)
        width = image.width()
        height = image.height()
        ptr = image.bits()
        ptr.setsize(image.byteCount())
        img_array = np.array(ptr).reshape(height, width, 4)  # 4 channels (RGBA)

        # Convert to RGB format (OpenCV uses BGR by default)
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)

        # Convert to grayscale (needed for background detection)
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

        # Apply a binary threshold or use edge detection to identify the background
        _, binary_mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

        # Invert the mask (background becomes white, foreground becomes black)
        background_mask = cv2.bitwise_not(binary_mask)

        # Convert the background to black & white by applying grayscale
        black_white_background = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

        # Convert the grayscale background back to a 3-channel image (to match original shape)
        black_white_background = cv2.cvtColor(black_white_background, cv2.COLOR_GRAY2RGB)

        # Mask the grayscale image to only affect the background
        background_with_bw = cv2.bitwise_and(black_white_background, black_white_background, mask=background_mask)

        # Mask the original image to keep the foreground intact
        foreground = cv2.bitwise_and(img_rgb, img_rgb, mask=binary_mask)

        # Combine the foreground and black & white background
        final_img = cv2.add(foreground, background_with_bw)

        # Convert the resulting image back to QImage
        final_img = cv2.cvtColor(final_img, cv2.COLOR_RGB2RGBA)
        result_image = QImage(final_img.data, final_img.shape[1], final_img.shape[0], QImage.Format_RGBA8888)

        # Convert the QImage back to QPixmap
        self.current_pixmap = QPixmap.fromImage(result_image)

        # Update the QLabel to display the image with the black & white background
        self.ui.imageLabel.setPixmap(self.current_pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

      
  
    def use_brush(self):
        """Enable brush functionality for drawing on the image."""
        if self.current_pixmap is None:
            QMessageBox.warning(self, "No Image", "Please load an image before using the brush tool.")
            return

        # Let the user select a brush color
        color = QColorDialog.getColor()
        if not color.isValid():
            return  # User canceled the color selection

        self.brush_active = True
        self.brush_color = color
        self.brush_size = 5  # You can adjust this value to change brush size

        # Save the original image for erasing later
        self.original_pixmap = self.current_pixmap.copy()

        print(f"Brush activated with color {color.name()} and size {self.brush_size}.")
        self.update_tool_label("Brush")

        # Connect mouse events for drawing
        self.ui.imageLabel.mousePressEvent = self.start_drawing
        self.ui.imageLabel.mouseMoveEvent = self.draw
        self.ui.imageLabel.mouseReleaseEvent = self.stop_drawing

    def start_drawing(self, event):
        """Start drawing when mouse is pressed."""
        if self.brush_active:
            self.drawing = True
            self.last_point = event.pos()

    def draw(self, event):
        """Draw on the image using the brush tool."""
        if not self.drawing or self.last_point is None:
            return

        painter = QPainter(self.current_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.brush_color, self.brush_size, Qt.SolidLine))
        painter.setBrush(self.brush_color)

        # Draw a line from the last point to the current position
        painter.drawLine(self.last_point, event.pos())

        # Save the new pixmap to the stroke history
        self.stroke_history.append(self.current_pixmap.copy())

        # Update the image with the new drawing
        self.ui.imageLabel.setPixmap(self.current_pixmap)
        self.last_point = event.pos()
        painter.end()

    def stop_drawing(self, event):
        """Stop drawing when mouse is released."""
        self.drawing = False
        self.last_point = None
        self.ui.imageLabel.mousePressEvent = None
        self.ui.imageLabel.mouseMoveEvent = None
        self.ui.imageLabel.mouseReleaseEvent = None

    def use_eraser(self):
        """Enable eraser functionality to remove brush strokes."""
        if not self.stroke_history:
            QMessageBox.warning(self, "No Strokes", "There are no brush strokes to erase.")
            return

        # Remove the last brush stroke from the history
        self.stroke_history.pop()

        # If there are strokes left, restore the last one
        if self.stroke_history:
            self.current_pixmap = self.stroke_history[-1].copy()
        else:
            self.current_pixmap = self.original_pixmap.copy()  # If no strokes left, reset to original image

        self.ui.imageLabel.setPixmap(self.current_pixmap)

       
        self.update_tool_label("Eraser")

        def update_tool_label(self, tool_name):
            """Update the status or tool label."""
            print(f"{tool_name} tool is active.")

  

    def text(self):
        """Add a draggable and editable textbox over the image."""
        if self.current_pixmap is None:
            QMessageBox.warning(self, "No Image", "Please load an image before adding text.")
            return
        
        self.text_font = QFont("Arial", 12)  # Default font
        self.text_color = QColor("black")  # Default color
        self.text_tool_active = False
        self.offset = None
        self.dragging = False
        self.text_color = Qt.white 
        

        # Open QFontDialog for font selection
        font, ok = QFontDialog.getFont(self.text_font, self, "Select Font")
        if not ok:
            return  # User canceled the font selection
        self.text_font = font  # Update the font
       
   

        # Open QColorDialog for text color selection
        color = QColorDialog.getColor(self.text_color, self, "Select Text Color")
        if not color.isValid():
            return  # User canceled the color selection
        self.text_color = color  # Update the color

        # Create the QTextEdit for multi-line text entry
        self.text_box = QTextEdit(self)
        self.text_box.setPlaceholderText("Enter text here")
        self.text_box.setFont(self.text_font)
        self.text_box.setStyleSheet(f"color: {self.text_color.name()}; background: transparent; border: none;")
        self.text_box.setParent(self.ui.imageLabel)
        # Set position and size of the text box over the image (adjusted to 50x50)
        self.text_box.setGeometry(50, 50, 200, 100)  # Position and size of the text box
        self.text_box.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable vertical scroll bar for clean look
        self.text_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scroll bar

        # Make sure the widget is shown
        self.text_box.show()

     
        # Connect text change event for dynamic resizing
        self.text_box.textChanged.connect(self.adjust_textbox_size)

          # Handle saving the text when the user finishes editing
        self.text_box.focusOutEvent = lambda event: self.save_text_to_image(self.text_box, self.text_box.pos())
    

        # Make the textbox draggable
        self.text_box.mousePressEvent = self.start_drag
        self.text_box.mouseMoveEvent = self.drag_textbox
        self.text_box.mouseReleaseEvent = self.stop_drag

        # Set the context menu for the text box (default actions like cut, copy, paste)
        self.text_box.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_box.customContextMenuRequested.connect(self.show_context_menu)

        self.dragging = False
        self.offset = None
        self.status_message.setText("Text tool activated. Drag and edit the textbox.")
    

    def adjust_textbox_size(self):
        """Adjust the size of the textbox dynamically based on its content."""
        font_metrics = self.text_box.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self.text_box.text() or self.text_box.placeholderText())
        self.text_box.setFixedWidth(text_width + 20)  # Add padding for cursor and spacing

    def start_drag(self, event):
        """Start dragging the textbox."""
        self.dragging = True
        self.offset = event.pos()

    def drag_textbox(self, event):
        """Drag the textbox."""
        if self.dragging:
            new_pos = self.text_box.pos() + (event.pos() - self.offset)
            self.text_box.move(new_pos)

    def stop_drag(self, event):
        """Stop dragging the textbox."""
        self.dragging = False
        self.offset = None


    def show_context_menu(self, pos):
        """Show the custom context menu."""
        context_menu = self.text_box.createStandardContextMenu()

        # Add custom actions to the context menu
        font_action = QAction("Change Font", self)
        font_action.triggered.connect(self.change_font)
        context_menu.addAction(font_action)

        color_action = QAction("Change Color", self)
        color_action.triggered.connect(self.change_color)
        context_menu.addAction(color_action)

        delete_action = QAction("Delete Text", self)
        delete_action.triggered.connect(self.delete_text)
        context_menu.addAction(delete_action)

        # Show the context menu
        context_menu.exec_(self.text_box.mapToGlobal(pos))

    def change_font(self):
        """Open font dialog to change font."""
        font, ok = QFontDialog.getFont(self.text_font, self, "Select Font")
        if ok:
            self.text_font = font
            self.text_box.setFont(self.text_font)

    def change_color(self):
        """Open color dialog to change text color."""
        color = QColorDialog.getColor(self.text_color, self, "Select Text Color")
        if color.isValid():
            self.text_color = color
            self.text_box.setStyleSheet(f"color: {self.text_color.name()}; background: transparent; border: none;")

    def delete_text(self):
        """Delete the QTextEdit (the text box) itself."""
        self.text_box.deleteLater()
        self.text_box = None  # Reset the text_box reference to avoid using it after deletion

    def adjust_textbox_size(self):
        """Adjust the size of the textbox dynamically based on its content."""
        font_metrics = self.text_box.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self.text_box.toPlainText() or self.text_box.placeholderText())
        self.text_box.setFixedWidth(text_width + 20)  # Add padding for cursor and spacing

    def start_drag(self, event):
        """Start dragging the textbox."""
        self.dragging = True
        self.offset = event.pos()

    def drag_textbox(self, event):
        """Drag the textbox."""
        if self.dragging:
            new_pos = self.text_box.pos() + (event.pos() - self.offset)
            self.text_box.move(new_pos)

    def stop_drag(self, event):
        """Stop dragging the textbox."""
        self.dragging = False
        self.offset = None

    def save_text_to_image(self, textbox, position):
        """Render the entered text onto the image."""
        if self.current_pixmap is None:
            return

        # Get the text from the textbox
        entered_text = textbox.toPlainText()
        if not entered_text.strip():  # If text is empty, discard
            textbox.deleteLater()
            return

        # Use QPainter to draw the text onto the image
        painter = QPainter(self.current_pixmap)
        painter.setPen(QPen(self.text_color, 1, Qt.SolidLine))
        painter.setFont(self.text_font)
        painter.drawText(position.x(), position.y() + self.text_font.pointSize(), entered_text)  # Adjust text position slightly
        painter.end()

        # Update the QLabel to reflect the changes
        self.ui.imageLabel.setPixmap(self.current_pixmap)

        # Remove the textbox after saving
        textbox.deleteLater()
        self.text_tool_active = False
        self.status_message.setText("Text added to the image.")






    def apply_rotation(self):
        """Rotates the image by a fixed angle."""
        if self.current_pixmap is None:
            QMessageBox.warning(self, "No Image", "Please load an image before using the rotation tool.")
            return

        try:
            # Increment rotation angle by 90 degrees (adjust as needed)
            self.rotation_angle = (self.rotation_angle + 90) % 360

            # Rotate the current image
            transform = QTransform()
            transform.rotate(self.rotation_angle)
            rotated_pixmap = self.current_pixmap.transformed(transform, Qt.SmoothTransformation)

            # Update the QLabel with the rotated image
            self.ui.imageLabel.setPixmap(rotated_pixmap)

            # Save the rotated image as the current state
            self.current_pixmap = rotated_pixmap
            print(f"Image rotated to {self.rotation_angle} degrees.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to rotate the image: {e}")

    def show_translation_popup(self):
        """Show the translation pop-up with direction buttons."""
      
        if not hasattr(self, 'translation_popup') or self.translation_popup is None:
            print("Creating a new translation popup.")
            self.translation_popup = QDialog(self)
            self.translation_popup.setWindowFlags(Qt.FramelessWindowHint)

            self.translation_popup.setWindowTitle("Translation Tool")
            self.translation_popup.setGeometry(170, 480, 180, 250)  # Adjust position and size

            layout = QVBoxLayout()

            # Create direction buttons with styles
            button_up = QPushButton("↑")
            button_up.setStyleSheet("background-color: rgb(70,70,70); color: white; font-size: 16px; padding: 10px; border-radius: 5px;")
            button_up.clicked.connect(lambda: self.apply_translation(0, -10))
            layout.addWidget(button_up)

            button_left = QPushButton("←")
            button_left.setStyleSheet("background-color: rgb(70,70,70); color: white; font-size: 16px; padding: 10px;border-radius: 5px;")
            button_left.clicked.connect(lambda: self.apply_translation(-10, 0))
            layout.addWidget(button_left)

            button_right = QPushButton("→")
            button_right.setStyleSheet("background-color: rgb(70,70,70); color: white; font-size: 16px; padding: 10px;border-radius: 5px;")
            button_right.clicked.connect(lambda: self.apply_translation(10, 0))
            layout.addWidget(button_right)

            button_down = QPushButton("↓")
            button_down.setStyleSheet("background-color: rgb(70,70,70); color: white; font-size: 16px; padding: 10px;border-radius: 5px;")
            button_down.clicked.connect(lambda: self.apply_translation(0, 10))
            layout.addWidget(button_down)

            # Add a close button with styles
            close_button = QPushButton("Close")
            close_button.setStyleSheet("background-color: rgb(105,105,105); color: white; font-size: 16px; padding: 10px;border-radius: 5px;")
            close_button.clicked.connect(self.translation_popup.close)
            layout.addWidget(close_button)

            self.translation_popup.setLayout(layout)

        print("Showing translation popup.")
        self.translation_popup.show()

    def apply_translation(self, dx=0, dy=0):
        """Translate (move) the image displayed in the QLabel."""
        if self.current_pixmap is None:
            QMessageBox.warning(self, "No Image", "Please load an image before using the translation tool.")
            return

        try:
            # Create a blank pixmap to hold the translated image
            translated_pixmap = QPixmap(self.current_pixmap.size())
            translated_pixmap.fill(Qt.transparent)  # Set background transparent

            # Use QPainter to draw the translated image
            painter = QPainter(translated_pixmap)
            painter.drawPixmap(dx, dy, self.current_pixmap)  # Apply the translation
            painter.end()

            # Update the QLabel with the translated pixmap
            self.ui.imageLabel.setPixmap(translated_pixmap)

            # Save the translated pixmap as the current state
            self.current_pixmap = translated_pixmap
            print(f"Image translated by dx={dx}, dy={dy}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to translate the image: {e}")

    def zoom_in(self):
        """Increase the zoom (scale up the image)."""
        if self.current_pixmap:
            scale_factor = 1.1  # Zoom-in by 10%
            self.apply_zoom(scale_factor)
        self.status_message.setText(f"Zoom applied on {self.current_pixmap}")
        self.update_tool_label("Zoom in")

    def zoom_out(self):
        """Decrease the zoom (scale down the image)."""
        if self.current_pixmap:
            scale_factor = 0.9  # Zoom-out by 10%
            self.apply_zoom(scale_factor)
        self.status_message.setText(f"Zoom applied on {self.current_pixmap}")
        self.update_tool_label("Zoom out")    

    def reset_zoom(self):
        """Reset the zoom to original size."""
        if self.original_pixmap:
            self.current_pixmap = self.original_pixmap  # Reset the image to original
            self.ui.imageLabel.setPixmap(self.original_pixmap)  # Set the original image
        else:
            print("Original image not available.")
        self.status_message.setText(f"Reset applied on {self.current_pixmap}")
        self.update_tool_label("Reset file")    

    def apply_zoom(self, scale_factor):
        """Apply zoom based on scale factor."""
        if self.current_pixmap:
            # Apply the zoom to current_pixmap
            new_width = int(self.current_pixmap.width() * scale_factor)
            new_height = int(self.current_pixmap.height() * scale_factor)
            
            # Scale the image
            scaled_pixmap = self.current_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Update the current_pixmap to the scaled image
            self.current_pixmap = scaled_pixmap
            self.ui.imageLabel.setPixmap(scaled_pixmap)
            print(f"Zoom applied with scale factor: {scale_factor}")
   

    def add_filter_to_tree(self, filter_name, parameters):
        """Dynamically add or update a filter and its parameters in the tree widget."""
        # Clear existing tree items (optional if you want to refresh)
        self.ui.tree_widget.clear()

        # Check if the filter already exists in the tree widget
        existing_items = self.ui.tree_widget.findItems(filter_name, QtCore.Qt.MatchExactly, 0)

        if existing_items:
            # If the filter already exists, update its parameters
            filter_item = existing_items[0]
            for param, value in parameters.items():
                # Iterate through the child items and update if the parameter exists
                found = False
                for i in range(filter_item.childCount()):
                    child_item = filter_item.child(i)
                    if child_item.text(0) == param:
                        # If it's a QSpinBox or QDoubleSpinBox, update the value
                        widget = self.ui.tree_widget.itemWidget(child_item, 1)
                        if isinstance(widget, QSpinBox):
                            widget.setValue(value)
                        elif isinstance(widget, QDoubleSpinBox):
                            widget.setValue(value)
                        found = True
                        break

                if not found:
                    # If the parameter doesn't exist, add it as a new child item
                    child_item = QtWidgets.QTreeWidgetItem(filter_item, [param, str(value)])
                    self.ui.tree_widget.setItemWidget(child_item, 1, self.create_editable_field(param, value))  # Make it editable
        else:
            # If the filter doesn't exist, create a new filter item
            self.current_filter = filter_name
            filter_item = QtWidgets.QTreeWidgetItem(self.ui.tree_widget, [filter_name])
            filter_item.setExpanded(True)
            self.filter_parameters = parameters

            # Add each parameter as a child item
            for param, value in parameters.items():
                param_item = QtWidgets.QTreeWidgetItem(filter_item, [param, str(value)])
                self.ui.tree_widget.setItemWidget(param_item, 1, self.create_editable_field(param, value))  # Make it editable

    def create_editable_field(self, param, value):
        """Create an editable field for a parameter value."""
        if isinstance(value, str):  # If it's a string, use QComboBox (for categorical values)
            return self.create_combo_box(param, value)
        elif isinstance(value, int):  # If it's an integer, use QSpinBox (for numeric values)
            return self.create_spin_box(param, value)
        elif isinstance(value, float):  # If it's a float, use QSlider (for range-based values)
            return self.create_slider(param, value)
        return QtWidgets.QLineEdit(str(value))  # Default to LineEdit for others
        
    def create_combo_box(self, param, value):
        """Create a QComboBox for categorical parameters."""
        combo_box = QtWidgets.QComboBox()
        
        # Populate options based on the parameter
        if param == "Noise Type":
            options = ["Gaussian", "Salt & Pepper", "Speckle"]
        else:
            options = value if isinstance(value, list) else [value]

        combo_box.addItems(options)
        combo_box.setStyleSheet("background-color: white; color: black; padding: 3px;")
        combo_box.setCurrentText(value)
        combo_box.currentTextChanged.connect(lambda: self.update_parameter_from_tree(param, combo_box))
        return combo_box

    def create_spin_box(self, param, value):
        """Create a QSpinBox for integer parameters."""
        spin_box = QtWidgets.QSpinBox()
        spin_box.setRange(1, 100)  # Default range (you can adjust this)
        spin_box.setValue(value)
        spin_box.setSingleStep(2) 
        spin_box.setStyleSheet("background-color: white; color: black; padding: 3px;")
        spin_box.valueChanged.connect(lambda: self.update_parameter_from_tree(param, spin_box))
        return spin_box

    def create_slider(self, param, value):
        """Create a QSlider for float range-based parameters."""
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 100)  # Set the slider range (0-100 as an example)
        slider.setValue(int(value * 10))  # Multiply float value by 10 to fit the slider range
        slider.setStyleSheet("background-color: white; color: black; padding: 3px;")
        slider.valueChanged.connect(lambda: self.update_parameter_from_tree(param, slider))
        return slider

    def update_parameter_from_tree(self, param, widget):
        """Handle parameter updates when the user edits a value in the tree widget."""
        if isinstance(widget, QtWidgets.QComboBox):
            value = widget.currentText()  # Get selected value from ComboBox
        elif isinstance(widget, QtWidgets.QSpinBox):
            value = widget.value()  # Get value from SpinBox
        elif isinstance(widget, QtWidgets.QSlider):
            value = widget.value() / 10  # Adjust the slider value back to float
        else:
            value = widget.text()  # Default for other widgets (like LineEdit)

        try:
            # Update the shared dictionary with the new value
            self.filter_parameters[param] = value
            print(f"Updated {param}: {value}")

            # Reapply the filter dynamically based on the current active filter
            if self.current_filter == "Gaussian Blur":
                kernel_size = self.filter_parameters.get("Kernel Size", 5)
                sigma = self.filter_parameters.get("Sigma", 1.5)
                self.gaussian_blur(kernel_size, sigma)
            elif self.current_filter == "Add Noise":
                noise_type = self.filter_parameters.get("Noise Type", "Gaussian")
                intensity = self.filter_parameters.get("Intensity", 10)
                self.add_noise(noise_type, intensity)
            elif self.current_filter == "Sharpen":
                sharpen_strength = self.filter_parameters.get("Sharpen Strength", 1)
                self.sharpen(sharpen_strength)  # Use your existing sharpen method
            elif self.current_filter == "Distortion":
                amplitude = self.filter_parameters.get("Amplitude", 15)
                frequency = self.filter_parameters.get("Frequency", 0.05)
                self.apply_distortion(amplitude, frequency)
            elif self.current_filter == "Mean Filter":
                kernel_size = self.filter_parameters.get("Kernel Size", 3)  # Default kernel size for mean filter
                self.apply_mean_filter(kernel_size)
            elif self.current_filter == "Edge Detection":
                low_threshold = self.filter_parameters.get("Low Threshold", 50)  # Default low threshold
                high_threshold = self.filter_parameters.get("High Threshold", 150)  # Default high threshold
                self.apply_edge_detection(low_threshold, high_threshold)
            elif self.current_filter == "Sobel Filter":
                kernel_size = self.filter_parameters.get("Kernel Size", 3)  # Default kernel size for Sobel filter
                self.apply_sobel_filter(kernel_size)
            elif self.current_filter == "Box Filter":
                kernel_size = self.filter_parameters.get("Kernel Size", 3)  # Default kernel size for Box filter
                self.apply_box_filter(kernel_size)
                self.add_filter_to_tree("Box Filter", {"Kernel Size": kernel_size})
           
            # Add more filter conditions as needed for other filters

        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
            # Reset to last valid value if the input is invalid
            widget.setValue(self.filter_parameters[param]) if isinstance(widget, QtWidgets.QSpinBox) else widget.setText(str(self.filter_parameters[param]))

    def switch_filter(self, filter_name, parameters):
        """Switch to a new filter and update parameters in the tree widget."""
        self.current_filter = filter_name
        if parameters:
            self.add_filter_to_tree(filter_name, parameters)
        else:
            QtWidgets.QMessageBox.warning(self, "Error", f"No parameters provided for '{filter_name}'.")


    def update_properties(self, pixmap, file_name):
        """Update the property widgets with the image details."""
        # Get image width and height
        width = pixmap.width()
        height = pixmap.height()

        # Extract the file format from the file extension
        format_ = file_name.split('.')[-1].lower()

        # Update spin boxes for width and height
        self.ui.spinBox_2.setValue(width)  # SpinBox for width
        self.ui.spinBox_7.setValue(height)  # SpinBox for height

        # Update combo box for image format
        index = self.ui.comboBox_8.findText(format_, Qt.MatchFixedString)
        if index >= 0:
            self.ui.comboBox_8.setCurrentIndex(index)

        # Update the QLineEdit for the file name
        self.ui.lineEdit.setText(file_name)  # Assuming lineEdit is the QLineEdit for file name

        # Disable the widgets to prevent editing
        self.ui.spinBox_2.setEnabled(False)
        self.ui.spinBox_7.setEnabled(False)
        self.ui.comboBox_8.setEnabled(False)
        self.ui.lineEdit.setEnabled(False)  # Disable the QLineEdit to p
   
    def open_file(self):
            # Open file dialog and allow the user to select an image or file
            file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)")

            if file_name:
                try:
                    # Load the image using QPixmap
                    pixmap = QPixmap(file_name)
                    if pixmap.isNull():
                        raise Exception("Failed to load image.")

                    # Save the original image pixmap to reset zoom later
                    self.original_pixmap = pixmap
                    self.current_pixmap = pixmap
                    self.current_file = file_name

                    # Set QLabel alignment to center
                    self.ui.imageLabel.setAlignment(Qt.AlignCenter)

                    # Set the pixmap to the QLabel from the UI
                    self.ui.imageLabel.setPixmap(pixmap)

                    # Scale the pixmap to fit within the QLabel (optional)
                    self.ui.imageLabel.setPixmap(pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                     # Update the property widgets
                    self.update_properties(pixmap, file_name)
                    print(f"File Opened: {file_name}")

                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to open the file: {e}")
            else:
                print("No file selected")
            self.status_message.setText(f"Image loaded: {file_name}")
            self.update_tool_label("None")

    def new_file(self):
        # Clear the current image and allow opening a new file
        self.ui.imageLabel.clear()  # Clear the QLabel for new image
        self.open_file()
        self.status_message.setText(f"new image loaded")
        self.update_tool_label("New image")
    
    def save_file(self):
        """Save the current file after letting the user adjust its name and location."""
        if not self.current_pixmap:
            QMessageBox.warning(self, "No Image", "There is no image to save.")
            return

        # Open file dialog for the user to choose the save location and filename
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "",
            "Image Files (*.png *.jpg *.bmp);;All Files (*)",
            options=options
        )

        # If the user cancels, file_path will be empty
        if not file_path:
            return

        try:
            # Save the pixmap to the selected file path
            if self.current_pixmap.save(file_path):
                self.status_message.setText(f"File saved: {file_path}")
                self.update_tool_label("Save file")
          
            else:
                QMessageBox.warning(self, "Error", "Failed to save the file.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error saving file: {e}")
        self.status_message.setText(f"File saved: {self.current_file}")
        self.update_tool_label("Save file")
           
    def save_as_file(self):
        # Open a file dialog for the user to select a location and file name
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "Images (*.png *.xpm *.jpg);;All Files (*)")

        if file_name:
            try:
                # Get the pixmap from the QLabel (currently displayed image)
                pixmap = self.ui.imageLabel.pixmap()

                # Save the image to the new file path
                if pixmap.save(file_name):
                    self.current_file = file_name  # Update the current file path
                    print(f"File saved as {file_name}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to save the file.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error saving file: {e}")
            self.status_message.setText(f"File saved as {self.current_file}")
            self.update_tool_label("Save image") 

    def close_app(self):
        # Optionally, ask the user to save before closing
        reply = QMessageBox.question(self, 'Close Application', 
                                     "Do you want to save your changes?", 
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                                     QMessageBox.Yes)

      
        if reply == QMessageBox.Yes:
            self.save_file()  # Save the file if the user chooses "Yes"
        elif reply == QMessageBox.No:
            self.close()  # Close without saving
        else:
            pass  # Do nothing if Cancel is clicked
        self.status_message.setText(f"Closing AuraEdit")
        self.update_tool_label("App Close")

    def cut_item(self):
        if not self.ui.imageLabel.pixmap():
            QMessageBox.warning(self, "Cut", "No image to cut!")
            return

        pixmap = self.ui.imageLabel.pixmap()
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(pixmap)
        self.ui.imageLabel.clear()
        print("Image cut and saved to clipboard.")
        self.status_message.setText(f"File cut")
        self.update_tool_label("Cut file")

    def copy_item(self):
        if not self.ui.imageLabel.pixmap():
            QMessageBox.warning(self, "Copy", "No image to copy!")
            return

        pixmap = self.ui.imageLabel.pixmap()
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(pixmap)
        self.status_message.setText(f"File Copied to clipboard{self.current_file}")
        self.update_tool_label("Copy file")

    def paste_item(self):
        clipboard = QApplication.clipboard()
        pixmap = clipboard.pixmap()

        if pixmap.isNull():
            QMessageBox.warning(self, "Paste", "Clipboard is empty or does not contain an image!")
            return

        self.ui.imageLabel.setPixmap(pixmap)
        self.status_message.setText(f"File pasted {pixmap}")
        self.update_tool_label("Paste file")

    def grayscale_filter(self):
        if not hasattr(self, 'current_file') or not self.current_file:
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return

        try:
            print(f"Applying grayscale filter to: {self.current_file}")

            # Load the image using PIL
            image = Image.open(self.current_file)

            # Convert the image to grayscale
            grayscale_image = image.convert("L")

            # Convert the grayscale image to a NumPy array
            grayscale_np = np.array(grayscale_image)

            # Convert the NumPy array back to a QImage
            height, width = grayscale_np.shape
            bytes_per_line = width
            grayscale_qimage = QImage(grayscale_np.data, width, height, bytes_per_line, QImage.Format_Grayscale8)

            # Convert the QImage to QPixmap
            pixmap = QPixmap.fromImage(grayscale_qimage)

            # Display the grayscale image in the QLabel
            self.ui.imageLabel.setPixmap(pixmap)
            self.ui.imageLabel.setPixmap(pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply grayscale filter: {e}")
        self.status_message.setText(f"Grayscale filter applied successfully on : {self.current_file}")
        self.update_tool_label("Grayscale Filter")
 
    def show_gaussian_blur_dialog(self):
        """ Show a dialog to get the kernel size and sigma for Gaussian Blur with OK and Cancel buttons. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Gaussian Blur Parameters")
        dialog.setStyleSheet("background-color: #333333; color: white;")  # Set dialog background and text color

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Kernel size input
        kernel_size_input = QSpinBox()
        kernel_size_input.setRange(3, 100)
        kernel_size_input.setValue(self.filter_parameters.get("Kernel Size", 5))  # Default value from filter_parameters
        kernel_size_input.setSingleStep(2)  # Ensure only odd values
        kernel_size_input.setStyleSheet("color: white; background-color: #555555;")
        form_layout.addRow("Kernel Size (Odd number):", kernel_size_input)

        # Sigma input
        sigma_input = QDoubleSpinBox()
        sigma_input.setRange(0.1, 100.0)
        sigma_input.setValue(self.filter_parameters.get("Sigma", 1.5))  # Default value from filter_parameters
        sigma_input.setSingleStep(0.1)
        sigma_input.setStyleSheet("color: white; background-color: #555555;")
        form_layout.addRow("Sigma:", sigma_input)

        layout.addLayout(form_layout)

        # OK and Cancel buttons
        button_layout = QHBoxLayout()

        # OK Button
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)

        # Cancel Button
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)

        # Add buttons to the layout
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        def on_ok_clicked():
            """ Handle OK button click. Update parameters and apply the filter. """
            # Update filter parameters and apply the filter only when OK is clicked
            self.filter_parameters["Kernel Size"] = kernel_size_input.value()
            self.filter_parameters["Sigma"] = sigma_input.value()

            # Update the tree widget with the new parameters
            self.add_filter_to_tree("Gaussian Blur", self.filter_parameters)

            # Apply the filter (Gaussian Blur) with the updated parameters
            self.gaussian_blur(self.filter_parameters["Kernel Size"], self.filter_parameters["Sigma"])

            # Close the dialog after applying the filter
            dialog.accept()

        def on_cancel_clicked():
            """ Handle Cancel button click. Do not apply any changes and close the dialog. """
            # Simply reject the dialog, not applying any changes
            dialog.reject()

        # Connect buttons to their respective functions
        ok_button.clicked.connect(on_ok_clicked)
        cancel_button.clicked.connect(on_cancel_clicked)

        # Show the dialog and wait for the user action
        dialog.exec_()

    def gaussian_blur(self, kernel_size, sigma):
        """ Apply Gaussian blur to the loaded image. """
        if not hasattr(self, 'current_file') or not self.current_file:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("No Image")
            msg.setText("Please load an image first.")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #333333; 
                    color: white; 
                }
                QMessageBox QLabel {
                    color: white; 
                }
                QMessageBox QPushButton {
            color: white; 
            background-color: #555555; 
            border: 1px solid #777777;
            padding: 5px;
            min-width: 100px;  /* Adjust the width of the button */
        }
                QMessageBox QPushButton:hover {
                    background-color: #666666;
                }
            """)
            msg.exec_()
            return

        try:
            # Load the image using PIL
            image = Image.open(self.current_file)

            # Convert to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert the image to a NumPy array
            image_np = np.array(image)

            # Ensure kernel size is odd
            kernel_size = kernel_size if kernel_size % 2 == 1 else kernel_size + 1

            # Apply Gaussian blur using OpenCV
            blurred_image_np = cv2.GaussianBlur(image_np, (kernel_size, kernel_size), sigma)

            # Convert back to QPixmap and display
            height, width, channels = blurred_image_np.shape
            bytes_per_line = channels * width
            blurred_image = QImage(
                blurred_image_np.data, width, height, bytes_per_line, QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(blurred_image)

            self.ui.imageLabel.setPixmap(pixmap)
            self.ui.imageLabel.setPixmap(
                pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )


        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply Gaussian blur: {e}")
        self.status_message.setText(f"Gaussian filter applied successfully on : {self.current_file}")
        self.update_tool_label("Gaussian Filter")

    def show_noise_dialog(self):
        """ Show a dialog to get parameters for adding noise. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Noise Parameters")
        dialog.setStyleSheet("background-color: #333333; color: white;")  # Dialog styling

        layout = QVBoxLayout()

        # Noise Type Selection
        noise_type_label = QLabel("Noise Type:")
        noise_type_label.setStyleSheet("color: white;")
        noise_type_combo = QComboBox()
        noise_type_combo.addItems(["Gaussian", "Salt & Pepper", "Speckle"])
        noise_type_combo.setStyleSheet("color: white; background-color: #555555;")

        # Intensity Input
        intensity_label = QLabel("Intensity (1-100):")
        intensity_label.setStyleSheet("color: white;")
        intensity_input = QSpinBox()
        intensity_input.setRange(1, 100)
        intensity_input.setValue(10)
        intensity_input.setStyleSheet("color: white; background-color: #555555;")

        layout.addWidget(noise_type_label)
        layout.addWidget(noise_type_combo)
        layout.addWidget(intensity_label)
        layout.addWidget(intensity_input)

        # Buttons (OK and Cancel)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet(
            """
            QDialogButtonBox QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 4px;
                min-width: 100px; 
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #666666;
            }
            """
        )
        layout.addWidget(buttons)
        dialog.setLayout(layout)

        def on_ok_clicked():
            # Get user-selected values
            noise_type = noise_type_combo.currentText()
            intensity = intensity_input.value()
            self.add_noise(noise_type, intensity)  # Apply the noise to the image
            self.add_filter_to_tree("Add Noise", {"Noise Type": noise_type, "Intensity": intensity})  # Update the tree widget
            dialog.accept()  # Close the dialog after applying the filter

        # Handle OK and Cancel actions
        buttons.accepted.connect(on_ok_clicked)
        buttons.rejected.connect(dialog.reject)  # Cancel button closes the dialog without applying the filter

        dialog.exec_()

    def add_noise(self, noise_type, intensity):
        """ Add noise to the loaded image. """
        if not hasattr(self, 'current_file') or not self.current_file:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("No Image")
            msg.setText("Please load an image first.")
            
                # Set text and background color for the message box
            msg.setStyleSheet("QMessageBox { background-color: #333333; color: white; }"
                      "QMessageBox QPushButton { background-color: #555555; color: white; }"
                      "QMessageBox QLabel { color: white; }")
            msg.exec_()
            return

        try:
            # Load the image using PIL
            image = Image.open(self.current_file)

            # Convert to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert the image to a NumPy array
            image_np = np.array(image)

            # Add noise based on type
            if noise_type == "Gaussian":
                mean = 0
                std = intensity / 100.0 * 255  # Adjust intensity to be a percentage of max pixel value
                gaussian_noise = np.random.normal(mean, std, image_np.shape)
                noisy_image_np = np.clip(image_np + gaussian_noise, 0, 255).astype(np.uint8)  # Add noise and clip to valid range

            elif noise_type == "Salt & Pepper":
                prob = intensity / 100.0
                noisy_image_np = image_np.copy()
                # Randomly assign salt (white) and pepper (black) pixels based on the probability
                salt_pepper = np.random.choice([0, 255], size=image_np.shape[:2], p=[1 - prob, prob])
                noisy_image_np[salt_pepper == 0] = 0  # Set pepper pixels to black
                noisy_image_np[salt_pepper == 255] = 255  # Set salt pixels to white

            elif noise_type == "Speckle":
                # Speckle noise is multiplicative noise
                speckle_noise = np.random.randn(*image_np.shape) * (intensity / 100.0)  # Adjust intensity
                noisy_image_np = np.clip(image_np + image_np * speckle_noise, 0, 255).astype(np.uint8)

            # Convert back to QPixmap and display
            height, width, channels = noisy_image_np.shape
            bytes_per_line = channels * width
            noisy_image = QImage(
                noisy_image_np.data, width, height, bytes_per_line, QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(noisy_image)

            self.ui.imageLabel.setPixmap(pixmap)
            self.ui.imageLabel.setPixmap(
                pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add noise: {e}")
        self.status_message.setText(f"Noise filter applied successfully on : {self.current_file}")
        self.update_tool_label("Noise Filter")    
   
    def show_distortion_dialog(self):
        """ Show a dialog to get the amplitude and frequency for the distortion effect. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Distortion Parameters")
        dialog.setStyleSheet("background-color: #333333; color: white;")  # Dialog styling   

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Amplitude - Controls the intensity of the distortion
        self.amplitude_input = QSpinBox()
        self.amplitude_input.setRange(1, 50)
        self.amplitude_input.setStyleSheet("color: white;")
        self.amplitude_input.setValue(15)  # Default value
        form_layout.addRow("Amplitude:", self.amplitude_input)

        # Frequency - Controls how often the wave oscillates
        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setRange(0.01, 1.0)
        self.frequency_input.setStyleSheet("color: white;")
        self.frequency_input.setValue(0.05)  # Default value
        form_layout.addRow("Frequency:", self.frequency_input)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet(
            """
            QDialogButtonBox QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 5px;
                min-width: 100px;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #666666;
            }
            """
        )

        # Define the button behavior
        def on_ok_clicked():
            # Get the user input values for distortion effect
            amplitude = self.amplitude_input.value()
            frequency = self.frequency_input.value()

            # Store the values in filter_parameters for later use
            self.filter_parameters["Amplitude"] = amplitude
            self.filter_parameters["Frequency"] = frequency

            # Apply the distortion filter
            self.apply_distortion(amplitude, frequency)

            # Update the tree with the distortion parameters
            self.add_filter_to_tree("Distortion", {"Amplitude": amplitude, "Frequency": frequency})

            # Close the dialog after applying the filter
            dialog.accept()

        # Connect the OK button to the on_ok_clicked function
        buttons.accepted.connect(on_ok_clicked)
        buttons.rejected.connect(dialog.reject)

        layout.addWidget(buttons)
        dialog.setLayout(layout)

        dialog.exec_()

    def apply_distortion(self, amplitude, frequency):
        """ Apply the distortion filter using the user-provided parameters. """
        if not hasattr(self, 'current_file') or not self.current_file:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("No Image")
            msg.setText("Please load an image first.")
            
                # Set text and background color for the message box
            msg.setStyleSheet("QMessageBox { background-color: #333333; color: white; }"
                      "QMessageBox QPushButton { background-color: #555555; color: white; }"
                      "QMessageBox QLabel { color: white; }")
            msg.exec_()
            return

        try:
            # Get the distortion parameters from the dialog
            amplitude = self.amplitude_input.value()
            frequency = self.frequency_input.value()

            # Load the image using PIL
            image = Image.open(self.current_file)
            image = image.convert("RGB")  # Ensure the image is in RGB mode

            # Convert the image to a numpy array for processing
            image_np = np.array(image)
            # Get the image dimensions
            height, width, _ = image_np.shape
            # Apply sinusoidal distortion
            distorted_image_np = np.zeros_like(image_np)

            for y in range(height):
                for x in range(width):
                    # Apply the sinusoidal distortion to the x-coordinate
                    new_x = int(x + amplitude * math.sin(frequency * y))
                    
                    # Ensure the new_x is within the image boundaries
                    new_x = max(0, min(new_x, width - 1))
                    
                    # Assign the pixel to the new position
                    distorted_image_np[y, x] = image_np[y, new_x]

            # Convert the numpy array back to an image
            distorted_image = Image.fromarray(distorted_image_np)

            # Convert the distorted image to QImage
            distorted_image_qimage = QImage(distorted_image.tobytes(), distorted_image.width, distorted_image.height,
                                            distorted_image.width * 3, QImage.Format_RGB888)

            # Convert QImage to QPixmap
            pixmap = QPixmap.fromImage(distorted_image_qimage)

            # Display the distorted image in the QLabel
            self.ui.imageLabel.setPixmap(pixmap)
            self.ui.imageLabel.setPixmap(pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply distortion filter: {e}")
        self.status_message.setText(f"Distort filter applied successfully on : {self.current_file}")
        self.update_tool_label("Distort Filter")    

    def show_sharpen_dialog(self):
        """ Show a dialog to get the sharpening strength. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Sharpen")

        # Apply stylesheet to change text color to white and button width
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e;  /* Dark background for contrast */
                color: white;  /* White text color */
            }
            QLabel {
                color: white;  /* White text color for labels */
            }

            QDialogButtonBox QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 5px;
                min-width: 120px;  /* Adjust width for OK and Cancel buttons */
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #666666;
            }
        """)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Sharpen strength input (SpinBox)
        self.sharpen_strength_input = QSpinBox()
        self.sharpen_strength_input.setRange(1, 100)  # Adjust the range as needed
        self.sharpen_strength_input.setStyleSheet("color: white; background-color: #444;")  # Styling the input box
        self.sharpen_strength_input.setValue(1)  # Default value
        form_layout.addRow("Sharpen Strength:", self.sharpen_strength_input)

        layout.addLayout(form_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet(
            """
            QDialogButtonBox QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 5px;
                min-width: 100px;  /* Adjust width for OK and Cancel buttons */
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #666666;
            }
            """
        )
        buttons.accepted.connect(lambda: self.apply_sharpen(dialog))  # Apply filter when OK is clicked
        buttons.rejected.connect(dialog.reject)  # Close the dialog when Cancel is clicked
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec_()  # Open the dialog and wait for user interaction

    def apply_sharpen(self, dialog):
        # Get the sharpen strength value from the dialog
        sharpen_strength = self.sharpen_strength_input.value()
        self.sharpen(sharpen_strength)  # Apply sharpen filter with the strength
        self.add_filter_to_tree("Sharpen", {"Sharpen Strength": sharpen_strength})  # Update the tree with the sharpen strength

        # Close the dialog after applying the filter
        dialog.accept()  # This will close the dialog

    def sharpen(self, sharpen_strength):
        """ Apply the sharpening filter to the image without saving it and preserve the colors. """
        if not hasattr(self, 'current_file') or not self.current_file:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("No Image")
            msg.setText("Please load an image first.")
            
            # Set text and background color for the message box
            msg.setStyleSheet("QMessageBox { background-color: #333333; color: white; }"
                    "QMessageBox QPushButton { background-color: #555555; color: white; }"
                    "QMessageBox QLabel { color: white; }")
            msg.exec_()
            return

        try:
            # Load the image using PIL
            image = Image.open(self.current_file)

            # Convert the image to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert the image to a numpy array (OpenCV uses numpy arrays)
            image_np = np.array(image)

            # Define a sharpening kernel, applying the sharpen_strength
            sharpen_kernel = np.array([[-1, -1, -1],
                                    [-1,  9, -1],
                                    [-1, -1, -1]]) * sharpen_strength

            # Apply the sharpening filter using OpenCV
            sharpened_image_np = cv2.filter2D(image_np, -1, sharpen_kernel)

            # Convert the numpy array back to a PIL Image
            sharpened_image_pil = Image.fromarray(sharpened_image_np)

            # Convert the PIL Image to QPixmap for display in PyQt
            sharpened_image_pil = sharpened_image_pil.convert("RGBA")  # Convert to RGBA format for PyQt compatibility
            data = sharpened_image_pil.tobytes("raw", "RGBA")
            qimage = QImage(data, sharpened_image_pil.width, sharpened_image_pil.height, sharpened_image_pil.width * 4, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            # Display the sharpened image in the QLabel
            self.ui.imageLabel.setPixmap(pixmap)
            self.ui.imageLabel.setPixmap(pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply sharpening filter: {e}")
        self.status_message.setText(f"Sharpen filter applied successfully on : {self.current_file}")
        self.update_tool_label("Sharpen Filter")    

    def sketch_filter(self):
        """ Apply the sketch filter to the image without saving it. """
        if not hasattr(self, 'current_file') or not self.current_file:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("No Image")
            msg.setText("Please load an image first.")
            
                # Set text and background color for the message box
            msg.setStyleSheet("QMessageBox { background-color: #333333; color: white; }"
                      "QMessageBox QPushButton { background-color: #555555; color: white; }"
                      "QMessageBox QLabel { color: white; }")
            msg.exec_()
            return

        try:
            # Load the image using PIL
            image = Image.open(self.current_file)

            # Convert the image to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert the image to a numpy array (OpenCV uses numpy arrays)
            image_np = np.array(image)

            # Convert the image to grayscale using OpenCV
            gray_image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

            # Invert the grayscale image
            inverted_gray_image_np = 255 - gray_image_np

            # Apply Gaussian blur to the inverted image
            blurred_image_np = cv2.GaussianBlur(inverted_gray_image_np, (21, 21), 0)

            # Invert the blurred image
            inverted_blurred_image_np = 255 - blurred_image_np

            # Create the sketch image by dividing the grayscale image by the inverted blurred image
            sketch_image_np = cv2.divide(gray_image_np, inverted_blurred_image_np, scale=256.0)

            # Convert the sketch image back to RGB for display purposes
            sketch_image_rgb = cv2.cvtColor(sketch_image_np, cv2.COLOR_GRAY2RGB)

            # Convert the processed image back to a PIL Image
            sketch_image_pil = Image.fromarray(sketch_image_rgb)

            # Convert the PIL Image to QPixmap for display in PyQt
            sketch_image_pil = sketch_image_pil.convert("RGBA")  # Convert to RGBA format for PyQt compatibility
            data = sketch_image_pil.tobytes("raw", "RGBA")
            qimage = QImage(data, sketch_image_pil.width, sketch_image_pil.height, sketch_image_pil.width * 4, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            # Display the sketch image in the QLabel
            self.ui.imageLabel.setPixmap(pixmap)
            self.ui.imageLabel.setPixmap(pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply sketch filter: {e}")
        self.status_message.setText(f"Sketch filter applied successfully on : {self.current_file}")
        self.update_tool_label("Sketch Filter")    

    def show_mean_filter_dialog(self):
        """ Show a dialog to get the kernel size for the mean filter. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Mean Filter")

        # Apply stylesheet to change text color to white and button width
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e;  /* Dark background for contrast */
                color: white;  /* White text color */
            }
            QLabel {
                color: white;  /* White text color for labels */
            }

            QDialogButtonBox QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 5px;
                min-width: 120px;  /* Adjust width for OK and Cancel buttons */
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #666666;
            }
        """)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Kernel Size input (SpinBox)
        self.kernel_size_input = QSpinBox()
        self.kernel_size_input.setRange(1, 100)  # Adjust the range as needed
        self.kernel_size_input.setStyleSheet("color: white; background-color: #444;")  # Styling the input box
        self.kernel_size_input.setValue(3)  # Default value
        form_layout.addRow("Kernel Size:", self.kernel_size_input)

        layout.addLayout(form_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("""
            QDialogButtonBox QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 5px;
                min-width: 100px;  /* Adjust width for OK and Cancel buttons */
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #666666;
            }
        """)
        
        # Updated connection for applying the mean filter
        buttons.accepted.connect(lambda: self.apply_mean_filter(self.kernel_size_input.value()))  # Pass kernel size value to apply_mean_filter
        buttons.accepted.connect(dialog.accept) 
        buttons.rejected.connect(dialog.reject)  # Close the dialog when Cancel is clicked
        layout.addWidget(buttons)
             # Close the dialog
      


        dialog.setLayout(layout)
        dialog.exec_()  # Ope
       
    def apply_mean_filter(self, kernel_size):
        """ Apply the mean filter using the provided kernel size. """
        if not hasattr(self, 'current_file') or not self.current_file:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("No Image")
            msg.setText("Please load an image first.")
            
            msg.setStyleSheet("QMessageBox { background-color: #333333; color: white; }"
                            "QMessageBox QPushButton { background-color: #555555; color: white; }"
                            "QMessageBox QLabel { color: white; }")
            msg.exec_()
            return

        try:
            # Load the image using PIL
            image = Image.open(self.current_file)

            # Convert the image to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert the image to a numpy array (OpenCV uses numpy arrays)
            image_np = np.array(image)

            # Create the kernel for the mean filter
            kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)

            # Apply the mean filter using OpenCV
            mean_filtered_image_np = cv2.filter2D(image_np, -1, kernel)

            # Convert the numpy array back to a PIL Image
            mean_filtered_image_pil = Image.fromarray(mean_filtered_image_np)

            # Convert the PIL Image to QPixmap for display in PyQt
            mean_filtered_image_pil = mean_filtered_image_pil.convert("RGBA")  # Convert to RGBA format for PyQt compatibility
            data = mean_filtered_image_pil.tobytes("raw", "RGBA")
            qimage = QImage(data, mean_filtered_image_pil.width, mean_filtered_image_pil.height, mean_filtered_image_pil.width * 4, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            # Display the mean-filtered image in the QLabel
            self.ui.imageLabel.setPixmap(pixmap)
            self.ui.imageLabel.setPixmap(pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

            # Update the tree with the filter parameters
            self.add_filter_to_tree("Mean Filter", {"Kernel Size": kernel_size})
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply mean filter: {e}")
        self.status_message.setText(f"Mean filter applied successfully on : {self.current_file}")
        self.update_tool_label("Mean Filter")    

    def show_edge_detection_dialog(self):
        """ Show a dialog to get the thresholds for edge detection. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Edge Detection Parameters")
        dialog.setStyleSheet("""
            QDialog {
                background-color: #333333;
                color: white;
            }
            QLabel {
                color: white;
            }
            QSpinBox {
                color: white;
                background-color: #444;
            }
            QDialogButtonBox QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 5px;
                min-width: 120px;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #666666;
            }
        """)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Low Threshold
        low_threshold_input = QSpinBox()
        low_threshold_input.setRange(1, 100)
        low_threshold_input.setValue(self.filter_parameters.get("Low Threshold", 50))  # Default value from tree
        form_layout.addRow("Low Threshold:", low_threshold_input)

        # High Threshold
        high_threshold_input = QSpinBox()
        high_threshold_input.setRange(1, 200)
        high_threshold_input.setValue(self.filter_parameters.get("High Threshold", 150))  # Default value from tree
        form_layout.addRow("High Threshold:", high_threshold_input)

        layout.addLayout(form_layout)

        # Dialog buttons (OK and Cancel)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        dialog.setLayout(layout)

        def on_ok_clicked():
            # Get user-selected values from the dialog
            low_threshold = low_threshold_input.value()
            high_threshold = high_threshold_input.value()

            # Apply edge detection filter
            self.apply_edge_detection(low_threshold, high_threshold)

            # Update filter parameters in the tree (Edge Detection)
            self.add_filter_to_tree("Edge Detection", {"Low Threshold": low_threshold, "High Threshold": high_threshold})

            dialog.accept()  # Close the dialog after applying the filter

        # Handle OK and Cancel actions
        buttons.accepted.connect(on_ok_clicked)
        buttons.rejected.connect(dialog.reject)  # Cancel button closes the dialog without applying the filter

        dialog.exec_()

    def apply_edge_detection(self, low_threshold, high_threshold):
        """ Apply the edge detection filter using the thresholds provided. """
        if not hasattr(self, 'current_file') or not self.current_file:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("No Image")
            msg.setText("Please load an image first.")
            
                # Set text and background color for the message box
            msg.setStyleSheet("QMessageBox { background-color: #333333; color: white; }"
                      "QMessageBox QPushButton { background-color: #555555; color: white; }"
                      "QMessageBox QLabel { color: white; }")
            msg.exec_()
            return
        try:
            image = Image.open(self.current_file)
            # Convert the image to grayscale (Edge detection works on grayscale images)
            gray_image = image.convert("L")
            image_np = np.array(gray_image)

            # Apply Canny edge detection
            edges = cv2.Canny(image_np, low_threshold, high_threshold)

            # Convert the edges array back to a PIL Image
            edges_pil = Image.fromarray(edges)

            # Convert the PIL Image to QPixmap for display in PyQt
            edges_pil = edges_pil.convert("RGBA")  # Convert to RGBA format for PyQt compatibility
            data = edges_pil.tobytes("raw", "RGBA")
            qimage = QImage(data, edges_pil.width, edges_pil.height, edges_pil.width * 4, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            # Display the edge-detected image in the QLabel
            self.ui.imageLabel.setPixmap(pixmap)
            self.ui.imageLabel.setPixmap(pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply edge detection: {e}")
        self.status_message.setText(f"Edge Detection filter applied successfully on : {self.current_file}")
        self.update_tool_label("Edge Detection Filter")    

    def show_sobel_dialog(self):
        """ Show a dialog to get the kernel size for the Sobel filter. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Sobel Filter Parameters")

        # Apply stylesheet to change text color to white
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e;  /* Dark background for contrast */
                color: white;  /* White text color */
            }
            QLabel {
                color: white;  /* White text color for labels */
            }
            QSpinBox {
                color: white;
                background-color: #444;  /* Dark background for input fields */
            }
            QDialogButtonBox {
                color: white;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #555;
                color: white;
            }
            QDialogButtonBox QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 5px;
                min-width: 120px;  /* Adjust width for OK and Cancel buttons */
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #666666;
            }
        """)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Create a kernel size input field for Sobel filter (odd numbers like 3, 5, 7)
        kernel_size_input = QSpinBox()
        kernel_size_input.setRange(3, 7)  # Kernel size range for Sobel filter
        kernel_size_input.setValue(self.filter_parameters.get("Kernel Size", 3))  # Default value from tree
        kernel_size_input.setSingleStep(2)  # Ensure the kernel size is always odd
        form_layout.addRow("Kernel Size (Odd number):", kernel_size_input)

        layout.addLayout(form_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        dialog.setLayout(layout)

        def on_ok_clicked():
            # Get user-selected kernel size from the dialog
            kernel_size = kernel_size_input.value()

            # Apply Sobel filter
            self.apply_sobel_filter(kernel_size)

            # Update filter parameters in the tree (Sobel filter)
            self.add_filter_to_tree("Sobel Filter", {"Kernel Size": kernel_size})

            dialog.accept()  # Close the dialog after applying the filter

        # Handle OK and Cancel actions
        buttons.accepted.connect(on_ok_clicked)
        buttons.rejected.connect(dialog.reject)

        dialog.exec_()
  
    def apply_sobel_filter(self, kernel_size):
        """ Apply the Sobel filter using the kernel size provided. """
        if not hasattr(self, 'current_file') or not self.current_file:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("No Image")
            msg.setText("Please load an image first.")
            
            # Set text and background color for the message box
            msg.setStyleSheet("QMessageBox { background-color: #333333; color: white; }"
                              "QMessageBox QPushButton { background-color: #555555; color: white; }"
                              "QMessageBox QLabel { color: white; }")
            msg.exec_()
            return

        try:
            image = Image.open(self.current_file)

            # Convert the image to grayscale
            grayscale_image = image.convert("L")

            # Convert the image to a numpy array (OpenCV uses numpy arrays)
            image_np = np.array(grayscale_image)

            # Apply the Sobel filter using OpenCV
            sobel_x = cv2.Sobel(image_np, cv2.CV_64F, 1, 0, ksize=kernel_size)  # Sobel X
            sobel_y = cv2.Sobel(image_np, cv2.CV_64F, 0, 1, ksize=kernel_size)  # Sobel Y
            sobel_edge = cv2.magnitude(sobel_x, sobel_y)  # Combine Sobel X and Sobel Y

            # Convert the result back to uint8 (range 0-255)
            sobel_edge = np.uint8(np.absolute(sobel_edge))

            # Convert the numpy array back to a PIL Image
            sobel_filtered_image_pil = Image.fromarray(sobel_edge)

            # Convert the PIL Image to QPixmap for display in PyQt
            sobel_filtered_image_pil = sobel_filtered_image_pil.convert("RGBA")  # Convert to RGBA format for PyQt compatibility
            data = sobel_filtered_image_pil.tobytes("raw", "RGBA")
            qimage = QImage(data, sobel_filtered_image_pil.width, sobel_filtered_image_pil.height, sobel_filtered_image_pil.width * 4, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            # Display the Sobel-filtered image in the QLabel
            self.ui.imageLabel.setPixmap(pixmap)
            self.ui.imageLabel.setPixmap(pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply Sobel filter: {e}")
        self.status_message.setText(f"Sobel filter applied successfully on : {self.current_file}")
        self.update_tool_label("Sobel Filter")    

    def show_box_filter_dialog(self):
        """ Show a dialog to get the kernel size for the Box Filter. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Linear Filter Parameters")

        # Apply stylesheet to change text color to white
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e;  /* Dark background for contrast */
                color: white;  /* White text color */
            }
            QLabel {
                color: white;  /* White text color for labels */
            }
            QSpinBox {
                color: white;
                background-color: #444;  /* Dark background for input fields */
            }
            QDialogButtonBox {
                color: white;
            }
            QDialogButtonBox QPushButton {
                color: white; 
                background-color: #555555; 
                border: 1px solid #777777; 
                padding: 5px;
                min-width: 120px;  /* Adjust width for OK and Cancel buttons */
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #666666;
            }
        """)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Create a kernel size input field for Box Filter (odd numbers like 3, 5, 7)
        kernel_size_input = QSpinBox()
        kernel_size_input.setRange(3, 50)  # Kernel size range for Box Filter (odd numbers)
        kernel_size_input.setValue(10)  # Default value, must be odd
        kernel_size_input.setSingleStep(2)  # Ensure the kernel size is always odd

        # To ensure that the value remains odd, we can adjust the value change event.
        def validate_odd_value(value):
            # If the value is even, set it to the nearest odd number
            if value % 2 == 0:
                value += 1
            kernel_size_input.setValue(value)

        # Connect the valueChanged signal to ensure odd value constraint
        kernel_size_input.valueChanged.connect(lambda: validate_odd_value(kernel_size_input.value()))

        form_layout.addRow("Kernel Size (Odd number):", kernel_size_input)

        layout.addLayout(form_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self.apply_box_filter(kernel_size_input.value()))
        buttons.accepted.connect(dialog.reject)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec_()

    def apply_box_filter(self, kernel_size):
        """ Apply the Box Filter using the kernel size provided. """
        if not hasattr(self, 'current_file') or not self.current_file:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("No Image")
            msg.setText("Please load an image first.")
            msg.setStyleSheet("QMessageBox { background-color: #333333; color: white; }"
                            "QMessageBox QPushButton { background-color: #555555; color: white; }"
                            "QMessageBox QLabel { color: white; }")
            msg.exec_()
            return

        try:
            # Load and process the image using PIL and OpenCV
            image = Image.open(self.current_file)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            image_np = np.array(image)
            box_filtered_image_np = cv2.boxFilter(image_np, -1, (kernel_size, kernel_size))

            box_filtered_image_pil = Image.fromarray(box_filtered_image_np)
            box_filtered_image_pil = box_filtered_image_pil.convert("RGBA")
            data = box_filtered_image_pil.tobytes("raw", "RGBA")
            qimage = QImage(data, box_filtered_image_pil.width, box_filtered_image_pil.height, box_filtered_image_pil.width * 4, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            # Display the Box-filtered image
            self.ui.imageLabel.setPixmap(pixmap)
            self.ui.imageLabel.setPixmap(pixmap.scaled(self.ui.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

            self.filter_parameters["Kernel Size"] = kernel_size
            # Add the filter to the tree or update it if already present
            self.add_filter_to_tree("Box Filter", {"Kernel Size": kernel_size})
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply Box filter: {e}")
        self.status_message.setText(f"Linear filter applied successfully on : {self.current_file}")
        self.update_tool_label("Linear Filter")    

    def show_about_dialog(self):
        about_message = """
            <h2 style="color: white;">About AuraEdit v1.0</h2>
            <p><b style="color: white;">Developed by Areeba Ghazal</b></p>
            <p><i style="color: white;">Email:</i> <a href="mailto:areebaghazal88@gmail.com" style="color: #add8e6;">areebaghazal88@gmail.com</a></p>
            
            <h3 style="color: white;">Description:</h3>
            <p style="color: white;">
                This is a powerful image processing application designed to help you edit, enhance, and apply various filters to your images with ease.
                The app provides tools like resizing, cropping, adjusting brightness/contrast, and applying advanced filters like Box Filter, Mean Filter, and Edge Detection.
                Whether you are a beginner or a professional, this app will help you achieve the results you desire quickly and efficiently.
            </p>
            
            <h3 style="color: white;">Features:</h3>
            <ul style="color: white;">
                <li>Apply various image filters (Box Filter, Mean Filter, Edge Detection)</li>
                <li>Adjust image brightness, contrast, and sharpness</li>
                <li>Resize and crop images with ease</li>
                <li>User-friendly interface for a seamless experience</li>
            </ul>
            
            <h3 style="color: white;">Version:</h3>
            <p style="color: white;">v1.0</p>
            
            <h3 style="color: white;">Credits:</h3>
            <p style="color: white;">Special thanks to all the contributors and open-source libraries used in this project!</p>
            """
                
        # Create a QMessageBox to show the About message
        about_box = QMessageBox(self)
        about_box.setWindowTitle("About Your App")
        # Set the icon (optional)
        about_box.setIcon(QMessageBox.Information)
        
        # Set the text to display HTML content for rich formatting
        about_box.setTextFormat(Qt.RichText)
        about_box.setText(about_message)
        about_box.setStyleSheet("""
        QMessageBox QPushButton {
            background-color: #555555;  /* Dark background for buttons */
            color: white;  /* White text color */
            border: 1px solid #777777;  /* Button border */
            padding: 5px 25px;
        }
        QMessageBox QPushButton:hover {
            background-color: #666666;  /* Lighter background when hovered */
        }
    """)
        
        # Display the message box
        about_box.exec_()
        self.status_message.setText(f"About AuraEdit")
        self.update_tool_label("About App")
   
    def setup_menu_actions(self):
        """ Connect View menu actions to toggle functions and sync check states. """
        self.ui.actionPropertiies.setCheckable(True)
        self.ui.actionMain_Window.setCheckable(True)
        self.ui.actionTools.setCheckable(True)

        # Connect menu actions to toggle functions
        self.ui.actionPropertiies.triggered.connect(self.toggle_properties)
        self.ui.actionMain_Window.triggered.connect(self.toggle_main_window)
        self.ui.actionTools.triggered.connect(self.toggle_tools)

        # Sync initial state
        self.sync_menu_checks()

    def sync_menu_checks(self):
        """ Sync menu actions with widget visibility. """
        self.ui.actionPropertiies.setChecked(self.ui.property_widget.isVisible())
        self.ui.actionMain_Window.setChecked(self.ui.main_window.isVisible())
        self.ui.actionTools.setChecked(
            self.ui.tools_widget.isVisible() or self.ui.scroll_area_tools_2.isVisible()
        )

    def toggle_properties(self):
        """ Toggle visibility of the Properties widget. """
        is_visible = not self.ui.property_widget.isVisible()
        self.ui.property_widget.setVisible(is_visible)
        self.ui.actionPropertiies.setChecked(is_visible)

    def toggle_main_window(self):
        """ Toggle visibility of the Main Window widget. """
        is_visible = not self.ui.main_window.isVisible()
        self.ui.main_window.setVisible(is_visible)
        self.ui.actionMain_Window.setChecked(is_visible)

    def toggle_tools(self):
        """ Toggle visibility of the Tools widgets. """
        is_visible = not (self.ui.scroll_area_tools_2.isVisible())
        # self.ui.tools_widget.setVisible(is_visible)
        self.ui.scroll_area_tools_2.setVisible(is_visible)
        self.ui.actionTools.setChecked(is_visible)


def main():
    app = QApplication(sys.argv)

    # Create the splash screen
    splash_pix = QPixmap("logoor2.png")  # Replace with your actual logo path
    
    # Resize the image to a larger size (for example, 600x600)
    splash_pix = splash_pix.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())

    # Show splash screen
    splash.show()

    # Wait for 3 seconds, then open the main window
    QTimer.singleShot(3000, splash.close)  # Close splash screen after 3 seconds

    # Create the main window and show it
    main_window = AuraEdit()
    
    # Start the event loop
    main_window.show()
    
    # Run the event loop
    app.exec_()

if __name__ == '__main__':
    main()

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = AuraEdit()
#     window.setup_menu_actions()
#     window.show()
#     sys.exit(app.exec_())
