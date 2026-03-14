import customtkinter as ctk


def build_recording_section(parent, controller, icons, tooltip):
    frame = ctk.CTkFrame(parent, fg_color="#111827", corner_radius=12)
    title = ctk.CTkLabel(frame, text="Recording", text_color="#e5e7eb")
    title.pack(anchor="w", padx=10, pady=(8, 0))
    row = ctk.CTkFrame(frame, fg_color="transparent")
    row.pack(fill="x", padx=6, pady=6)

    btn_record = ctk.CTkButton(
        row,
        text=f"{icons['record']} Record",
        command=controller.start_recording,
        fg_color="#ef4444",
        hover_color="#dc2626",
        corner_radius=12,
        height=36,
    )
    btn_record.pack(side="left", padx=4, pady=4)
    tooltip(btn_record, "Record macro events")

    btn_stop = ctk.CTkButton(
        row,
        text=f"{icons['stop']} Stop",
        command=controller.stop_recording,
        fg_color="#f59e0b",
        hover_color="#d97706",
        corner_radius=12,
        height=36,
    )
    btn_stop.pack(side="left", padx=4, pady=4)
    btn_stop.configure(state="disabled")
    tooltip(btn_stop, "Stop recording")

    indicator = ctk.CTkLabel(row, text="●", text_color="#374151")
    indicator.pack(side="left", padx=(8, 4))

    return frame, btn_record, btn_stop, indicator
