import cv2
from pyzbar import pyzbar
import csv
from collections import defaultdict
from datetime import datetime

URL = "http://<MOBILE_IP>:8080/video"
CONFIRM_THRESHOLD = 3                      
DATASET_PATH = "C:\\<YOUR_PATH>\\barcode_products.csv" 

dataset = {}
with open(DATASET_PATH, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        dataset[row['BarcodeNumber (UPC/EAN)']] = row

def get_product_info(barcode):
    """Retrieve product info from dataset"""
    return dataset.get(barcode, None)

def check_expiry(expiry_date):
    """Calculate expiry status"""
    today = datetime.today()
    try:
        expiry = datetime.strptime(expiry_date, "%d-%m-%Y") 
    except ValueError:
        return "Invalid expiry date", (0,0,255)
    
    delta_days = (expiry - today).days
    if delta_days < 0:
        return "❌ Expired", (0,0,255)
    elif delta_days <= 30:
        return f"⚠️ Near expiry ({delta_days} days left)", (0,255,255)
    else:
        return f"✅ Safe ({delta_days} days left)", (0,255,0)

barcode_count = defaultdict(int)
cap = cv2.VideoCapture(URL)
if not cap.isOpened():
    print("Error: Cannot open camera stream")
    exit()

print("[INFO] Starting Smart Barcode Scanner...")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            data = barcode.data.decode('utf-8')
            barcode_count[data] += 1

            x, y, w, h = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if barcode_count[data] >= CONFIRM_THRESHOLD:
                print(f"[CONFIRMED] Barcode {data} confirmed!")

                product_info = get_product_info(data)
                if product_info:
                    expiry_status, color = check_expiry(product_info['ExpiryDate'])
                    info_text = (f"Product Name: {product_info['ProductName']}\n"
                                 f"MFG: {product_info['ManufactureDate']}\n"
                                 f"Expiry: {product_info['ExpiryDate']}\n"
                                 f"Price: {product_info['Price']}\n"
                                 f"{expiry_status}")
                    print(info_text)
                else:
                    info_text = f"Barcode {data} not found in dataset"
                    color = (255,0,0)
                    print(info_text)

                cv2.putText(frame, info_text, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                cv2.imshow("Smart Barcode Scanner", frame)
                cv2.waitKey(2000) 
                cap.release()
                cv2.destroyAllWindows()
                exit()

            else:
                cv2.putText(frame, f"Scanning: {data} ({barcode_count[data]})",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

        cv2.imshow("Smart Barcode Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Exiting by user.")
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
