import threading
import time
import urllib.request
import webbrowser

from dashboard import start_dashboard_server

PORT = 8001
URL = f"http://127.0.0.1:{PORT}"


def wait_for_server(url: str = URL, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    server_thread = threading.Thread(
        target=start_dashboard_server,
        args=("127.0.0.1", PORT),
        daemon=True,
    )
    server_thread.start()

    if not wait_for_server():
        raise RuntimeError(f"Dashboard server could not start on {URL}")

    print(f"Opening dashboard in your default browser: {URL}")
    webbrowser.open(URL)
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()