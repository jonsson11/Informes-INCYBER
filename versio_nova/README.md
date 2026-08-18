# 🛡️ BitDefender API Report Generator

<p align="center">
  <img src="assets/logo_portada.png" width="180">
</p>

<p align="center">
<b>Professional PDF report generator for Bitdefender GravityZone using the official JSON-RPC API.</b>
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![Bitdefender](https://img.shields.io/badge/Bitdefender-GravityZone-red?style=for-the-badge)
![PDF](https://img.shields.io/badge/Output-PDF-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

</p>

---

## 📖 Overview

**BitDefender API Report Generator** automates the creation of professional customer reports by collecting security information directly from the **Bitdefender GravityZone API**.

The application retrieves endpoint inventory, protection status, malware events, quarantine activity and security audit information before generating a polished PDF report ready to be delivered to customers.

Designed for **MSPs**, **IT departments** and **Cybersecurity providers** that manage multiple organizations from a single GravityZone console.

---

# ✨ Features

* 📊 Executive PDF reports
* 🖥️ Endpoint inventory
* 🛡️ Endpoint protection status
* ☣️ Malware detections summary
* 🔒 Security audit events
* 📦 Quarantine statistics
* 📈 Security metrics generation
* 🏢 Multi-company support
* ⚙️ Command-line interface
* 📅 Configurable reporting period
* 🎨 Corporate branding support

---

# 📂 Project Structure

```text
BitDefenderAPI_ReportGenerator/
│
├── api/
│   └── bitdefender.py
│
├── pdf/
│   └── PDF generation engine
│
├── reports/
│   ├── Endpoint Status
│   ├── Malware Status
│   ├── Security Audit
│   └── Quarantine
│
├── services/
│   ├── Statistics
│   ├── Date ranges
│   └── Helpers
│
├── assets/
│   ├── Logos
│   └── Icons
│
├── informes/
│   └── Generated PDF reports
│
├── config.py
└── main.py
```

---

# ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/jonsson11/BitDefenderAPI_ReportGenerator.git

cd BitDefenderAPI_ReportGenerator
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Configuration

Edit `config.py` and configure:

* GravityZone API Host
* API Key
* Reporting interval
* Companies to exclude

Example:

```python
API_HOST = "https://cloudgz.gravityzone.bitdefender.com/api/v1.0/jsonrpc"
API_KEY = "YOUR_API_KEY"
```

> **Security recommendation**
>
> Never commit your API Key.
>
> It is recommended to load credentials using environment variables or a `.env` file.

---

# 🚀 Usage

Generate reports for every company:

```bash
python main.py
```

Generate a report for a specific customer:

```bash
python main.py -E "Customer Name"
```

---

# 📑 Generated Report

Each generated report includes:

* Executive summary
* Endpoint inventory
* Managed vs Active devices
* Operating systems distribution
* Physical vs Virtual machines
* Protection status
* Malware detections
* Quarantine activity
* Security audit events
* Security indicators
* Monthly statistics

Reports are automatically saved inside:

```text
informes/
```

---

# 📊 Workflow

```text
GravityZone API
        │
        ▼
Retrieve Companies
        │
        ▼
Collect Endpoint Data
        │
        ▼
Collect Security Events
        │
        ▼
Generate Statistics
        │
        ▼
Render PDF
        │
        ▼
Customer Report
```

---

# 🛠 Technologies

* Python
* Requests
* Bitdefender GravityZone JSON-RPC API
* ReportLab (PDF generation)
* Modular architecture

---

# 🎯 Intended Audience

This project is ideal for:

* Managed Service Providers (MSPs)
* Cybersecurity consultancies
* Internal IT departments
* SOC teams
* Security administrators

---

# 🤝 Contributing

Contributions are welcome.

If you would like to improve the project:

1. Fork the repository.
2. Create your feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a Pull Request.

---

# 📄 License

This project is distributed under the MIT License.

---

# ⭐ Support

If you find this project useful, consider giving it a ⭐ on GitHub.

It helps the project grow and encourages future development.

---

<p align="center">

Made with ❤️ for the Bitdefender community.

</p>
