import logging
import threading
import tkinter as tk
from tkinter import messagebox

from gui.widgets import FinalDocumentsPerPartyDialog
from models.dto import FinalDocumentsDTO

logger = logging.getLogger(__name__)


class DocumentGenerationHandler:
    """Хендлер для керування процесом генерації документів у фоновому режимі."""

    def __init__(self, window):
        self.window = window  # Посилання на AppFormWindow
        self.doc_gen = window.doc_gen
        self.app_service = window.app_service
        self.data_handler = window.data_handler

    def generate_vc(self, app_data, parties):
        """Запуск генерації ВЦ документів"""
        self.window.btn_gen_vc.configure(state="disabled", text=" Генерується...")
        self.window.btn_gen_final.configure(state="disabled")

        # Збираємо лог для відладки
        debug_log_lines = []

        def _bg_gen():
            try:
                debug_log_lines.append(f"📋 Заявка: {app_data.get('app_number')}")
                debug_log_lines.append(f"📦 Партій: {len(parties)}")
                debug_log_lines.append("=" * 60)

                # Зберігаємо дані через дата-хендлер
                self.data_handler.save_all(app_data, parties)
                debug_log_lines.append("✅ Дані збережено в БД")

                # Детальний лог кожної партії
                for i, p in enumerate(parties, 1):
                    debug_log_lines.append(
                        f"   Партія {i}: код='{p.get('party_code')}', "
                        f"продукт='{p.get('product_name', '')[:40]}...', "
                        f"дата='{p.get('party_date')}'"
                    )
                debug_log_lines.append("=" * 60)

                # Генерація
                results = self.doc_gen.generate_vc_documents(app_data, parties)
                debug_log_lines.append(f"\n📊 Результати: {results}")

                self.window.after(
                    0, lambda: self._on_vc_success(results, "\n".join(debug_log_lines))
                )
            except Exception as e:
                error_msg = str(e)
                debug_log_lines.append(f"\n❌ КРИТИЧНА ПОМИЛКА: {error_msg}")
                logger.error(f"Помилка генерації ВЦ: {error_msg}", exc_info=True)
                self.window.after(
                    0,
                    lambda msg=error_msg, log="\n".join(debug_log_lines): self._on_error(
                        msg, log
                    ),
                )

        threading.Thread(target=_bg_gen, daemon=True).start()

    def generate_final(self, app_data, parties):
        """Запуск генерації фінальних документів"""
        # 0. Спочатку зберігаємо актуальний стан
        try:
            result = self.data_handler.save_all(app_data, parties)
            app_id = result["app_id"]
            party_ids_list = result["party_ids"]
        except Exception as e:
            logger.error(f"Помилка збереження перед генерацією: {e}")
            self._on_error(f"Не вдалося зберегти дані: {e}")
            return

        # Отримуємо актуальні дані з БД (щоб мати всі ID)
        db_parties = self.app_service.get_parties_for_application(app_id)

        # Конвертуємо DTO назад у дикти для генератора (тимчасово, поки генератор не на DTO)
        parties_to_process = []
        for p in db_parties:
            parties_to_process.append(
                {
                    "id": p.id,
                    "app_id": p.app_id,
                    "product_name": p.product_name,
                    "party_code": p.party_code,
                    "party_date": p.party_date,
                    "mfg_date": p.mfg_date,
                    "quantity": p.quantity,
                    "unit": p.unit,
                    "shelf_life_months": p.shelf_life_months,
                    "standards": p.standards,
                    "protocol_number": p.protocol_number or "",
                    "protocol_date": p.protocol_date or "",
                    "cert_number": p.cert_number or "",
                    "cert_date": p.cert_date or "",
                    "version": p.version or "",
                }
            )

        # 1. Збір даних через діалоги (має бути в основному потоці)
        collected_data = []
        for party_index, (party, party_db_id) in enumerate(
            zip(parties_to_process, party_ids_list), 1
        ):
            dialog = FinalDocumentsPerPartyDialog(self.window, party, party_index)
            self.window.wait_window(dialog)

            if dialog.final_data is None:
                logger.warning(f"Користувач скасував введення для партії {party_index}")
                continue

            collected_data.append(
                {
                    "party": party,
                    "party_db_id": party_db_id,
                    "party_index": party_index,
                    "final_data": dialog.final_data,
                }
            )

        if not collected_data:
            return

        # 2. Фонова генерація
        self.window.btn_gen_final.configure(state="disabled", text="⏳ Генерирую...")
        self.window.btn_gen_vc.configure(state="disabled")

        def _bg_final_gen():
            success_count = 0
            try:
                for item in collected_data:
                    p_idx = item["party_index"]
                    f_data = item["final_data"]
                    p_db_id = item["party_db_id"]
                    orig_party = item["party"]

                    # Оновлюємо дані партії
                    party_with_final = dict(orig_party)
                    party_with_final.update(
                        {
                            "protocol_number": f_data.get("protocol_number", ""),
                            "protocol_date": f_data.get("protocol_date", ""),
                            "cert_number": f_data.get("cert_number", ""),
                            "cert_date": f_data.get("cert_date", ""),
                        }
                    )

                    # Зберігаємо в БД
                    final_dto = FinalDocumentsDTO(
                        protocol_number=f_data.get("protocol_number", ""),
                        protocol_date=f_data.get("protocol_date", ""),
                        cert_number=f_data.get("cert_number", ""),
                        cert_date=f_data.get("cert_date", ""),
                    )
                    self.app_service.update_party_final_documents(p_db_id, final_dto)

                    # !!! ВАЖЛИВО: Оновлюємо дані в пам'яті головного вікна,
                    # щоб при натисканні "Зберегти" в основній формі дані не перетерлися старими
                    for p in self.window.parties:
                        if p.get("id") == p_db_id:
                            p.update({
                                "protocol_number": f_data.get("protocol_number", ""),
                                "protocol_date": f_data.get("protocol_date", ""),
                                "cert_number": f_data.get("cert_number", ""),
                                "cert_date": f_data.get("cert_date", ""),
                            })
                            break

                    # Генеруємо файли
                    results = self.doc_gen.generate_final_documents_for_party(
                        party_with_final, app_data, p_idx
                    )

                    if any(v == 1 and not isinstance(v, str) for v in results.values()):
                        success_count += 1

                self.window.after(
                    0,
                    lambda: self._on_final_success(success_count, len(collected_data)),
                )
            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"Помилка генерації фінальних документів: {error_msg}",
                    exc_info=True,
                )
                self.window.after(0, lambda msg=error_msg: self._on_error(msg))

        threading.Thread(target=_bg_final_gen, daemon=True).start()

    def _on_vc_success(self, results, debug_log: str = ""):
        self.window.btn_gen_vc.configure(state="normal", text=" Документи для ВЦ")
        self.window.btn_gen_final.configure(state="normal")
        messagebox.showinfo("Генерація завершена", "✅ Документи для ВЦ згенеровано!")

    def _on_final_success(self, success_count, total_count):
        self.window.btn_gen_final.configure(
            state="normal", text="🏆 Фінальні документи"
        )
        self.window.btn_gen_vc.configure(state="normal")
        self.window.refresh_parties_table()
        messagebox.showinfo(
            "Завершено",
            f"✅ Оброблено партій: {success_count} з {total_count}",
        )

    def _on_error(self, error_msg, debug_log: str = ""):
        self.window.btn_gen_vc.configure(state="normal", text=" Документи для ВЦ")
        self.window.btn_gen_final.configure(
            state="normal", text=" Фінальні документи"
        )
        messagebox.showerror("Помилка", f"Сталася помилка:\n{error_msg}")
