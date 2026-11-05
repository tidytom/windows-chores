#!/usr/bin/env python3
# Stopwatch (Tkinter) — Windows-style stopwatch with laps
# - Per‑lap reset on face
# - Table: # | Lap | Total | Avg  (Fastest/Slowest appended to Lap cell, no extra column)
# - Auto TXT logging to stopwatch_log.txt in the Documents folder
# - Always‑on‑top toggle and compact widget
# - No keyboard shortcuts

import os, time, datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox

BG = "#eef3f7"; FG = "#1f2937"; SUB = "#6b7280"; BORDER = "#c7d2e2"; BLUE = "#0b74ff"; GREY = "#e5e7eb"

def documents_dir() -> str:
    """The user's Documents folder (also when Windows moved it, for example to OneDrive)."""
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0 and buf.value:   # 5 = My Documents
                return buf.value
        except Exception:
            pass
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    return docs if os.path.isdir(docs) else os.path.expanduser("~")


class CircleButton(tk.Canvas):
    def __init__(self, master, diameter=56, bg_fill=GREY, glyph="▶", glyph_size=16, command=None, state=tk.NORMAL):
        super().__init__(master, width=diameter, height=diameter, bg=BG, highlightthickness=0, bd=0)
        self.d=diameter; self.bg_fill=bg_fill; self.glyph=glyph; self.glyph_size=glyph_size; self.command=command; self.state=state
        self._draw(); self.bind("<Button-1>", self._click)
    def _draw(self):
        self.delete("all"); pad=2; r=self.d-pad; fill=self.bg_fill if self.state==tk.NORMAL else "#f2f4f6"
        self.create_oval(pad,pad,r,r,fill=fill,outline="#d0d7e2")
        self.create_text(self.d//2,self.d//2,text=self.glyph,fill=("white" if self.bg_fill==BLUE else "#6b7280"),font=("Segoe UI Symbol",self.glyph_size,"bold"))
    def _click(self,_):
        if self.state==tk.NORMAL and callable(self.command): self.command()
    def set_glyph(self,g): self.glyph=g; self._draw()
    def set_state(self,s): self.state=s; self._draw()

class Stopwatch:
    def __init__(self, root: tk.Tk):
        self.root=root; self.root.title("Stopwatch — Windows Style"); self.root.configure(bg=BG); self.root.minsize(540,460)
        # widget attrs first
        self.widget=None; self.widget_time_var=tk.StringVar(value=self._fmt(0.0))
        # logging
        self.log_path=os.path.join(documents_dir(),"stopwatch_log.txt"); self._session_open=False
        # timing
        self.running=False; self.lap_start_perf=0.0; self.lap_accum=0.0; self.session_total=0.0; self.laps=[]
        # ui
        self._build_ui()
        # timers
        self._tick_ms=20; self._avg_ms=60_000
        self._schedule_tick(); self._schedule_avg()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        shell=tk.Frame(self.root,bg=BG); shell.pack(fill=tk.BOTH,expand=True,padx=14,pady=14)
        card=tk.Frame(shell,bg="#f7fafc",bd=1,highlightthickness=1,highlightbackground=BORDER); card.pack(fill=tk.BOTH,expand=True)
        inner=tk.Frame(card,bg="#f7fafc"); inner.pack(fill=tk.BOTH,expand=True,padx=16,pady=16)
        top=tk.Frame(inner,bg="#f7fafc"); top.pack(fill=tk.X)
        self.topmost_var=tk.BooleanVar(value=False)
        tk.Checkbutton(top,text="Always on top",bg="#f7fafc",activebackground="#f7fafc",command=self._toggle_topmost,variable=self.topmost_var).pack(side=tk.LEFT)
        ttk.Button(top,text="Widget On/Off",command=self.toggle_widget).pack(side=tk.RIGHT)
        self.time_var=tk.StringVar(value=self._fmt(0.0))
        tk.Label(inner,textvariable=self.time_var,bg="#f7fafc",fg=FG,font=("Consolas",44,"bold")).pack(fill=tk.X,pady=(8,0))
        sub=tk.Frame(inner,bg="#f7fafc"); sub.pack(fill=tk.X)
        for txt,w in (("hr",8),("min",8),("sec",8)):
            tk.Label(sub,text=txt,bg="#f7fafc",fg=SUB,width=w,anchor="center",font=("Segoe UI",12)).pack(side=tk.LEFT,expand=True)
        ctrl=tk.Frame(inner,bg="#f7fafc"); ctrl.pack(pady=10)
        self.play_btn=CircleButton(ctrl,diameter=64,bg_fill=BLUE,glyph="▶",glyph_size=18,command=self.toggle_start_pause); self.play_btn.pack(side=tk.LEFT,padx=8)
        self.lap_btn=CircleButton(ctrl,diameter=56,bg_fill=GREY,glyph="Lap",glyph_size=12,command=self.lap,state=tk.DISABLED); self.lap_btn.pack(side=tk.LEFT,padx=8)
        self.reset_btn=CircleButton(ctrl,diameter=56,bg_fill=GREY,glyph="↺",glyph_size=16,command=self.reset,state=tk.DISABLED); self.reset_btn.pack(side=tk.LEFT,padx=8)
        # Table: 4 columns only. Fastest/Slowest appended in Lap cell.
        self.columns=("#","Lap","Total","Avg")
        self.tree=ttk.Treeview(inner,columns=self.columns,show="headings",height=9)
        for col,w in zip(self.columns,(50,170,120,120)):
            self.tree.heading(col,text=col); self.tree.column(col,anchor=tk.CENTER,width=w,stretch=False)
        self.tree.tag_configure("fast", foreground="#16a34a")
        self.tree.tag_configure("slow", foreground="#dc2626")
        self.tree.pack(fill=tk.BOTH,expand=True,pady=(6,0))
        self.avg_var=tk.StringVar(value="Average (session): —"); ttk.Label(inner,textvariable=self.avg_var).pack(anchor="e",pady=(6,0))
        ttk.Label(inner,text=f"Logging to: {self.log_path}").pack(anchor="w",pady=(4,0))
        style=ttk.Style(self.root)
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("Treeview", rowheight=26)

    # timing helpers
    def _now(self)->float: return time.perf_counter()
    def _lap_elapsed(self)->float: return (self.lap_accum+(self._now()-self.lap_start_perf)) if self.running else self.lap_accum

    # actions
    def toggle_start_pause(self):
        if self.running:
            self.lap_accum=self._lap_elapsed(); self.running=False
            # Lap only works while running, so it is off while paused
            self.play_btn.set_glyph("▶"); self.lap_btn.set_state(tk.DISABLED); self.reset_btn.set_state(tk.NORMAL)
        else:
            if not self._session_open: self._open_session_log()
            self.lap_start_perf=self._now(); self.running=True
            self.play_btn.set_glyph("⏸"); self.lap_btn.set_state(tk.NORMAL); self.reset_btn.set_state(tk.NORMAL)
        self._sync_widget()

    def lap(self):
        if not self.running:
            return
        lap_time = self._lap_elapsed()
        if lap_time <= 0:
            return
        self.laps.append(lap_time); self.session_total += lap_time
        self._log_lap(len(self.laps), lap_time)
        self._rebuild_table()
        # prepare next lap
        self.lap_accum = 0.0; self.lap_start_perf = self._now(); self.time_var.set(self._fmt(0.0))
        if self.widget and self.widget.winfo_exists(): self.widget_time_var.set(self._fmt(0.0))

    def reset(self):
        # Ask whenever there is something to lose, running or paused
        if (self.running or self.laps or self.lap_accum>0) and not messagebox.askyesno("Reset","Reset stopwatch and clear laps? This will close the current log session."):
            return
        self._close_session_log()
        self.running=False; self.lap_start_perf=0.0; self.lap_accum=0.0; self.session_total=0.0; self.laps.clear()
        for iid in self.tree.get_children(): self.tree.delete(iid)
        self.time_var.set(self._fmt(0.0)); self.play_btn.set_glyph("▶"); self.lap_btn.set_state(tk.DISABLED); self.reset_btn.set_state(tk.DISABLED)
        self._update_avg_label(); self._sync_widget()

    # table and updates
    def _rebuild_table(self):
        totals=[]; t=0.0
        for v in self.laps: t+=v; totals.append(t)
        fast_i=slow_i=None
        if len(self.laps)>=2:
            mn=min(self.laps); mx=max(self.laps)
            fast_i=self.laps.index(mn); slow_i=self.laps.index(mx)
        for iid in self.tree.get_children(): self.tree.delete(iid)
        for i in range(len(self.laps)-1,-1,-1):
            lap=self.laps[i]; total=totals[i]; avg_to_row=sum(self.laps[:i+1])/(i+1)
            label=""
            if fast_i is not None and i==fast_i: label="  Fastest"
            if slow_i is not None and i==slow_i: label = (label+"  Slowest") if label else "  Slowest"
            lap_cell=f"{self._fmt(lap)}{label}"
            tags=()
            if i==fast_i: tags+=("fast",)
            if i==slow_i: tags+=("slow",)
            self.tree.insert("",0,values=(i+1,lap_cell,self._fmt(total),self._fmt(avg_to_row)),tags=tags)
        self._update_avg_label()

    def _schedule_tick(self): self._update_face(); self.root.after(self._tick_ms,self._schedule_tick)
    def _update_face(self):
        val=self._lap_elapsed(); self.time_var.set(self._fmt(val))
        if self.widget and self.widget.winfo_exists(): self.widget_time_var.set(self._fmt(val))
    def _schedule_avg(self): self._update_avg_label(); self.root.after(self._avg_ms,self._schedule_avg)
    def _update_avg_label(self):
        if self.laps:
            avg=sum(self.laps)/len(self.laps); self.avg_var.set(f"Average (session): {self._fmt(avg)} across {len(self.laps)} lap(s)")
        else:
            self.avg_var.set("Average (session): —")

    # widget
    def toggle_widget(self):
        if self.widget and self.widget.winfo_exists(): self.widget.destroy(); self.widget=None
        else: self._show_widget()
    def _show_widget(self):
        w=tk.Toplevel(self.root); self.widget=w; w.overrideredirect(True); w.attributes("-topmost",True)
        WIDTH,HEIGHT,MARGIN=230,118,12; x=w.winfo_screenwidth()-WIDTH-MARGIN; y=MARGIN; w.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")
        container=tk.Frame(w,bg=BG,bd=1,highlightthickness=1,highlightbackground=BORDER); container.pack(fill=tk.BOTH,expand=True)
        def start_drag(e):
            w._sx = e.x_root - w.winfo_x()
            w._sy = e.y_root - w.winfo_y()
        def do_drag(e):
            w.geometry(f"+{e.x_root - w._sx}+{e.y_root - w._sy}")
        container.bind("<ButtonPress-1>",start_drag); container.bind("<B1-Motion>",do_drag)
        tk.Label(container,textvariable=self.widget_time_var,font=("Consolas",24,"bold"),bg=BG,fg=FG).pack(pady=(8,2))
        row=tk.Frame(container,bg=BG); row.pack()
        self._widget_play=tk.Button(row,text=("⏸" if self.running else "▶"),width=3,command=self.toggle_start_pause); self._widget_play.pack(side=tk.LEFT,padx=6)
        self._widget_lap=tk.Button(row,text="Lap",width=3,command=self.lap); self._widget_lap.pack(side=tk.LEFT,padx=6)
        tk.Button(row,text="↺",width=3,command=self.reset).pack(side=tk.LEFT,padx=6)
        tk.Button(container,text="✕",command=self.toggle_widget,relief=tk.FLAT,bg=BG).pack(anchor="ne",padx=6,pady=4)
        self._sync_widget()
    def _sync_widget(self):
        """Keep the widget's play/pause icon and Lap button in step with the main window."""
        if self.widget and self.widget.winfo_exists():
            self._widget_play.config(text=("⏸" if self.running else "▶"))
            self._widget_lap.config(state=(tk.NORMAL if self.running else tk.DISABLED))

    # logging
    def _open_session_log(self):
        self._session_open=True; stamp=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"); self._log_line(f"[SESSION START] {stamp}")
    def _close_session_log(self):
        if not self._session_open: return
        total=sum(self.laps); laps=len(self.laps); avg=(total/laps) if laps else 0.0
        stamp=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"); self._log_line(f"[SESSION END]   {stamp} | laps={laps} | total={self._fmt(total)} | avg={self._fmt(avg)}\n"); self._session_open=False
    def _log_lap(self,idx:int,lap_time:float):
        total=sum(self.laps); avg=sum(self.laps)/len(self.laps); self._log_line(f"LAP {idx:02d} | lap={self._fmt(lap_time)} | total={self._fmt(total)} | avg={self._fmt(avg)}")
    def _log_line(self,text:str):
        try:
            with open(self.log_path,"a",encoding="utf-8") as f:
                f.write(text+"\n"); f.flush(); os.fsync(f.fileno())
        except Exception: pass

    # close
    def _on_close(self): self._close_session_log(); self.root.destroy()

    # misc
    def _toggle_topmost(self): self.root.attributes("-topmost",bool(self.topmost_var.get()))
    @staticmethod
    def _fmt(sec:float)->str:
        sec=max(0.0,float(sec)); h=int(sec//3600); m=int((sec%3600)//60); s=int(sec%60); hund=int((sec-int(sec))*100)
        return f"{h:02d}:{m:02d}:{s:02d}.{hund:02d}"

if __name__=="__main__":
    root=tk.Tk(); app=Stopwatch(root); root.mainloop()
