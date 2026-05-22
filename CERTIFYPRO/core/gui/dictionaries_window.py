"""
Вікно управління довідниками (БД)
Дозволяє переглядати, додавати, редагувати та видаляти:
- Продукцію
- Стандарти НД
- Потужності
- Склад
"""

import logging
from tkinter import messagebox, ttk

import customtkinter as ctk

import config
from gui.client_badge import add_client_badge
from gui.gui_utils import (
    add_context_menu,
    restore_window_geometry,
    save_window_geometry,
)
from models.dto import (
    IngredientDTO,
    ProductDTO,
    ProductionFacilityDTO,
    StandardDTO,
)

logger = logging.getLogger(__name__)


class GenericEditDialog(ctk.CTkToplevel):
    """Універсальний діалог для додавання/редагування записів"""

    def __init__(self, parent, title: str, fields: list, current_values: dict = None):
        super().__init__(parent)
        self.title(title)
        # Збільшено вікно для кращого відображення
        self.geometry("700x500")
        self.transient(parent)
        self.grab_set()

        self.fields = fields
        self.current_values = current_values or {}
        self.result = None
        self.entries = {}

        self.create_widgets()

        # Відновлюємо збережену геометрію
        self.after(
            100,
            lambda: restore_window_geometry(self, "GenericEditDialog", 700, 500),
        )
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Бейдж клієнта
        self.after(200, lambda: add_client_badge(self))

    def create_widgets(self):
        # Прокрутка
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        for i, field in enumerate(self.fields):
            key = field["key"]
            label = field["label"]
            f_type = field.get("type", "entry")
            required = field.get("required", False)
            multiline = field.get("multiline", False)  # Новий параметр

            lbl_text = f"{label}*" if required else label
            ctk.CTkLabel(scroll_frame, text=lbl_text).grid(
                row=i, column=0, sticky="nw", pady=10, padx=5
            )

            if f_type == "combo":
                options = field.get("options", [])
                entry = ctk.CTkComboBox(scroll_frame, values=options, width=350)
                if self.current_values.get(key) is not None:
                    entry.set(str(self.current_values[key]))
                elif options:
                    entry.set(options[0])
            elif multiline:
                # Багаторядкове текстове поле (компактне)
                entry = ctk.CTkTextbox(scroll_frame, width=450, height=50, wrap="word")
                if self.current_values.get(key) is not None:
                    entry.insert("0.0", str(self.current_values[key]))
            else:
                entry = ctk.CTkEntry(scroll_frame, width=400)
                if self.current_values.get(key) is not None:
                    entry.insert(0, str(self.current_values[key]))

            entry.grid(row=i, column=1, pady=10, padx=5, sticky="ew")
            if not multiline:
                add_context_menu(entry, self)
            self.entries[key] = {
                "widget": entry,
                "required": required,
                "multiline": multiline,
            }

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        ctk.CTkButton(
            btn_frame,
            text="✅ Зберегти",
            fg_color=config.COLORS["success"],
            command=self.on_save,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="❌ Скасувати",
            fg_color="gray",
            command=self.destroy,
        ).pack(side="left", padx=10)

    def on_save(self):
        result = {}
        for key, info in self.entries.items():
            widget = info["widget"]
            if info.get("multiline"):
                # Для багаторядкового поля
                val = widget.get("0.0", "end-1c").strip()
            else:
                val = widget.get().strip() if hasattr(widget, "get") else ""
            if info["required"] and not val:
                messagebox.showerror("Помилка", "Заповніть всі обов'язкові поля!")
                return
            result[key] = val

        self.result = result
        self.on_closing()

    def on_closing(self):
        """Зберігаємо геометрію та закриваємо"""
        save_window_geometry(self, "GenericEditDialog")
        self.destroy()


class DictionariesWindow(ctk.CTkToplevel):
    def __init__(self, parent, dict_service):
        super().__init__(parent)

        self.title("📚 Управління Довідниками")
        self.geometry("1100x700")
        self.transient(parent)
        self.grab_set()

        self.dict_service = dict_service
        # Для зворотної сумісності - dict_service також використовується як db
        self.db = dict_service

        self.create_widgets()

        # Відновлюємо збережену геометрію
        self.after(
            100,
            lambda: restore_window_geometry(self, "DictionariesWindow", 1100, 700),
        )
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Бейдж клієнта
        self.after(200, lambda: add_client_badge(self))

    def create_widgets(self):
        # Заголовок
        ctk.CTkLabel(
            self,
            text="📚 Управління системними довідниками",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=15)

        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        self.tabview.add("Продукція")
        self.tabview.add("Стандарти НД")
        self.tabview.add("Потужності")
        self.tabview.add("Склад")

        self.setup_products_tab()
        self.setup_standards_tab()
        self.setup_facilities_tab()
        self.setup_ingredients_tab()

        # Кнопка закриття
        ctk.CTkButton(
            self, text="❌ Закрити", command=self.on_closing, fg_color="gray"
        ).pack(pady=15)

    def refresh_all_tabs(self):
        """Оновити дані у всіх вкладках"""
        try:
            self.load_products()
            self.load_standards()
            self.load_facilities()
            self.load_ingredients()
            logger.info("🔄 Усі вкладки довідників оновлено")
        except Exception as e:
            logger.error(f"Помилка оновлення вкладок: {e}")

    def on_closing(self):
        """Зберігаємо геометрію та закриваємо"""
        save_window_geometry(self, "DictionariesWindow")
        self.destroy()

    # ================== ПРОДУКЦІЯ ==================
    def setup_products_tab(self):
        tab = self.tabview.tab("Продукція")

        self.tree_prod = self._create_treeview(
            tab,
            columns=("Назва продукції", "ТУ", "Термін (міс)"),
            widths=(500, 300, 130),
            stretch_cols=["Назва продукції", "ТУ"],
        )
        self._create_crud_buttons(tab, self.add_prod, self.edit_prod, self.delete_prod)
        self.load_products()

    def load_products(self):
        self._clear_tree(self.tree_prod)
        if not self.dict_service:
            logger.warning("dict_service не ініціалізовано")
            return
        products = self.dict_service.get_all_products()
        for product in products:
            # ProductDTO -> tuple для treeview
            row = (product.name, product.tu_code, product.shelf_life_months)
            self.tree_prod.insert("", "end", values=row)

    def add_prod(self):
        fields = [
            {"key": "name", "label": "Назва продукції", "required": True},
            {
                "key": "tu_code",
                "label": "ТУ (Технічні умови)",
                "required": False,
            },
            {
                "key": "shelf_life_months",
                "label": "Термін зберігання (міс)",
                "required": False,
            },
        ]
        dialog = GenericEditDialog(self, "Додати продукцію", fields)
        self.wait_window(dialog)
        if dialog.result:
            try:
                product = ProductDTO(
                    name=dialog.result["name"],
                    tu_code=dialog.result.get("tu_code", ""),
                    shelf_life_months=int(dialog.result.get("shelf_life_months", 36)),
                )
                self.dict_service.add_product(product)
                self.load_products()
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def edit_prod(self):
        selected = self.tree_prod.selection()
        if not selected:
            return messagebox.showwarning("Увага", "Оберіть запис!")
        vals = self.tree_prod.item(selected[0])["values"]
        old_name = vals[0]

        fields = [
            {"key": "name", "label": "Назва продукції", "required": True},
            {
                "key": "tu_code",
                "label": "ТУ (Технічні умови)",
                "required": False,
            },
            {
                "key": "shelf_life_months",
                "label": "Термін зберігання (міс)",
                "required": False,
            },
        ]
        curr = {
            "name": vals[0],
            "tu_code": vals[1],
            "shelf_life_months": vals[2],
        }
        dialog = GenericEditDialog(self, "Редагувати продукцію", fields, curr)
        self.wait_window(dialog)
        if dialog.result:
            try:
                product = ProductDTO(
                    name=dialog.result["name"],
                    tu_code=dialog.result.get("tu_code", ""),
                    shelf_life_months=int(dialog.result.get("shelf_life_months", 36)),
                )
                self.dict_service.update_product(old_name, product)
                self.load_products()
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def delete_prod(self):
        """Видалити вибрану продукцію"""
        selected = self.tree_prod.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть продукцію для видалення!")
            return

        name = self.tree_prod.item(selected[0])["values"][0]

        # 1. Перевірка чи використовується в заявках
        is_used = self.dict_service.is_product_in_use(name)
        if is_used:
            msg = (
                f"⚠️ Продукція '{name}' використовується в існуючих заявках!\n\n"
                "Видалення може призвести до системних помилок при відкритті цих заявок.\n"
                "Ви впевнені, що хочете видалити її?"
            )
            if not messagebox.askyesno("Попередження", msg):
                return
        else:
            if not messagebox.askyesno(
                "Підтвердження", f"Видалити продукцію '{name}' та її склад?"
            ):
                return

        # 2. Спроба видалення
        try:
            self.dict_service.delete_product(name)
            self.load_products()
            # Також оновлюємо вкладку складу, щоб відобразити видалення інгредієнтів
            if hasattr(self, "load_ingredients"):
                self.load_ingredients()
            messagebox.showinfo("Успіх", f"Продукцію '{name}' видалено.")
        except Exception as e:
            messagebox.showerror(
                "Помилка видалення",
                f"Не вдалося видалити продукцію:\n{str(e)}",
            )

    # ================== СТАНДАРТИ ==================
    def setup_standards_tab(self):
        tab = self.tabview.tab("Стандарти НД")
        self.tree_std = self._create_treeview(
            tab,
            columns=("ID (Назва НД)", "Опис"),
            widths=(130, 800),
            stretch_cols=["Опис"],
        )
        self._create_crud_buttons(tab, self.add_std, self.edit_std, self.del_std)
        self.load_standards()

    def load_standards(self):
        self._clear_tree(self.tree_std)
        if not self.dict_service:
            logger.warning("dict_service не ініціалізовано")
            return
        standards = self.dict_service.get_all_standards()
        for std in standards:
            # StandardDTO -> tuple (id, description)
            row = (std.id, std.description)
            self.tree_std.insert("", "end", values=row)

    def add_std(self):
        fields = [
            {"key": "id", "label": "Номер НД (цифри)", "required": True},
            {
                "key": "description",
                "label": "Опис / Назва стандарту",
                "required": True,
            },
        ]
        dialog = GenericEditDialog(self, "Додати стандарт", fields)
        self.wait_window(dialog)
        if dialog.result:
            try:
                std_id = int(dialog.result["id"])
                standard = StandardDTO(
                    id=std_id,
                    description=dialog.result["description"],
                    active=True,
                )
                self.dict_service.add_standard(standard)
                self.load_standards()
            except ValueError:
                messagebox.showerror("Помилка", "ID повинен бути числом!")
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def edit_std(self):
        selected = self.tree_std.selection()
        if not selected:
            return messagebox.showwarning("Увага", "Оберіть запис!")
        vals = self.tree_std.item(selected[0])["values"]
        old_id = vals[0]

        fields = [
            {"key": "id", "label": "Номер НД (цифри)", "required": True},
            {
                "key": "description",
                "label": "Опис / Назва стандарту",
                "required": True,
            },
        ]
        curr = {"id": vals[0], "description": vals[1]}
        dialog = GenericEditDialog(self, "Редагувати стандарт", fields, curr)
        self.wait_window(dialog)
        if dialog.result:
            try:
                std_id = int(dialog.result["id"])
                standard = StandardDTO(
                    id=std_id,
                    description=dialog.result["description"],
                    active=True,
                )
                self.dict_service.update_standard(old_id, standard)
                self.load_standards()
            except ValueError:
                messagebox.showerror("Помилка", "ID повинен бути числом!")
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def del_std(self):
        selected = self.tree_std.selection()
        if not selected:
            return messagebox.showwarning("Увага", "Оберіть запис!")
        std_id = self.tree_std.item(selected[0])["values"][0]
        if messagebox.askyesno("Підтвердження", f"Видалити стандарт з ID {std_id}?"):
            self.dict_service.delete_standard(std_id)
            self.load_standards()

    # ================== ПОТУЖНОСТІ ==================
    def setup_facilities_tab(self):
        tab = self.tabview.tab("Потужності")
        self.tree_fac = self._create_treeview(
            tab,
            columns=("Адреса виробництва",),
            widths=(1000,),
            stretch_cols=["Адреса виробництва"],
            row_height=35,  # Оптимальна висота рядків
        )
        self._create_crud_buttons(tab, self.add_fac, self.edit_fac, self.del_fac)
        self.load_facilities()

    def load_facilities(self):
        self._clear_tree(self.tree_fac)
        if not self.dict_service:
            logger.warning("dict_service не ініціалізовано")
            return
        facilities = self.dict_service.get_all_facilities()
        for facility in facilities:
            # ProductionFacilityDTO -> показуємо тільки адресу
            self.tree_fac.insert("", "end", values=(facility.address,))

    def add_fac(self):
        fields = [
            {
                "key": "address",
                "label": "Адреса виробництва",
                "required": True,
                "multiline": True,  # Багаторядкове поле
            }
        ]
        dialog = GenericEditDialog(self, "Додати потужність", fields)
        self.wait_window(dialog)
        if dialog.result:
            try:
                facility = ProductionFacilityDTO(address=dialog.result["address"])
                self.dict_service.add_facility(facility)
                self.load_facilities()
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def edit_fac(self):
        selected = self.tree_fac.selection()
        if not selected:
            return messagebox.showwarning("Увага", "Оберіть запис!")
        old_address = self.tree_fac.item(selected[0])["values"][0]

        fields = [
            {
                "key": "address",
                "label": "Адреса виробництва",
                "required": True,
                "multiline": True,  # Багаторядкове поле
            }
        ]
        curr = {"address": old_address}
        dialog = GenericEditDialog(self, "Редагувати потужність", fields, curr)
        self.wait_window(dialog)
        if dialog.result:
            try:
                facility = ProductionFacilityDTO(address=dialog.result["address"])
                self.dict_service.update_facility(old_address, facility)
                self.load_facilities()
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def del_fac(self):
        selected = self.tree_fac.selection()
        if not selected:
            return messagebox.showwarning("Увага", "Оберіть запис!")
        address = self.tree_fac.item(selected[0])["values"][0]
        if messagebox.askyesno("Підтвердження", f"Видалити потужність:\n{address}?"):
            self.dict_service.delete_facility(address)
            self.load_facilities()

    # ================== СКЛАД ==================
    def setup_ingredients_tab(self):
        tab = self.tabview.tab("Склад")
        self.tree_ing = self._create_treeview(
            tab,
            columns=(
                "ID",
                "Продукція",
                "Варіант складу",
                "Назва (хім)",
                "Торгова марка",
                "CAS",
                "Сертифікат",
            ),
            widths=(110, 200, 130, 200, 130, 110, 200),
            stretch_cols=["Продукція", "Назва (хім)", "Сертифікат"],
        )
        self._create_crud_buttons(tab, self.add_ing, self.edit_ing, self.del_ing)
        self.load_ingredients()

    def load_ingredients(self):
        self._clear_tree(self.tree_ing)
        if not self.dict_service:
            logger.warning("dict_service не ініціалізовано")
            return
        ingredients = self.dict_service.get_all_ingredients()
        for ing in ingredients:
            # IngredientDTO -> tuple (id, product_name, version, chemical_name, trade_mark, cas_number, certificate)
            row = (
                ing.id,
                ing.product_name,
                ing.version or "",
                ing.chemical_name,
                ing.trade_mark or "",
                ing.cas_number or "",
                ing.certificate or "",
            )
            self.tree_ing.insert("", "end", values=row)

    def _get_product_names(self):
        if not self.dict_service:
            logger.warning("dict_service не ініціалізовано")
            return []
        products = self.dict_service.get_all_products()
        return [p.name for p in products]

    def add_ing(self):
        products = self._get_product_names()
        fields = [
            {
                "key": "product_name",
                "label": "Продукція (прив'язка)",
                "type": "combo",
                "options": products,
                "required": True,
            },
            {
                "key": "version",
                "label": "Версія складу (буква)",
                "required": False,
            },
            {
                "key": "chemical_name",
                "label": "Хімічна назва",
                "required": True,
            },
            {"key": "trade_mark", "label": "Торгова марка"},
            {"key": "cas_number", "label": "CAS"},
            {"key": "certificate", "label": "Сертифікат/КР"},
        ]
        dialog = GenericEditDialog(self, "Додати інгредієнт", fields)
        self.wait_window(dialog)
        if dialog.result:
            try:
                ingredient = IngredientDTO(
                    product_name=dialog.result["product_name"],
                    version=dialog.result.get("version", ""),
                    chemical_name=dialog.result["chemical_name"],
                    trade_mark=dialog.result.get("trade_mark", ""),
                    cas_number=dialog.result.get("cas_number", ""),
                    certificate=dialog.result.get("certificate", ""),
                )
                self.dict_service.add_ingredient(ingredient)
                self.load_ingredients()
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def edit_ing(self):
        selected = self.tree_ing.selection()
        if not selected:
            return messagebox.showwarning("Увага", "Оберіть запис!")
        vals = self.tree_ing.item(selected[0])["values"]
        ing_id = vals[0]

        products = self._get_product_names()
        fields = [
            {
                "key": "product_name",
                "label": "Продукція (прив'язка)",
                "type": "combo",
                "options": products,
                "required": True,
            },
            {
                "key": "version",
                "label": "Версія складу (буква)",
                "required": False,
            },
            {
                "key": "chemical_name",
                "label": "Хімічна назва",
                "required": True,
            },
            {"key": "trade_mark", "label": "Торгова марка"},
            {"key": "cas_number", "label": "CAS"},
            {"key": "certificate", "label": "Сертифікат/КР"},
        ]
        curr = {
            "product_name": vals[1],
            "version": vals[2],
            "chemical_name": vals[3],
            "trade_mark": vals[4],
            "cas_number": vals[5],
            "certificate": vals[6],
        }
        dialog = GenericEditDialog(self, "Редагувати інгредієнт", fields, curr)
        self.wait_window(dialog)
        if dialog.result:
            try:
                ingredient = IngredientDTO(
                    product_name=dialog.result["product_name"],
                    version=dialog.result.get("version", ""),
                    chemical_name=dialog.result["chemical_name"],
                    trade_mark=dialog.result.get("trade_mark", ""),
                    cas_number=dialog.result.get("cas_number", ""),
                    certificate=dialog.result.get("certificate", ""),
                )
                self.dict_service.update_ingredient(ing_id, ingredient)
                self.load_ingredients()
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def del_ing(self):
        selected = self.tree_ing.selection()
        if not selected:
            return messagebox.showwarning("Увага", "Оберіть запис!")
        vals = self.tree_ing.item(selected[0])["values"]
        ing_id = vals[0]
        name = vals[3]
        if messagebox.askyesno("Підтвердження", f"Видалити інгредієнт '{name}'?"):
            self.dict_service.delete_ingredient(ing_id)
            self.load_ingredients()

    # ================== ДОПОМІЖНІ МЕТОДИ ==================
    def _create_treeview(
        self, parent, columns, widths, stretch_cols=None, row_height=None
    ):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        stretch_cols = stretch_cols or []
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            # Якщо колонка в переліку stretch_cols - вона розширюється, інакше - фіксована
            is_stretch = col in stretch_cols
            tree.column(
                col,
                width=width,
                stretch=is_stretch,
                anchor="w" if is_stretch else "center",
            )

        # Встановлюємо збільшену висоту рядків якщо вказано
        if row_height is not None:
            style = ttk.Style()
            style.configure("Treeview", rowheight=row_height)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    def _create_crud_buttons(self, parent, add_cmd, edit_cmd, del_cmd):
        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(pady=10)

        ctk.CTkButton(
            btn_frame,
            text="➕ Додати",
            command=add_cmd,
            fg_color=config.COLORS["success"],
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="✏️ Редагувати",
            command=edit_cmd,
            fg_color=config.COLORS["info"],
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame, text="🗑️ Видалити", command=del_cmd, fg_color="red"
        ).pack(side="left", padx=10)

    def _clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)
