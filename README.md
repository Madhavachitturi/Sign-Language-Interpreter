---

# ✋ Sign Language Interpreter (ASL)

A **Machine Learning based Sign Language Interpreter** that detects and translates **American Sign Language (ASL) alphabets (A–Z)** into text in real-time using computer vision.

The system uses **MediaPipe hand tracking** to extract hand landmarks and a **Random Forest Classifier** trained on a custom dataset to recognize gestures accurately.

---

## 🚀 Features

• Recognizes **26 ASL alphabets (A–Z)**
• **Real-time gesture detection** using webcam
• **Custom dataset collection pipeline**
• **MediaPipe hand landmark extraction**
• **Random Forest ML model for classification**
• Lightweight and runs on **CPU without GPU**

---

## 🧠 Tech Stack

* **Python**
* **OpenCV**
* **MediaPipe**
* **Scikit-learn**
* **NumPy**
* **Random Forest Classifier**

---

## 📂 Project Structure

```
Sign-Language-Interpreter
│
├── collect_imgs.py        # Collect gesture images using webcam
├── create_dataset.py      # Convert collected images to training dataset
├── train_classifier.py    # Train Random Forest model
├── inference_classifier.py# Run real-time gesture detection
│
├── model.p                # Trained ML model
├── data.pickle            # Processed dataset
├── asl.jpg                # ASL reference chart
│
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 📊 Dataset

A **custom dataset** was created for this project.

* **26 Classes (A–Z)**
* **~200 frames collected per alphabet**
* Captured using **webcam**
* Hand landmarks extracted using **MediaPipe**

The dataset was converted into numerical feature vectors before training the model.

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/jiyajahnavi/Sign-Language-Interpreter.git
cd Sign-Language-Interpreter
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 📸 Step 1: Collect Gesture Images

Run the script to collect gesture images.

```bash
python collect_imgs.py
```

Capture around **200 images per alphabet gesture**.

---

## 🗂 Step 2: Create Dataset

Convert collected images into a structured dataset.

```bash
python create_dataset.py
```

This will generate:

```
data.pickle
```

---

## 🤖 Step 3: Train the Model

Train the **Random Forest classifier**.

```bash
python train_classifier.py
```

This generates the trained model:

```
model.p
```

---

## 🎥 Step 4: Run Real-Time Interpreter

Run the gesture recognition system:

```bash
python inference_classifier.py
```

The webcam will start and the system will **predict ASL letters in real-time**.

---

## 🔍 How It Works

1️⃣ **OpenCV** captures webcam frames
2️⃣ **MediaPipe** detects hand landmarks (21 key points)
3️⃣ Landmarks are converted into feature vectors
4️⃣ **Random Forest Classifier** predicts the ASL letter
5️⃣ Prediction is displayed on screen

---

## 📈 Model

Algorithm used:

**Random Forest Classifier**

Why Random Forest?

• Works well with small datasets
• Handles non-linear relationships
• Fast training and inference
• Good accuracy for gesture classification

---

## 🔮 Future Improvements

• Add **word and sentence detection**
• Improve accuracy with **deep learning models (CNN / LSTM)**
• Add **speech output from predicted text**
• Support **dynamic gestures**

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 👩‍💻 Author

**Jiya Jahnavi**

If you like this project, consider **⭐ starring the repository**.

---
