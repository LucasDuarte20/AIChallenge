#!/usr/bin/env python3
"""
CONATEL — Asistente de Agenda Comercial
Interfaz moderna con CustomTkinter (dark mode, paleta Conatel).
Empaquetable con PyInstaller en un .exe portable para Windows.
"""
from __future__ import annotations

import os
import sys
import tkinter as tk
from datetime import date, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError:
    _root = tk.Tk()
    _root.withdraw()
    messagebox.showerror(
        "Dependencia faltante",
        "Falta customtkinter.\nInstalá con: pip install customtkinter",
    )
    sys.exit(1)

try:
    from tkcalendar import Calendar

    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

try:
    from PIL import Image, ImageTk

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from agenda_app.excel_io import (
    load_clients,
    save_workbook,
    write_agenda_flat_sheet,
    write_last_visits,
    write_next_visits,
    write_weekly_agenda_sheet,
)
from agenda_app.planner import build_agenda, visits_to_simple_rows

# ── Paleta Conatel (dark mode) ────────────────────────────────────
RED = "#D31920"
RED_HOVER = "#E8222B"
RED_DARK = "#A3141A"

GRAY = "#6B7B8D"
GRAY_LIGHT = "#8A9BAE"
GRAY_DARK = "#4A5568"

BG_DARK = "#0D1117"
BG_SURFACE = "#161B22"
BG_CARD = "#1C2333"
BG_CARD_ALT = "#212D3F"
BG_INPUT = "#0D1117"

TEXT = "#F0F6FC"
TEXT_DIM = "#8B949E"
TEXT_MUTED = "#484F58"

GREEN = "#2EA043"
GREEN_HOVER = "#3FB950"

FONT = "Segoe UI"


# ── Helpers ───────────────────────────────────────────────────────
def resource_path(relative: str) -> str:
    """Ruta absoluta a un recurso — funciona en dev y en PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


# ── Pantalla principal ────────────────────────────────────────────
class AgendaApp(ctk.CTk):
    """Ventana principal con dos opciones: crear agenda / actualizar planilla."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")

        self.title("CONATEL — Asistente de Agenda Comercial")
        self.geometry("920x660")
        self.minsize(820, 580)
        self.configure(fg_color=BG_DARK)

        # Estado compartido
        self._excel_path: Path | None = None
        self._wb = None
        self._sheet_name: str = ""
        self._header_row: int = 3
        self._clients: list = []

        self._set_icon()
        self._build_header()
        self._build_body()
        self._build_status()

    # ── Ícono de ventana ──────────────────────────────────────
    def _set_icon(self) -> None:
        if not HAS_PIL:
            return
        try:
            p = resource_path(os.path.join("assets", "conatel_logo.png"))
            if not os.path.exists(p):
                return
            img = Image.open(p).resize((32, 32), Image.LANCZOS)
            self._icon = ImageTk.PhotoImage(img)
            self.iconphoto(False, self._icon)
        except Exception:
            pass

    # ── Header ────────────────────────────────────────────────
    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=0, height=72)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        row = ctk.CTkFrame(hdr, fg_color="transparent")
        row.pack(fill="x", padx=24, expand=True)

        # Logo o texto fallback
        logo_ok = False
        if HAS_PIL:
            try:
                lp = resource_path(os.path.join("assets", "conatel_logo.png"))
                if os.path.exists(lp):
                    raw = Image.open(lp)
                    ratio = 44 / raw.height
                    self._logo_ctk = ctk.CTkImage(
                        light_image=raw, dark_image=raw,
                        size=(int(raw.width * ratio), 44),
                    )
                    ctk.CTkLabel(row, image=self._logo_ctk, text="").pack(
                        side="left", pady=14,
                    )
                    logo_ok = True
            except Exception:
                pass
        if not logo_ok:
            ctk.CTkLabel(
                row, text="CONATEL", text_color=RED,
                font=(FONT, 26, "bold"),
            ).pack(side="left", pady=14)

        # Línea de acento roja
        ctk.CTkFrame(
            row, fg_color=RED, width=3, height=40, corner_radius=2,
        ).pack(side="left", padx=16)

        # Título
        titles = ctk.CTkFrame(row, fg_color="transparent")
        titles.pack(side="left")
        ctk.CTkLabel(
            titles, text="Asistente de Agenda Comercial",
            font=(FONT, 16, "bold"), text_color=TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            titles, text="Organización inteligente de visitas",
            font=(FONT, 11), text_color=TEXT_DIM,
        ).pack(anchor="w")

    # ── Cuerpo con tarjetas ───────────────────────────────────
    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=48, pady=(24, 12))

        ctk.CTkLabel(
            body, text="¿Qué querés hacer?",
            font=(FONT, 22, "bold"), text_color=TEXT,
        ).pack(pady=(12, 28))

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(expand=True, fill="both")
        row.grid_columnconfigure((0, 1), weight=1)
        row.grid_rowconfigure(0, weight=1)

        self._card(
            row, 0, "📅", "Crear Agenda",
            "Generá tu agenda de visitas\nbasada en prioridad, cercanía\ny frecuencia de contacto.",
            "Crear agenda", self._on_create,
        )
        self._card(
            row, 1, "📝", "Actualizar Planilla",
            "Actualizá las fechas de\núltima visita de los clientes\nque contactaste.",
            "Actualizar visitas", self._on_update,
        )

    def _card(self, parent, col, icon, title, desc, btn_text, cmd) -> None:
        c = ctk.CTkFrame(
            parent, fg_color=BG_CARD, corner_radius=16,
            border_width=1, border_color=GRAY_DARK,
        )
        c.grid(row=0, column=col, padx=14, pady=8, sticky="nsew")

        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(expand=True, padx=32, pady=32)

        ctk.CTkLabel(inner, text=icon, font=(FONT, 46)).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner, text=title, font=(FONT, 20, "bold"), text_color=TEXT,
        ).pack(pady=(0, 6))
        ctk.CTkLabel(
            inner, text=desc, font=(FONT, 12),
            text_color=TEXT_DIM, justify="center",
        ).pack(pady=(0, 24))

        ctk.CTkButton(
            inner, text=btn_text, font=(FONT, 14, "bold"),
            fg_color=RED, hover_color=RED_HOVER, corner_radius=8,
            height=42, command=cmd,
        ).pack(fill="x")

        # Hover effect en borde de la tarjeta
        c.bind("<Enter>", lambda _: c.configure(border_color=RED))
        c.bind("<Leave>", lambda _: c.configure(border_color=GRAY_DARK))

    # ── Barra de estado ───────────────────────────────────────
    def _build_status(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=0, height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status = ctk.CTkLabel(
            bar, text="  Sin archivo cargado", font=(FONT, 11),
            text_color=TEXT_MUTED, anchor="w",
        )
        self._status.pack(side="left", padx=12, fill="x")

        ctk.CTkLabel(
            bar, text="v1.1  ", font=(FONT, 10), text_color=TEXT_MUTED,
        ).pack(side="right", padx=8)

    def set_status(self, text: str, color: str = TEXT_DIM) -> None:
        self._status.configure(text=f"  {text}", text_color=color)

    # ── Carga de datos ────────────────────────────────────────
    def _load_excel(self) -> bool:
        path = filedialog.askopenfilename(
            title="Seleccionar planilla de clientes",
            filetypes=[("Excel", "*.xlsx"), ("Todos", "*.*")],
        )
        if not path:
            return False
        try:
            clients, wb, sheet, hdr = load_clients(path)
        except Exception as exc:
            messagebox.showerror("Error al abrir el archivo", str(exc))
            return False
        self._excel_path = Path(path)
        self._wb = wb
        self._sheet_name = sheet
        self._header_row = hdr
        self._clients = clients
        self.set_status(
            f"📁 {self._excel_path.name} — {len(clients)} clientes", GREEN,
        )
        return True

    def _ensure(self) -> bool:
        if self._wb and self._clients:
            return True
        return self._load_excel()

    # ── Acciones ──────────────────────────────────────────────
    def _on_create(self) -> None:
        if self._ensure():
            CreateAgendaWindow(self)

    def _on_update(self) -> None:
        if self._ensure():
            UpdateWindow(self)


# ══════════════════════════════════════════════════════════════════
#  Ventana: Crear Agenda
# ══════════════════════════════════════════════════════════════════
class CreateAgendaWindow(ctk.CTkToplevel):
    """Configuración y generación de agenda de visitas."""

    def __init__(self, app: AgendaApp) -> None:
        super().__init__(app)
        self.app = app
        self.title("Crear Agenda — CONATEL")
        self.geometry("1020x720")
        self.minsize(900, 620)
        self.configure(fg_color=BG_DARK)
        self.transient(app)
        self.grab_set()

        self._visits: list = []
        self._first_next: dict = {}

        self._build()

    # ── UI ────────────────────────────────────────────────────
    def _build(self) -> None:
        # Header
        hdr = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="📅  Crear Agenda de Visitas",
            font=(FONT, 15, "bold"), text_color=TEXT,
        ).pack(side="left", padx=20)

        # Barra de archivo
        fbar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=32)
        fbar.pack(fill="x")
        fbar.pack_propagate(False)
        ctk.CTkLabel(
            fbar,
            text=f"  📁 {self.app._excel_path.name}   •   "
                 f"{len(self.app._clients)} clientes",
            font=(FONT, 11), text_color=TEXT_DIM,
        ).pack(side="left", padx=16)

        # Layout de dos columnas
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        # ── IZQUIERDA: Configuración ──────────────────────────
        left = ctk.CTkFrame(body, fg_color=BG_CARD, corner_radius=12)
        left.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        lp = ctk.CTkFrame(left, fg_color="transparent")
        lp.pack(fill="both", expand=True, padx=16, pady=14)

        ctk.CTkLabel(
            lp, text="Configuración",
            font=(FONT, 15, "bold"), text_color=TEXT,
        ).pack(anchor="w", pady=(0, 14))

        # Vendedor
        self._section_label(lp, "Vendedor")
        execs = sorted({
            (c.executive_code or "").strip()
            for c in self.app._clients
            if (c.executive_code or "").strip()
        })
        self._vendor = tk.StringVar(value=execs[0] if execs else "")
        ctk.CTkComboBox(
            lp, values=execs, variable=self._vendor, width=220,
            fg_color=BG_INPUT, border_color=GRAY_DARK,
            button_color=RED, button_hover_color=RED_HOVER,
            dropdown_fg_color=BG_SURFACE,
        ).pack(anchor="w", pady=(2, 10))

        # Calendario
        self._section_label(lp, "Fecha de inicio")
        cal_box = ctk.CTkFrame(lp, fg_color=BG_INPUT, corner_radius=8)
        cal_box.pack(fill="x", pady=(2, 10))

        today = date.today()
        if HAS_CALENDAR:
            cal_kw: dict = dict(
                selectmode="day",
                year=today.year, month=today.month, day=today.day,
                background=BG_SURFACE, foreground=TEXT,
                selectbackground=RED, selectforeground="#FFF",
                normalbackground=BG_CARD, normalforeground=TEXT,
                weekendbackground=BG_CARD, weekendforeground=GRAY_LIGHT,
                headersbackground=BG_SURFACE, headersforeground=RED,
                bordercolor=GRAY_DARK,
                othermonthbackground=BG_DARK, othermonthforeground=TEXT_MUTED,
                othermonthwebackground=BG_DARK, othermonthweforeground=TEXT_MUTED,
                font=(FONT, 10), borderwidth=0,
            )
            # Intentar locale en español
            self._cal = None
            for loc in ("es_UY", "es_ES", "es", None):
                try:
                    kw = {**cal_kw}
                    if loc:
                        kw["locale"] = loc
                    self._cal = Calendar(cal_box, **kw)
                    break
                except Exception:
                    continue
            if self._cal is None:
                self._cal = Calendar(cal_box, **cal_kw)
            self._cal.pack(padx=6, pady=6)
        else:
            self._date_entry = ctk.CTkEntry(
                cal_box, placeholder_text="DD/MM/AAAA",
                fg_color=BG_DARK, border_color=GRAY_DARK,
            )
            self._date_entry.pack(padx=6, pady=6, fill="x")

        # Visitas por día
        self._section_label(lp, "Visitas por día")
        vpd_row = ctk.CTkFrame(lp, fg_color="transparent")
        vpd_row.pack(fill="x", pady=(2, 10))
        self._vpd = tk.IntVar(value=3)
        self._vpd_lbl = ctk.CTkLabel(
            vpd_row, text="3", font=(FONT, 14, "bold"),
            text_color=RED, width=28,
        )
        self._vpd_lbl.pack(side="right")
        ctk.CTkSlider(
            vpd_row, from_=1, to=8, number_of_steps=7,
            variable=self._vpd,
            fg_color=BG_INPUT, progress_color=RED,
            button_color=RED, button_hover_color=RED_HOVER,
            command=lambda v: self._vpd_lbl.configure(text=str(int(v))),
        ).pack(side="left", fill="x", expand=True)

        # Duración (semanas)
        self._section_label(lp, "Duración")
        dur_row = ctk.CTkFrame(lp, fg_color="transparent")
        dur_row.pack(fill="x", pady=(2, 10))
        self._weeks = tk.IntVar(value=1)
        self._wk_lbl = ctk.CTkLabel(
            dur_row, text="1 semana", font=(FONT, 13, "bold"),
            text_color=RED, width=100,
        )
        self._wk_lbl.pack(side="right")

        def _upd_wk(v):
            w = int(v)
            self._wk_lbl.configure(
                text=f"{w} {'semana' if w == 1 else 'semanas'}",
            )

        ctk.CTkSlider(
            dur_row, from_=1, to=52, number_of_steps=51,
            variable=self._weeks,
            fg_color=BG_INPUT, progress_color=RED,
            button_color=RED, button_hover_color=RED_HOVER,
            command=_upd_wk,
        ).pack(side="left", fill="x", expand=True)

        # Botón generar
        self._gen_btn = ctk.CTkButton(
            lp, text="🚀  Generar Agenda", font=(FONT, 14, "bold"),
            fg_color=RED, hover_color=RED_HOVER,
            corner_radius=8, height=44,
            command=self._generate,
        )
        self._gen_btn.pack(fill="x", pady=(14, 0))

        # Barra de progreso (oculta)
        self._prog = ctk.CTkProgressBar(
            lp, fg_color=BG_INPUT, progress_color=RED,
        )

        # ── DERECHA: Vista previa ─────────────────────────────
        right = ctk.CTkFrame(body, fg_color=BG_CARD, corner_radius=12)
        right.grid(row=0, column=1, padx=(6, 0), sticky="nsew")
        rp = ctk.CTkFrame(right, fg_color="transparent")
        rp.pack(fill="both", expand=True, padx=16, pady=14)

        ctk.CTkLabel(
            rp, text="Vista previa",
            font=(FONT, 15, "bold"), text_color=TEXT,
        ).pack(anchor="w", pady=(0, 10))

        self._preview = ctk.CTkScrollableFrame(
            rp, fg_color=BG_SURFACE, corner_radius=8,
        )
        self._preview.pack(fill="both", expand=True)

        # Placeholder
        ctk.CTkLabel(
            self._preview,
            text="La vista previa aparecerá aquí\n"
                 "luego de generar la agenda.",
            font=(FONT, 12), text_color=TEXT_MUTED, justify="center",
        ).pack(expand=True, pady=80)

        # Botón guardar (oculto, se muestra tras generar)
        self._save_btn = ctk.CTkButton(
            rp, text="💾  Guardar Excel", font=(FONT, 14, "bold"),
            fg_color=GREEN, hover_color=GREEN_HOVER,
            corner_radius=8, height=44,
            command=self._save,
        )
        # No se packea hasta tener preview

    # ── helpers ───────────────────────────────────────────────
    @staticmethod
    def _section_label(parent, text: str) -> None:
        ctk.CTkLabel(
            parent, text=text,
            font=(FONT, 12, "bold"), text_color=TEXT_DIM,
        ).pack(anchor="w")

    def _start_date(self) -> date:
        if HAS_CALENDAR:
            return self._cal.selection_get()
        s = getattr(self, "_date_entry", None)
        if s:
            txt = s.get().strip()
            try:
                p = txt.split("/")
                return date(int(p[2]), int(p[1]), int(p[0]))
            except Exception:
                pass
        return date.today()

    # ── Generación ────────────────────────────────────────────
    def _generate(self) -> None:
        vendor = self._vendor.get().strip()
        if not vendor:
            messagebox.showwarning(
                "Dato requerido", "Elegí un vendedor.", parent=self,
            )
            return

        sd = self._start_date()
        horizon = int(self._weeks.get()) * 7
        vpd = int(self._vpd.get())

        self._gen_btn.configure(state="disabled", text="Generando…")
        self._prog.pack(fill="x", pady=(6, 0))
        self._prog.set(0)
        self.update_idletasks()

        try:
            self._prog.set(0.3)
            self.update_idletasks()

            visits, first_next = build_agenda(
                self.app._clients, vendor, sd, horizon,
                visits_per_day=vpd,
            )

            self._prog.set(0.7)
            self.update_idletasks()

            if not visits:
                messagebox.showinfo(
                    "Sin datos",
                    "No hay clientes para ese vendedor.",
                    parent=self,
                )
                return

            self._visits = visits
            self._first_next = first_next
            self._render_preview(visits)

            self._prog.set(1.0)
            self.update_idletasks()

        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)
        finally:
            self._gen_btn.configure(
                state="normal", text="🚀  Generar Agenda",
            )
            self._prog.pack_forget()

    # ── Preview ───────────────────────────────────────────────
    def _render_preview(self, visits: list) -> None:
        for w in self._preview.winfo_children():
            w.destroy()

        # Estadísticas
        n = len(visits)
        clients_n = len({id(v.client) for v in visits})
        days_n = len({v.visit_at.date() for v in visits})

        stats_f = ctk.CTkFrame(self._preview, fg_color=BG_CARD, corner_radius=8)
        stats_f.pack(fill="x", padx=4, pady=4)
        for val, lbl in [
            (str(n), "visitas"),
            (str(clients_n), "clientes"),
            (str(days_n), "días"),
        ]:
            sf = ctk.CTkFrame(stats_f, fg_color="transparent")
            sf.pack(side="left", expand=True, padx=6, pady=8)
            ctk.CTkLabel(
                sf, text=val, font=(FONT, 20, "bold"), text_color=RED,
            ).pack()
            ctk.CTkLabel(
                sf, text=lbl, font=(FONT, 10), text_color=TEXT_DIM,
            ).pack()

        # Visitas agrupadas por fecha
        DAYS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        rows = visits_to_simple_rows(visits[:40])
        cur_date = None

        for r in rows:
            if r["fecha"] != cur_date:
                cur_date = r["fecha"]
                from datetime import datetime as _dt

                d = _dt.strptime(cur_date, "%Y-%m-%d").date()
                ctk.CTkLabel(
                    self._preview,
                    text=f"  {DAYS[d.weekday()]} {d.strftime('%d/%m/%Y')}",
                    font=(FONT, 12, "bold"), text_color=RED, anchor="w",
                ).pack(fill="x", padx=4, pady=(8, 2))

            vf = ctk.CTkFrame(
                self._preview, fg_color=BG_CARD,
                corner_radius=6, height=30,
            )
            vf.pack(fill="x", padx=4, pady=1)
            vf.pack_propagate(False)

            ctk.CTkLabel(
                vf, text=r["hora"], font=(FONT, 11, "bold"),
                text_color=TEXT_DIM, width=46,
            ).pack(side="left", padx=8)
            ctk.CTkLabel(
                vf, text=r["cliente"], font=(FONT, 11),
                text_color=TEXT, anchor="w",
            ).pack(side="left", fill="x", expand=True)
            if r["dirección"]:
                ctk.CTkLabel(
                    vf, text=r["dirección"][:28], font=(FONT, 10),
                    text_color=TEXT_MUTED,
                ).pack(side="right", padx=6)

        if len(visits) > 40:
            ctk.CTkLabel(
                self._preview,
                text=f"… y {len(visits) - 40} visitas más",
                font=(FONT, 11), text_color=TEXT_MUTED,
            ).pack(pady=8)

        # Mostrar botón guardar
        self._save_btn.pack(fill="x", pady=(10, 0))

    # ── Guardar ───────────────────────────────────────────────
    def _save(self) -> None:
        vendor = self._vendor.get().strip()

        # Escribir fechas de próxima visita en la planilla
        write_next_visits(
            self.app._wb, self.app._sheet_name,
            self.app._header_row, self._first_next,
        )
        # Escribir hojas de agenda
        write_agenda_flat_sheet(self.app._wb, self._visits)
        write_weekly_agenda_sheet(self.app._wb, self._visits)

        out = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"agenda_{vendor}_{date.today().isoformat()}.xlsx",
            parent=self,
        )
        if not out:
            return

        try:
            save_workbook(self.app._wb, out)
        except Exception as exc:
            messagebox.showerror("Error al guardar", str(exc), parent=self)
            return

        # Recargar archivo guardado
        try:
            clients, wb, sheet, hdr = load_clients(out)
            self.app._clients = clients
            self.app._wb = wb
            self.app._sheet_name = sheet
            self.app._header_row = hdr
            self.app._excel_path = Path(out)
            self.app.set_status(
                f"📁 {self.app._excel_path.name} — {len(clients)} clientes",
                GREEN,
            )
        except Exception:
            pass

        messagebox.showinfo(
            "¡Listo!",
            f"Agenda generada: {len(self._visits)} visitas.\n"
            f"Próxima visita escrita para {len(self._first_next)} clientes.\n\n"
            f"Archivo: {out}",
            parent=self,
        )
        self.destroy()


# ══════════════════════════════════════════════════════════════════
#  Ventana: Actualizar Planilla
# ══════════════════════════════════════════════════════════════════
class UpdateWindow(ctk.CTkToplevel):
    """Actualizar fechas de última visita por vendedor."""

    def __init__(self, app: AgendaApp) -> None:
        super().__init__(app)
        self.app = app
        self.title("Actualizar Planilla — CONATEL")
        self.geometry("960x640")
        self.minsize(850, 520)
        self.configure(fg_color=BG_DARK)
        self.transient(app)
        self.grab_set()

        self._entries: list[tuple[int, str, ctk.CTkEntry]] = []
        self._build()

    def _build(self) -> None:
        # Header
        hdr = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="📝  Actualizar Fechas de Visita",
            font=(FONT, 15, "bold"), text_color=TEXT,
        ).pack(side="left", padx=20)

        # Controles superiores
        ctrl = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        ctrl.pack(fill="x")
        ci = ctk.CTkFrame(ctrl, fg_color="transparent")
        ci.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(
            ci, text="Vendedor:", font=(FONT, 12, "bold"), text_color=TEXT_DIM,
        ).pack(side="left")

        execs = sorted({
            (c.executive_code or "").strip()
            for c in self.app._clients
            if (c.executive_code or "").strip()
        })
        self._vendor = tk.StringVar(value=execs[0] if execs else "")
        ctk.CTkComboBox(
            ci, values=execs, variable=self._vendor, width=200,
            fg_color=BG_INPUT, border_color=GRAY_DARK,
            button_color=RED, button_hover_color=RED_HOVER,
            dropdown_fg_color=BG_SURFACE,
        ).pack(side="left", padx=(8, 12))

        ctk.CTkButton(
            ci, text="Cargar", font=(FONT, 12),
            fg_color=RED, hover_color=RED_HOVER,
            corner_radius=6, height=30, width=100,
            command=self._refresh,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            ci, text="📅 Marcar todos hoy", font=(FONT, 12),
            fg_color=GRAY, hover_color=GRAY_LIGHT,
            corner_radius=6, height=30, width=150,
            command=self._mark_today,
        ).pack(side="left", padx=4)

        # Hint
        ctk.CTkLabel(
            self,
            text="  Solo completá fecha donde hubo visita "
                 "(AAAA-MM-DD). Podés usar el botón «Hoy».",
            font=(FONT, 11), text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=18, pady=(6, 0))

        # Cabecera de tabla
        th = ctk.CTkFrame(
            self, fg_color=BG_SURFACE, corner_radius=0, height=34,
        )
        th.pack(fill="x", padx=18, pady=(6, 0))
        th.pack_propagate(False)
        for text, w in [
            ("Cliente", 320), ("Última visita", 110),
            ("Nueva fecha", 150), ("", 60),
        ]:
            ctk.CTkLabel(
                th, text=text, font=(FONT, 11, "bold"),
                text_color=TEXT_DIM, width=w, anchor="w",
            ).pack(side="left", padx=(8, 0))

        # Cuerpo de tabla (scrollable)
        self._tbl = ctk.CTkScrollableFrame(
            self, fg_color=BG_INPUT, corner_radius=0,
        )
        self._tbl.pack(fill="both", expand=True, padx=18)

        # Barra inferior con botones
        bot = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=0)
        bot.pack(fill="x")
        bi = ctk.CTkFrame(bot, fg_color="transparent")
        bi.pack(pady=10)

        ctk.CTkButton(
            bi, text="Cancelar", font=(FONT, 13),
            fg_color=GRAY, hover_color=GRAY_LIGHT,
            corner_radius=8, height=38, width=120,
            command=self.destroy,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            bi, text="💾  Guardar cambios", font=(FONT, 13, "bold"),
            fg_color=GREEN, hover_color=GREEN_HOVER,
            corner_radius=8, height=38, width=180,
            command=self._save,
        ).pack(side="left", padx=6)

    # ── Cargar clientes ───────────────────────────────────────
    def _refresh(self) -> None:
        for w in self._tbl.winfo_children():
            w.destroy()
        self._entries.clear()

        vendor = self._vendor.get().strip()
        if not vendor:
            return

        pool = [
            c for c in self.app._clients
            if (c.executive_code or "").strip() == vendor
        ]
        if not pool:
            ctk.CTkLabel(
                self._tbl,
                text="No hay clientes para este vendedor.",
                font=(FONT, 12), text_color=TEXT_MUTED,
            ).pack(pady=20)
            return

        for i, c in enumerate(pool):
            bg = BG_CARD if i % 2 == 0 else BG_CARD_ALT
            rf = ctk.CTkFrame(
                self._tbl, fg_color=bg, corner_radius=0, height=36,
            )
            rf.pack(fill="x", pady=1)
            rf.pack_propagate(False)

            ctk.CTkLabel(
                rf, text=(c.name or "")[:48], font=(FONT, 11),
                text_color=TEXT, width=320, anchor="w",
            ).pack(side="left", padx=(8, 0))

            cur = c.last_visit.strftime("%d/%m/%Y") if c.last_visit else "—"
            ctk.CTkLabel(
                rf, text=cur, font=(FONT, 11),
                text_color=TEXT_DIM, width=110, anchor="w",
            ).pack(side="left")

            ent = ctk.CTkEntry(
                rf, width=140, height=26,
                fg_color=BG_INPUT, border_color=GRAY_DARK,
                placeholder_text="AAAA-MM-DD", font=(FONT, 11),
            )
            ent.pack(side="left")
            self._entries.append((c.row_index, c.name or "", ent))

            def _today(e=ent):
                e.delete(0, "end")
                e.insert(0, date.today().isoformat())

            ctk.CTkButton(
                rf, text="Hoy", width=50, height=24,
                font=(FONT, 10), fg_color=GRAY_DARK,
                hover_color=GRAY, corner_radius=4,
                command=_today,
            ).pack(side="left", padx=(6, 4))

    # ── Marcar todos hoy ──────────────────────────────────────
    def _mark_today(self) -> None:
        t = date.today().isoformat()
        for _, _, e in self._entries:
            e.delete(0, "end")
            e.insert(0, t)

    # ── Guardar ───────────────────────────────────────────────
    def _save(self) -> None:
        vendor = self._vendor.get().strip()
        updates: dict[int, date] = {}

        for ri, name, ent in self._entries:
            s = ent.get().strip()
            if not s:
                continue
            try:
                parts = s.split("-")
                if len(parts) != 3:
                    raise ValueError
                updates[ri] = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, TypeError):
                messagebox.showerror(
                    "Fecha inválida",
                    f"Formato esperado: AAAA-MM-DD.\n"
                    f"Problema con: {s!r}\nCliente: {name}",
                    parent=self,
                )
                return

        if not updates:
            messagebox.showwarning(
                "Sin cambios", "No ingresaste fechas nuevas.", parent=self,
            )
            return

        write_last_visits(
            self.app._wb, self.app._sheet_name,
            self.app._header_row, updates,
        )

        out = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"planilla_actualizada_{vendor}_"
                        f"{date.today().isoformat()}.xlsx",
            parent=self,
        )
        if not out:
            return

        try:
            save_workbook(self.app._wb, out)
        except Exception as exc:
            messagebox.showerror("Error al guardar", str(exc), parent=self)
            return

        # Recargar
        try:
            clients, wb, sheet, hdr = load_clients(out)
            self.app._clients = clients
            self.app._wb = wb
            self.app._sheet_name = sheet
            self.app._header_row = hdr
            self.app._excel_path = Path(out)
            self.app.set_status(
                f"📁 {self.app._excel_path.name} — {len(clients)} clientes",
                GREEN,
            )
        except Exception:
            pass

        messagebox.showinfo(
            "¡Listo!",
            f"Se actualizaron {len(updates)} fechas de última visita.\n\n"
            f"Archivo: {out}",
            parent=self,
        )
        self.destroy()


# ══════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════
def main() -> None:
    app = AgendaApp()
    app.mainloop()


if __name__ == "__main__":
    _log = Path(__file__).resolve().parent / "agenda_error.log"
    try:
        main()
    except BaseException:
        import traceback

        try:
            _log.write_text(traceback.format_exc(), encoding="utf-8")
        except OSError:
            pass
        raise
