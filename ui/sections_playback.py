import customtkinter as ctk


def build_playback_section(parent, controller, icons, tooltip):
    frame = ctk.CTkFrame(parent, fg_color="#111827", corner_radius=12)
    title = ctk.CTkLabel(frame, text="Playback", text_color="#e5e7eb")
    title.pack(anchor="w", padx=10, pady=(8, 0))
    row = ctk.CTkFrame(frame, fg_color="transparent")
    row.pack(fill="x", padx=6, pady=6)

    btn_play = ctk.CTkButton(
        row,
        text=f"{icons['play']} Play",
        command=controller.play,
        fg_color="#3b82f6",
        hover_color="#2563eb",
        corner_radius=12,
        height=36,
    )
    btn_play.grid(row=0, column=0, padx=4, pady=4)
    tooltip(btn_play, "Play current macro")

    ctk.CTkLabel(row, text="Speed", text_color="#9ca3af").grid(row=0, column=1, padx=(6, 2), pady=4)
    entry_speed = ctk.CTkEntry(
        row, width=60, textvariable=controller.speed_var,
        fg_color="#0f172a", border_color="#1f2937", corner_radius=10,
    )
    entry_speed.grid(row=0, column=2, padx=2, pady=4)

    ctk.CTkLabel(row, text="Repeat", text_color="#9ca3af").grid(row=0, column=3, padx=(6, 2), pady=4)
    entry_repeat = ctk.CTkEntry(
        row, width=50, textvariable=controller.repeat_var,
        fg_color="#0f172a", border_color="#1f2937", corner_radius=10,
    )
    entry_repeat.grid(row=0, column=4, padx=2, pady=4)

    return frame, btn_play, entry_speed, entry_repeat
