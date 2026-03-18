# 🎨 AI Color Detection System

A Computer Vision project that detects colors in images using Python, OpenCV, and Machine Learning (KMeans).
The system allows users to click on an image to identify color names and RGB values, and also extracts the top 5 dominant colors.

---

## 🚀 Features

* 🎯 Detect color name by clicking on image
* 🎨 Display RGB values dynamically
* 🧠 Use Kaggle dataset for accurate color naming
* 🔍 Extract **unique colors** from image
* 📊 Identify **Top 5 dominant colors** using KMeans
* 🖼️ Interactive UI using OpenCV
* 🌐 (Optional) Flask Web App support

---

## 🧠 Technologies Used

* Python
* OpenCV
* Pandas
* NumPy
* Scikit-learn (KMeans)
* Matplotlib (for visualization)
* Flask (optional for web version)

---

## 📂 Project Structure

```
color-detection-project/
│
├── main.py
├── colors.csv
├── image.jpg
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

1. Clone the repository:

```
git clone https://github.com/your-username/color-detection-project.git
cd color-detection-project
```

2. Create virtual environment:

```
python -m venv venv
venv\Scripts\activate   # Windows
```

3. Install dependencies:

```
pip install -r requirements.txt
```

---

## ▶️ How to Run

```
python main.py
```

---

## 🎯 Usage

* Open the application
* Click anywhere on the image
* The system will display:

  * Color name
  * RGB values
* A separate window shows the **Top 5 dominant colors**

---

## 📊 Example Output

* 🎨 Color Name: *Air Force Blue*
* 🔢 RGB: (93, 138, 168)
* 📈 Top Colors: Displayed as color bars

---

## 🧪 Machine Learning Part

We used **KMeans Clustering** to:

* Group similar colors
* Extract dominant colors
* Improve color analysis

---

## 🔥 Future Improvements

* 🌐 Deploy as Flask Web App
* 🎥 Real-time color detection (camera)
* 📊 Show percentage of each color
* 🖥️ Build modern UI (React / Streamlit)
* 📱 Mobile integration

---

## 📸 Demo



---

## 🤝 Contributing

Feel free to fork the project and improve it.

---

## 📬 Contact

* LinkedIn: https://linkedin.com/in/your-profile
* GitHub: https://github.com/SayedAbdalsamie

---

## ⭐ Don't forget to star the repo if you like it!
