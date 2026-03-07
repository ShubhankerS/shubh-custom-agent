# 🚀 TrueNAS Intelligence Agent
**AI-Powered Monitoring & Storage Management using Gemini 3 Flash**

An intelligent, containerized agent designed to bridge the gap between AI and Enterprise Storage. This project leverages the Gemini 3 Flash model to provide real-time insights, pool health analysis, and automated documentation retrieval for TrueNAS SCALE 25.10 (Goldeye).

---

## ✨ Key Features
* **Gemini 3 Integration:** Uses the latest Google AI models via `litellm` for high-speed ZFS pool analysis.
* **RAG-Powered Brain:** (Retrieval-Augmented Generation) Capable of reading local TrueNAS manuals for accurate troubleshooting.
* **Dockerized Deployment:** Fully containerized for 24/7 operation on TrueNAS SCALE or any Linux server.
* **Automated CI/CD:** Integrated GitHub Actions ensure code integrity and Docker build success on every push.
* **Secure by Design:** Zero-secrets policy; handles private credentials via environment variables and `.gitignore`.

---

## 🏗️ Architecture
The agent is built with a decoupled architecture to ensure scalability:
- **Backend:** Python FastAPI for high-performance API endpoints.
- **Brain:** Custom logic using `litellm` to interface with LLMs.
- **Orchestration:** Docker Compose manages volumes, networking, and persistent storage.

---

## 🚀 Getting Started

### Prerequisites
- TrueNAS SCALE 25.10 or a Linux machine with Docker installed.
- A Google Gemini API Key.

### 1. Installation
Clone the repository to your server:
```bash
git clone [https://github.com/YOUR_USERNAME/shubh-custom-agent.git](https://github.com/YOUR_USERNAME/shubh-custom-agent.git)
cd shubh-custom-agent