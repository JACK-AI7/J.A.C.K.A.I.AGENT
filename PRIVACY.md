# J.A.R.V.I.S. (JACK) - DATA PRIVACY DECLARATION

This document outlines the strict privacy and data security protocols enforced by the TITAN Architecture.

## 1. Offline-First Operation
All primary AI processing (The "Brain") remains on your local machine via Ollama and Faster-Whisper. Your voice and text queries never leave your local environment for inference.

## 2. Hardcoded Privacy Guards
JACK is programmed with a "Privacy Core" that forbids the sharing of:
- Personal Identifiable Information (Names, Addresses, etc.)
- Login Credentials and Cookies
- Private local files and source code
- System access tokens

## 3. Web Interaction Security
When JACK performs web tasks (e.g., searching the web or checking Gmail), data is strictly limited to the minimum required for the task. 
- **Searches**: Queries are processed through DuckDuckGo (privacy-focused).
- **Automation**: Real-time session data is never cached or transmitted externally by JACK.

## 4. User Control
The collection of diagnostic telemetry is disabled by default. You have 100% control over the repository and its autonomous capabilities.

---
**JACK TITAN CORE: YOUR DATA IS YOURS.**
