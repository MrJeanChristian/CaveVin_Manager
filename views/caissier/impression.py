# ============================================================
# views/caissier/impression.py — Dialogue config + test imprimante
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
import utils.thermal_printer as tp


class ImpressionDialog(ctk.CTkToplevel):
    """
    Fenêtre de configuration et test de l'imprimante thermique.
    Appelable depuis tickets.py et historique.py.
    """
    def __init__(self, parent, ticket=None, lignes=None):
        super().__init__(parent)
        self.ticket = ticket
        self.lignes = lignes
        self.title("Imprimante Thermique")
        self.geometry("480x540")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])
        self.grab_set()
        self._build()

    def _build(self):
        C = COLORS
        ctk.CTkLabel(self, text="Configuration Imprimante",
                     font=FONTS["heading"], text_color=C["gold"]).pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Parametres de connexion ESC/POS",
                     font=FONTS["small"], text_color=C["text_muted"]).pack(pady=(0, 16))

        form = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                             border_width=1, border_color=C["border"])
        form.pack(fill="x", padx=20, pady=(0, 12))

        # Type d'imprimante
        ctk.CTkLabel(form, text="Type de connexion", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14, pady=(12, 1))
        self.type_var = ctk.StringVar(value=tp.PRINTER_TYPE)
        type_frame = ctk.CTkFrame(form, fg_color="transparent")
        type_frame.pack(fill="x", padx=14, pady=(0, 10))
        for t in ["usb", "network", "serial", "file"]:
            ctk.CTkRadioButton(type_frame, text=t.upper(), variable=self.type_var, value=t,
                                fg_color=C["accent"], text_color=C["text"],
                                font=FONTS["small"], command=self._toggle_fields).pack(side="left", padx=8)

        # USB
        self.usb_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.usb_frame.pack(fill="x", padx=14)
        ctk.CTkLabel(self.usb_frame, text="Vendor ID (hex ex: 0x0416)",
                     font=FONTS["small"], text_color=C["text_muted"]).pack(anchor="w")
        self.e_vendor = ctk.CTkEntry(self.usb_frame, height=34, fg_color=C["bg_dark"],
                                      border_color=C["border"], text_color=C["text"], font=FONTS["body"])
        self.e_vendor.insert(0, hex(tp.USB_VENDOR_ID))
        self.e_vendor.pack(fill="x", pady=(2, 6))
        ctk.CTkLabel(self.usb_frame, text="Product ID (hex ex: 0x5011)",
                     font=FONTS["small"], text_color=C["text_muted"]).pack(anchor="w")
        self.e_product = ctk.CTkEntry(self.usb_frame, height=34, fg_color=C["bg_dark"],
                                       border_color=C["border"], text_color=C["text"], font=FONTS["body"])
        self.e_product.insert(0, hex(tp.USB_PRODUCT_ID))
        self.e_product.pack(fill="x", pady=(2, 10))

        # Réseau
        self.net_frame = ctk.CTkFrame(form, fg_color="transparent")
        ctk.CTkLabel(self.net_frame, text="Adresse IP",
                     font=FONTS["small"], text_color=C["text_muted"]).pack(anchor="w")
        self.e_host = ctk.CTkEntry(self.net_frame, height=34, fg_color=C["bg_dark"],
                                    border_color=C["border"], text_color=C["text"], font=FONTS["body"])
        self.e_host.insert(0, tp.NETWORK_HOST)
        self.e_host.pack(fill="x", pady=(2, 6))
        ctk.CTkLabel(self.net_frame, text="Port",
                     font=FONTS["small"], text_color=C["text_muted"]).pack(anchor="w")
        self.e_port = ctk.CTkEntry(self.net_frame, height=34, fg_color=C["bg_dark"],
                                    border_color=C["border"], text_color=C["text"], font=FONTS["body"])
        self.e_port.insert(0, str(tp.NETWORK_PORT))
        self.e_port.pack(fill="x", pady=(2, 10))

        # Série / Fichier
        self.serial_frame = ctk.CTkFrame(form, fg_color="transparent")
        ctk.CTkLabel(self.serial_frame, text="Port / Fichier (ex: /dev/usb/lp0)",
                     font=FONTS["small"], text_color=C["text_muted"]).pack(anchor="w")
        self.e_serial = ctk.CTkEntry(self.serial_frame, height=34, fg_color=C["bg_dark"],
                                      border_color=C["border"], text_color=C["text"], font=FONTS["body"])
        self.e_serial.insert(0, tp.SERIAL_PORT)
        self.e_serial.pack(fill="x", pady=(2, 10))

        self._toggle_fields()

        # Boutons
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(btns, text="Test imprimante", height=40,
                      fg_color=C["bg_card"], hover_color=C["border"],
                      text_color=C["text"], font=FONTS["badge"],
                      command=self._test).pack(fill="x", pady=(0, 6))

        if self.ticket and self.lignes:
            ctk.CTkButton(btns, text="Imprimer ce ticket", height=44,
                          fg_color=C["accent"], hover_color=C["accent2"],
                          text_color=C["white"], font=("Helvetica", 13, "bold"),
                          command=self._imprimer).pack(fill="x", pady=(0, 6))

        ctk.CTkButton(btns, text="Fermer", height=36,
                      fg_color="transparent", hover_color=C["bg_sidebar"],
                      text_color=C["text_muted"], font=FONTS["small"],
                      command=self.destroy).pack(fill="x")

        # Zone log
        self.lbl_log = ctk.CTkLabel(self, text="", font=FONTS["small"],
                                     text_color=C["text_muted"], wraplength=440)
        self.lbl_log.pack(pady=8)

    def _toggle_fields(self):
        t = self.type_var.get()
        self.usb_frame.pack_forget()
        self.net_frame.pack_forget()
        self.serial_frame.pack_forget()
        if t == "usb":
            self.usb_frame.pack(fill="x", padx=14)
        elif t == "network":
            self.net_frame.pack(fill="x", padx=14)
        else:
            self.serial_frame.pack(fill="x", padx=14)

    def _apply_config(self):
        tp.PRINTER_TYPE = self.type_var.get()
        try:
            tp.USB_VENDOR_ID  = int(self.e_vendor.get(), 16)
            tp.USB_PRODUCT_ID = int(self.e_product.get(), 16)
        except: pass
        tp.NETWORK_HOST = self.e_host.get().strip()
        try: tp.NETWORK_PORT = int(self.e_port.get())
        except: pass
        tp.SERIAL_PORT  = self.e_serial.get().strip()
        tp.FILE_PATH    = self.e_serial.get().strip()

    def _test(self):
        self._apply_config()
        self.lbl_log.configure(text="Test en cours...", text_color=COLORS["text_muted"])
        self.update()
        ok, msg = tp.tester_imprimante()
        self.lbl_log.configure(
            text=("OK  " if ok else "ERREUR  ") + msg,
            text_color=COLORS["success"] if ok else COLORS["danger"]
        )

    def _imprimer(self):
        self._apply_config()
        self.lbl_log.configure(text="Impression en cours...", text_color=COLORS["text_muted"])
        self.update()
        ok, msg = tp.imprimer_ticket(self.ticket, self.lignes)
        self.lbl_log.configure(
            text=("OK  " if ok else "ERREUR  ") + msg,
            text_color=COLORS["success"] if ok else COLORS["danger"]
        )
