# 🎨 Public Art Style Intelligence
### *Classifier + Style Fingerprint Generator + Similarity Search + Clustering + Explainability*
A 7-day ML project built on **80,000 public art images** to create an AI system that can **understand, classify, compare, and explain** visual art styles.

---

## 🚀 What This System Does

**1) Classifies artwork style (Azure Custom Vision)**
* Trained on **80k images**, auto-tagged
* Outputs **top-1 style** + confidence

**2) Generates a unique “Style Fingerprint Vector” (CLIP Embeddings)**
* 512-dim embedding per image
* Captures aesthetic + composition + texture
* Enables similarity + clustering

**3) Returns Top-3 visually similar artworks (Vector Search)**
* Qdrant/FAISS engine
* **<50 ms** retrieval
* Great for exploration + recommendation

**4) Discovers hidden “Micro-Genres” (Unsupervised Clustering)**
* KMeans/HDBSCAN on CLIP embeddings
* Reveals **latent art communities** beyond labels

**5) Explains predictions with Grad-CAM**
* Heatmaps show which regions influenced the classifier
* Adds transparency + interpretability

---

## 🖥️ Streamlit App (End-to-End UI)
Upload an image → AI returns:
- Predicted style
- Style fingerprint visual summary
- Top-3 similar pieces
- Micro-genre cluster ID
- Grad-CAM explanation
All in **~1.5 seconds** per query.

---

## 🧠 Tech Stack
**Azure Custom Vision · CLIP · PyTorch · Qdrant/FAISS · Streamlit · Grad-CAM · sklearn (clustering)**

---

## 📊 Key Stats
* **80,000+ images** processed
* **512-dim aesthetic fingerprints**
* **Top-3 similarity search in <50 ms**
* **7-day build**
* **100% reproducible pipeline**

---

## 📬 Contact

If you want to discuss the project, reach out:

**Pakhi Tyagi**
GitHub: github.com/pakhi-1411-2002
Email: [pakhi1411j@gmail.com](mailto:pakhi1411j@gmail.com)

If you want, I can generate a **visuall
y aesthetic version** with emojis, badges, or a more “research-paper” style version.
