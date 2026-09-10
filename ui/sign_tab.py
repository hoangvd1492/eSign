import os
import threading
from typing import List, Optional, Dict, Any
from tkinter import filedialog, messagebox
import customtkinter

from core.pdf_signer import WindowsTokenSigner, CertItem
from core.config import config


class SignTab(customtkinter.CTkFrame):
    """Tab thực hiện ký số tài liệu PDF"""

    def __init__(self, master, active_color=("#3a7ebf", "#1f538d"), **kwargs):
        super().__init__(master, fg_color="#ffffff", **kwargs)
        self.active_color = active_color

        self.cert_list: List[CertItem] = []
        self.selected_cert: Optional[CertItem] = None
        self.documents: List[Dict[str, Any]] = []

        self._init_ui()

        # Tự động quét chứng thư số sau khi giao diện sẵn sàng
        self.after(200, self.refresh_certificates)

    def _init_ui(self):
        # 1. Khối Chọn Chứng Thư Số
        header_container = customtkinter.CTkFrame(self, fg_color="transparent")
        header_container.pack(fill="x", pady=4)

        # Cột 0 (ComboBox) dãn rộng hết cỡ, cột 1 (Button) vừa với nội dung
        header_container.grid_columnconfigure(0, weight=1)
        header_container.grid_columnconfigure(1, weight=0)

        # --- Hàng 1: Quét chứng thư số ---
        self.cert_combobox = customtkinter.CTkOptionMenu(
            header_container,
            values=["Đang quét chứng thư số..."],
            height=32,
            font=customtkinter.CTkFont(family="Arial", size=12),
            command=self.on_certificate_selected,
        )
        self.cert_combobox.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(4, 4))

        self.btn_refresh = customtkinter.CTkButton(
            header_container,
            text="🔄 Quét CA",
            width=110,
            height=32,
            font=customtkinter.CTkFont(family="Arial", size=12),
            command=self.refresh_certificates,
        )
        self.btn_refresh.grid(row=0, column=1, sticky="e", pady=(4, 4))

        # --- Hàng 2: Quét chữ ký ---
        self.signature_combobox = customtkinter.CTkOptionMenu(
            header_container,
            values=["Đang quét chữ ký..."],
            height=32,
            font=customtkinter.CTkFont(family="Arial", size=12),
        )
        self.signature_combobox.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(4, 4))

        self.btn_refresh_signature = customtkinter.CTkButton(
            header_container,
            text="🔄 Quét Chữ Ký",
            width=110,
            height=32,
            font=customtkinter.CTkFont(family="Arial", size=12),
        )
        self.btn_refresh_signature.grid(row=1, column=1, sticky="e", pady=(4, 4))

        # 2. Khối nút chức năng điều khiển tài liệu
        control_group = customtkinter.CTkFrame(self, fg_color="transparent")
        control_group.pack(fill="x", pady=4)

        # Chia đều 4 cột
        for col in range(4):
            control_group.grid_columnconfigure(col, weight=1)

        self.btn_1 = customtkinter.CTkButton(
            control_group,
            text="📤Tải file",
            height=32,
            text_color="#ffffff",
            command=self.on_upload_files,
        )
        self.btn_1.grid(row=0, column=0, padx=2, pady=4, sticky="ew")

        self.btn_2 = customtkinter.CTkButton(
            control_group,
            text="📁Tải thư mục",
            height=32,
            text_color="#ffffff",
            command=self.on_upload_folder,
        )
        self.btn_2.grid(row=0, column=1, padx=2, pady=4, sticky="ew")

        self.btn_3 = customtkinter.CTkButton(
            control_group,
            text="❌Xóa file",
            height=32,
            fg_color="#FF9966",
            hover_color="#FF6600",
            text_color="#ffffff",
            command=self.on_delete_files,
        )
        self.btn_3.grid(row=0, column=2, padx=2, pady=4, sticky="ew")

        self.btn_4 = customtkinter.CTkButton(
            control_group,
            text="✍️Ký số",
            height=32,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            text_color="#ffffff",
            command=self.on_sign_click,
        )
        self.btn_4.grid(row=0, column=3, padx=2, pady=4, sticky="ew")

        # 4. Thông báo trạng thái - ghim chặt ở cạnh dưới
        self.status_label = customtkinter.CTkLabel(
            self,
            text="Sẵn sàng thực hiện ký số.",
            font=customtkinter.CTkFont(family="Arial", size=12),
            text_color="#666666",
            anchor="w",
        )
        self.status_label.pack(side="bottom", fill="x")

        # 3. ScrollView danh sách tài liệu (chiếm toàn bộ phần giữa)
        self.scroll_frame = customtkinter.CTkScrollableFrame(
            self,
            fg_color="#f8f9fa",
            border_width=1,
            border_color="#e0e0e0",
        )
        self.scroll_frame.pack(fill="both", expand=True, pady=(4, 6))

        self.empty_label = customtkinter.CTkLabel(
            self.scroll_frame,
            text="Chưa có tài liệu nào.\nBấm '📤Tải file' hoặc '📁Tải thư mục' để thêm tài liệu cần ký.",
            font=customtkinter.CTkFont(family="Arial", size=13),
            text_color="#888888",
        )
        self.empty_label.pack(pady=40)

    def on_upload_files(self):
        """Chọn 1 hoặc nhiều file PDF và thêm vào danh sách"""
        files = filedialog.askopenfilenames(
            title="Chọn các file PDF cần ký",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if files:
            self.add_documents(list(files))

    def on_upload_folder(self):
        """Chọn thư mục và quét toàn bộ các file PDF bên trong"""
        folder = filedialog.askdirectory(title="Chọn thư mục chứa file PDF")
        if folder:
            pdf_files = []
            for root_dir, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        pdf_files.append(os.path.join(root_dir, f))
            if pdf_files:
                self.add_documents(pdf_files)
            else:
                messagebox.showinfo("Thông báo", "Không tìm thấy file PDF nào trong thư mục đã chọn.")

    def add_documents(self, paths: List[str]):
        """Thêm các file PDF vào danh sách hiện tại (giữ nguyên các file cũ, không xóa)"""
        existing_paths = {doc["path"] for doc in self.documents}
        added_count = 0

        for p in paths:
            norm_path = os.path.normpath(p)
            if norm_path in existing_paths:
                continue

            if not self.documents:
                self.empty_label.pack_forget()

            doc_info = {
                "path": norm_path,
                "name": os.path.basename(norm_path),
            }

            row = customtkinter.CTkFrame(
                self.scroll_frame,
                fg_color="#ffffff",
                border_width=1,
                border_color="#e5e7eb",
                corner_radius=4,
            )
            row.pack(fill="x", pady=2, padx=2)

            # Icon tài liệu
            icon_lbl = customtkinter.CTkLabel(
                row,
                text="📄",
                font=customtkinter.CTkFont(size=20),
            )
            icon_lbl.pack(side="left", padx=(10, 6))

            # Nút xóa nhanh từng dòng
            btn_remove = customtkinter.CTkButton(
                row,
                text="✕",
                width=26,
                height=26,
                fg_color="transparent",
                text_color="#999999",
                hover_color="#fee2e2",
                font=customtkinter.CTkFont(size=12, weight="bold"),
                command=lambda filepath=norm_path: self.remove_document(filepath),
            )
            btn_remove.pack(side="right", padx=(4, 8))

            # Khối thông tin: Tên file, URI, và Trạng thái
            info_box = customtkinter.CTkFrame(row, fg_color="transparent")
            info_box.pack(side="left", fill="x", expand=True, pady=4)

            name_lbl = customtkinter.CTkLabel(
                info_box,
                text=doc_info["name"],
                font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"),
                text_color="#1a1a1a",
                anchor="w",
                height=16,
            )
            name_lbl.pack(fill="x", anchor="w")

            uri_lbl = customtkinter.CTkLabel(
                info_box,
                text=doc_info["path"],
                font=customtkinter.CTkFont(family="Arial", size=10),
                text_color="#666666",
                anchor="w",height=16,
            )
            uri_lbl.pack(fill="x", anchor="w")

            status_lbl = customtkinter.CTkLabel(
                info_box,
                text="Trạng thái: Chờ ký",
                font=customtkinter.CTkFont(family="Arial", size=10),
                text_color="#888888",
                anchor="w",height=16,
            )
            status_lbl.pack(fill="x", anchor="w")

            doc_info["frame"] = row
            doc_info["status_lbl"] = status_lbl
            self.documents.append(doc_info)
            existing_paths.add(norm_path)
            added_count += 1

        self.status_label.configure(
            text=f"Đã thêm {added_count} file mới. Tổng cộng: {len(self.documents)} tài liệu.",
            text_color="#1f538d",
        )

    def update_doc_status(self, doc: Dict[str, Any], text: str, text_color: str):
        """Cập nhật text trạng thái của tài liệu"""
        lbl = doc.get("status_lbl")
        if lbl and lbl.winfo_exists():
            lbl.configure(text=text, text_color=text_color)

    def remove_document(self, path: str):
        """Xóa một tài liệu cụ thể khỏi danh sách"""
        for doc in list(self.documents):
            if doc["path"] == path:
                doc["frame"].destroy()
                self.documents.remove(doc)
                break
        if not self.documents:
            self.empty_label.pack(pady=40)
        self.status_label.configure(
            text=f"Danh sách hiện có {len(self.documents)} tài liệu.",
            text_color="#666666",
        )

    def on_delete_files(self):
        """Xóa toàn bộ file trong danh sách không cần select"""
        if not self.documents:
            return

        for doc in list(self.documents):
            doc["frame"].destroy()
        self.documents.clear()
        self.empty_label.pack(pady=40)
        self.status_label.configure(
            text="Đã xóa toàn bộ danh sách tài liệu.",
            text_color="#D32F2F",
        )

    def on_sign_click(self):
        """Thực hiện ký số các tài liệu trong danh sách"""
        if not self.selected_cert:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn chứng thư số trước khi ký.")
            return

        if not self.documents:
            messagebox.showwarning("Cảnh báo", "Vui lòng tải lên ít nhất 1 tài liệu để ký.")
            return

        docs_to_sign = list(self.documents)

        # Đặt lại trạng thái ban đầu cho toàn bộ danh sách
        for d in docs_to_sign:
            self.update_doc_status(d, "Trạng thái: Chờ ký", "#888888")

        self.btn_4.configure(state="disabled", text="ĐANG KÝ...")
        self.status_label.configure(
            text=f"Bắt đầu ký {len(docs_to_sign)} tài liệu... Vui lòng nhập mã PIN nếu có yêu cầu.",
            text_color="#1f538d",
        )

        def sign_worker():
            success_count = 0
            error_list = []
            tsa_url = config.tsa_url

            for idx, doc in enumerate(docs_to_sign, start=1):
                input_path = doc["path"]
                dir_name, base_name = os.path.split(input_path)
                name, ext = os.path.splitext(base_name)
                output_path = os.path.join(dir_name, f"{name}_signed{ext}")

                self.after(0, lambda d=doc, i=idx, n=doc["name"]: (
                    self.update_doc_status(d, "Trạng thái: Đang ký...", "#1f538d"),
                    self.status_label.configure(
                        text=f"Đang ký ({i}/{len(docs_to_sign)}): {n}...",
                        text_color="#1f538d",
                    )
                ))

                try:
                    WindowsTokenSigner.sign_pdf(
                        cert_item=self.selected_cert,
                        input_pdf_path=input_path,
                        output_pdf_path=output_path,
                        tsa_url=tsa_url,
                    )
                    success_count += 1
                    self.after(0, lambda d=doc: self.update_doc_status(d, "Trạng thái: ✓ Đã ký", "#2E7D32"))
                except Exception as e:
                    error_list.append(f"{doc['name']}: {str(e)}")
                    err_brief = str(e).split("\n")[0][:45]
                    self.after(0, lambda d=doc, err=err_brief: self.update_doc_status(d, f"Trạng thái: ✕ Thất bại ({err})", "#D32F2F"))

            def finish():
                self.btn_4.configure(state="normal", text="✍️Ký số")
                if not error_list:
                    self.status_label.configure(
                        text=f"✅ Ký thành công toàn bộ {success_count} tài liệu!",
                        text_color="#2E7D32",
                    )
                    messagebox.showinfo(
                        "Thành công",
                        f"Đã ký thành công {success_count}/{len(docs_to_sign)} tài liệu!",
                    )
                else:
                    self.status_label.configure(
                        text=f"⚠️ Ký xong {success_count}/{len(docs_to_sign)} file. Có {len(error_list)} file lỗi.",
                        text_color="#D32F2F",
                    )
                    err_msg = "\n".join(error_list[:5])
                    if len(error_list) > 5:
                        err_msg += f"\n... và {len(error_list) - 5} lỗi khác."
                    messagebox.showwarning(
                        "Kết quả ký số",
                        f"Ký thành công: {success_count}\nLỗi:\n{err_msg}",
                    )

            self.after(0, finish)

        threading.Thread(target=sign_worker, daemon=True).start()

    def refresh_certificates(self):
        """Quét lại danh sách chứng thư số từ Windows Certificate Store / USB Token"""
        self.status_label.configure(text="Đang quét chứng thư số từ USB Token...", text_color="#1f538d")
        self.btn_refresh.configure(state="disabled")

        def worker():
            certs = WindowsTokenSigner.list_certificates()
            self.after(0, lambda: self._on_certificates_loaded(certs))

        threading.Thread(target=worker, daemon=True).start()

    def _on_certificates_loaded(self, certs: List[CertItem]):
        self.cert_list = certs
        self.btn_refresh.configure(state="normal")

        if not certs:
            self.cert_combobox.configure(values=["[Không tìm thấy chứng thư số]"])
            self.cert_combobox.set("[Không tìm thấy chứng thư số]")
            self.selected_cert = None
            self.status_label.configure(text="Không tìm thấy chứng thư số.", text_color="#D32F2F")
            return

        options = [f"[{c.index}] {c.subject}" for c in certs]
        self.cert_combobox.configure(values=options)
        self.cert_combobox.set(options[0])
        self.selected_cert = certs[0]
        self.status_label.configure(text=f"Đã tìm thấy {len(certs)} chứng thư số khả dụng.", text_color="#2E7D32")

    def on_certificate_selected(self, choice_text: str):
        for c in self.cert_list:
            if choice_text.startswith(f"[{c.index}]"):
                self.selected_cert = c
                break
