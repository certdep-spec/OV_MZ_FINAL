"""
Бейдж клієнта — відображає поточного клієнта у правому верхньому куті вікна.

Використання:
    from gui.client_badge import add_client_badge
    add_client_badge(self)  # у __init__ після створення вікна
"""

import customtkinter as ctk

import config


def add_client_badge(
    window: ctk.CTk | ctk.CTkToplevel, corner: str = "top_right"
) -> ctk.CTkLabel:
    """
    Додати бейдж з назвою поточного клієнта у кут вікна.

    Args:
        window: Вікно (MainWindow або CTkToplevel)
        corner: Кут розміщення ("top_right" | "top_left")

    Returns:
        Створений віджет мітки (можна приховати/видалити за потребою)

    Приклад:
        add_client_badge(self)  # "АФІНА" у правому верхньому куті
    """
    # Визначаємо назву клієнта
    client_name = _get_client_display_name()

    # Кольори бейджа
    fg_color = "#1A5F8A"
    text_color = "#FFFFFF"

    badge = ctk.CTkLabel(
        window,
        text=f"🏢 {client_name}",
        font=ctk.CTkFont(size=11, weight="bold"),
        fg_color=fg_color,
        text_color=text_color,
        corner_radius=6,
    )

    # Розміщуємо у правому верхньому куті
    badge.place(relx=0.99, rely=0.01, anchor="ne")

    return badge


def _get_client_display_name() -> str:
    """
    Отримати коротку назву поточного клієнта для відображення.

    Повертає DEFAULT_COMPANY якщо клієнт ініціалізований,
    інакше — "CERTIFYPRO".
    """
    try:
        name = getattr(config, "DEFAULT_COMPANY", None)
        if name:
            # Скорочуємо довгі назви
            if len(name) > 30:
                return name[:27] + "…"
            return name
    except Exception:
        pass
    return "CERTIFYPRO"
