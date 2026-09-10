import os
from tkinter import filedialog, messagebox
from typing import Dict, Any, List, Optional, Callable
import customtkinter
from ui.sign_modal import SignatureModal


class CustomSignTab(customtkinter.CTkFrame):
    """Tab quản lý cấu hình các mẫu chữ ký số"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#ffffff", **kwargs)

        # Danh sách các mẫu chữ ký cấu hình trước (tạm thời để trống)
        self.signatures: List[Dict[str, Any]] = []

        self._init_ui()

    def _init_ui(self):
        # 1. Thanh tiêu đề và nút chức năng phía trên
        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(4, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        # Cột trái: Tiêu đề danh sách
        title_box = customtkinter.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        lbl_title = customtkinter.CTkLabel(
            title_box,
            text="CẤU HÌNH CHỮ KÝ",
            font=customtkinter.CTkFont(family="Arial", size=15, weight="bold"),
            text_color="#1a1a1a",
        )
        lbl_title.pack(anchor="w")

        # Cột phải: Nút Tạo mới
        self.btn_create = customtkinter.CTkButton(
            header_frame,
            text="➕ Tạo mới",
            width=110,
            height=32,
            font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"),
            text_color="#ffffff",
            command=self.open_create_modal,
        )
        self.btn_create.grid(row=0, column=1, sticky="e")

        # 2. ScrollView hiển thị danh sách các mẫu chữ ký
        self.scroll_frame = customtkinter.CTkScrollableFrame(
            self,
            fg_color="#f8f9fa",
            border_width=1,
            border_color="#e0e0e0",
        )
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, 6))

        # Nhãn hiển thị khi danh sách trống
        self.empty_label = customtkinter.CTkLabel(
            self.scroll_frame,
            text="Chưa có mẫu chữ ký nào được cấu hình.\nBấm nút '➕ Tạo mới' để thiết lập mẫu chữ ký.",
            font=customtkinter.CTkFont(family="Arial", size=13),
            text_color="#888888",
            justify="center",
        )
        self.empty_label.pack(pady=60)

        # Trạng thái tổng số mẫu chữ ký ở đáy
        self.status_label = customtkinter.CTkLabel(
            self,
            text="Tổng số: 0 mẫu chữ ký.",
            font=customtkinter.CTkFont(family="Arial", size=12),
            text_color="#666666",
            anchor="w",
        )
        self.status_label.pack(side="bottom", fill="x")

        # Render danh sách ban đầu (trống)
        self.render_signatures()

    def render_signatures(self):
        """Hiển thị lại toàn bộ danh sách chữ ký"""
        # Xóa tất cả widget con trong scroll_frame ngoại trừ empty_label
        for child in self.scroll_frame.winfo_children():
            if child != self.empty_label:
                child.destroy()

        if not self.signatures:
            self.empty_label.pack(pady=60)
            self.status_label.configure(text="Tổng số: 0 mẫu chữ ký.")
            return

        self.empty_label.pack_forget()
        self.status_label.configure(text=f"Tổng số: {len(self.signatures)} mẫu chữ ký.")

        for idx, sig in enumerate(self.signatures):
            row = customtkinter.CTkFrame(
                self.scroll_frame,
                fg_color="#ffffff",
                border_width=1,
                border_color="#e5e7eb",
                corner_radius=4,
            )
            row.pack(fill="x", pady=3, padx=2)

            # Icon chữ ký
            icon_lbl = customtkinter.CTkLabel(
                row,
                text="✍️",
                font=customtkinter.CTkFont(size=22),
            )
            icon_lbl.pack(side="left", padx=(10, 8))

            # Nhóm nút hành động bên phải: Xóa & Sửa
            btn_delete = customtkinter.CTkButton(
                row,
                text="🗑️ Xóa",
                width=65,
                height=28,
                fg_color="#fee2e2",
                hover_color="#fca5a5",
                text_color="#dc2626",
                font=customtkinter.CTkFont(family="Arial", size=11, weight="bold"),
                command=lambda s=sig: self.delete_signature(s),
            )
            btn_delete.pack(side="right", padx=(4, 8), pady=8)

            btn_edit = customtkinter.CTkButton(
                row,
                text="✏️ Sửa",
                width=65,
                height=28,
                fg_color="#e0f2fe",
                hover_color="#bae6fd",
                text_color="#0284c7",
                font=customtkinter.CTkFont(family="Arial", size=11, weight="bold"),
                command=lambda s=sig: self.open_edit_modal(s),
            )
            btn_edit.pack(side="right", padx=(4, 4), pady=8)

            # Khối thông tin mẫu chữ ký
            info_box = customtkinter.CTkFrame(row, fg_color="transparent")
            info_box.pack(side="left", fill="x", expand=True, pady=6)

            name_lbl = customtkinter.CTkLabel(
                info_box,
                text=sig.get("name", "Chưa đặt tên"),
                font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"),
                text_color="#1a1a1a",
                anchor="w",
                height=18,
            )
            name_lbl.pack(fill="x", anchor="w")

            details = f"Kiểu: {sig.get('type', 'N/A')}"
            if sig.get("page_option"):
                details += f" | {sig.get('page_option')}"
            if sig.get("pos_x_pct") is not None and sig.get("pos_y_pct") is not None:
                details += f" (X: {sig['pos_x_pct']}%, Y: {sig['pos_y_pct']}%)"
            if sig.get("reason"):
                details += f" | Lý do: {sig.get('reason')}"
            if sig.get("image_path"):
                details += f" | Ảnh: {os.path.basename(sig.get('image_path'))}"

            desc_lbl = customtkinter.CTkLabel(
                info_box,
                text=details,
                font=customtkinter.CTkFont(family="Arial", size=10),
                text_color="#666666",
                anchor="w",
                height=16,
            )
            desc_lbl.pack(fill="x", anchor="w")

    def open_create_modal(self):
        """Mở cửa sổ top-level để tạo mới mẫu chữ ký"""
        root_window = self.winfo_toplevel()

        def on_save(new_sig: Dict[str, Any]):
            self.signatures.append(new_sig)
            self.render_signatures()

        SignatureModal(
            parent=root_window,
            title="Tạo mẫu chữ ký mới",
            mode="create",
            on_save=on_save,
        )

    def open_edit_modal(self, sig: Dict[str, Any]):
        """Mở cửa sổ top-level để chỉnh sửa mẫu chữ ký đã có"""
        root_window = self.winfo_toplevel()

        def on_save(updated_sig: Dict[str, Any]):
            sig.update(updated_sig)
            self.render_signatures()

        SignatureModal(
            parent=root_window,
            title="Chỉnh sửa mẫu chữ ký",
            mode="edit",
            initial_data=sig,
            on_save=on_save,
        )

    def delete_signature(self, sig: Dict[str, Any]):
        """Xóa mẫu chữ ký khỏi danh sách"""
        name = sig.get("name", "mẫu chữ ký này")
        confirmed = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa '{name}' không?",
            parent=self.winfo_toplevel(),
        )
        if confirmed:
            if sig in self.signatures:
                self.signatures.remove(sig)
                self.render_signatures()
