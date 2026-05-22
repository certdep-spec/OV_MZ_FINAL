"""
Діалог управління заявниками (клієнтами).

Додавання, редагування, видалення заявників.
"""

import logging
from tkinter import messagebox, ttk
from typing import Optional

import customtkinter as ctk
from client_launcher.applicants_db import ApplicantDTO, ApplicantsDB
from client_launcher.geometry_manager import (
    restore_window_geometry,
    save_window_geometry,
)

logger = logging.getLogger(__name__)


class ApplicantsManagerDialog(ctk.CTkToplevel):
    """Діалог управління заявниками"""

    def __init__(self, parent=None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)

        self.title("⚙️ Керування заявниками")
        self.geometry("800x500")

        if parent:
            self.transient(parent)
            self.grab_set()

        self.db = ApplicantsDB()

        self._create_widgets()
        self._load_applicants()

        # Відновлення геометрії
        self.after(
            100,
            lambda: restore_window_geometry(self, "ApplicantsManagerDialog", 800, 500),
        )
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        """Створення віджетів"""
        # Заголовок
        ctk.CTkLabel(
            self,
            text="⚙️ Керування заявниками",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=10)

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=5)

        ctk.CTkButton(
            btn_frame,
            text="➕ Додати",
            height=30,
            fg_color="#2B7CB9",
            command=self._on_add,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="✏️ Редагувати",
            height=30,
            fg_color="#2E8B57",
            command=self._on_edit,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🗑️ Видалити",
            height=30,
            fg_color="#DC143C",
            command=self._on_delete,
        ).pack(side="left", padx=5)

        # Таблиця
        columns = (
            "№",
            "nazva_pidpryyemstva",
            "adresa_pidpryyemstva",
            "kod_edrpou",
            "kerivnik",
            "papka_proektu",
            "template_suffix",
        )

        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=12,
        )

        headers = {
            "№": "№",
            "nazva_pidpryyemstva": "Назва підприємства",
            "adresa_pidpryyemstva": "Адреса",
            "kod_edrpou": "ЄДРПОУ",
            "kerivnik": "Керівник",
            "papka_proektu": "Папка проекту",
            "template_suffix": "Суфікс",
        }

        widths = {
            "№": 40,
            "nazva_pidpryyemstva": 200,
            "adresa_pidpryyemstva": 250,
            "kod_edrpou": 100,
            "kerivnik": 120,
            "papka_proektu": 100,
            "template_suffix": 60,
        }

        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col])

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Кнопка закриття
        ctk.CTkButton(
            self,
            text="✅ Закрити",
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color="gray",
            command=self.destroy,
        ).pack(pady=10)

    def _load_applicants(self):
        """Завантаження заявників в таблицю"""
        # Очищення
        for item in self.tree.get_children():
            self.tree.delete(item)

        applicants = self.db.get_all_applicants()

        for i, a in enumerate(applicants, 1):
            # Зберігаємо database ID у тегах — це ключове виправлення!
            self.tree.insert(
                "",
                "end",
                values=(
                    i,
                    a.nazva_pidpryyemstva,
                    a.adresa_pidpryyemstva,
                    a.kod_edrpou,
                    a.kerivnik,
                    a.papka_proektu,
                    a.template_suffix,
                ),
                tags=(str(a.id),),
            )

    def _get_selected_item(self):
        """Отримати обраний елемент"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Увага", "Оберіть запис!")
            return None
        return selection[0]

    def _get_selected_applicant(self) -> Optional[ApplicantDTO]:
        """Отримати DTO обраного заявника з справжнім database ID"""
        item = self._get_selected_item()
        if item is None:
            return None

        values = self.tree.item(item, "values")
        # Читаємо database ID з тегів — це виправляє баг пошуку за назвою!
        tags = self.tree.item(item, "tags")
        db_id = int(tags[0]) if tags else 0

        return ApplicantDTO(
            id=db_id,
            nazva_pidpryyemstva=values[1],
            adresa_pidpryyemstva=values[2],
            kod_edrpou=values[3],
            kerivnik=values[4],
            papka_proektu=values[5],
            template_suffix=values[6] if len(values) > 6 else "_Д",
        )

    def _on_add(self):
        """Додавання нового заявника"""
        dialog = ApplicantEditDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            # Отладочное логирование
            try:
                from client_launcher.debug_logger import log_stage

                log_stage(
                    "1_LAUNCHER_DIALOG_SAVE",
                    {
                        "nazva_pidpryyemstva": dialog.result.nazva_pidpryyemstva,
                        "adresa_pidpryyemstva": dialog.result.adresa_pidpryyemstva,
                        "kod_edrpou": dialog.result.kod_edrpou,
                        "kerivnik": dialog.result.kerivnik,
                        "papka_proektu": dialog.result.papka_proektu,
                    },
                )
            except Exception as e:
                logger.warning(f"Не удалось записать debug лог: {e}")

            import sqlite3

            try:
                # auto_provision=True за замовчуванням — створить папки, БД, profiles.yaml
                self.db.add_applicant(dialog.result)
                self._load_applicants()

                # Показуємо інформаційне повідомлення про створену інфраструктуру
                messagebox.showinfo(
                    "Успіх",
                    "Заявника додано!\n\n"
                    "📁 Створено папку проекту\n"
                    "💾 Ініціалізовано пусту БД\n"
                    "📝 Зареєстровано в profiles.yaml",
                )
            except sqlite3.IntegrityError as e:
                messagebox.showerror("Помилка", str(e))
            except RuntimeError as e:
                # Помилка provisioner — інфраструктуру не створено
                messagebox.showerror(
                    "Помилка створення інфраструктури",
                    f"Заявника додано в реєстр, але не вдалося створити інфраструктуру:\n\n"
                    f"{str(e)}\n\n"
                    f"Спробуйте додати повторно або зверніться до адміністратора.",
                )
                self._load_applicants()  # Перезавантажуємо (може бути видалено при відкаті)

    def _on_edit(self):
        """Редагування обраного заявника"""
        applicant = self._get_selected_applicant()
        if applicant is None:
            return

        dialog = ApplicantEditDialog(self, applicant)
        self.wait_window(dialog)

        if dialog.result:
            # Використовуємо справжній database ID з DTO — більше ніякого пошуку за назвою!
            dialog.result.id = applicant.id
            self.db.update_applicant(dialog.result)
            self._load_applicants()
            messagebox.showinfo("Успіх", "Дані оновлено!")

    def _on_delete(self):
        """Видалення обраного заявника"""
        applicant = self._get_selected_applicant()
        if applicant is None:
            return

        # Запитуємо також про видалення папки даних
        confirm = messagebox.askyesno(
            "Підтвердження",
            f"Видалити заявника '{applicant.nazva_pidpryyemstva}'?\n\n"
            f"⚠️ Папка проекту '{applicant.papka_proektu}' ТАКОЖ буде видалена!\n"
            f"Всі дані клієнта (БД, документи) будуть втрачені.",
        )

        if confirm:
            # Використовуємо справжній database ID — більше ніякого пошуку за назвою!
            self.db.delete_applicant(applicant.id, delete_folder=True)
            self._load_applicants()
            messagebox.showinfo("Успіх", "Заявника видалено!")

    def _on_close(self):
        """Збереження геометрії перед закриттям"""
        save_window_geometry(self, "ApplicantsManagerDialog")
        self.destroy()


class ApplicantEditDialog(ctk.CTkToplevel):
    """Діалог редагування даних заявника"""

    def __init__(self, parent, applicant: Optional[ApplicantDTO] = None):
        super().__init__(parent)

        self.title("➕ Новий заявник" if not applicant else "✏️ Редагування")
        self.geometry("450x450")
        self.transient(parent)
        self.grab_set()

        self.result: Optional[ApplicantDTO] = None
        self._is_editing = applicant is not None

        if applicant:
            self._applicant = applicant
        else:
            self._applicant = ApplicantDTO()

        self._create_widgets()

        if self._is_editing:
            self._fill_fields()

        # Відновлення геометрії
        self.after(
            100, lambda: restore_window_geometry(self, "ApplicantEditDialog", 450, 450)
        )
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        """Створення полів форми"""
        ctk.CTkLabel(
            self,
            text="➕ Новий заявник" if not self._is_editing else "✏️ Редагування",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=15)

        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Назва підприємства
        ctk.CTkLabel(form_frame, text="Назва підприємства:").grid(
            row=0, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_nazva = ctk.CTkEntry(form_frame, width=300)
        self.entry_nazva.grid(row=0, column=1, pady=8, padx=10)

        # Адреса
        ctk.CTkLabel(form_frame, text="Адреса:").grid(
            row=1, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_adresa = ctk.CTkEntry(form_frame, width=300)
        self.entry_adresa.grid(row=1, column=1, pady=8, padx=10)

        # ЄДРПОУ
        ctk.CTkLabel(form_frame, text="ЄДРПОУ:").grid(
            row=2, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_edrpou = ctk.CTkEntry(form_frame, width=300)
        self.entry_edrpou.grid(row=2, column=1, pady=8, padx=10)

        # Керівник
        ctk.CTkLabel(form_frame, text="Керівник:").grid(
            row=3, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_kerivnik = ctk.CTkEntry(form_frame, width=300)
        self.entry_kerivnik.grid(row=3, column=1, pady=8, padx=10)

        # Папка проекту
        ctk.CTkLabel(form_frame, text="Папка проекту:").grid(
            row=4, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_papka = ctk.CTkEntry(form_frame, width=300)
        self.entry_papka.grid(row=4, column=1, pady=8, padx=10)

        # Суфікс шаблонів
        ctk.CTkLabel(form_frame, text="Суфікс шаблонів:").grid(
            row=5, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_suffix = ctk.CTkEntry(form_frame, width=300, placeholder_text="Наприклад: _П")
        self.entry_suffix.grid(row=5, column=1, pady=8, padx=10)

        # Прив'язуємо буфер обміну (один раз для всього вікна)
        self.after(100, lambda: self._enable_clipboard_bindings(self.entry_nazva))

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="✅ Зберегти",
            height=35,
            fg_color="#2E8B57",
            command=self._on_save,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="❌ Скасувати",
            height=35,
            fg_color="gray",
            command=self.destroy,
        ).pack(side="left", padx=10)

    def _enable_clipboard_bindings(self, entry_widget):
        """
        Додає підтримку буфера обміну (Ctrl+C, Ctrl+V, Ctrl+X) для CTkEntry.

        Використовуємо bind_class на рівні всього вікна.
        Для Ctrl+V використовуємо пряму роботу з clipboard замість event_generate.
        """
        try:
            root = self.winfo_toplevel()

            # Використовуємо bind_class на рівні вікна — це працює для всіх Entry
            root.bind_class("Entry", "<Control-c>", self._on_ctrl_c)
            root.bind_class("Entry", "<Control-v>", self._on_ctrl_v)
            root.bind_class("Entry", "<Control-x>", self._on_ctrl_x)

            # Правая кнопка мыши — контекстное меню
            root.bind_class("Entry", "<Button-3>", self._on_right_click)

            logger.info("✅ Буфер обміну активовано через bind_class")
        except Exception as e:
            logger.error(f"❌ Помилка активації буфера обміну: {e}", exc_info=True)

    def _on_ctrl_c(self, event):
        """Обробка Ctrl+C — копіювати."""
        try:
            widget = event.widget
            if widget.selection_present():
                selected_text = widget.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
                logger.debug(f"📋 Скопійовано: {selected_text[:50]}...")
        except Exception as e:
            logger.debug(f"⚠️ Ctrl+C помилка: {e}")

    def _on_ctrl_v(self, event):
        """Обробка Ctrl+V — вставити."""
        try:
            widget = event.widget
            clipboard_text = self.clipboard_get()
            if clipboard_text:
                # Вставляємо в позицію курсора або замінюємо виділене
                if widget.selection_present():
                    widget.delete("sel.first", "sel.last")
                widget.insert("insert", clipboard_text)
                logger.debug(f"📋 Вставлено: {clipboard_text[:50]}...")
        except Exception as e:
            logger.debug(f"⚠️ Ctrl+V помилка: {e}")

    def _on_ctrl_x(self, event):
        """Обробка Ctrl+X — вирізати."""
        try:
            widget = event.widget
            if widget.selection_present():
                selected_text = widget.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
                widget.delete("sel.first", "sel.last")
                logger.debug(f"✂️ Вирізано: {selected_text[:50]}...")
        except Exception as e:
            logger.debug(f"⚠️ Ctrl+X помилка: {e}")

    def _on_right_click(self, event):
        """Обробка правої кнопки миші — показуємо контекстне меню."""
        try:
            from tkinter import Menu

            widget = event.widget
            menu = Menu(self, tearoff=0)
            menu.add_command(
                label="Вирізати", command=lambda: widget.event_generate("<<Cut>>")
            )
            menu.add_command(
                label="Копіювати", command=lambda: widget.event_generate("<<Copy>>")
            )
            menu.add_command(
                label="Вставити", command=lambda: widget.event_generate("<<Paste>>")
            )
            menu.add_separator()
            menu.add_command(
                label="Виділити все", command=lambda: widget.select_range(0, "end")
            )

            menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            logger.warning(f"⚠️ Помилка контекстного меню: {e}")

    def _fill_fields(self):
        """Заповнення полів даними"""
        self.entry_nazva.insert(0, self._applicant.nazva_pidpryyemstva)
        self.entry_adresa.insert(0, self._applicant.adresa_pidpryyemstva)
        self.entry_edrpou.insert(0, self._applicant.kod_edrpou)
        self.entry_kerivnik.insert(0, self._applicant.kerivnik)
        self.entry_papka.insert(0, self._applicant.papka_proektu)
        self.entry_suffix.insert(0, self._applicant.template_suffix or "_Д")

    def _on_save(self):
        """Збереження даних"""
        nazva = self.entry_nazva.get().strip()
        adresa = self.entry_adresa.get().strip()
        edrpou = self.entry_edrpou.get().strip()
        kerivnik = self.entry_kerivnik.get().strip()
        papka = self.entry_papka.get().strip()
        suffix = self.entry_suffix.get().strip()

        # Логування для відладки
        logger.info(
            f"📝 Збереження заявника: nazva='{nazva}', papka='{papka}', edrpou='{edrpou}'"
        )

        if not nazva or not adresa or not papka:
            messagebox.showerror(
                "Помилка", "Заповніть обов'язкові поля!\n(Назва, Адреса, Папка)"
            )
            return

        # Валідація ЄДРПОУ
        from client_launcher.applicants_db import ApplicantsDB

        valid, msg = ApplicantsDB.validate_edrpou(edrpou)
        if not valid:
            messagebox.showerror("Помилка", f"Невірний ЄДРПОУ: {msg}")
            return

        self.result = ApplicantDTO(
            nazva_pidpryyemstva=nazva,
            adresa_pidpryyemstva=adresa,
            kod_edrpou=edrpou,
            kerivnik=kerivnik,
            papka_proektu=papka,
            template_suffix=suffix or "_Д",
        )

        # Закриваємо вікно ВІДРАЗУ, щоб не блокувати UI
        self._on_close()

        # Виконуємо ініціалізацію шаблонів у фоні (безпечно)
        self._after_save_cleanup(papka, suffix or "_Д")

    def _after_save_cleanup(self, papka, suffix):
        """Перевірка та створення шаблонів після збереження (безпечно)"""
        try:
            from .client_provisioner import _copy_base_templates, _PROJECT_ROOT
            
            # Шлях до папки даних клієнта
            client_data_dir = _PROJECT_ROOT / "data" / papka
            templates_dir = client_data_dir / "templates"
            
            if not templates_dir.exists():
                logger.info(f"📁 Ініціалізація відсутніх шаблонів для {papka}...")
                
                class DummyResult:
                    def __init__(self): self.warnings = []
                
                res = DummyResult()
                _copy_base_templates(client_data_dir, suffix, res)
                
                if res.warnings:
                    for w in res.warnings: logger.warning(f"⚠️ {w}")
                else:
                    logger.info(f"✅ Шаблони для {papka} створено успішно")
        except Exception as e:
            logger.error(f"❌ Не вдалося ініціалізувати шаблони: {e}")

    def _on_close(self):
        """Збереження геометрії перед закриттям"""
        try:
            # Оновлюємо віджети перед отриманням розмірів
            self.update_idletasks()
            save_window_geometry(self, "ApplicantEditDialog")
        except Exception as e:
            logger.warning(f"⚠️ Не вдалося зберегти геометрію: {e}")
        self.destroy()
