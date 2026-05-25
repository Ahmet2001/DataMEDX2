# DataMEDX2

This repository is a comprehensive workspace containing oncology data analysis tools, clinical decision support systems, and AI-powered data processing agents. The project consists of two main parts: clinical data analytics files and the independently running AI automation panel (`BrowserAgent`).

---

## 📂 Project Structure

```text
DataMEDX2/
├── BrowserAgent/              # AI Automation & Agent Studio panel (Independent Project)
├── hackathon_veri.csv         # [Local Only] 114MB raw clinical dataset containing 1,000 patients (under .gitignore)
├── okunabilir_onizleme.csv    # Lightweight preview containing the first 30 rows of the dataset
├── veri_okuma_rehberi.md      # Detailed Turkish guide explaining the structure and columns of the clinical data
├── .gitignore                 # Excludes large files and sensitive credentials from GitHub tracking
└── README.md                  # Main project documentation (this file)
```

---

## 📊 Clinical Data Analytics

At the root directory, there is an oncology-focused dataset compiled from raw hospital and clinical epicrisis records.

* **`hackathon_veri.csv`**: A detailed clinical dataset covering the complete journey of 1,000 patients (lab results, prescriptions, pathology reports, physical examinations, and genetic tests). *Due to GitHub's 100 MB file size limit, this file is ignored in git and kept only in your local workspace.*
* **`okunabilir_onizleme.csv`**: A 30-row preview dataset designed to help you quickly understand the schema, columns, and data formats without loading the large CSV file.
* **`veri_okuma_rehberi.md`**: A Turkish reference guide detailing column groups (demographics, timeline, orders/prescriptions, lab tests) and highlighting critical aspects to keep in mind when processing this data with NLP/AI models.

---

## 🤖 BrowserAgent (Agent Studio & Control Panel)

The `BrowserAgent` directory is an independent application that uses LLMs and specialized SubModels to perform web automation, clinical data analysis, content generation, and multi-agent management.

### Features
* **Health AI Tools:** Built-in clinical analysis utilities including text cleaning, cohort filtering, laboratory trend analysis, drug summary extraction, and metastasis search.
* **Agent Studio:** A visual control room UI to manage, configure, and compile custom agent bundles.
* **Social & Content Automation:** Automated scheduling and posting mechanisms for X (Twitter), Instagram, and YouTube.
* **Doctor Panel UI:** A Qt-based GUI (`qt_doctor_panel.py`) and a web interface (`doctor.html`) to query clinical records, generate patient timelines, and compile patient reports.

### Setup and Running Instructions

To run the `BrowserAgent` application locally:

1. **Install Dependencies:**
   ```bash
   cd BrowserAgent
   chmod +x run.sh
   ./run.sh
   ```
   *This script automatically creates a virtual environment (`.venv`), installs required dependencies, and boots up the backend panel.*

2. **Open the Web Control Panel:**
   Once the application starts, navigate to the following URL in your web browser:
   * **http://127.0.0.1:8001/panel**

3. **Launch the Qt Doctor Panel:**
   If you want to start the desktop clinical analysis interface:
   ```bash
   chmod +x run_qt_doctor.sh
   ./run_qt_doctor.sh
   ```

---

## ⚠️ Important Notes

1. **Sensitive Credentials:** The `.env` or `.env.secrets` files inside the `BrowserAgent` folder contain API keys (Gemini, Telegram, etc.). Because this repository is **public**, these credential files are git-ignored for security. Make a copy of `.env.example`, fill in your own keys, and save it as `.env` to work locally.
2. **Personal Health Information (PHI):** Since the clinical dataset contains free-text fields with sensitive medical records, ensure strict compliance with data privacy regulations and anonymization standards when processing or training models.
