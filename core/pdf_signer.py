# pdf_signer.py
import ctypes
from ctypes import wintypes
from datetime import datetime
from dataclasses import dataclass
from typing import List

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from pyhanko.sign.signers.pdf_signer import Signer
from pyhanko.sign.timestamps import HTTPTimeStamper
from asn1crypto import algos, x509 as asn1_x509
import hashlib

# Load thư viện Windows CAPI & CNG
crypt32 = ctypes.WinDLL("crypt32.dll", use_last_error=True)
ncrypt = ctypes.WinDLL("ncrypt.dll", use_last_error=True)

CERT_STORE_PROV_SYSTEM_W = 10
CERT_SYSTEM_STORE_CURRENT_USER = 0x00010000
CERT_SYSTEM_STORE_LOCAL_MACHINE = 0x00020000
CERT_KEY_PROV_INFO_PROP_ID = 2
CERT_NAME_SIMPLE_DISPLAY_TYPE = 4
CERT_NAME_ISSUER_FLAG = 0x1
CRYPT_ACQUIRE_PREFER_NCRYPT_FLAG = 0x00020000
BCRYPT_PAD_PKCS1 = 0x00000002

class BCRYPT_PKCS1_PADDING_INFO(ctypes.Structure):
    _fields_ = [
        ("pszAlgId", wintypes.LPCWSTR)
    ]

class CRYPT_INTEGER_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte))
    ]

class CERT_INFO(ctypes.Structure):
    _fields_ = [
        ("dwVersion", wintypes.DWORD),
        ("SerialNumber", CRYPT_INTEGER_BLOB),
        ("SignatureAlgorithm", ctypes.c_byte * 16),
        ("Issuer", CRYPT_INTEGER_BLOB),
        ("NotBefore", wintypes.FILETIME),
        ("NotAfter", wintypes.FILETIME),
    ]

class CERT_CONTEXT(ctypes.Structure):
    _fields_ = [
        ("dwCertEncodingType", wintypes.DWORD),
        ("pbCertEncoded", ctypes.c_void_p),
        ("cbCertEncoded", wintypes.DWORD),
        ("pCertInfo", ctypes.POINTER(CERT_INFO)),
        ("hCertStore", wintypes.HANDLE),
    ]
PCERT_CONTEXT = ctypes.POINTER(CERT_CONTEXT)

class CRYPT_KEY_PROV_INFO(ctypes.Structure):
    _fields_ = [
        ("pwszContainerName", wintypes.LPWSTR),
        ("pwszProvName", wintypes.LPWSTR),
        ("dwProvType", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("cProvParam", wintypes.DWORD),
        ("rgProvParam", ctypes.c_void_p),
        ("dwKeySpec", wintypes.DWORD),
    ]

crypt32.CertOpenStore.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.HANDLE, wintypes.DWORD, ctypes.c_wchar_p]
crypt32.CertOpenStore.restype = wintypes.HANDLE
crypt32.CertEnumCertificatesInStore.argtypes = [wintypes.HANDLE, PCERT_CONTEXT]
crypt32.CertEnumCertificatesInStore.restype = PCERT_CONTEXT
crypt32.CertDuplicateCertificateContext.argtypes = [PCERT_CONTEXT]
crypt32.CertDuplicateCertificateContext.restype = PCERT_CONTEXT
crypt32.CertGetCertificateContextProperty.argtypes = [PCERT_CONTEXT, wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
crypt32.CertGetCertificateContextProperty.restype = wintypes.BOOL
crypt32.CertGetNameStringW.argtypes = [PCERT_CONTEXT, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.LPWSTR, wintypes.DWORD]
crypt32.CertGetNameStringW.restype = wintypes.DWORD
crypt32.CertCloseStore.argtypes = [wintypes.HANDLE, wintypes.DWORD]
crypt32.CertFreeCertificateContext.argtypes = [PCERT_CONTEXT]
crypt32.CertFreeCertificateContext.restype = wintypes.BOOL
crypt32.CryptAcquireCertificatePrivateKey.argtypes = [
    PCERT_CONTEXT, wintypes.DWORD, ctypes.c_void_p,
    ctypes.POINTER(wintypes.HANDLE), ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.BOOL)
]
crypt32.CryptAcquireCertificatePrivateKey.restype = wintypes.BOOL

@dataclass
class CertItem:
    index: int
    subject: str
    issuer: str
    serial: str
    valid_from: str
    valid_to: str
    provider_name: str
    container_name: str
    scope: str
    raw_der: bytes
    p_cert_context: PCERT_CONTEXT

class _PyHankoTokenSigner(Signer):
    """Signer tùy chỉnh cho pyHanko gọi xuống USB Token qua Windows CNG."""
    def __init__(self, cert_item: CertItem):
        self.cert_item = cert_item
        cert_asn1 = asn1_x509.Certificate.load(cert_item.raw_der)
        
        # Chỉ định trực tiếp cấu trúc ASN.1 tương thích pyhanko
        sig_mech = algos.SignedDigestAlgorithm({
            'algorithm': algos.SignedDigestAlgorithmId('sha256_rsa')
        })

        super().__init__(
            signing_cert=cert_asn1,
            cert_registry=None,
            signature_mechanism=sig_mech
        )

    async def async_sign_raw(self, data: bytes, digest_algorithm: str, dry_run=False) -> bytes:
        return self.sign_raw(data, digest_algorithm, dry_run=dry_run)

    def sign_raw(self, data: bytes, digest_algorithm: str, dry_run=False) -> bytes:
        if dry_run:
            return b"\x00" * 256

        # Hash dữ liệu trước khi chuyển cho NCryptSignHash
        digest_alg = (digest_algorithm or "sha256").lower()
        if digest_alg == 'sha256':
            hash_bytes = hashlib.sha256(data).digest()
            alg_id = "SHA256"
        elif digest_alg == 'sha384':
            hash_bytes = hashlib.sha384(data).digest()
            alg_id = "SHA384"
        elif digest_alg == 'sha512':
            hash_bytes = hashlib.sha512(data).digest()
            alg_id = "SHA512"
        elif digest_alg == 'sha1':
            hash_bytes = hashlib.sha1(data).digest()
            alg_id = "SHA1"
        else:
            hash_bytes = hashlib.sha256(data).digest()
            alg_id = "SHA256"

        h_priv_key = wintypes.HANDLE()
        dw_key_spec = wintypes.DWORD()
        f_caller_free = wintypes.BOOL()

        ok = crypt32.CryptAcquireCertificatePrivateKey(
            self.cert_item.p_cert_context,
            CRYPT_ACQUIRE_PREFER_NCRYPT_FLAG,
            None,
            ctypes.byref(h_priv_key),
            ctypes.byref(dw_key_spec),
            ctypes.byref(f_caller_free)
        )
        if not ok:
            err = ctypes.get_last_error()
            raise ctypes.WinError(err)

        try:
            pad_info = BCRYPT_PKCS1_PADDING_INFO(pszAlgId=alg_id)
            hash_buf = (ctypes.c_ubyte * len(hash_bytes)).from_buffer_copy(hash_bytes)
            cb_signature = wintypes.DWORD(0)

            # Lấy kích thước chữ ký
            status = ncrypt.NCryptSignHash(
                h_priv_key, ctypes.byref(pad_info), hash_buf, len(hash_bytes),
                None, 0, ctypes.byref(cb_signature), BCRYPT_PAD_PKCS1
            )
            if status != 0:
                raise RuntimeError(f"NCryptSignHash size check thất bại: 0x{status & 0xFFFFFFFF:08X}")

            sig_buf = (ctypes.c_ubyte * cb_signature.value)()
            status = ncrypt.NCryptSignHash(
                h_priv_key, ctypes.byref(pad_info), hash_buf, len(hash_bytes),
                sig_buf, cb_signature.value, ctypes.byref(cb_signature), BCRYPT_PAD_PKCS1
            )
            if status != 0:
                raise RuntimeError(f"Ký hash bằng Token thất bại: 0x{status & 0xFFFFFFFF:08X}")

            return bytes(sig_buf)
        finally:
            if f_caller_free.value and h_priv_key:
                ncrypt.NCryptFreeObject(h_priv_key)

class WindowsTokenSigner:
    @staticmethod
    def _filetime_to_dt(ft) -> str:
        timestamp = (ft.dwHighDateTime << 32) + ft.dwLowDateTime
        epoch_diff = 116444736000000000
        if timestamp < epoch_diff:
            return "N/A"
        return datetime.fromtimestamp((timestamp - epoch_diff) / 10_000_000).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _get_name(p_cert, flag=0) -> str:
        length = crypt32.CertGetNameStringW(p_cert, CERT_NAME_SIMPLE_DISPLAY_TYPE, flag, None, None, 0)
        if length <= 1:
            return "<Unknown>"
        buf = ctypes.create_unicode_buffer(length)
        crypt32.CertGetNameStringW(p_cert, CERT_NAME_SIMPLE_DISPLAY_TYPE, flag, None, buf, length)
        return buf.value

    @staticmethod
    def _get_serial(p_cert) -> str:
        cert_info = p_cert.contents.pCertInfo.contents
        serial_blob = cert_info.SerialNumber
        raw_bytes = bytes((ctypes.c_ubyte * serial_blob.cbData).from_address(ctypes.addressof(serial_blob.pbData.contents)))
        return raw_bytes[::-1].hex().upper()

    @classmethod
    def list_certificates(cls) -> List[CertItem]:
        scopes = {
            "CurrentUser": CERT_SYSTEM_STORE_CURRENT_USER,
            "LocalMachine": CERT_SYSTEM_STORE_LOCAL_MACHINE
        }
        certs = []
        idx = 1

        for scope_name, scope_flag in scopes.items():
            h_store = crypt32.CertOpenStore(CERT_STORE_PROV_SYSTEM_W, 0, 0, scope_flag, "My")
            if not h_store:
                continue

            p_cert = None
            while True:
                p_cert = crypt32.CertEnumCertificatesInStore(h_store, p_cert)
                if not p_cert:
                    break

                cb_data = wintypes.DWORD(0)
                if not crypt32.CertGetCertificateContextProperty(p_cert, CERT_KEY_PROV_INFO_PROP_ID, None, ctypes.byref(cb_data)):
                    continue

                buf = (ctypes.c_byte * cb_data.value)()
                crypt32.CertGetCertificateContextProperty(p_cert, CERT_KEY_PROV_INFO_PROP_ID, buf, ctypes.byref(cb_data))
                prov = ctypes.cast(buf, ctypes.POINTER(CRYPT_KEY_PROV_INFO)).contents

                raw_der = bytes((ctypes.c_ubyte * p_cert.contents.cbCertEncoded).from_address(
                    ctypes.cast(p_cert.contents.pbCertEncoded, ctypes.c_void_p).value
                ))

                # Lọc chứng thư số: Chỉ lấy chứng thư dùng cho ký số, loại bỏ Root CA / Intermediate CA
                try:
                    cert_obj = asn1_x509.Certificate.load(raw_der)
                    # 1. Bỏ qua nếu là chứng thư CA (Basic Constraints: CA=True)
                    if cert_obj.ca:
                        continue

                    # 2. Kiểm tra Key Usage (mục đích sử dụng khóa)
                    if cert_obj.key_usage_value is not None:
                        ku_native = cert_obj.key_usage_value.native
                        # Bắt buộc phải có quyền ký số (digital_signature hoặc non_repudiation)
                        if not ({'digital_signature', 'non_repudiation'} & ku_native):
                            continue
                except Exception:
                    continue

                p_cert_dup = crypt32.CertDuplicateCertificateContext(p_cert)
                c_info = p_cert.contents.pCertInfo.contents
                item = CertItem(
                    index=idx,
                    subject=cls._get_name(p_cert, 0),
                    issuer=cls._get_name(p_cert, CERT_NAME_ISSUER_FLAG),
                    serial=cls._get_serial(p_cert),
                    valid_from=cls._filetime_to_dt(c_info.NotBefore),
                    valid_to=cls._filetime_to_dt(c_info.NotAfter),
                    provider_name=prov.pwszProvName,
                    container_name=prov.pwszContainerName,
                    scope=scope_name,
                    raw_der=raw_der,
                    p_cert_context=p_cert_dup
                )
                certs.append(item)
                idx += 1

            crypt32.CertCloseStore(h_store, 0)
        return certs

    @staticmethod
    def sign_pdf(
        cert_item: CertItem,
        input_pdf_path: str,
        output_pdf_path: str,
        reason: str = "Xac nhan tinh toan ven cua tai lieu",
        location: str = "Ha Noi, Viet Nam",
        page: int = 0,                         # Trang 1 (0-indexed: trang 1 là 0)
        box: tuple = (370, 50, 560, 130),      # (x_trái, y_dưới, x_phải, y_trên) - Góc dưới bên phải
        tsa_url: str = "http://ca.gov.vn/tsa", # Máy chủ TSA của Ban Cơ yếu Chính phủ
        use_cades: bool = True                 # True: Chuẩn CAdES/PAdES (chuẩn Bộ TT&TT), False: Chuẩn CMS (Adobe cũ)
    ):
        token_signer = _PyHankoTokenSigner(cert_item)
        field_name = f"Signature_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        subfilter = fields.SigSeedSubFilter.PADES if use_cades else fields.SigSeedSubFilter.ADOBE_PKCS7_DETACHED

        timestamper = None
        if tsa_url:
            print(f"-> Đang kết nối lấy dấu thời gian chuẩn TSA từ: {tsa_url}")
            timestamper = HTTPTimeStamper(url=tsa_url, timeout=10)

        with open(input_pdf_path, "rb") as inf:
            w = IncrementalPdfFileWriter(inf)
            with open(output_pdf_path, "wb") as outf:
                signers.sign_pdf(
                    w,
                    signers.PdfSignatureMetadata(
                        field_name=field_name,
                        md_algorithm='sha256',
                        name=cert_item.subject,
                        reason=reason,
                        location=location,
                        subfilter=subfilter
                    ),
                    signer=token_signer,
                    timestamper=timestamper,
                    new_field_spec=fields.SigFieldSpec(
                        sig_field_name=field_name,
                        on_page=page,
                        box=box
                    ),
                    output=outf
                )