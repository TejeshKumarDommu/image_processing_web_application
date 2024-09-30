import cv2
import torch
from pathlib import Path

weights_path = Path(r"C:\Users\Personal\Desktop\myproject\best.pt")  # Provide the path to your weights file
model = torch.hub.load('ultralytics/yolov5', 'custom' , path=weights_path)

img_path = r"C:\Users\Personal\Desktop\project_1\train_data\images\test\A1_1.jpg"  # Provide the path to your image file
img = cv2.imread(img_path)

# Perform inference
results = model(img)

# Display results
results.show()

# Save results
results.save(Path("output"))

# Optionally, save annotated image
annotated_img = results.render()[0]
cv2.imwrite("output/annotated_image.jpg", annotated_img)
