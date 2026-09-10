import os
from tkinter import filedialog, messagebox
from typing import Dict, Any, Optional, Callable
import customtkinter


class SignatureModal(customtkinter.CTkToplevel):
    """Cửa sổ Top-level cấu hình mẫu chữ ký kèm trang PDF giả lập trực quan vị trí & kích thước"""

    PAGE_WIDTH = 320
    PAGE_HEIGHT = 450
    DEFAULT_BOX_WIDTH = 130
    DEFAULT_BOX_HEIGHT = 55

    def __init__(
        self,
        parent,
        title: str = "Tạo mẫu chữ ký mới",
        mode: str = "create",
        initial_data: Optional[Dict[str, Any]] = None,
        on_save: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        super().__init__(parent)

        self.parent = parent
        self.mode = mode
        self.initial_data = initial_data or {}
        self.on_save = on_save

        self.title(title)
        self.resizable(False, False)

        # Kích thước khung chữ ký ban đầu
        self.box_width = int(self.initial_data.get("box_width", self.DEFAULT_BOX_WIDTH))
        self.box_height = int(self.initial_data.get("box_height", self.DEFAULT_BOX_HEIGHT))

        # Kích thước modal
        modal_width = 890
        modal_height = 600
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()

        pos_x = max(0, parent_x + int((parent_w - modal_width) / 2))
        pos_y = max(0, parent_y + int((parent_h - modal_height) / 2))
        self.geometry(f"{modal_width}x{modal_height}+{pos_x}+{pos_y}")

        # Modal attributes
        self.transient(parent)
        self.grab_set()

        # Dữ liệu kéo thả di chuyển & thay đổi kích thước
        self._drag_data = {"x": 0, "y": 0}
        self._resize_start = {"x": 0, "y": 0, "w": self.box_width, "h": self.box_height}
        self.current_pos_x = 0
        self.current_pos_y = 0

        self._init_ui()

    def _init_ui(self):
        # Khung chính chia làm 2 cột: Trái (PDF giả lập) - Phải (Form cấu hình)
        main_layout = customtkinter.CTkFrame(self, fg_color="#f8f9fa", corner_radius=0)
        main_layout.pack(fill="both", expand=True)

        # ---------------------------------------------------------------------
        # CỘT TRÁI: Trang PDF giả lập trực quan vị trí & kích thước chữ ký
        # ---------------------------------------------------------------------
        left_panel = customtkinter.CTkFrame(main_layout, fg_color="transparent", width=370)
        left_panel.pack(side="left", fill="both", padx=(16, 8), pady=12)
        left_panel.pack_propagate(False)

        lbl_pdf_title = customtkinter.CTkLabel(
            left_panel,
            text="Trực quan vị trí & kích thước trên trang PDF",
            font=customtkinter.CTkFont(family="Arial", size=13, weight="bold"),
            text_color="#1a1a1a",
        )
        lbl_pdf_title.pack(anchor="w", pady=(0, 2))

        lbl_pdf_sub = customtkinter.CTkLabel(
            left_panel,
            text="💡 Kéo ô để di chuyển | Kéo góc xanh ⤡ hoặc mép để chỉnh cỡ",
            font=customtkinter.CTkFont(family="Arial", size=10),
            text_color="#666666",
        )
        lbl_pdf_sub.pack(anchor="w", pady=(0, 6))

        # Khung đại diện cho tờ giấy A4
        self.pdf_page = customtkinter.CTkFrame(
            left_panel,
            width=self.PAGE_WIDTH,
            height=self.PAGE_HEIGHT,
            fg_color="#ffffff",
            border_color="#cbd5e1",
            border_width=1,
            corner_radius=4,
        )
        self.pdf_page.pack(anchor="center")
        self.pdf_page.pack_propagate(False)

        # Vẽ nội dung giả lập của văn bản A4
        self._draw_mock_document()

        # Khung chữ ký có thể kéo thả di chuyển & co dãn
        self.sig_box = customtkinter.CTkFrame(
            self.pdf_page,
            width=self.box_width,
            height=self.box_height,
            fg_color="#eff6ff",
            border_color="#2563eb",
            border_width=2,
            corner_radius=4,
        )
        self.sig_box.pack_propagate(False)

        self.lbl_sig_preview_icon = customtkinter.CTkLabel(
            self.sig_box,
            text="✍️",
            font=customtkinter.CTkFont(size=14),
        )
        self.lbl_sig_preview_icon.pack(side="left", padx=(6, 4))

        sig_preview_text_box = customtkinter.CTkFrame(self.sig_box, fg_color="transparent")
        sig_preview_text_box.pack(side="left", fill="both", expand=True, pady=4)

        self.lbl_sig_preview_name = customtkinter.CTkLabel(
            sig_preview_text_box,
            text=self.initial_data.get("name") or "Chữ ký mẫu",
            font=customtkinter.CTkFont(family="Arial", size=10, weight="bold"),
            text_color="#1d4ed8",
            anchor="w",
        )
        self.lbl_sig_preview_name.pack(fill="x", anchor="w")

        self.lbl_sig_preview_desc = customtkinter.CTkLabel(
            sig_preview_text_box,
            text="Chữ ký điện tử",
            font=customtkinter.CTkFont(family="Arial", size=8),
            text_color="#3b82f6",
            anchor="w",
        )
        self.lbl_sig_preview_desc.pack(fill="x", anchor="w")

        # Nút kéo góc co dãn (Bottom-Right Corner Resize Handle)
        self.resize_handle = customtkinter.CTkLabel(
            self.sig_box,
            text="⤡",
            width=18,
            height=18,
            fg_color="#2563eb",
            text_color="#ffffff",
            corner_radius=3,
            font=customtkinter.CTkFont(size=11, weight="bold"),
            cursor="size_nw_se",
        )
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se", x=-1, y=-1)
        self.resize_handle.bind("<Button-1>", self._on_resize_corner_start)
        self.resize_handle.bind("<B1-Motion>", self._on_resize_corner_motion)

        # Mép kéo chỉnh chiều rộng (Right Edge Resize Handle)
        self.resize_edge_r = customtkinter.CTkFrame(
            self.sig_box,
            width=6,
            fg_color="#93c5fd",
            corner_radius=0,
            cursor="size_we",
        )
        self.resize_edge_r.place(relx=1.0, rely=0.0, relheight=0.72, anchor="ne")
        self.resize_edge_r.bind("<Button-1>", self._on_resize_width_start)
        self.resize_edge_r.bind("<B1-Motion>", self._on_resize_width_motion)

        # Mép kéo chỉnh chiều cao (Bottom Edge Resize Handle)
        self.resize_edge_b = customtkinter.CTkFrame(
            self.sig_box,
            height=6,
            fg_color="#93c5fd",
            corner_radius=0,
            cursor="size_ns",
        )
        self.resize_edge_b.place(relx=0.0, rely=1.0, relwidth=0.72, anchor="sw")
        self.resize_edge_b.bind("<Button-1>", self._on_resize_height_start)
        self.resize_edge_b.bind("<B1-Motion>", self._on_resize_height_motion)

        # Gắn sự kiện kéo thả di chuyển cho khung chữ ký và các thành phần bên trong
        self._bind_drag(self.sig_box)
        self._bind_drag(self.lbl_sig_preview_icon)
        self._bind_drag(sig_preview_text_box)
        self._bind_drag(self.lbl_sig_preview_name)
        self._bind_drag(self.lbl_sig_preview_desc)

        # Hỗ trợ con lăn chuột (MouseWheel) để phóng to/thu nhỏ nhanh kích thước ô chữ ký
        self._bind_mousewheel(self.sig_box)
        self._bind_mousewheel(self.lbl_sig_preview_icon)
        self._bind_mousewheel(sig_preview_text_box)
        self._bind_mousewheel(self.lbl_sig_preview_name)
        self._bind_mousewheel(self.lbl_sig_preview_desc)

        # Các nút định vị nhanh bên dưới trang PDF (Hàng 1)
        pos_btn_frame = customtkinter.CTkFrame(left_panel, fg_color="transparent")
        pos_btn_frame.pack(fill="x", pady=(8, 2))

        btn_br = customtkinter.CTkButton(
            pos_btn_frame,
            text="Góc dưới phải",
            height=25,
            font=customtkinter.CTkFont(family="Arial", size=10),
            fg_color="#e2e8f0",
            text_color="#1e293b",
            hover_color="#cbd5e1",
            command=self._pos_bottom_right,
        )
        btn_br.pack(side="left", expand=True, fill="x", padx=(0, 2))

        btn_bl = customtkinter.CTkButton(
            pos_btn_frame,
            text="Góc dưới trái",
            height=25,
            font=customtkinter.CTkFont(family="Arial", size=10),
            fg_color="#e2e8f0",
            text_color="#1e293b",
            hover_color="#cbd5e1",
            command=self._pos_bottom_left,
        )
        btn_bl.pack(side="left", expand=True, fill="x", padx=2)

        btn_center = customtkinter.CTkButton(
            pos_btn_frame,
            text="Chính giữa",
            height=25,
            font=customtkinter.CTkFont(family="Arial", size=10),
            fg_color="#e2e8f0",
            text_color="#1e293b",
            hover_color="#cbd5e1",
            command=self._pos_center,
        )
        btn_center.pack(side="left", expand=True, fill="x", padx=(2, 0))

        # Các nút chọn cỡ nhanh bên dưới trang PDF (Hàng 2)
        size_btn_frame = customtkinter.CTkFrame(left_panel, fg_color="transparent")
        size_btn_frame.pack(fill="x", pady=(2, 0))

        btn_s = customtkinter.CTkButton(
            size_btn_frame,
            text="Cỡ nhỏ (100×45)",
            height=25,
            font=customtkinter.CTkFont(family="Arial", size=10),
            fg_color="#f1f5f9",
            text_color="#475569",
            hover_color="#e2e8f0",
            command=lambda: self._set_box_size(100, 45),
        )
        btn_s.pack(side="left", expand=True, fill="x", padx=(0, 2))

        btn_m = customtkinter.CTkButton(
            size_btn_frame,
            text="Cỡ vừa (130×55)",
            height=25,
            font=customtkinter.CTkFont(family="Arial", size=10),
            fg_color="#f1f5f9",
            text_color="#475569",
            hover_color="#e2e8f0",
            command=lambda: self._set_box_size(130, 55),
        )
        btn_m.pack(side="left", expand=True, fill="x", padx=2)

        btn_l = customtkinter.CTkButton(
            size_btn_frame,
            text="Cỡ lớn (160×70)",
            height=25,
            font=customtkinter.CTkFont(family="Arial", size=10),
            fg_color="#f1f5f9",
            text_color="#475569",
            hover_color="#e2e8f0",
            command=lambda: self._set_box_size(160, 70),
        )
        btn_l.pack(side="left", expand=True, fill="x", padx=(2, 0))

        # ---------------------------------------------------------------------
        # CỘT PHẢI: Form cấu hình thông tin mẫu chữ ký
        # ---------------------------------------------------------------------
        right_panel = customtkinter.CTkFrame(
            main_layout,
            fg_color="#ffffff",
            border_color="#e2e8f0",
            border_width=1,
            corner_radius=4,
        )
        right_panel.pack(side="right", fill="both", expand=True, padx=(8, 16), pady=12)

        form_container = customtkinter.CTkFrame(right_panel, fg_color="transparent")
        form_container.pack(fill="both", expand=True, padx=16, pady=12)

        # Tiêu đề Form
        header_text = "TẠO MẪU CHỮ KÝ MỚI" if self.mode == "create" else "CHỈNH SỬA MẪU CHỮ KÝ"
        lbl_form_title = customtkinter.CTkLabel(
            form_container,
            text=header_text,
            font=customtkinter.CTkFont(family="Arial", size=15, weight="bold"),
            text_color="#1a1a1a",
        )
        lbl_form_title.pack(anchor="w", pady=(0, 10))

        # 1. Tên mẫu chữ ký
        lbl_name = customtkinter.CTkLabel(
            form_container,
            text="Tên mẫu chữ ký (*):",
            font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"),
            text_color="#333333",
        )
        lbl_name.pack(anchor="w", pady=(2, 1))

        self.entry_name = customtkinter.CTkEntry(
            form_container,
            placeholder_text="Ví dụ: Chữ ký phê duyệt, Chữ ký Giám đốc...",
            height=32,
        )
        self.entry_name.pack(fill="x", pady=(0, 8))
        if "name" in self.initial_data:
            self.entry_name.insert(0, self.initial_data["name"])
        self.entry_name.bind("<KeyRelease>", self._on_name_change)

        # 2. Trang áp dụng ký
        lbl_page = customtkinter.CTkLabel(
            form_container,
            text="Trang áp dụng ký:",
            font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"),
            text_color="#333333",
        )
        lbl_page.pack(anchor="w", pady=(2, 1))

        self.page_options = [
            "Trang cuối cùng (Khuyên dùng)",
            "Trang đầu tiên",
            "Tất cả các trang",
        ]
        self.page_combobox = customtkinter.CTkOptionMenu(
            form_container,
            values=self.page_options,
            height=32,
            font=customtkinter.CTkFont(family="Arial", size=12),
        )
        self.page_combobox.pack(fill="x", pady=(0, 8))
        if "page_option" in self.initial_data and self.initial_data["page_option"] in self.page_options:
            self.page_combobox.set(self.initial_data["page_option"])

        # 3. Kiểu hiển thị chữ ký
        lbl_type = customtkinter.CTkLabel(
            form_container,
            text="Kiểu hiển thị:",
            font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"),
            text_color="#333333",
        )
        lbl_type.pack(anchor="w", pady=(2, 1))

        self.type_options = [
            "Hình ảnh con dấu / chữ ký (Scan, PNG)",
            "Chỉ thông tin văn bản chứng thư số",
            "Cả hình ảnh và thông tin văn bản",
        ]
        self.type_combobox = customtkinter.CTkOptionMenu(
            form_container,
            values=self.type_options,
            height=32,
            font=customtkinter.CTkFont(family="Arial", size=12),
            command=self._on_type_changed,
        )
        self.type_combobox.pack(fill="x", pady=(0, 8))
        if "type" in self.initial_data and self.initial_data["type"] in self.type_options:
            self.type_combobox.set(self.initial_data["type"])

        # 4. File hình ảnh chữ ký (nếu có)
        self.lbl_image = customtkinter.CTkLabel(
            form_container,
            text="Đường dẫn file ảnh chữ ký:",
            font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"),
            text_color="#333333",
        )
        self.lbl_image.pack(anchor="w", pady=(2, 1))

        self.image_row = customtkinter.CTkFrame(form_container, fg_color="transparent")
        self.image_row.pack(fill="x", pady=(0, 8))
        self.image_row.grid_columnconfigure(0, weight=1)
        self.image_row.grid_columnconfigure(1, weight=0)

        self.entry_image_path = customtkinter.CTkEntry(
            self.image_row,
            placeholder_text="Chọn file ảnh PNG/JPG...",
            height=32,
        )
        self.entry_image_path.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        if "image_path" in self.initial_data:
            self.entry_image_path.insert(0, self.initial_data["image_path"])

        self.btn_browse_img = customtkinter.CTkButton(
            self.image_row,
            text="📁 Chọn ảnh",
            width=85,
            height=32,
            text_color="#ffffff",
            command=self._browse_image,
        )
        self.btn_browse_img.grid(row=0, column=1, sticky="e")

        # 5. Lý do ký (Reason)
        lbl_reason = customtkinter.CTkLabel(
            form_container,
            text="Lý do ký (Reason):",
            font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"),
            text_color="#333333",
        )
        lbl_reason.pack(anchor="w", pady=(2, 1))

        self.entry_reason = customtkinter.CTkEntry(
            form_container,
            placeholder_text="Ví dụ: Phê duyệt văn bản, Xác nhận hợp đồng...",
            height=32,
        )
        self.entry_reason.pack(fill="x", pady=(0, 8))
        if "reason" in self.initial_data:
            self.entry_reason.insert(0, self.initial_data["reason"])

        # 6. Thông tin tọa độ & kích thước hiển thị (Read-only status card)
        coord_box = customtkinter.CTkFrame(form_container, fg_color="#f1f5f9", corner_radius=4)
        coord_box.pack(fill="x", pady=(2, 10), padx=0)

        self.lbl_coord = customtkinter.CTkLabel(
            coord_box,
            text=f"Tọa độ: X = 0%, Y = 0% | Kích thước: {self.box_width}×{self.box_height}px",
            font=customtkinter.CTkFont(family="Arial", size=11, weight="bold"),
            text_color="#1e293b",
        )
        self.lbl_coord.pack(pady=6)

        # 7. Checkbox tùy chọn
        self.check_show_time = customtkinter.CTkCheckBox(
            form_container,
            text="Hiển thị thời gian ký (Signing Time)",
            font=customtkinter.CTkFont(family="Arial", size=11),
        )
        self.check_show_time.pack(anchor="w", pady=(2, 12))
        if self.initial_data.get("show_time", True):
            self.check_show_time.select()
        else:
            self.check_show_time.deselect()

        # 8. Các nút Lưu / Hủy
        action_row = customtkinter.CTkFrame(form_container, fg_color="transparent")
        action_row.pack(fill="x", side="bottom")

        btn_cancel = customtkinter.CTkButton(
            action_row,
            text="Hủy",
            width=85,
            height=34,
            fg_color="#9E9E9E",
            hover_color="#757575",
            text_color="#ffffff",
            font=customtkinter.CTkFont(family="Arial", size=12),
            command=self.destroy,
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        btn_save = customtkinter.CTkButton(
            action_row,
            text="💾 Lưu mẫu chữ ký",
            width=135,
            height=34,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            text_color="#ffffff",
            font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"),
            command=self._save_signature,
        )
        btn_save.pack(side="right")

        # Khởi tạo vị trí ban đầu
        self._init_signature_position()
        self._on_type_changed(self.type_combobox.get())

    def _draw_mock_document(self):
        """Vẽ các đường kẻ giả lập văn bản A4"""
        doc_header = customtkinter.CTkFrame(self.pdf_page, fg_color="transparent")
        doc_header.pack(fill="x", padx=16, pady=(16, 12))

        # Tiêu đề giả lập
        bar_title = customtkinter.CTkFrame(doc_header, fg_color="#94a3b8", height=10, width=170, corner_radius=2)
        bar_title.pack(anchor="center", pady=(0, 4))
        bar_sub = customtkinter.CTkFrame(doc_header, fg_color="#cbd5e1", height=6, width=110, corner_radius=2)
        bar_sub.pack(anchor="center")

        # Nội dung các đoạn văn bản giả lập
        doc_body = customtkinter.CTkFrame(self.pdf_page, fg_color="transparent")
        doc_body.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        line_configs = [
            (280, 5), (260, 5), (275, 5), (190, 5),
            (280, 5), (270, 5), (285, 5), (210, 5),
            (280, 5), (265, 5), (275, 5), (180, 5),
            (280, 5), (270, 5), (260, 5), (140, 5),
        ]
        for w, h in line_configs:
            line_bar = customtkinter.CTkFrame(doc_body, fg_color="#f1f5f9", height=h, width=w, corner_radius=2)
            line_bar.pack(anchor="w", pady=3)

    def _set_box_size(self, w: int, h: int):
        """Cập nhật kích thước khung chữ ký và điều chỉnh vị trí phù hợp"""
        max_w = min(240, self.PAGE_WIDTH - self.current_pos_x)
        max_h = min(150, self.PAGE_HEIGHT - self.current_pos_y)
        self.box_width = max(65, min(max_w, int(w)))
        self.box_height = max(30, min(max_h, int(h)))

        self.sig_box.configure(width=self.box_width, height=self.box_height)
        # Giữ vị trí trong giới hạn khung trang
        self._set_box_position(self.current_pos_x, self.current_pos_y)

    # ------------------ KÉO GÓC CO DÃN ------------------
    def _on_resize_corner_start(self, event):
        self._resize_start = {
            "x": event.x_root,
            "y": event.y_root,
            "w": self.box_width,
            "h": self.box_height,
        }

    def _on_resize_corner_motion(self, event):
        dw = event.x_root - self._resize_start["x"]
        dh = event.y_root - self._resize_start["y"]
        self._set_box_size(self._resize_start["w"] + dw, self._resize_start["h"] + dh)

    # ------------------ KÉO MÉP PHẢI (RỘNG) ------------------
    def _on_resize_width_start(self, event):
        self._resize_start = {
            "x": event.x_root,
            "y": event.y_root,
            "w": self.box_width,
            "h": self.box_height,
        }

    def _on_resize_width_motion(self, event):
        dw = event.x_root - self._resize_start["x"]
        self._set_box_size(self._resize_start["w"] + dw, self.box_height)

    # ------------------ KÉO MÉP DƯỚI (CAO) ------------------
    def _on_resize_height_start(self, event):
        self._resize_start = {
            "x": event.x_root,
            "y": event.y_root,
            "w": self.box_width,
            "h": self.box_height,
        }

    def _on_resize_height_motion(self, event):
        dh = event.y_root - self._resize_start["y"]
        self._set_box_size(self.box_width, self._resize_start["h"] + dh)

    # ------------------ PHÓNG TO / THU NHỎ BẰNG CON LĂN CHUỘT ------------------
    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mouse_wheel)

    def _on_mouse_wheel(self, event):
        delta = 6 if event.delta > 0 else -6
        new_w = self.box_width + delta * 2
        new_h = self.box_height + delta
        self._set_box_size(new_w, new_h)

    # ------------------ ĐỊNH VỊ VỊ TRÍ ------------------
    def _init_signature_position(self):
        """Đặt vị trí ban đầu của chữ ký từ dữ liệu cũ hoặc mặc định góc dưới phải"""
        init_pct_x = self.initial_data.get("pos_x_pct")
        init_pct_y = self.initial_data.get("pos_y_pct")

        if init_pct_x is not None and init_pct_y is not None:
            x = int((float(init_pct_x) / 100.0) * self.PAGE_WIDTH)
            y = int((float(init_pct_y) / 100.0) * self.PAGE_HEIGHT)
            self._set_box_position(x, y)
        else:
            self._pos_bottom_right()

    def _set_box_position(self, x: int, y: int):
        max_x = self.PAGE_WIDTH - self.box_width
        max_y = self.PAGE_HEIGHT - self.box_height
        x = max(0, min(x, max_x))
        y = max(0, min(y, max_y))

        self.current_pos_x = x
        self.current_pos_y = y
        self.sig_box.place(x=x, y=y)

        # Tính tỷ lệ % so với khổ trang
        pct_x = round((x / self.PAGE_WIDTH) * 100, 1)
        pct_y = round((y / self.PAGE_HEIGHT) * 100, 1)
        self.lbl_coord.configure(
            text=f"Tọa độ: X = {pct_x}% | Y = {pct_y}% | Kích thước: {self.box_width}×{self.box_height}px"
        )

    def _pos_bottom_right(self):
        x = self.PAGE_WIDTH - self.box_width - 15
        y = self.PAGE_HEIGHT - self.box_height - 25
        self._set_box_position(x, y)

    def _pos_bottom_left(self):
        x = 15
        y = self.PAGE_HEIGHT - self.box_height - 25
        self._set_box_position(x, y)

    def _pos_center(self):
        x = (self.PAGE_WIDTH - self.box_width) // 2
        y = (self.PAGE_HEIGHT - self.box_height) // 2
        self._set_box_position(x, y)

    # ------------------ KÉO THẢ DI CHUYỂN VỊ TRÍ ------------------
    def _bind_drag(self, widget):
        widget.bind("<Button-1>", self._on_drag_start)
        widget.bind("<B1-Motion>", self._on_drag_motion)

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root

    def _on_drag_motion(self, event):
        dx = event.x_root - self._drag_data["x"]
        dy = event.y_root - self._drag_data["y"]

        new_x = self.current_pos_x + dx
        new_y = self.current_pos_y + dy

        self._set_box_position(new_x, new_y)

        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root

    def _on_name_change(self, event):
        name = self.entry_name.get().strip() or "Chữ ký mẫu"
        if len(name) > 16:
            name = name[:16] + "..."
        self.lbl_sig_preview_name.configure(text=name)

    def _on_type_changed(self, choice: str):
        """Ẩn/hiện trường chọn ảnh tùy thuộc kiểu hiển thị"""
        if choice == "Chỉ thông tin văn bản chứng thư số":
            self.lbl_image.pack_forget()
            self.image_row.pack_forget()
        else:
            self.lbl_image.pack(anchor="w", pady=(2, 1), before=self.entry_reason)
            self.image_row.pack(fill="x", pady=(0, 8), before=self.entry_reason)

    def _browse_image(self):
        """Mở hộp thoại chọn file ảnh chữ ký"""
        path = filedialog.askopenfilename(
            parent=self,
            title="Chọn file ảnh con dấu / chữ ký",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All Files", "*.*")],
        )
        if path:
            self.entry_image_path.delete(0, "end")
            self.entry_image_path.insert(0, os.path.normpath(path))

    def _save_signature(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên mẫu chữ ký.", parent=self)
            self.entry_name.focus()
            return

        sig_type = self.type_combobox.get()
        page_option = self.page_combobox.get()
        image_path = self.entry_image_path.get().strip()
        reason = self.entry_reason.get().strip()
        show_time = bool(self.check_show_time.get())

        # Tính tọa độ theo % và px
        pct_x = round((self.current_pos_x / self.PAGE_WIDTH) * 100, 1)
        pct_y = round((self.current_pos_y / self.PAGE_HEIGHT) * 100, 1)

        data = {
            "name": name,
            "type": sig_type,
            "page_option": page_option,
            "image_path": image_path,
            "reason": reason,
            "pos_x_pct": pct_x,
            "pos_y_pct": pct_y,
            "box_width": self.box_width,
            "box_height": self.box_height,
            "show_time": show_time,
        }

        if self.on_save:
            self.on_save(data)

        self.destroy()