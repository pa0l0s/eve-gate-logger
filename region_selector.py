import tkinter as tk
from typing import Optional
from config import Region

def select_region() -> Optional[Region]:
    """
    Opens a fullscreen semi-transparent overlay.
    User clicks and drags to select the overview region.
    Returns the selected Region, or None if cancelled (Escape).
    """
    result: list[Optional[Region]] = [None]

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)
    root.attributes("-topmost", True)
    root.configure(bg="black")
    root.title("Eve Gate Logger — Select Overview Region (Escape to cancel)")

    canvas = tk.Canvas(root, cursor="cross", bg="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    start_x = start_y = 0
    rect_id = None

    def on_press(event: tk.Event) -> None:
        nonlocal start_x, start_y, rect_id
        start_x, start_y = event.x, event.y
        if rect_id:
            canvas.delete(rect_id)

    def on_drag(event: tk.Event) -> None:
        nonlocal rect_id
        if rect_id:
            canvas.delete(rect_id)
        rect_id = canvas.create_rectangle(
            start_x, start_y, event.x, event.y,
            outline="red", width=2
        )

    def on_release(event: tk.Event) -> None:
        x1 = min(start_x, event.x)
        y1 = min(start_y, event.y)
        x2 = max(start_x, event.x)
        y2 = max(start_y, event.y)
        if x2 - x1 > 10 and y2 - y1 > 10:
            result[0] = Region(x=x1, y=y1, width=x2 - x1, height=y2 - y1)
        root.destroy()

    def on_escape(event: tk.Event) -> None:
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)

    root.mainloop()
    return result[0]

if __name__ == "__main__":
    region = select_region()
    print(f"Selected: {region}")
