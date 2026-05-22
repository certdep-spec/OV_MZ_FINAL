"""
Головне вікно програми CertifyPro
v2.0: Інтеграція з DI Container
"""

import logging
from tkinter import filedialog, messagebox

import customtkinter as ctk

import config
from exceptions import ConfigurationError, DatabaseError
from gui.client_badge import add_client_badge
from gui.gui_utils import restore_window_geometry, save_window_geometry

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{config.APP_NAME} v{config.VERSION}")
        self.geometry("700x450")
        self.minsize(700, 450)

        ctk.set_appearance_mode(config.APPEARANCE_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)

        # ===== ІНІЦІАЛІЗАЦІЯ СЕРВІСІВ ЧЕРЕЗ DI CONTAINER =====
        try:
            from di import DIContainer
            from documents.vc_generator import VCDocumentGenerator

            self.di_container = DIContainer()

            # Отримуємо сервіси через контейнер
            self.app_service = self.di_container.get_app_service()
            self.dict_service = self.di_container.get_dict_service()
            self.doc_service = self.di_container.get_doc_service()
            self.import_service = self.di_container.get_import_service()

            # VCDocumentGenerator використовує doc_service
            self.doc_gen = VCDocumentGenerator(
                str(config.TEMPLATES_DIR),
                str(config.DOCUMENTS_DIR),
                document_service=self.doc_service,
            )

        except (DatabaseError, ConfigurationError):
            raise
        except Exception:
            logger.error("Помилка імпорту/ініціалізації модулів", exc_info=True)
            self.doc_gen = None
            self.app_service = None
            self.dict_service = None
            self.doc_service = None
            self.import_service = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_widgets()
        # Відновлюємо збережену геометрію головного вікна
        self.after(100, lambda: restore_window_geometry(self, "MainWindow", 700, 450))
        self.after(100, self.show_welcome)
        # Бейдж клієнта у правому верхньому куті
        self.after(200, lambda: add_client_badge(self))

    def create_widgets(self):
        """Створення всіх віджетів"""

        # ===== ЛІВА ПАНЕЛЬ (МЕНЮ) =====
        self.sidebar = ctk.CTkFrame(
            self, width=220, corner_radius=0, fg_color="#2B2B2B"
        )
        self.sidebar.pack(side="left", fill="y")

        # Логотип
        self.lbl_title = ctk.CTkLabel(
            self.sidebar,
            text=f"⚙️ {config.APP_NAME}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#2B7CB9",
        )
        self.lbl_title.pack(pady=20)

        # Кнопка "Нова Заявка"
        self.btn_new_app = ctk.CTkButton(
            self.sidebar,
            text="➕ Нова Заявка",
            height=40,
            font=ctk.CTkFont(size=14),
            command=self.open_app_form,
        )
        self.btn_new_app.pack(pady=10, padx=10, fill="x")

        # Кнопка "Відкрити Заявку"
        self.btn_open_app = ctk.CTkButton(
            self.sidebar,
            text="📂 Відкрити Заявку",
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=config.COLORS["info"],
            command=self.open_existing_app,
        )
        self.btn_open_app.pack(pady=10, padx=10, fill="x")

        # Кнопка "Імпорт з Excel"
        self.btn_import = ctk.CTkButton(
            self.sidebar,
            text="📥 Імпорт з Excel",
            height=40,
            font=ctk.CTkFont(size=14),
            command=self.import_excel,
        )
        self.btn_import.pack(pady=10, padx=10, fill="x")

        # Кнопка "Історія"
        self.btn_history = ctk.CTkButton(
            self.sidebar,
            text="📜 Історія Заявок",
            height=40,
            font=ctk.CTkFont(size=14),
            command=self.show_history,
        )
        self.btn_history.pack(pady=10, padx=10, fill="x")

        # Кнопка "Довідники"
        self.btn_dictionaries = ctk.CTkButton(
            self.sidebar,
            text="📚 Довідники",
            height=40,
            font=ctk.CTkFont(size=14),
            command=self.open_dictionaries,
            fg_color=config.COLORS.get("warning", "#DAA520"),
        )
        self.btn_dictionaries.pack(pady=10, padx=10, fill="x")

        # Розділювач
        separator = ctk.CTkFrame(self.sidebar, height=2, fg_color="gray")
        separator.pack(pady=20, padx=10, fill="x")

        # Інфо про версію
        self.lbl_version = ctk.CTkLabel(
            self.sidebar,
            text=f"Версія {config.VERSION}",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        self.lbl_version.pack(side="bottom", pady=10)

        # ===== ПРАВА ПАНЕЛЬ (КОНТЕНТ) =====
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#3B3B3B")
        self.content_frame.pack(side="right", fill="both", expand=True)

        self.show_welcome()

    def show_welcome(self):
        """Показ екрану привітання"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        lbl_welcome = ctk.CTkLabel(
            self.content_frame,
            text=f"🎉 Ласкаво просимо до {config.APP_NAME}!",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#2B7CB9",
        )
        lbl_welcome.pack(pady=50)

        lbl_subtitle = ctk.CTkLabel(
            self.content_frame,
            text="Система автоматизації документації сертифікації",
            font=ctk.CTkFont(size=16),
            text_color="white",
        )
        lbl_subtitle.pack(pady=10)

        # Статистика
        stats_frame = ctk.CTkFrame(self.content_frame, fg_color="#2B2B2B")
        stats_frame.pack(pady=20)

        apps_count = 0
        if self.app_service:
            try:
                apps = self.app_service.get_all_applications()
                apps_count = len(apps)
            except Exception:
                logger.warning("Не вдалося завантажити статистику", exc_info=True)

        lbl_stats = ctk.CTkLabel(
            stats_frame,
            text=f"📊 Заявок в базі: {apps_count}",
            font=ctk.CTkFont(size=14),
            text_color="white",
        )
        lbl_stats.pack(pady=10)

    def open_app_form(self):
        """Відкриття форми нової заявки"""
        try:
            from gui.app_form import AppFormWindow

            self.form_window = AppFormWindow(
                self,
                self.app_service,
                self.doc_gen,
                self.dict_service,
                app_data=None,
            )
            self.wait_window(self.form_window)
            self.show_welcome()
        except Exception as e:
            logger.error("Не вдалося відкрити форму", exc_info=True)
            messagebox.showerror("Помилка", f"Не вдалося відкрити форму:\n{e}")

    def open_existing_app(self):
        """Відкриття існуючої заявки з бази"""
        try:
            from gui.app_form import AppFormWindow
            from gui.app_selector import AppSelectorDialog

            selector = AppSelectorDialog(self, self.app_service)
            self.wait_window(selector)

            if selector.selected_app:
                self.form_window = AppFormWindow(
                    self,
                    self.app_service,
                    self.doc_gen,
                    self.dict_service,
                    app_data=selector.selected_app,
                )
                self.wait_window(self.form_window)

            # Оновлюємо лічильник на головному екрані
            self.show_welcome()
        except Exception as e:
            logger.error("Не вдалося відкрити заявку", exc_info=True)
            messagebox.showerror("Помилка", f"Не вдалося відкрити заявку:\n{e}")

    def import_excel(self):
        """Імпорт даних з Excel"""
        file_path = filedialog.askopenfilename(
            title="Виберіть Excel файл",
            filetypes=[("Excel files", "*.xlsx *.xlsm")],
        )
        if file_path:
            if self.import_service:
                try:
                    stats = self.import_service.import_from_excel(file_path)
                    messagebox.showinfo(
                        "Імпорт завершено",
                        f"✅ Продуктів: {stats['products']}\n"
                        f"✅ Стандартів: {stats['standards']}\n"
                        f"✅ Потужностей: {stats['facilities']}\n"
                        f"✅ Складу: {stats['ingredients']}\n"
                        f"📝 Заявок: {stats['applications']}\n"
                        f"📦 Партій: {stats['parties']}\n"
                        f"❌ Помилок: {stats['errors']}",
                    )
                    self.show_welcome()

                    # Оновлюємо вікно довідників, якщо воно відкрите
                    if (
                        hasattr(self, "dictionaries_window")
                        and self.dictionaries_window.winfo_exists()
                    ):
                        self.dictionaries_window.refresh_all_tabs()
                except Exception as e:
                    logger.error("Не вдалося імпортувати Excel", exc_info=True)
                    messagebox.showerror("Помилка", f"Не вдалося імпортувати:\n{e}")
            else:
                messagebox.showerror("Помилка", "Сервіс імпорту не ініціалізовано")

    def show_history(self):
        """Показ історії заявок"""
        if self.app_service:
            try:
                apps = self.app_service.get_all_applications()
                if apps:
                    msg = "📋 ІСТОРІЯ ЗАЯВОК:\n\n"
                    for app in apps[:10]:
                        msg += f"№ {app.app_number} від {app.app_date}\n"
                        msg += f"   {app.company_name}\n\n"
                    messagebox.showinfo("Історія", msg)
                else:
                    messagebox.showinfo("Історія", "База даних порожня")
            except Exception as e:
                logger.error("Помилка показу історії", exc_info=True)
                messagebox.showerror("Помилка", str(e))
        else:
            messagebox.showinfo("Історія", "База даних не ініціалізована")

    def open_dictionaries(self):
        """Відкриття вікна управління довідниками"""
        try:
            from gui.dictionaries_window import DictionariesWindow

            # Перевіряємо, чи вікно вже відкрите
            if (
                hasattr(self, "dictionaries_window")
                and self.dictionaries_window.winfo_exists()
            ):
                self.dictionaries_window.lift()
                self.dictionaries_window.focus_set()
                return

            self.dictionaries_window = DictionariesWindow(self, self.dict_service)
        except Exception as e:
            logger.error("Не вдалося відкрити довідники", exc_info=True)
            messagebox.showerror("Помилка", f"Не вдалося відкрити довідники:\n{e}")

    def on_closing(self):
        """Акуратне закриття застосунку."""
        try:
            # Зберігаємо розмір та позицію головного вікна
            save_window_geometry(self, "MainWindow")

            # Перевірка цілісності БД та бекап
            if self.app_service:
                try:
                    if self.app_service.run_integrity_check():
                        logger.info("Перевірка цілісності БД: OK")
                    else:
                        logger.warning("Перевірка цілісності БД: ПОМИЛКА")

                    backup_dir = str(config.DATA_DIR / "backups")
                    backup_path = self.app_service.backup_database(backup_dir, max_backups=5)
                    if backup_path:
                        logger.info("Бекап БД: %s", backup_path)
                except Exception:
                    logger.warning("Не вдалося створити бекап БД", exc_info=True)

            # Закриття сервісів
            for service_name in [
                "app_service",
                "dict_service",
                "doc_service",
                "import_service",
            ]:
                service = getattr(self, service_name, None)
                if service and hasattr(service, "close"):
                    service.close()

            logger.info("Застосунок закрито")
        finally:
            self.destroy()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
