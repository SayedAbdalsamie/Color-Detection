import cv2
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

# =========================
# Load Image + Resize
# =========================
img = cv2.imread("colorpic.jpg")

if img is None:
    print("❌ Image not found")
    exit()

max_width = 1200
max_height = 800

h, w, _ = img.shape
scale = min(max_width / w, max_height / h)
img = cv2.resize(img, (int(w * scale), int(h * scale)))

# =========================
# Load Colors Dataset
# =========================
colors = pd.read_csv("colors.csv", header=None)
colors.columns = ["id", "color_name", "hex", "r", "g", "b"]

# =========================
# KMeans Top 5 Colors
# =========================
pixels = img.reshape(-1, 3)

if len(pixels) > 10000:
    pixels_sample = pixels[np.random.choice(pixels.shape[0], 10000, replace=False)]
else:
    pixels_sample = pixels

kmeans = KMeans(n_clusters=5, n_init=10)
kmeans.fit(pixels_sample)

centers = kmeans.cluster_centers_.astype(int)

labels = kmeans.labels_
counts = np.bincount(labels)
sorted_idx = np.argsort(counts)[::-1]

top_colors = centers[sorted_idx]

# =========================
# Create Top Colors Image
# =========================
bar_height = 100
bar_width = 600

top_img = np.zeros((bar_height, bar_width, 3), dtype="uint8")

step = bar_width // 5

for i, color in enumerate(top_colors):
    b, g, r = int(color[0]), int(color[1]), int(color[2])
    top_img[:, i * step : (i + 1) * step] = (b, g, r)


# =========================
# Get Color Name
# =========================
def get_color_name(R, G, B):
    minimum = float("inf")
    cname = ""

    for i in range(len(colors)):
        d = (
            abs(R - int(colors.loc[i, "r"]))
            + abs(G - int(colors.loc[i, "g"]))
            + abs(B - int(colors.loc[i, "b"]))
        )

        if d <= minimum:
            minimum = d
            cname = colors.loc[i, "color_name"]

    return cname


# =========================
# Mouse Click
# =========================
clicked = False
r = g = b = 0


def click_event(event, x, y, flags, param):
    global clicked, r, g, b

    if event == cv2.EVENT_LBUTTONDOWN:
        clicked = True
        b, g, r = img[y, x]
        b, g, r = int(b), int(g), int(r)


# =========================
# Windows Setup
# =========================
cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
cv2.namedWindow("Top 5 Colors", cv2.WINDOW_NORMAL)

cv2.setMouseCallback("Image", click_event)

# =========================
# Main Loop
# =========================
while True:

    display_img = img.copy()

    if clicked:
        name = get_color_name(r, g, b)

        # draw rectangle on top
        cv2.rectangle(display_img, (20, 20), (800, 70), (b, g, r), -1)

        text = f"{name}  R={r} G={g} B={b}"

        if r + g + b > 600:
            text_color = (0, 0, 0)
        else:
            text_color = (255, 255, 255)

        cv2.putText(
            display_img, text, (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2
        )

    cv2.imshow("Image", display_img)
    cv2.imshow("Top 5 Colors", top_img)

    if cv2.waitKey(20) & 0xFF == 27:
        break

cv2.destroyAllWindows()
