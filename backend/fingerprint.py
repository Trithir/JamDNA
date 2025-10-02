import subprocess, json, hashlib

def compute_fingerprint(path):
    result = subprocess.run(
        ["fpcalc", "-json", path], capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return data["fingerprint"], data["duration"]

def file_sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
