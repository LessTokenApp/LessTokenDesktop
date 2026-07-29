"""Tkinter desktop interface for LessToken."""
import os
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .ai.processor import AIProcessor, get_operation_labels
from .clipboard.monitor import ClipboardMonitor
from .config import AppConfig
from .files import load_text_from_file, save_text_to_file
from .image import ClipboardImageWatcher, ImageOptimizer, ImageTextReader


def _icon_path() -> Path:
    """Locate the bundled app icon, whether running from source or frozen."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent.parent
    return base / "assets" / "icon.ico"


class ClipboardOptimizerApp:
    """Desktop UI for text, image, and file workflows."""

    def __init__(self, root: tk.Tk, config: AppConfig) -> None:
        self.root = root
        self.config = config
        self.monitor = ClipboardMonitor(config.poll_interval_seconds)

        # Get API key for selected provider
        api_key = None
        if config.ai_provider == "openai":
            api_key = config.openai_api_key
        elif config.ai_provider == "claude":
            api_key = config.claude_api_key
        elif config.ai_provider == "gemini":
            api_key = config.gemini_api_key

        # Initialize processor with all features
        self.processor = AIProcessor(
            provider=config.ai_provider,
            model=config.provider_models.get(config.ai_provider, "gpt-4o-mini"),
            api_key=api_key,
            tracking_enabled=True,
            caching_enabled=True,
            quality_level="balanced",
        )

        self.image_optimizer = ImageOptimizer(config.output_dir)
        self.current_image = None
        self.last_image_path: Path | None = None
        self.operation_labels = get_operation_labels()
        self.label_to_key = {label: key for key, label in self.operation_labels.items()}
        self.status = tk.StringVar(value=self._initial_status())
        self.operation_label_var = tk.StringVar(value=self.operation_labels["clean"])
        self.image_format_var = tk.StringVar(value="JPEG")
        self.max_width_var = tk.IntVar(value=1600)
        self.quality_var = tk.IntVar(value=80)

        self.auto_shrink_var = tk.BooleanVar(value=False)
        self.auto_status_label: ttk.Label | None = None
        self.image_watcher = ClipboardImageWatcher(
            self.image_optimizer,
            on_result=self._on_auto_shrink,
            on_error=self._on_auto_shrink_error,
        )
        self._auto_poll_job = None

        # Token tracking variables
        self.monthly_budget_var = tk.DoubleVar(value=50.0)
        self.quality_level_var = tk.StringVar(value="balanced")

        self.root.title(config.app_name)
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        try:
            self.root.iconbitmap(default=str(_icon_path()))
        except tk.TclError:
            pass  # icon file missing or unsupported on this platform; not fatal
        self._build_layout()
        # Ctrl+V only pastes an image while the Görsel tab is active; on any
        # other tab a Text widget's own built-in paste binding already
        # handles it first and stops the event from reaching this one.
        self.root.bind_all("<Control-v>", self._on_ctrl_v_pressed)
        self.root.after(300, self.load_clipboard_text)
        self.root.after(5000, self.refresh_status_bar)

    def _initial_status(self) -> str:
        if self.processor.is_ai_enabled:
            return "Hazır - OpenAI modu aktif"
        return "Hazır - yerel mod aktif"

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.rowconfigure(1, weight=1)
        outer.columnconfigure(0, weight=1)

        # Title with stats
        header_frame = ttk.Frame(outer)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(header_frame, text="LessToken", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)

        # Notebook tabs
        notebook = ttk.Notebook(outer)
        notebook.grid(row=1, column=0, sticky="nsew", pady=10)
        self._build_text_tab(notebook)
        self._build_image_tab(notebook)
        self._build_file_tab(notebook)
        self._build_stats_tab(notebook)
        self._build_settings_tab(notebook)
        self.notebook = notebook

        # Enhanced status bar
        status_frame = ttk.Frame(outer)
        status_frame.grid(row=2, column=0, sticky="ew")
        ttk.Label(status_frame, textvariable=self.status).pack(side=tk.LEFT, expand=True, fill=tk.X)

    def _build_text_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="Metin")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        tab.rowconfigure(5, weight=1)
        ttk.Label(tab, text="Kaynak metin").grid(row=0, column=0, sticky="w")
        self.input_text = tk.Text(tab, height=9, wrap="word", undo=True)
        self.input_text.grid(row=1, column=0, sticky="nsew", pady=(4, 10))
        controls = ttk.Frame(tab)
        controls.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(controls, text="Panodan al", command=self.load_clipboard_text).pack(side=tk.LEFT)
        ttk.Button(controls, text="Çalıştır", command=self.run_selected_text_operation).pack(side=tk.LEFT, padx=6)
        ttk.Combobox(controls, textvariable=self.operation_label_var, values=list(self.operation_labels.values()), width=22, state="readonly").pack(side=tk.LEFT)
        ttk.Button(controls, text="Sonucu panoya kopyala", command=self.copy_text_result).pack(side=tk.LEFT, padx=6)
        ttk.Button(controls, text="Sonucu kaydet", command=self.save_text_result).pack(side=tk.LEFT)
        ttk.Button(controls, text="Temizle", command=self.clear_text).pack(side=tk.RIGHT)
        quick = ttk.Frame(tab)
        quick.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        for key, label in self.operation_labels.items():
            ttk.Button(quick, text=label, command=lambda item=key: self.run_text_operation(item)).pack(side=tk.LEFT, padx=(0, 6), pady=2)
        ttk.Label(tab, text="Sonuç").grid(row=4, column=0, sticky="w")
        self.output_text = tk.Text(tab, height=9, wrap="word", undo=True)
        self.output_text.grid(row=5, column=0, sticky="nsew", pady=(4, 0))

    def _build_image_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="Görsel")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(3, weight=1)
        top = ttk.Frame(tab)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Button(top, text="Panodaki görseli al", command=self.load_clipboard_image).pack(side=tk.LEFT)
        ttk.Button(top, text="Görsel dosyası aç", command=self.open_image_file).pack(side=tk.LEFT, padx=6)
        ttk.Button(top, text="Görseli küçült ve kaydet", command=self.resize_current_image).pack(side=tk.LEFT)
        ttk.Button(top, text="Son görseli panoya kopyala", command=self.copy_last_image).pack(side=tk.LEFT, padx=6)
        auto = ttk.Frame(tab)
        auto.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Checkbutton(
            auto,
            text="Otomatik küçült (panoyu izle)",
            variable=self.auto_shrink_var,
            command=self.toggle_auto_shrink,
        ).pack(side=tk.LEFT)
        self.auto_status_label = ttk.Label(auto, text="kapalı")
        self.auto_status_label.pack(side=tk.LEFT, padx=10)

        options = ttk.Frame(tab)
        options.grid(row=1, column=0, sticky="ew", pady=10)
        ttk.Label(options, text="Maks. genişlik").pack(side=tk.LEFT)
        ttk.Spinbox(options, from_=320, to=8000, increment=100, textvariable=self.max_width_var, width=8).pack(side=tk.LEFT, padx=6)
        ttk.Label(options, text="Kalite").pack(side=tk.LEFT)
        ttk.Spinbox(options, from_=30, to=100, increment=5, textvariable=self.quality_var, width=6).pack(side=tk.LEFT, padx=6)
        ttk.Label(options, text="Format").pack(side=tk.LEFT)
        ttk.Combobox(options, textvariable=self.image_format_var, values=["JPEG", "PNG", "WEBP"], width=8, state="readonly").pack(side=tk.LEFT, padx=6)
        ttk.Button(options, text="Görselden metin oku", command=self.extract_image_text).pack(side=tk.LEFT, padx=8)
        ttk.Button(options, text="Bilgi ver", command=self.describe_image).pack(side=tk.LEFT)
        ttk.Label(tab, text="Görsel işlemi sonucu").grid(row=2, column=0, sticky="w")
        self.image_info_text = tk.Text(tab, height=14, wrap="word")
        self.image_info_text.grid(row=3, column=0, sticky="nsew", pady=(4, 0))
        self.image_info_text.tag_configure("link", foreground="blue", underline=True)
        self.image_info_text.tag_bind("link", "<Button-1>", self._on_file_link_click)
        self.image_info_text.tag_bind("link", "<Enter>", lambda e: self.image_info_text.config(cursor="hand2"))
        self.image_info_text.tag_bind("link", "<Leave>", lambda e: self.image_info_text.config(cursor="arrow"))

    def _build_file_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="Dosya")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        controls = ttk.Frame(tab)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(controls, text="Dosyadan metin yükle", command=self.load_file_text).pack(side=tk.LEFT)
        ttk.Button(controls, text="Metin sekmesine aktar", command=self.move_file_text_to_text_tab).pack(side=tk.LEFT, padx=6)
        ttk.Button(controls, text="Sonucu dosyaya kaydet", command=self.save_file_text).pack(side=tk.LEFT)
        ttk.Button(controls, text="Temizle", command=self.clear_file_text).pack(side=tk.RIGHT)
        self.file_text = tk.Text(tab, height=20, wrap="word", undo=True)
        self.file_text.grid(row=1, column=0, sticky="nsew")

    def load_clipboard_text(self) -> None:
        clipboard_text = self.monitor.read_current()
        if not clipboard_text:
            self.status.set("Panoda okunabilir metin yok.")
            return
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", clipboard_text)
        self.status.set("Pano metni alındı.")

    def run_selected_text_operation(self) -> None:
        label = self.operation_label_var.get()
        self.run_text_operation(self.label_to_key.get(label, "clean"))

    def run_text_operation(self, operation: str) -> None:
        source = self.input_text.get("1.0", tk.END).strip()
        if not source:
            messagebox.showinfo("Bilgi", "Önce panodan metin al veya metin yaz.")
            return
        result = self.processor.optimize_text(source, operation)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", result)
        self.status.set(f"{self.operation_labels.get(operation, 'İşlem')} tamamlandı.")

    def copy_text_result(self) -> None:
        result = self.output_text.get("1.0", tk.END).strip()
        if not result:
            messagebox.showinfo("Bilgi", "Kopyalanacak sonuç yok.")
            return
        try:
            self.monitor.write_text(result)
        except RuntimeError as exc:
            messagebox.showerror("Hata", str(exc))
            return
        self.status.set("Sonuç panoya kopyalandı.")

    def save_text_result(self) -> None:
        result = self.output_text.get("1.0", tk.END).strip()
        if not result:
            messagebox.showinfo("Bilgi", "Kaydedilecek sonuç yok.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt"), ("Markdown", "*.md")])
        if path:
            save_text_to_file(path, result)
            self.status.set(f"Sonuç kaydedildi: {path}")

    def clear_text(self) -> None:
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.status.set("Metin alanları temizlendi.")

    def load_clipboard_image(self) -> None:
        try:
            image = self.image_optimizer.get_clipboard_image()
        except RuntimeError as exc:
            messagebox.showerror("Hata", str(exc))
            return
        if image is None:
            self._set_image_info("Panoda görsel bulunamadı.")
            return
        self.current_image = image
        self._set_image_info(self.image_optimizer.describe_image(image))
        self.status.set("Panodaki görsel alındı.")

    def open_image_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif")])
        if not path:
            return
        try:
            self.current_image = self.image_optimizer.open_image(path)
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))
            return
        self._set_image_info(f"Dosya açıldı: {path}\n{self.image_optimizer.describe_image(self.current_image)}")
        self.status.set("Görsel dosyası açıldı.")

    def _on_ctrl_v_pressed(self, event=None) -> None:
        try:
            current_tab = self.notebook.tab(self.notebook.select(), "text")
        except tk.TclError:
            return
        if current_tab != "Görsel":
            return
        self.paste_and_shrink_image()

    def paste_and_shrink_image(self) -> None:
        """Ctrl+V on the Görsel tab: grab, shrink, and copy back in one step."""
        try:
            image = self.image_optimizer.get_clipboard_image()
        except RuntimeError as exc:
            messagebox.showerror("Hata", str(exc))
            return
        if image is None:
            self._set_image_info("Panoda görsel bulunamadı.")
            self.status.set("Panoda görsel bulunamadı.")
            return

        self.current_image = image
        try:
            result = self.image_optimizer.save_resized(
                image, self.max_width_var.get(), self.quality_var.get(), self.image_format_var.get()
            )
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))
            return

        self.last_image_path = result.path
        copied = self.image_optimizer.copy_image_to_clipboard(result.path)
        text, links = self._format_image_result(result)
        self._set_image_info_with_links(text, links)

        kb = result.new_bytes / 1024
        ow, oh = result.original_size
        w, h = result.new_size
        if copied:
            self.status.set(f"Yapıştırılan görsel küçültüldü: {ow}x{oh} -> {w}x{h} ({kb:.0f} KB). Panoya kopyalandı.")
        else:
            self.status.set(f"Görsel küçültüldü ({ow}x{oh} -> {w}x{h}) ama panoya kopyalanamadı. Dosya: {result.path}")

    def toggle_auto_shrink(self) -> None:
        """Start or stop watching the clipboard for images to shrink."""
        if self.auto_shrink_var.get():
            self.image_watcher.enabled = True
            # Adopt the current clipboard so switching this on does not
            # rewrite an image the user already had.
            self.image_watcher.prime()
            self._schedule_auto_poll()
            self._set_auto_status("izleniyor")
            self.status.set("Pano izleniyor: yeni görseller otomatik küçültülecek.")
        else:
            self.image_watcher.enabled = False
            if self._auto_poll_job is not None:
                self.root.after_cancel(self._auto_poll_job)
                self._auto_poll_job = None
            self._set_auto_status("kapalı")
            self.status.set("Pano izleme durduruldu.")

    def _schedule_auto_poll(self) -> None:
        interval_ms = max(200, int(self.config.poll_interval_seconds * 1000))
        self._auto_poll_job = self.root.after(interval_ms, self._auto_poll)

    def _auto_poll(self) -> None:
        if not self.auto_shrink_var.get():
            self._auto_poll_job = None
            return
        # Pick up any settings the user changed since the last tick.
        self.image_watcher.max_width = self.max_width_var.get()
        self.image_watcher.quality = self.quality_var.get()
        self.image_watcher.fmt = self.image_format_var.get()
        self.image_watcher.poll()
        self._schedule_auto_poll()

    def _on_auto_shrink(self, result) -> None:
        kb = result.new_bytes / 1024
        w, h = result.new_size
        ow, oh = result.original_size
        if result.copied:
            self._set_auto_status(f"{ow}x{oh} -> {w}x{h}, {kb:.0f} KB")
            self.status.set(
                f"Panodaki görsel küçültüldü: {ow}x{oh} -> {w}x{h} ({kb:.0f} KB). "
                "Yapıştırmaya hazır."
            )
        else:
            self._set_auto_status(f"{ow}x{oh} -> {w}x{h}, kopyalanamadı")
            self.status.set(
                f"Görsel küçültüldü ({ow}x{oh} -> {w}x{h}, {kb:.0f} KB) ama panoya kopyalanamadı."
            )

    def _on_auto_shrink_error(self, exc: Exception) -> None:
        self._set_auto_status("hata")
        self.status.set(f"Otomatik küçültme başarısız: {exc}")

    def _set_auto_status(self, text: str) -> None:
        if self.auto_status_label is not None:
            self.auto_status_label.config(text=text)

    def resize_current_image(self) -> None:
        if self.current_image is None:
            messagebox.showinfo("Bilgi", "Önce panodan veya dosyadan görsel alın.")
            return
        try:
            result = self.image_optimizer.save_resized(self.current_image, self.max_width_var.get(), self.quality_var.get(), self.image_format_var.get())
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))
            return
        self.last_image_path = result.path
        text, links = self._format_image_result(result)
        self._set_image_info_with_links(text, links)
        self.status.set(f"Görsel kaydedildi: {result.path}")

    def copy_last_image(self) -> None:
        if self.last_image_path is None:
            messagebox.showinfo("Bilgi", "Önce bir görseli küçültüp kaydet.")
            return
        copied = self.image_optimizer.copy_image_to_clipboard(self.last_image_path)
        if copied:
            self.status.set("Son görsel panoya kopyalandı.")
        else:
            messagebox.showinfo("Bilgi", "Panoya görsel kopyalamak için pywin32 gerekir. Dosya kaydedildi.")

    def extract_image_text(self) -> None:
        if self.current_image is None:
            messagebox.showinfo("Bilgi", "Önce panodan veya dosyadan görsel alın.")
            return

        self.status.set("Görselden metin okunuyor...")
        self.root.update_idletasks()

        reader = ImageTextReader(self.image_optimizer, self._vision_provider())
        result = reader.read(self.current_image)
        self._set_image_info(result.text)

        if result.source in {"none", "error"}:
            self.status.set(result.text)
            return

        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", result.text)

        note = "yerel OCR" if result.source == "tesseract" else result.source
        cost = f", ~${result.cost_usd:.4f}" if result.cost_usd else ""
        self.status.set(
            f"Görselden metin okundu ({note}{cost}) ve Metin sekmesine aktarıldı."
        )

    def _vision_provider(self):
        """Return a provider that can read images, or None."""
        keys = {
            "openai": self.config.openai_api_key,
            "claude": self.config.claude_api_key,
            "gemini": self.config.gemini_api_key,
        }
        name = self.config.ai_provider
        if name not in keys or not keys[name]:
            return None

        try:
            from .ai.providers import ProviderFactory

            provider = ProviderFactory.create(name, keys[name])
        except Exception:
            # A missing SDK or bad credentials should not break the button;
            # read() reports the situation to the user instead.
            return None

        return provider if getattr(provider, "supports_vision", False) else None

    def describe_image(self) -> None:
        if self.current_image is None:
            messagebox.showinfo("Bilgi", "Önce panodan veya dosyadan görsel alın.")
            return
        self._set_image_info(self.image_optimizer.describe_image(self.current_image))

    def _set_image_info(self, text: str) -> None:
        self.image_info_text.delete("1.0", tk.END)
        self.image_info_text.insert("1.0", text)

    def _format_image_result(self, result) -> tuple[str, list[tuple[str, int, int]]] | str:
        kb = result.new_bytes / 1024
        return (
            f"Kaydedilen dosya: {result.path}\n"
            f"Eski boyut: {result.original_size[0]}x{result.original_size[1]}\n"
            f"Yeni boyut: {result.new_size[0]}x{result.new_size[1]}\n"
            f"Yeni dosya boyutu: {kb:.1f} KB",
            [("link", len("Kaydedilen dosya: "), len("Kaydedilen dosya: ") + len(result.path))]
        )

    def _set_image_info_with_links(self, text: str, links: list[tuple[str, int, int]] | None = None) -> None:
        self.image_info_text.delete("1.0", tk.END)
        self.image_info_text.insert("1.0", text)
        if links:
            for tag, start, end in links:
                self.image_info_text.tag_add(tag, f"1.{start}", f"1.{end}")

    def _on_file_link_click(self, event) -> None:
        try:
            index = self.image_info_text.index(f"@{event.x},{event.y}")
            line_start = f"{index.split('.')[0]}.0"
            line_end = f"{index.split('.')[0]}.end"
            line_text = self.image_info_text.get(line_start, line_end)

            if ":" in line_text and "/" in line_text or "\\" in line_text:
                path_part = line_text.split(": ", 1)[-1].strip()
                if os.path.exists(path_part):
                    if os.path.isfile(path_part):
                        os.startfile(os.path.dirname(path_part))
                    else:
                        os.startfile(path_part)
        except Exception as exc:
            messagebox.showerror("Hata", f"Dosya açılamadı: {exc}")

    def load_file_text(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Supported", "*.txt;*.md;*.csv;*.json;*.py;*.js;*.html;*.css;*.pdf;*.docx"), ("All files", "*.*")])
        if not path:
            return
        try:
            text = load_text_from_file(path)
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))
            return
        self.file_text.delete("1.0", tk.END)
        self.file_text.insert("1.0", text)
        self.status.set(f"Dosya yüklendi: {path}")

    def move_file_text_to_text_tab(self) -> None:
        text = self.file_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Bilgi", "Aktarılacak metin yok.")
            return
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", text)
        self.status.set("Dosya metni Metin sekmesine aktarıldı.")

    def save_file_text(self) -> None:
        text = self.file_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Bilgi", "Kaydedilecek metin yok.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt"), ("Markdown", "*.md")])
        if path:
            save_text_to_file(path, text)
            self.status.set(f"Dosya kaydedildi: {path}")

    def clear_file_text(self) -> None:
        self.file_text.delete("1.0", tk.END)
        self.status.set("Dosya alanı temizlendi.")

    def _build_stats_tab(self, notebook: ttk.Notebook) -> None:
        """Build statistics and cost tracking tab."""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="İstatistikler")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        # Summary section
        summary_frame = ttk.LabelFrame(tab, text="Özet (30 gün)", padding=10)
        summary_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        try:
            stats = self.processor.tracker.get_summary(period_days=30)
            summary_text = f"""
Toplam API Çağrısı: {stats['total_calls']}
Girdi Token: {stats['total_input_tokens']:,}
Çıktı Token: {stats['total_output_tokens']:,}
Toplam Maliyet: ${stats['total_cost']:.2f}
            """.strip()
        except Exception:
            summary_text = "Token takibi kullanılamıyor"

        ttk.Label(summary_frame, text=summary_text, justify=tk.LEFT).pack(anchor="w")

        # Recommendations section
        recommendations_frame = ttk.LabelFrame(tab, text="Öneriler", padding=10)
        recommendations_frame.grid(row=1, column=0, sticky="nsew")
        recommendations_frame.rowconfigure(0, weight=1)
        recommendations_frame.columnconfigure(0, weight=1)

        try:
            recommendations = self.processor.tracker.get_recommendations()
            if recommendations:
                rec_text = "\n\n".join([
                    f"💡 {rec.title}\n   {rec.description}\n   Tahmini tasarruf: ${rec.estimated_savings:.2f}/ay"
                    for rec in recommendations[:3]
                ])
            else:
                rec_text = "Şu anda öneri yok"
        except Exception:
            rec_text = "Öneriler kullanılamıyor"

        rec_display = tk.Text(recommendations_frame, height=8, wrap="word")
        rec_display.grid(row=0, column=0, sticky="nsew")
        rec_display.insert("1.0", rec_text)
        rec_display.config(state=tk.DISABLED)

    def _build_settings_tab(self, notebook: ttk.Notebook) -> None:
        """Build settings and configuration tab."""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="Ayarlar")
        tab.columnconfigure(0, weight=1)

        # Provider selection
        ttk.Label(tab, text="AI Sağlayıcı", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        provider_frame = ttk.Frame(tab)
        provider_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        providers = ["claude", "openai", "gemini", "ollama", "local"]
        provider_var = tk.StringVar(value=self.config.ai_provider)
        for provider in providers:
            ttk.Radiobutton(provider_frame, text=provider.capitalize(), variable=provider_var, value=provider).pack(side=tk.LEFT, padx=10)

        # Quality level
        ttk.Label(tab, text="Kalite Seviyesi", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 5))
        ttk.Scale(tab, from_=0, to=2, orient=tk.HORIZONTAL, variable=self.quality_level_var, command=self._on_quality_changed).grid(row=3, column=0, sticky="ew", pady=(0, 15))
        quality_labels = ttk.Frame(tab)
        quality_labels.grid(row=4, column=0, sticky="ew", pady=(0, 15))
        for i, label in enumerate(["Ekonomik", "Dengeli", "Premium"]):
            ttk.Label(quality_labels, text=label).pack(side=tk.LEFT, expand=True)

        # Monthly budget
        ttk.Label(tab, text="Aylık Bütçe (USD)", font=("Segoe UI", 10, "bold")).grid(row=5, column=0, sticky="w", pady=(0, 5))
        budget_frame = ttk.Frame(tab)
        budget_frame.grid(row=6, column=0, sticky="ew", pady=(0, 15))
        ttk.Spinbox(budget_frame, from_=5, to=1000, textvariable=self.monthly_budget_var, width=10).pack(side=tk.LEFT)

        # Feature toggles
        ttk.Label(tab, text="Özellikler", font=("Segoe UI", 10, "bold")).grid(row=7, column=0, sticky="w", pady=(0, 5))
        features_frame = ttk.Frame(tab)
        features_frame.grid(row=8, column=0, sticky="ew")
        ttk.Checkbutton(features_frame, text="Prompt Optimizasyonu Aktif").pack(anchor="w", pady=2)
        ttk.Checkbutton(features_frame, text="Yerel Önbellekleme Aktif").pack(anchor="w", pady=2)
        ttk.Checkbutton(features_frame, text="Token Takibi Aktif").pack(anchor="w", pady=2)

    def refresh_status_bar(self) -> None:
        """Update status bar with current token usage."""
        try:
            stats = self.processor.tracker.get_summary(period_days=30)
            budget = self.monthly_budget_var.get()
            used_percent = (stats["total_cost"] / budget * 100) if budget > 0 else 0
            quality_display = {"budget": "Ekonomik", "balanced": "Dengeli", "premium": "Premium"}.get(
                self.quality_level_var.get(), self.quality_level_var.get()
            )
            status_text = f"Token: {stats['total_input_tokens']:,} | Maliyet: ${stats['total_cost']:.2f}/${budget} | Kalite: {quality_display}"
            self.status.set(status_text)
        except Exception:
            pass
        # Schedule next refresh
        self.root.after(5000, self.refresh_status_bar)

    def _on_quality_changed(self, value: str) -> None:
        """Handle quality level slider change."""
        quality_map = {0: "budget", 1: "balanced", 2: "premium"}
        self.quality_level_var.set(quality_map.get(int(float(value)), "balanced"))


def run_gui(config: AppConfig) -> None:
    """Launch the desktop UI."""
    root = tk.Tk()
    ClipboardOptimizerApp(root, config)
    root.mainloop()
