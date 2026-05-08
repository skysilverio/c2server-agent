# 🛸 Project: C2 Server and Agent (Phase 1 - The Core Engine)

## 📖 Introduction & Project Overview
I created this Command & Control (C2) and agent in Python as the first phase of many phases to learn and practice red team tactics and how the blue team can react and be proactive in these attacks. The C2 server acts as a "beacon" and "delivery man" to provide "tasks" to agents to demonstrate the mechanics of **Remote Code Execution (RCE)** through a cryptographically secure tunnel. 

Every packet—from the initial agent heartbeat to the final command output—is wrapped in **Fernet (AES-128)** encryption. This ensures that even if the traffic is captured by Network Detection and Response (NDR) tools, the actual intent and data remain invisible to the observer.

---

## 🛡️ Red Team Framework Alignment (MITRE ATT&CK)
This project simulates real-world adversary behavior by implementing the following techniques:

| ID | Technique | Implementation |
| :--- | :--- | :--- |
| **T1071.001** | **Application Layer Protocol: Web Protocols** | Uses standard HTTP POST requests to blend with legitimate web traffic. |
| **T1573.001** | **Encrypted Channel: Symmetric Cryptography** | Implements AES-based Fernet encryption for all data in transit. |
| **T1059.003** | **Command & Scripting Interpreter: Windows Command Shell** | Leverages `subprocess` to interact with the underlying OS. |
| **T1029** | **Scheduled Transfer** | Implements a consistent beaconing "heartbeat" (10s interval). |
| **T1020** | **Automated Exfiltration** | Automatically encrypts and pushes command results to the `/result` endpoint. |

---

## 🔍 Server Core Code Breakdown
The server script is organized into distinct modules to ensure a separation of concerns between cryptographic authentication, state management, and HTTP request handling.

### 1. The Cryptographic Gateway (cipher_suite)
This is the foundation of the "Cryptographic Sandwich". It instantiates a global Fernet symmetric encryption object. Both the server and agent must possess this exact key to communicate, ensuring that even if traffic is captured, Network Detection and Response (NDR) tools cannot read the plaintext payloads.

### 2. The State Manager (tasks dictionary)
The "Memory" of the server.
* It maintains an in-memory Python dictionary mapping unique Agent IDs to specific OS commands.
* By leveraging the `.pop()` method, it enforces a strict "fire-and-forget" model, guaranteeing that commands are executed exactly once and instantly purged from memory.

### 3. The Task Orchestrator (/beacon endpoint)
This route acts as the command dispatcher.
* It extracts the JSON payload and decrypts the ID, dropping the connection immediately if the cryptographic signature fails.
* If the task queue is empty, it securely defaults to encrypting and issuing a `SLEEP` command to maintain the agent's active connection without consuming unnecessary CPU cycles.

### 4. The Exfiltration Receiver (/result endpoint)
This route manages secure data ingestion.
* It expects dual-encrypted JSON payloads containing both the agent's identity and the command output.
* It decrypts both fields and logs them to the server's standard output. To any network observer, this data simply looks like meaningless, high-entropy blobs.

### 5. The Listener Initialization (if __name__ == "__main__":)
The server's entry point. It handles the startup sequence:
* Prints the initialization key to the console for easy synchronization with agents.
* Binds the Flask application to `127.0.0.1` on port `5000`, opening the port to accept external incoming web traffic.

---

## 🔍 Agent Core Code Breakdown
The agent script is organized into distinct functions to ensure execution resilience, zero-visibility transit, and operational security (OpSec).

### 1. The Cryptographic Identity (cipher_suite & AGENT_ID)
This establishes the "digital disguise" for the payload. It loads the pre-shared Fernet key and assigns a unique identifier. This identity is encrypted and attached to every outbound request to authenticate the agent to the C2 server.

### 2. The Execution Engine (execute_task)
This function acts as the bridge to the host operating system.
* It checks for the "SLEEP" command to abort safely and save CPU cycles.
* It hooks directly into the host shell via `subprocess.run(capture_output=True)` to capture both successful output (`stdout`) and errors (`stderr`).
* It features a built-in failsafe that injects a success message if `stdout` is empty (e.g., when running commands like `mkdir`), preventing the agent from crashing when encrypting a null payload.

### 3. The Beacon Pulse (send_beacon)
The "Heartbeat" of the remote payload.
* It encrypts the agent's identity and issues an HTTP POST request to the server to check for pending tasks.
* It is engineered with broad `try/except: pass` blocks. If the C2 server goes offline, it fails silently to prevent Python tracebacks from alerting the compromised user.

### 4. The Exfiltration Module (send_result)
This manages the outward data flow.
* Triggered immediately after a task finishes, it encrypts the combined terminal output and the agent's ID.
* It pushes this dual-encrypted payload to the server's `/result` route, utilizing the same silent failure logic as the beacon to survive network interruptions.

### 5. The Persistence Loop (main)
The agent's control room. It handles the continuous operation sequence:
* Enters an infinite `while True` loop to keep the process alive indefinitely.
* Triggers the beaconing function.
* Instructs the process to sleep for a defined interval (e.g., 10 seconds) before repeating the cycle.

---

## 🏗️ Technical Debt & Lessons Learned

Developing this core engine revealed several critical "Blue Team" detection points that serve as the roadmap for future development:

### 1. The "Heartbeat" Detection (Entropy)
* **Debt:** The agent currently beacons exactly every 10 seconds.
* **Lesson:** Fixed-interval communication creates a perfect rhythmic spike in network traffic analysis.
* **Fix:** Future iterations will implement **Jitter** (randomizing the sleep interval by ±X%) to break the mathematical pattern.

### 2. The Hardcoded Key Problem
* **Debt:** The Fernet Symmetric Key is hardcoded into the source.
* **Lesson:** If an IR (Incident Response) team captures the agent, they can reverse-engineer it to find the key and decrypt all historical traffic.
* **Fix:** Not too sure yet, but it will need to deal with some sort of dynamic key exchange for server/agent persistence.

### 3. Cleartext URI Signatures
* **Debt:** The routes `/beacon` and `/result` are static and obvious.
* **Lesson:** Modern firewalls can block traffic based on specific URI strings regardless of encryption.
* **Fix:** Implementing **Malleable C2 Profiles** where URI paths look like legitimate traffic (e.g., `/api/v1/updates` or `/images/loading.gif`).

---

## 🚀 Future Phases: Enterprise Cloud Deployment & Detection Lab

The next evolution of this project is to become a fully realized, cloud-hosted Red/Blue Team laboratory. The goal is to deploy the infrastructure in AWS, simulate real-world attacks, and actively monitor the environment using enterprise-grade security posture tools.

### 🌐 Phase 1: Attack Infrastructure (The C2 Server)
The C2 Server will be migrated from `localhost` to a hardened AWS environment to act as the external threat actor.

* **Compute Layer:** Hosted on an AWS EC2 instance running Ubuntu 24.04 LTS.
* **Production Stack:** Transitioning from the Flask development server to a robust WSGI pipeline using **Gunicorn** and **Nginx** (Reverse Proxy).
* **Persistence:** Managed via Linux `systemd` to ensure the C2 listener survives server reboots.
* **Network Cloaking:** Strict AWS Security Groups will limit SSH access to the operator's IP while leaving HTTPS open for agent check-ins.

### 🎯 Phase 2: The "Walled Garden" Target Environment
To safely test the agent and execute payloads (like XSS or Command Injection), a separate, isolated AWS environment will be constructed.

* **The Target:** Deployment of an intentionally vulnerable web application (e.g., OWASP Juice Shop or Damn Vulnerable Web App) inside an isolated VPC.
* **The Agent Payload:** The C2 agent will be deployed on this target machine, executing commands remotely ordered by the C2 server.
* **Access Control:** The target environment's Security Groups will be strictly configured so that only the operator and the C2 server can communicate with it, preventing unauthorized internet-wide exploitation.

### 🛡️ Phase 3: Defensive Telemetry & Threat Hunting (Blue Teaming)
Once the attack infrastructure is live and the agent is actively beaconing, the focus shifts to Detection Engineering and Cloud Security Posture Management (CSPM).

* **CloudGuard / AWS Native Security:** Integration of Check Point CloudGuard (or AWS native equivalents like GuardDuty and WAF) to monitor the cloud perimeter. 
* **Traffic Analysis:** Utilizing VPC Flow Logs and Amazon CloudWatch to visualize the encrypted "Cryptographic Sandwich" traffic. The goal is to identify network anomalies, such as the rhythmic 10-second beaconing pattern, without being able to read the encrypted payload.
* **Detection & Remediation:** * Writing custom AWS WAF rules to drop non-JSON POST requests or block unauthorized HTTP methods.
    * Setting up EventBridge and Lambda to automatically quarantine the target EC2 instance if anomalous outbound C2 traffic is detected.

---

> ⚠️ **LEGAL & ETHICAL DISCLAIMER**
> This project is a Proof-of-Concept developed strictly for educational purposes, defensive threat research, and authorized testing within isolated laboratory environments. The creator assumes no liability and is not responsible for any misuse or damage caused by this framework. **Do not deploy or utilize this software against any systems or networks for which you do not possess explicit, documented authorization.**
