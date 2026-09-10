from typing import Callable, Union
import customtkinter

from ui.sign_tab import SignTab
from ui.custom_sign_tab import CustomSignTab
from ui.settings_tab import SettingsTab

# Cấu hình giao diện chung
customtkinter.set_appearance_mode("Light")
customtkinter.set_default_color_theme("blue")

customtkinter.ThemeManager.theme["CTkButton"]["corner_radius"] = 4
customtkinter.ThemeManager.theme["CTkFrame"]["corner_radius"] = 0
customtkinter.ThemeManager.theme["CTkEntry"]["corner_radius"] = 4


class App(customtkinter.CTk):

    def __init__(self):
        super().__init__()

        self.title("IDSC eSIGN - Ký Số Tài Liệu PDF")

        # 1. Căn giữa cửa sổ trên màn hình
        window_width = 860
        window_height = 560
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)

        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.minsize(750, 480)

        # 2. Thiết lập lưới chính (2 cột: Sidebar cố định, Content dãn)
        self.grid_columnconfigure(0, weight=0)  # Cột Sidebar
        self.grid_columnconfigure(1, weight=1)  # Cột Content
        self.grid_rowconfigure(0, weight=1)

        # 3. Sidebar bên trái
        self.sidebar_frame = customtkinter.CTkFrame(self, width=200)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.pack_propagate(False)

        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="IDSC eSIGN",
            font=customtkinter.CTkFont(size=18, weight="bold"),
        )
        self.logo_label.pack(padx=20, pady=10)

        # Định cấu hình màu Active / Inactive
        self.active_color = ("#3a7ebf", "#1f538d")  # Màu khi active
        self.inactive_color = "transparent"  # Màu khi không active
        btn_height = 45
        self.text_active_color = "#ffffff"
        self.text_inactive_color = "#000000"

        # Nút 1: Trang chủ (Ký tài liệu)
        self.btn_1 = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Trang chủ",
            height=btn_height,
            corner_radius=0,    
            fg_color=self.inactive_color,
            anchor="w",  # Căn chữ sang trái cho đẹp
            font=customtkinter.CTkFont(family="Arial", size=14),
            command=lambda: self.set_active_button(self.btn_1),
        )
        self.btn_1.pack(fill="x")

        # Nút 2: Mẫu chữ ký
        self.btn_custom_sign = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Mẫu chữ ký",
            height=btn_height,
            corner_radius=0,
            font=customtkinter.CTkFont(family="Arial", size=14),
            fg_color=self.inactive_color,
            anchor="w",
            command=lambda: self.set_active_button(self.btn_custom_sign),
        )
        self.btn_custom_sign.pack(fill="x")

        # Nút 3: Cài đặt
        self.btn_2 = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Cấu hình",
            height=btn_height,
            corner_radius=0,
            font=customtkinter.CTkFont(family="Arial", size=14),
            fg_color=self.inactive_color,
            anchor="w",
            command=lambda: self.set_active_button(self.btn_2),
        )
        self.btn_2.pack(fill="x")

        # Danh sách các nút menu để quản lý trạng thái
        self.menu_buttons = [self.btn_1, self.btn_custom_sign, self.btn_2]

        # 4. Content bên phải
        self.content_frame = customtkinter.CTkFrame(self, fg_color="#ffffff")
        self.content_frame.grid(row=0, column=1, sticky="nsew")

        # Tách các tab thành các class độc lập
        self.tab_home = SignTab(self.content_frame, active_color=self.active_color)
        self.tab_custom_sign = CustomSignTab(self.content_frame)
        self.tab_settings = SettingsTab(self.content_frame)

        # Mặc định kích hoạt nút "Trang chủ" đầu tiên
        self.set_active_button(self.btn_1)

    def set_active_button(self, active_btn):
        """Đổi màu nút được chọn và reset các nút còn lại"""
        for btn in self.menu_buttons:
            if btn == active_btn:
                btn.configure(fg_color=self.active_color, text_color=self.text_active_color)
            else:
                btn.configure(fg_color=self.inactive_color, text_color=self.text_inactive_color)

        # Ẩn toàn bộ các tab trước
        self.tab_home.pack_forget()
        self.tab_custom_sign.pack_forget()
        self.tab_settings.pack_forget()

        # Chuyển đổi hiển thị tab tương ứng
        if active_btn == self.btn_1:
            self.tab_home.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        elif active_btn == self.btn_custom_sign:
            self.tab_custom_sign.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        elif active_btn == self.btn_2:
            self.tab_settings.pack(fill="both", expand=True, padx=20, pady=(0, 15))


if __name__ == "__main__":
    app = App()
    app.mainloop()