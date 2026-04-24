import socket

# Configuration
PORT = 8080 
print(f"--- SERVEUR D'ÉCOUTE GPS ACTIF SUR LE PORT {PORT} ---")
print("En attente de données du boîtier Coban...")

def start_sniffer():
    # Création du socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', PORT))
        s.listen(5)
        
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"\n[+] Connexion reçue de : {addr}")
                data = conn.recv(1024)
                if data:
                    # Affichage de la trame brute
                    print(f"--- TRAME REÇUE (Texte) ---")
                    print(data.decode('utf-8', errors='ignore'))
                    print(f"--- TRAME REÇUE (Hexadécimal) ---")
                    print(data.hex())
                    
                    # Réponse standard Coban pour maintenir la connexion
                    if data.startswith(b"##"):
                        conn.sendall(b"LOAD")
                        print("[>] Réponse 'LOAD' envoyée au boîtier.")

if __name__ == "__main__":
    try:
        start_sniffer()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
