from tkinter import messagebox
import customtkinter

from core.config import config


class SettingsTab(customtkinter.CTkFrame):
    """Tab Cài đặt cấu hình TSA và giao diện"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#ffffff", **kwargs)
        self._init_ui()
        self.bind("<Map>", lambda e: self.reload_config())

    def _init_ui(self):
        box = customtkinter.CTkFrame(self, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=0, pady=0)

        inner = customtkinter.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="x", padx=4, pady=4)

        label_tab = customtkinter.CTkLabel(
            inner,
            text="CẤU HÌNH CHUNG",
            font=customtkinter.CTkFont(family="Arial", size=16, weight="bold"),
            text_color="#1a1a1a",
        )
        label_tab.pack(anchor="w", pady=(0, 4))

        lbl_tsa = customtkinter.CTkLabel(
            inner,
            text="Máy chủ TSA (Dấu thời gian):",
            font=customtkinter.CTkFont(family="Arial", size=13, weight="bold"),
            text_color="#1a1a1a",
        )
        lbl_tsa.pack(anchor="w", pady=(0, 4))

        self.entry_tsa = customtkinter.CTkEntry(inner, height=32)
        self.entry_tsa.pack(fill="x", pady=(0, 12))
        self.reload_config()

        # Nút Áp dụng
        self.btn_apply = customtkinter.CTkButton(
            inner,
            text="Áp dụng",
            width=110,
            height=32,
            font=customtkinter.CTkFont(family="Arial", size=13, weight="bold"),
            command=self.apply_settings,
        )
        self.btn_apply.pack(anchor="w", pady=(0, 18))

        lbl_info = customtkinter.CTkLabel(
            inner,
            text="Phần mềm IDSC eSign v1.0\nHỗ trợ ký số.",
            font=customtkinter.CTkFont(family="Arial", size=12),
            text_color="#666666",
            justify="left",
        )
        lbl_info.pack(anchor="w")

    def reload_config(self):
        """Khôi phục lại giá trị input từ cấu hình đã lưu trong conf.ini"""
        config.load()
        self.entry_tsa.delete(0, "end")
        self.entry_tsa.insert(0, config.tsa_url)

    def get_tsa_url(self) -> str:
        return self.entry_tsa.get().strip()

    def apply_settings(self):
        """Lưu cấu hình vào conf.ini, nạp lại global config và hiển thị overlay chặn cửa sổ chính"""
        new_tsa = self.entry_tsa.get().strip()
        if not new_tsa:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập địa chỉ máy chủ TSA.")
            return

        self._show_overlay_loading(new_tsa)


    def _show_overlay_loading(self, new_tsa: str):
        root = self.winfo_toplevel()

        # 1. Overlay frame phủ toàn bộ cửa sổ chính (thay thế Toplevel)
        # Bắt sự kiện click để chuột không xuyên xuống các widget phía dưới
        overlay = customtkinter.CTkFrame(root, fg_color="#f1f1f1", corner_radius=0)
        overlay.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        overlay.lift()  # Đưa lên lớp cao nhất
        overlay.bind("<Button-1>", lambda e: "break")

        # 2. Hộp thoại modal ở trung tâm
        card = customtkinter.CTkFrame(
            overlay,
            width=360,
            height=175,
            fg_color="#ffffff",
            corner_radius=8,
            border_width=1,
            border_color="#d0d7de",
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)  # Giữ kích thước cố định

        # 3. Trạng thái Loading
        title_lbl = customtkinter.CTkLabel(
            card,
            text="Đang áp dụng cấu hình...",
            font=customtkinter.CTkFont(family="Arial", size=15, weight="bold"),
            text_color="#1a1a1a",
        )
        title_lbl.pack(pady=(25, 12))

        progress = customtkinter.CTkProgressBar(card, width=260, height=6, mode="indeterminate")
        progress.pack(pady=(0, 10))
        progress.start()

        sub_lbl = customtkinter.CTkLabel(
            card,
            text="Đang lưu cấu hình...",
            font=customtkinter.CTkFont(family="Arial", size=11),
            text_color="#666666",
        )
        sub_lbl.pack()

        def do_save():
            # Lưu cấu hình
            config.tsa_url = new_tsa
            config.save()
            config.load()

            # Cập nhật giao diện thành công
            progress.stop()
            progress.pack_forget()
            sub_lbl.pack_forget()

            title_lbl.configure(text="✅ Đã lưu cấu hình thành công!", text_color="#2E7D32")

            def close_overlay():
                overlay.destroy()

            btn_close = customtkinter.CTkButton(
                card,
                text="Đóng",
                width=90,
                height=30,
                corner_radius=4,
                font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"),
                command=close_overlay,
            )
            btn_close.pack(pady=(10, 0))

        self.after(500, do_save)