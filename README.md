# 🏥 Provider Portal Automation Bot (Playwright + IMAP)

## 📌 Overview
This Python project automates the **Provider Portal workflow** for patient authorization requests.  
It combines **Playwright (browser automation)**, **IMAP (IONOS email OTP retrieval)**, and **CSV-based patient data** to fully automate the process of submitting, verifying, and downloading patient request PDFs.

---

## ✨ Features
- 🔑 **Automated login with OTP** (retrieved from IONOS email via IMAP + Pyzmail)
- 📂 **CSV-based patient data import** (demographics, provider, CPT/diagnosis codes)
- ⚕️ **Patient processing loop**:
  - Fill demographics & insurance
  - Diagnostic Imaging card handling
  - Provider/facility lookup with address map
  - CPT & Diagnosis code entry
  - Conditional **Q&A workflows** for CPT codes `93306`, `78452`, `78431`
- 📑 **PDF download** with custom filenames into a shared network folder
- 🖼 **Automatic screenshots** on errors
- ⏱ Retry logic for patient/member selection
- 🛑 Exit gracefully anytime with `=` key (keyboard listener)

---

## 🛠 Tech Stack
- **Python 3.9+**
- [Playwright](https://playwright.dev/python/) (browser automation)
- [IMAPClient](https://imapclient.readthedocs.io/) + [Pyzmail](https://pypi.org/project/pyzmail36/) (OTP email parsing)
- [Pynput](https://pynput.readthedocs.io/en/latest/) (keyboard listener)
- Built-in: `csv`, `re`, `time`, `os`, `threading`

---

## 📦 Setup & Installation

1. **Clone the repo**

   git clone https://github.com/your-org/provider-portal-automation.git
   cd provider-portal-automation
Install dependencies

pip install playwright imapclient pyzmail36 pynput
playwright install chromium
Prepare patients.csv
Example columns:

first_name,last_name,dob,member_id,date_of_service,phone,phone_type,provider_name,provider_type,facility_type,cpt_code,diagnosis_code
John,Doe,01/01/1980,123456,2025-08-10,8325551111,Mobile,MEMORIAL KATY CARDIOLOGY,1,cvcp,93306,I10
Update credentials in the script

form_data = {
    "user_id": "abc@hiisight.com",
    "password": "Abc@2025",
    "email_address": "Base@hiisight.com",
    "email_password": "User@1443101",
    "patients": load_patients_from_csv("patients.csv")
}
🚀 Running the Bot
bash
Copy
Edit
python main.py
The browser opens and logs in automatically.

OTP is fetched from IONOS inbox.

Patients are processed sequentially.

PDFs are downloaded into:

objectivec

📸 Error Handling
If an error occurs, the bot captures a screenshot under:


./screenshots/
Logs are printed to console for debugging.

⚠️ Notes
Screen selectors may break if the Provider Portal UI changes.

provider_type in CSV must match ADDRESS_MAP codes:

1 → Cardiology

2 → Radiology

3 → Orthopedics

Exit at any time by pressing =.

📜 License
MIT License — free to use and modify.

---

👉 Do you want me to also generate a **patients.csv template file** (with sample rows) so you can drop it directly into your repo along with this README?








Ask ChatGPT
