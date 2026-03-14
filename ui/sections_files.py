import customtkinter as ctk


def build_files_section(parent, controller, icons, tooltip):
    frame = ctk.CTkFrame(parent, fg_color="#111827", corner_radius=12)
    title = ctk.CTkLabel(frame, text="Files", text_color="#e5e7eb")
    title.pack(anchor="w", padx=10, pady=(8, 0))
    row = ctk.CTkFrame(frame, fg_color="transparent")
    row.pack(fill="x", padx=6, pady=6)

    btn_save = ctk.CTkButton(
        row,
        text=f"{icons['save']} Save",
        command=controller.save,
        fg_color="#1f2937",
        hover_color="#374151",
        corner_radius=10,
        height=30,
    )
    btn_save.pack(side="left", padx=4, pady=4)
    tooltip(btn_save, "Save macro to file")

    btn_load = ctk.CTkButton(
        row,
        text=f"{icons['load']} Load",
        command=controller.load,
        fg_color="#1f2937",
        hover_color="#374151",
        corner_radius=10,
        height=30,
    )
    btn_load.pack(side="left", padx=4, pady=4)
    tooltip(btn_load, "Load macro from file")

    btn_folder = ctk.CTkButton(
        row,
        text=f"{icons['folder']} Open Screenshot Folder",
        command=controller.open_capture_folder,
        fg_color="#1f2937",
        hover_color="#374151",
        corner_radius=10,
        height=30,
    )
    btn_folder.pack(side="left", padx=4, pady=4)
    tooltip(btn_folder, "Open screenshot storage folder")

    return frame, btn_save, btn_load, btn_folder
