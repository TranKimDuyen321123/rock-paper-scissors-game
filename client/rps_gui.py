#rps_gui.py
import tkinter as tk
from tkinter import messagebox
# Không cần import threading ở đây vì GUI không sử dụng trực tiếp luồng phụ.

# Sử dụng tk.Tk làm cửa sổ chính
class RPSClientGUI(tk.Tk):
    def __init__(self, send_callback, player_name_callback):
        super().__init__()
        self.title("Rock Paper Scissors - Multiplayer")
        self.geometry("450x500") # Mở rộng khung nhìn một chút
        self.resizable(False, False) # Cố định kích thước cửa sổ

        # Callback để gửi data: Hàm này sẽ gọi send_json() trong client core
        self.send_move_to_server = send_callback
        self.get_player_name = player_name_callback
        
        self._setup_initial_ui()

    def _setup_initial_ui(self):
        # Thiết lập màu sắc và font chung
        FONT_TITLE = ('Arial', 18, 'bold')
        FONT_SCORE = ('Arial', 14, 'bold')
        FONT_INFO = ('Arial', 11, 'italic')
        
        # Tiêu đề
        tk.Label(self, text="Kéo Búa Bao - Multiplayer", font=FONT_TITLE, fg="#0056b3").pack(pady=(20, 10))

        # 1. Khung nhập tên và kết nối
        self.name_frame = tk.Frame(self)
        self.name_frame.pack(pady=10)
        tk.Label(self.name_frame, text="Tên bạn:", font=('Arial', 12)).pack(side=tk.LEFT)
        self.name_entry = tk.Entry(self.name_frame, width=20, font=('Arial', 12))
        self.name_entry.pack(side=tk.LEFT, padx=10)
        
        self.connect_btn = tk.Button(
            self.name_frame, 
            text="KẾT NỐI", 
            command=self._connect_action,
            bg="#28a745", # Màu xanh lá
            fg="white", 
            font=('Arial', 10, 'bold'),
            width=10
        )
        self.connect_btn.pack(side=tk.LEFT)
        
        # --- Dòng phân cách ---
        tk.Frame(self, height=1, bg="lightgray").pack(fill='x', padx=20, pady=10)

        # 2. Khung thông tin và điểm số
        self.info_label = tk.Label(self, text="Vui lòng nhập tên và nhấn KẾT NỐI.", fg="blue", font=('Arial', 12))
        self.info_label.pack(pady=(10, 5))
        
        self.score_label = tk.Label(self, text="Điểm: Bạn 0 - Đối thủ 0", font=FONT_SCORE, fg="#333333")
        self.score_label.pack(pady=5)
        
        # Nhãn hiển thị thông tin chi tiết về đối thủ/trò chơi
        self.opponent_info = tk.Label(self, text="", font=FONT_INFO, fg="gray")
        self.opponent_info.pack(pady=5)
        
        # --- Dòng phân cách ---
        tk.Frame(self, height=1, bg="lightgray").pack(fill='x', padx=20, pady=10)

        # 3. Khung nút chơi game
        self.game_frame = tk.Frame(self)
        # Ẩn đi cho đến khi kết nối thành công
        
        # Định nghĩa kiểu nút chơi game
        button_options = {
            'width': 12, 'height': 4, 'font': ('Arial', 12, 'bold'), 
            'fg': 'white', 'relief': tk.RAISED, 'bd': 3
        }
        
        # Nút ROCK
        tk.Button(self.game_frame, text="ROCK (Búa)", command=lambda: self._send_move('rock'), bg="#dc3545", **button_options).pack(side=tk.LEFT, padx=5)
        # Nút PAPER
        tk.Button(self.game_frame, text="PAPER (Bao)", command=lambda: self._send_move('paper'), bg="#ffc107", **button_options).pack(side=tk.LEFT, padx=5)
        # Nút SCISSORS
        tk.Button(self.game_frame, text="SCISSORS (Kéo)", command=lambda: self._send_move('scissors'), bg="#007bff", **button_options).pack(side=tk.LEFT, padx=5)
        
        self.enable_game_controls(False) # Khởi đầu ẩn

    def _connect_action(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Lỗi", "Tên không được để trống.")
            return
        
        # Gọi callback trong client core để bắt đầu kết nối
        self.get_player_name(name)
        self.connect_btn.config(state=tk.DISABLED)
        self.name_entry.config(state=tk.DISABLED)
        self.display_info("Đang kết nối...", color="orange")
        
    def _send_move(self, move):
        # Gửi hành động (move) về client core để nó gửi qua socket
        self.send_move_to_server(move)
        
        # Vô hiệu hóa nút để tránh spam và thông báo chờ
        self.opponent_info.config(text="Đang chờ đối thủ ra đòn...")
        for widget in self.game_frame.winfo_children():
            widget.config(state=tk.DISABLED)
        self.info_label.config(text=f"Bạn đã ra: {move.upper()}")

    # --- CÁC HÀM CẬP NHẬT GIAO DIỆN TỪ CLIENT CORE ---
    
    def display_info(self, msg, color="blue"):
        """Hiển thị thông báo chính."""
        self.info_label.config(text=msg, fg=color)
        
    def update_score(self, you_score, opp_score, opp_name):
        """Cập nhật nhãn điểm số."""
        self.score_label.config(text=f"Điểm: Bạn {you_score} - {opp_name} {opp_score}")
        self.opponent_info.config(text=f"Đang đấu với: {opp_name}") # Cập nhật thông tin đối thủ
        
    def enable_game_controls(self, enable=True):
        """Bật/Tắt và hiển thị/ẩn khung điều khiển trò chơi."""
        if enable:
            self.game_frame.pack(pady=20)
            for widget in self.game_frame.winfo_children():
                widget.config(state=tk.NORMAL)
            self.opponent_info.config(text="Hãy chọn Búa, Kéo, hoặc Bao!")
        else:
            self.game_frame.pack_forget() # Ẩn khung chơi game
            for widget in self.game_frame.winfo_children():
                widget.config(state=tk.DISABLED)