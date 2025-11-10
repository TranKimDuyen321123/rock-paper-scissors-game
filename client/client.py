#client.py
import socket
import json
import threading
import time
import queue 
import tkinter as tk 
from rps_gui import RPSClientGUI 

HOST = '127.0.0.1'
PORT = 50007

class GameClient:
    """
    Lớp chính quản lý kết nối Socket và giao diện Tkinter.
    Sử dụng Queue để truyền dữ liệu an toàn giữa luồng phụ (Socket) và luồng chính (GUI).
    """
    def __init__(self, root):
        self.root = root
        self.s = None
        self.player_name = ""
        self.running = True
        self.message_queue = queue.Queue() 
        self.is_main_loop_running = True # Dùng để kiểm tra trạng thái main loop
        
        self.gui = RPSClientGUI(self.send_move, self.set_player_name_and_connect)
        
        # Bổ sung: Thêm hàm xử lý khi đóng cửa sổ
        self.gui.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_closing(self):
        """Hàm được gọi khi người dùng đóng cửa sổ (nhấn nút X)."""
        # Đưa sự kiện ngắt kết nối vào Queue để xử lý an toàn
        self.message_queue.put({'type': 'disconnect', 'reason': "Client closing."})
        
    def set_player_name_and_connect(self, name):
        """
        Bắt đầu kết nối Socket.
        Chạy trong Main Thread (khi nhấn nút Connect).
        """
        self.player_name = name
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((HOST, PORT))
            
            self.send_json({'type': 'name', 'name': self.player_name})
            
            self.gui.display_info("Connected. Waiting for opponent...")
            self.gui.update_score(0, 0, "Opponent")
            
            # Bắt đầu luồng nhận dữ liệu (Thread phụ)
            threading.Thread(target=self.receive_data_thread, daemon=True).start()
            
            # Lên lịch kiểm tra Queue định kỳ (an toàn trong Main Loop)
            self.gui.after(100, self.process_queue) 
            
        except Exception as e:
            self.gui.display_info(f"Connection error: {e}")
            self.gui.connect_btn.config(state=tk.NORMAL)
            self.gui.name_entry.config(state=tk.NORMAL)

    def send_json(self, obj):
        """Gửi dữ liệu JSON qua socket."""
        if self.s:
            try:
                data = json.dumps(obj) + '\n'
                self.s.sendall(data.encode())
            except socket.error as e:
                # Nếu gửi lỗi, đưa sự kiện ngắt kết nối vào Queue
                self.message_queue.put({'type': 'disconnect', 'reason': f"Send error: {e}"})
                
    def send_move(self, move):
        """Callback từ GUI để gửi lựa chọn đi."""
        self.send_json({'type':'choice','choice':move})

    def recv_json(self):
        """Nhận dữ liệu JSON (chạy trong luồng phụ)."""
        buffer = ''
        while self.running:
            try:
chunk = self.s.recv(4096).decode()
                if not chunk:
                    # Server đóng, đưa sự kiện ngắt kết nối vào Queue
                    self.message_queue.put({'type': 'disconnect', 'reason': "Server closed connection."})
                    return None
                buffer += chunk
                
                if '\n' in buffer:
                    line, buffer = buffer.split('\n',1)
                    return json.loads(line)
                    
            except (socket.error, json.JSONDecodeError, UnicodeDecodeError):
                return None
                
    def handle_disconnect(self, reason):
        """Thực hiện dọn dẹp và đóng GUI (Chỉ chạy an toàn trong Main Thread)."""
        if not self.is_main_loop_running:
            return

        print(f"Handling disconnect: {reason}")
        self.running = False
        self.is_main_loop_running = False 
        
        self.gui.display_info(f"Disconnected: {reason}. Closing...", color="red")
        try:
            if self.s: self.s.close()
        except: pass
        
        # Dừng hẳn GUI sau 3 giây
        self.gui.after(3000, self.gui.quit) 

    def process_queue(self):
        """
        Xử lý các tin nhắn từ hàng đợi và cập nhật GUI.
        Chạy định kỳ 100ms trong Main Thread.
        """
        while not self.message_queue.empty():
            msg = self.message_queue.get()
            mtype = msg.get('type')
            
            # --- Xử lý sự kiện ngắt kết nối an toàn ---
            if mtype == 'disconnect':
                self.handle_disconnect(msg.get('reason'))
                break 

            # --- Logic cập nhật GUI ---
            elif mtype == 'info':
                self.gui.display_info(msg.get('msg'))
                if 'GAME OVER' in msg.get('msg'):
                    self.gui.enable_game_controls(False)
            
            elif mtype == 'start':
                score = msg.get('current_score', {'you': 0, 'opponent': 0})
                opponent = msg.get('opponent_name', 'Opponent')
                
                self.gui.update_score(score['you'], score['opponent'], opponent)
                self.gui.display_info(f"New Round! {msg.get('msg')}")
                self.gui.enable_game_controls(True) 
                
            elif mtype == 'result':
                score = msg.get('current_score', {'you': 0, 'opponent': 0})
                # Lấy tên đối thủ từ score_label
                opponent_text = self.gui.score_label.cget("text")
                opponent = opponent_text.split(' - ')[1].split(' ')[0] if ' - ' in opponent_text else 'Opponent'

                result_text = f"Round Result: {msg.get('outcome').upper()}!"
                result_text += f"\nYour move: {msg.get('your_choice')} - Opponent: {msg.get('opponent_choice')}"
self.gui.display_info(result_text)
                self.gui.update_score(score['you'], score['opponent'], opponent)
            
        # Lên lịch gọi lại hàm này sau 100ms
        if self.running and self.is_main_loop_running:
            self.gui.after(100, self.process_queue)


    def receive_data_thread(self):
        """Luồng chạy riêng để nhận dữ liệu từ Server, CHỈ ĐẶT VÀO QUEUE."""
        while self.running:
            msg = self.recv_json()
            if msg is None:
                # Lệnh break sẽ thoát vòng lặp, sau đó gửi tin nhắn ngắt kết nối
                break 
            
            self.message_queue.put(msg) 
            
        # Nếu vòng lặp kết thúc do Server đóng hoặc lỗi, gửi tin nhắn ngắt kết nối an toàn
        if self.running: 
             self.message_queue.put({'type': 'disconnect', 'reason': "Connection lost."})
             
        self.running = False


if __name__ == '__main__':
    root = tk.Tk()
    app = GameClient(root)
    root.mainloop()
