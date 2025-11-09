# server/server.py
import socket
import threading
import json
# Import game_logic.py (cần đảm bảo tệp này nằm cùng thư mục)
from game_logic import get_result 

HOST = '0.0.0.0'
PORT = 50007  
MAX_SCORE = 3 # Điểm tối đa để thắng trận đấu

# Simple protocol: JSON messages terminated by newline.

clients_lock = threading.Lock()
# Cấu trúc mới: list chứa (connection, address, name)
waiting_clients = [] 

def send_json(conn, obj):
    """Gửi dữ liệu JSON qua socket."""
    data = json.dumps(obj) + '\n'
    conn.sendall(data.encode())

def recv_json(conn):
    """Nhận dữ liệu JSON qua socket."""
    buffer = ''
    while True:
        try:
            chunk = conn.recv(4096).decode()
        except:
            return None # Lỗi nhận dữ liệu
            
        if not chunk:
            return None # Server đóng kết nối
            
        buffer += chunk
        # Xử lý tin nhắn theo định dạng newline-delimited
        if '\n' in buffer:
            line, buffer = buffer.split('\n',1)
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                # Bỏ qua nếu tin nhắn bị lỗi cú pháp JSON
                continue 

def handle_match(c1, c2, n1, n2):
    """Xử lý logic đa vòng chơi giữa 2 client."""
    print(f'Match started: {n1} vs {n2}')
    score1, score2 = 0, 0

    try:
        # Vòng lặp cho đến khi một người đạt MAX_SCORE
        while score1 < MAX_SCORE and score2 < MAX_SCORE:
            # 1. Gửi thông báo bắt đầu vòng mới và điểm số
            msg_start = f'New Round! Score: {n1}: {score1} - {n2}: {score2}. Send your choice:'
            
            # Gửi thông tin riêng biệt cho từng client (điểm số của họ là 'you')
            send_json(c1, {'type':'start', 'msg':msg_start, 'opponent_name': n2, 'current_score': {'you': score1, 'opponent': score2}})
            send_json(c2, {'type':'start', 'msg':msg_start, 'opponent_name': n1, 'current_score': {'you': score2, 'opponent': score1}})

            # 2. Chờ nhận lựa chọn từ 2 người chơi
            m1 = recv_json(c1)
            m2 = recv_json(c2)

            if m1 is None or m2 is None: 
                # Nếu một người thoát, thông báo cho người còn lại
                if m1 is None: send_json(c2, {'type':'info', 'msg':f'Opponent {n1} disconnected. Match ended.'})
                if m2 is None: send_json(c1, {'type':'info', 'msg':f'Opponent {n2} disconnected. Match ended.'})
                break

            choice1 = m1.get('choice','').lower()
            choice2 = m2.get('choice','').lower()
            
            # 3. Xử lý logic game và tính điểm
            result1 = get_result(choice1, choice2)
            if result1 == 'win':
                result2, score1 = 'lose', score1 + 1
            elif result1 == 'lose':
                result2, score2 = 'win', score2 + 1
            else:
                result2 = 'draw'

            # 4. Gửi kết quả vòng chơi
            send_json(c1, {'type':'result','your_choice':choice1,'opponent_choice':choice2,'outcome':result1, 'current_score': {'you': score1, 'opponent': score2}})
            send_json(c2, {'type':'result','your_choice':choice2,'opponent_choice':choice1,'outcome':result2, 'current_score': {'you': score2, 'opponent': score1}})

        # 5. Gửi thông báo kết thúc trận đấu (Chỉ khi có người đạt MAX_SCORE)
        if score1 >= MAX_SCORE or score2 >= MAX_SCORE:
            final_msg1 = "YOU WIN THE MATCH!" if score1 > score2 else "YOU LOSE THE MATCH!"
            send_json(c1, {'type':'info', 'msg':f'*** GAME OVER *** Final Score: {n1} {score1} - {n2} {score2}. {final_msg1}'})
            
            final_msg2 = "YOU WIN THE MATCH!" if score2 > score1 else "YOU LOSE THE MATCH!"
            send_json(c2, {'type':'info', 'msg':f'*** GAME OVER *** Final Score: {n2} {score2} - {n1} {score1}. {final_msg2}'})


    except Exception as e:
        print(f'Match error for {n1} vs {n2}:', e)
        # Thông báo lỗi cho client còn lại nếu có thể
    finally:
        print(f'Match between {n1} and {n2} ended.')
        try: c1.close()
        except: pass
        try: c2.close()
        except: pass

def client_thread(conn, addr):
    print('Client connected', addr)
    
    # Bổ sung: Bước 1 - Nhận tên người chơi
    name_msg = recv_json(conn)
    if name_msg is None or name_msg.get('type') != 'name':
        print('Client did not send name or disconnected immediately. Disconnecting.')
        conn.close()
        return
    client_name = name_msg.get('name', f'Player-{addr[1]}')
    print(f'Client {addr} identified as {client_name}')
    
    # Bước 2 - Thêm vào danh sách chờ và thử ghép cặp
    with clients_lock:
        waiting_clients.append((conn, addr, client_name))
        if len(waiting_clients) >= 2:
            # Lấy 2 client đầu tiên
            (c1, a1, n1) = waiting_clients.pop(0)
            (c2, a2, n2) = waiting_clients.pop(0)
            
            # Bắt đầu luồng xử lý trận đấu
            t = threading.Thread(target=handle_match, args=(c1,c2,n1,n2), daemon=True)
            t.start()
        else:
            # Thông báo client đang chờ
            send_json(conn, {'type':'info','msg':f'Waiting for an opponent, {client_name} (Total waiting: {len(waiting_clients)})...'})
    # Luồng kết thúc ở đây; luồng handle_match sẽ quản lý và đóng socket sau trận đấu

def main():
    print('Starting RPS server on port', PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    try:
        while True:
            conn, addr = s.accept()
            # Bắt đầu luồng mới cho mỗi client kết nối
            t = threading.Thread(target=client_thread, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print('Server shutting down')
    finally:
        s.close()

if __name__ == '__main__':
    main()