#rps_gui.py
import tkinter as tk
from tkinter import messagebox
import threading

# Thay vì kế thừa tk.Tk (tạo cửa sổ), ta kế thừa tk.Frame (khung) để 
# nó được nhúng vào cửa sổ chính (root) trong client.py.
# Tuy nhiên, để đơn giản hóa, ta giữ lại logic tạo cửa sổ trong file rps_gui.
class RPSClientGUI(tk.Tk):
    def __init__(self, send_callback, player_name_callback):
        super().__init__()
        self.title("Rock Paper Scissors - Multiplayer")
        self.geometry("400x450")
        
        # Callback để gửi data: Hàm này sẽ gọi send_json() trong client core
        self.send_move_to_server = send_callback
        self.get_player_name = player_name_callback
        
        self._setup_initial_ui()

    def _setup_initial_ui(self):
        # 1. Khung nhập tên và kết nối
        self.name_frame = tk.Frame(self)
        self.name_frame.pack(pady=20)
        tk.Label(self.name_frame, text="Your Name:").pack(side=tk.LEFT)
        self.name_entry = tk.Entry(self.name_frame, width=20)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        self.connect_btn = tk.Button(self.name_frame, text="Connect", command=self._connect_action)
        self.connect_btn.pack(side=tk.LEFT)
        
        # 2. Khung thông tin và điểm số
        self.info_label = tk.Label(self, text="Please enter your name and connect.", fg="blue")
        self.info_label.pack(pady=10)
        
        # Thêm một nhãn để hiển thị thông tin chi tiết về đối thủ/trò chơi
        self.opponent_info = tk.Label(self, text="", font=('Arial', 10, 'italic'))
        self.opponent_info.pack(pady=5)
        
        self.score_label = tk.Label(self, text="Score: You 0 - Opponent 0", font=('Arial', 14, 'bold'))
        self.score_label.pack(pady=5)
        
        # 3. Khung nút chơi game
        self.game_frame = tk.Frame(self)
        self.game_frame.pack(pady=20)
        self.game_frame.pack_forget() # Ẩn đi cho đến khi kết nối thành công

        tk.Button(self.game_frame, text="ROCK", command=lambda: self._send_move('rock'), width=10, height=3).pack(side=tk.LEFT, padx=5)
        tk.Button(self.game_frame, text="PAPER", command=lambda: self._send_move('paper'), width=10, height=3).pack(side=tk.LEFT, padx=5)
        tk.Button(self.game_frame, text="SCISSORS", command=lambda: self._send_move('scissors'), width=10, height=3).pack(side=tk.LEFT, padx=5)
        
    def _connect_action(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Name cannot be empty.")
            return
        
        # Gọi callback trong client core để bắt đầu kết nối
        self.get_player_name(name)
        self.connect_btn.config(state=tk.DISABLED)
        self.name_entry.config(state=tk.DISABLED)
        
    def _send_move(self, move):
        # Gửi hành động (move) về client core để nó gửi qua socket
self.send_move_to_server(move)
        # Tạm thời vô hiệu hóa nút để tránh spam
        for widget in self.game_frame.winfo_children():
            widget.config(state=tk.DISABLED)
        self.info_label.config(text="Waiting for opponent's move...")

    # --- CÁC HÀM CẬP NHẬT GIAO DIỆN TỪ CLIENT CORE ---
    
    def display_info(self, msg, color="blue"):
        self.info_label.config(text=msg, fg=color)
        
    def update_score(self, you_score, opp_score, opp_name):
        self.score_label.config(text=f"Score: You {you_score} - {opp_name} {opp_score}")
        
    def enable_game_controls(self, enable=True):
        if enable:
            self.game_frame.pack(pady=20)
            for widget in self.game_frame.winfo_children():
                widget.config(state=tk.NORMAL)
        else:
            self.game_frame.pack_forget()@