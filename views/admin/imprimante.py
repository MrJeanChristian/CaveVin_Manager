# ============================================================
# views/admin/imprimante.py — Configuration imprimante thermique
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
import sys, os, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS


class ImprimanteView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self._build()
        self._load_config()

    def _build(self):
        C = COLORS
        ctk.CTkLabel(self, text="  Configuration Imprimante Thermique",
                     font=FONTS["heading"], text_color=C["gold"]).pack(anchor="w", padx=24, pady=(20, 16))

        # ---- Carte principale ----
        card = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                             border_width=1, border_color=C["border"])
        card.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Type de connexion
        ctk.CTkLabel(card, text="Type de connexion", font=FONTS["body"],
                     text_color=C["text_muted"]).pack(anchor="w", padx=20, pady=(20, 4))
        self.type_var = ctk.StringVar(value="usb")
        type_row = ctk.CTkFrame(card, fg_color="transparent")
        type_row.pack(fill="x", padx=20, pady=(0, 16))
        for val, label in [("usb","USB"), ("network","Réseau/IP"),
                           ("serial","Série (COM)"), ("file","Fichier test")]:
            ctk.CTkRadioButton(type_row, text=label, variable=self.type_var,
                                value=val, font=FONTS["body"], text_color=C["text"],
                                fg_color=C["accent"],
                                command=self._on_type_change).pack(side="left", padx=12)

        # Colonnes
        cols_row = ctk.CTkFrame(card, fg_color="transparent")
        cols_row.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(cols_row, text="Largeur (colonnes) :", font=FONTS["body"],
                     text_color=C["text_muted"]).pack(side="left")
        self.cols_var = ctk.StringVar(value="42")
        ctk.CTkComboBox(cols_row, variable=self.cols_var, values=["32","42","48"],
                         width=80, fg_color=C["bg_dark"], border_color=C["border"],
                         text_color=C["text"], font=FONTS["body"]).pack(side="left", padx=8)
        ctk.CTkLabel(cols_row, text="(57mm=32  |  80mm=42 ou 48)",
                     font=FONTS["small"], text_color=C["text_muted"]).pack(side="left", padx=4)

        # ---- Sections par type ----
        # USB
        self.frame_usb = ctk.CTkFrame(card, fg_color=C["bg_dark"], corner_radius=8)
        self.frame_usb.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(self.frame_usb, text="Paramètres USB",
                     font=FONTS["badge"], text_color=C["gold"]).pack(anchor="w", padx=12, pady=(10, 4))
        row_usb = ctk.CTkFrame(self.frame_usb, fg_color="transparent")
        row_usb.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(row_usb, text="idVendor (hex) :", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left")
        self.e_vendor = ctk.CTkEntry(row_usb, width=100, height=32,
                                      fg_color=C["bg_card"], border_color=C["border"],
                                      text_color=C["text"], font=FONTS["mono"])
        self.e_vendor.pack(side="left", padx=8)
        ctk.CTkLabel(row_usb, text="idProduct (hex) :", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left", padx=(12, 0))
        self.e_product = ctk.CTkEntry(row_usb, width=100, height=32,
                                       fg_color=C["bg_card"], border_color=C["border"],
                                       text_color=C["text"], font=FONTS["mono"])
        self.e_product.pack(side="left", padx=8)
        ctk.CTkLabel(self.frame_usb,
                     text="  Trouver vos IDs : ouvrir un terminal et taper  lsusb",
                     font=FONTS["small"], text_color=C["text_muted"]).pack(anchor="w", padx=12, pady=(0, 8))

        # Réseau
        self.frame_net = ctk.CTkFrame(card, fg_color=C["bg_dark"], corner_radius=8)
        ctk.CTkLabel(self.frame_net, text="Paramètres Réseau",
                     font=FONTS["badge"], text_color=C["gold"]).pack(anchor="w", padx=12, pady=(10, 4))
        row_net = ctk.CTkFrame(self.frame_net, fg_color="transparent")
        row_net.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(row_net, text="Adresse IP :", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left")
        self.e_ip = ctk.CTkEntry(row_net, width=140, height=32,
                                  fg_color=C["bg_card"], border_color=C["border"],
                                  text_color=C["text"], font=FONTS["mono"])
        self.e_ip.pack(side="left", padx=8)
        ctk.CTkLabel(row_net, text="Port :", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left")
        self.e_port = ctk.CTkEntry(row_net, width=70, height=32,
                                    fg_color=C["bg_card"], border_color=C["border"],
                                    text_color=C["text"], font=FONTS["mono"])
        self.e_port.pack(side="left", padx=8)

        # Série
        self.frame_ser = ctk.CTkFrame(card, fg_color=C["bg_dark"], corner_radius=8)
        ctk.CTkLabel(self.frame_ser, text="Paramètres Série",
                     font=FONTS["badge"], text_color=C["gold"]).pack(anchor="w", padx=12, pady=(10, 4))
        row_ser = ctk.CTkFrame(self.frame_ser, fg_color="transparent")
        row_ser.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(row_ser, text="Port :", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left")
        self.e_serial = ctk.CTkEntry(row_ser, width=160, height=32,
                                      fg_color=C["bg_card"], border_color=C["border"],
                                      text_color=C["text"], font=FONTS["mono"],
                                      placeholder_text="/dev/ttyUSB0")
        self.e_serial.pack(side="left", padx=8)
        ctk.CTkLabel(row_ser, text="Baud :", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left")
        self.e_baud = ctk.CTkEntry(row_ser, width=80, height=32,
                                    fg_color=C["bg_card"], border_color=C["border"],
                                    text_color=C["text"], font=FONTS["mono"])
        self.e_baud.pack(side="left", padx=8)

        # Fichier test
        self.frame_file = ctk.CTkFrame(card, fg_color=C["bg_dark"], corner_radius=8)
        ctk.CTkLabel(self.frame_file, text="Fichier de sortie (test sans imprimante)",
                     font=FONTS["badge"], text_color=C["gold"]).pack(anchor="w", padx=12, pady=(10, 4))
        row_file = ctk.CTkFrame(self.frame_file, fg_color="transparent")
        row_file.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(row_file, text="Chemin :", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left")
        self.e_file = ctk.CTkEntry(row_file, width=280, height=32,
                                    fg_color=C["bg_card"], border_color=C["border"],
                                    text_color=C["text"], font=FONTS["mono"])
        self.e_file.pack(side="left", padx=8)

        # ---- Boutons ----
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=16)
        ctk.CTkButton(btn_row, text="  Enregistrer", height=40,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._save).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="  Imprimer ticket test", height=40,
                      fg_color=C["bg_dark"], hover_color=C["bg_sidebar"],
                      border_width=1, border_color=C["border"],
                      text_color=C["text"], font=FONTS["badge"],
                      command=self._test_print).pack(side="left")

        self.lbl_status = ctk.CTkLabel(card, text="", font=FONTS["body"])
        self.lbl_status.pack(pady=(0, 16))

        # Aide
        aide = ctk.CTkFrame(card, fg_color=C["bg_sidebar"], corner_radius=8)
        aide.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkLabel(aide, text=(
            "  Droits USB Linux : ouvrir un terminal et taper :\n"
            "  sudo usermod -aG lp $USER\n"
            "  puis redémarrer votre session."
        ), font=FONTS["small"], text_color=C["text_muted"],
           justify="left").pack(anchor="w", padx=12, pady=8)

        self._on_type_change()

    def _on_type_change(self):
        t = self.type_var.get()
        for frame in [self.frame_usb, self.frame_net, self.frame_ser, self.frame_file]:
            frame.pack_forget()
        if t == "usb":     self.frame_usb.pack(fill="x", padx=20, pady=(0, 8))
        elif t == "network":self.frame_net.pack(fill="x", padx=20, pady=(0, 8))
        elif t == "serial": self.frame_ser.pack(fill="x", padx=20, pady=(0, 8))
        elif t == "file":   self.frame_file.pack(fill="x", padx=20, pady=(0, 8))

    def _load_config(self):
        try:
            from utils.thermal_printer import PRINTER_CONFIG as PC
            self.type_var.set(PC.get("type", "usb"))
            self.cols_var.set(str(PC.get("columns", 42)))
            self.e_vendor.delete(0, "end");  self.e_vendor.insert(0,  hex(PC.get("usb_vendor", 0x0416)))
            self.e_product.delete(0, "end"); self.e_product.insert(0, hex(PC.get("usb_product", 0x5011)))
            self.e_ip.delete(0, "end");      self.e_ip.insert(0, PC.get("network_host", "192.168.1.100"))
            self.e_port.delete(0, "end");    self.e_port.insert(0, str(PC.get("network_port", 9100)))
            self.e_serial.delete(0, "end");  self.e_serial.insert(0, PC.get("serial_port", "/dev/ttyUSB0"))
            self.e_baud.delete(0, "end");    self.e_baud.insert(0, str(PC.get("serial_baud", 9600)))
            self.e_file.delete(0, "end");    self.e_file.insert(0, PC.get("file_path", "/tmp/ticket.txt"))
            self._on_type_change()
        except Exception:
            pass

    def _save(self):
        try:
            from utils import thermal_printer as tp
            tp.PRINTER_CONFIG["type"]         = self.type_var.get()
            tp.PRINTER_CONFIG["columns"]      = int(self.cols_var.get())
            tp.PRINTER_CONFIG["usb_vendor"]   = int(self.e_vendor.get(), 16)
            tp.PRINTER_CONFIG["usb_product"]  = int(self.e_product.get(), 16)
            tp.PRINTER_CONFIG["network_host"] = self.e_ip.get().strip()
            tp.PRINTER_CONFIG["network_port"] = int(self.e_port.get() or 9100)
            tp.PRINTER_CONFIG["serial_port"]  = self.e_serial.get().strip()
            tp.PRINTER_CONFIG["serial_baud"]  = int(self.e_baud.get() or 9600)
            tp.PRINTER_CONFIG["file_path"]    = self.e_file.get().strip()
            self.lbl_status.configure(text="  Configuration enregistrée !", text_color=COLORS["success"])
        except Exception as e:
            self.lbl_status.configure(text=f"Erreur : {e}", text_color=COLORS["danger"])

    def _test_print(self):
        self._save()
        self.lbl_status.configure(text="Impression en cours...", text_color=COLORS["gold"])
        self.update()
        def do_print():
            try:
                from utils.thermal_printer import tester_imprimante
                tester_imprimante()
                self.after(0, lambda: self.lbl_status.configure(
                    text="  Ticket test imprimé avec succès !", text_color=COLORS["success"]))
            except Exception as e:
                self.after(0, lambda: self.lbl_status.configure(
                    text=f"Erreur : {e}", text_color=COLORS["danger"]))
        threading.Thread(target=do_print, daemon=True).start()
