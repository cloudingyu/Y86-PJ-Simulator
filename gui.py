import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import subprocess
import platform
import os
import re

class ModernY86Visualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Y86-64 Simulator - Ultimate GUI")
        self.root.geometry("1400x900")
        
        # --- 字体配置 ---
        # 1. 代码/数据字体: 用于寄存器、内存、源码、HEX值 (硬核风格)
        self.font_code = "Maple Mono"
        # 2. 界面字体: 用于按钮、标题、标签 (人文风格)
        self.font_ui = "LXGW Wenkai Mono"
        
        # --- 配色方案 (Light Theme) ---
        self.colors = {
            "bg": "#fafafa",           # 整体背景
            "panel_bg": "#f3f3f3",     # 面板背景
            "fg": "#333333",           # 默认文字
            "accent": "#0078d4",       # 强调色 (蓝)
            "accent_hover": "#2b88d8", 
            "highlight": "#d13438",    # 数据变化高亮 (红)
            "line_hl": "#e1f0fa",      # 源码行高亮 (浅蓝)
            "mem_bg": "#ffffff",       # 表格/源码背景
            "mem_fg": "#0451a5",       # 数据颜色 (深蓝)
            "stat_ok": "#107c10",      # 状态正常 (绿)
            "stat_err": "#d13438",     # 状态错误 (红)
            "cache_title": "#d13438",  # Cache 标题颜色
            "grid_line": "#e0e0e0"     # 表格线颜色
        }
        
        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        
        self.configure_styles()
        self.root.configure(bg=self.colors["bg"])

        self.states = []
        self.current_step = 0
        self.reg_widgets = {} 
        self.pc_to_line = {} 
        
        self.setup_ui()

    def configure_styles(self):
        # 基础样式
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Panel.TFrame", background=self.colors["panel_bg"], relief="flat")
        
        # UI 标签 (LXGW)
        self.style.configure("TLabel", 
            background=self.colors["bg"], 
            foreground=self.colors["fg"], 
            font=(self.font_ui, 12)
        )
        self.style.configure("Header.TLabel", 
            background=self.colors["panel_bg"], 
            foreground=self.colors["fg"], 
            font=(self.font_ui, 14, "bold")
        )
        
        # 数值标签 (Maple)
        self.style.configure("Value.TLabel", 
            background=self.colors["panel_bg"], 
            foreground=self.colors["mem_fg"], 
            font=(self.font_code, 13)
        )
        
        # 按钮样式 (LXGW)
        self.style.configure("Accent.TButton", 
            background=self.colors["accent"], 
            foreground="white", 
            borderwidth=0,
            font=(self.font_ui, 12, "bold"),
            padding=(15, 10)
        )
        self.style.map("Accent.TButton",
            background=[('active', self.colors["accent_hover"]), ('disabled', '#cccccc')],
            foreground=[('disabled', '#666666')]
        )
        
        # 状态栏样式 (Maple)
        self.style.configure("Status.TLabel", 
            background=self.colors["panel_bg"], 
            foreground=self.colors["stat_ok"], 
            font=(self.font_code, 15, "bold")
        )
        self.style.configure("Cache.TLabel", 
            background=self.colors["panel_bg"], 
            foreground=self.colors["cache_title"], 
            font=(self.font_code, 15, "bold")
        )

        # 表格 (Treeview) 样式
        self.style.configure("Treeview.Heading", 
            font=(self.font_ui, 12, "bold"),
            background=self.colors["panel_bg"],
            foreground=self.colors["fg"],
            relief="flat"
        )
        self.style.configure("Treeview", 
            background=self.colors["mem_bg"],
            foreground=self.colors["mem_fg"],
            fieldbackground=self.colors["mem_bg"],
            font=(self.font_code, 13),
            rowheight=28,
            borderwidth=0
        )
        self.style.map('Treeview', 
            background=[('selected', self.colors["line_hl"])], 
            foreground=[('selected', self.colors["mem_fg"])]
        )

    def setup_ui(self):
        # 1. 顶部控制栏
        control_bar = ttk.Frame(self.root, style="TFrame", padding=(15, 20))
        control_bar.pack(side=tk.TOP, fill=tk.X)
        
        btn_frame = ttk.Frame(control_bar, style="TFrame")
        btn_frame.pack(side=tk.LEFT)
        
        self.btn_load = ttk.Button(btn_frame, text="Load", style="Accent.TButton", command=self.load_program)
        self.btn_load.pack(side=tk.LEFT, padx=(0, 15))
        
        self.btn_prev = ttk.Button(btn_frame, text="◀ Step Back", style="Accent.TButton", command=self.prev_step, state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT, padx=8)
        
        self.btn_next = ttk.Button(btn_frame, text="Step Over ▶", style="Accent.TButton", command=self.next_step, state=tk.DISABLED)
        self.btn_next.pack(side=tk.LEFT, padx=8)

        self.lbl_progress = ttk.Label(control_bar, text="Ready", font=(self.font_ui, 12))
        self.lbl_progress.pack(side=tk.RIGHT, padx=15)

        # 2. 主内容区 (三栏布局)
        main_pane = ttk.Frame(self.root, style="TFrame", padding=15)
        main_pane.pack(fill=tk.BOTH, expand=True)
        
        main_pane.columnconfigure(0, weight=1) # 左：状态
        main_pane.columnconfigure(1, weight=2) # 中：源码
        main_pane.columnconfigure(2, weight=1) # 右：内存
        main_pane.rowconfigure(0, weight=1)

        # --- 左侧面板 ---
        left_panel = ttk.Frame(main_pane, style="TFrame")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        self.create_status_card(left_panel)
        self.create_cache_card(left_panel)
        self.create_register_card(left_panel)

        # --- 中间面板：源代码 ---
        mid_panel = ttk.Frame(main_pane, style="Panel.TFrame")
        mid_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 15))
        
        ttk.Label(mid_panel, text="Source Code", style="Header.TLabel", padding=15).pack(fill=tk.X)
        
        src_frame = ttk.Frame(mid_panel, style="Panel.TFrame")
        src_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.src_text = tk.Text(src_frame,
            bg=self.colors["mem_bg"], 
            fg=self.colors["fg"],
            insertbackground="black",
            font=(self.font_code, 13),
            bd=0,
            highlightthickness=0,
            state=tk.DISABLED,
            wrap=tk.NONE,
            padx=15, pady=10
        )
        self.src_text.tag_config("current_line", background=self.colors["line_hl"])
        
        src_scroll_y = ttk.Scrollbar(src_frame, orient="vertical", command=self.src_text.yview)
        src_scroll_x = ttk.Scrollbar(src_frame, orient="horizontal", command=self.src_text.xview)
        self.src_text.configure(yscrollcommand=src_scroll_y.set, xscrollcommand=src_scroll_x.set)
        
        src_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        src_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.src_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- 右侧面板：内存 (表格) ---
        right_panel = ttk.Frame(main_pane, style="Panel.TFrame")
        right_panel.grid(row=0, column=2, sticky="nsew")
        
        ttk.Label(right_panel, text="Memory", style="Header.TLabel", padding=15).pack(fill=tk.X)
        
        mem_frame = ttk.Frame(right_panel, style="Panel.TFrame")
        mem_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 使用 Treeview
        columns = ("addr", "val")
        self.mem_tree = ttk.Treeview(mem_frame, columns=columns, show="headings", selectmode="browse")
        
        self.mem_tree.heading("addr", text="Address")
        self.mem_tree.heading("val", text="Value (Hex)")
        self.mem_tree.column("addr", width=120, anchor="center")
        self.mem_tree.column("val", width=220, anchor="center")
        
        mem_scroll = ttk.Scrollbar(mem_frame, orient="vertical", command=self.mem_tree.yview)
        self.mem_tree.configure(yscrollcommand=mem_scroll.set)
        
        mem_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.mem_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_status_card(self, parent):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=20)
        card.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(card, text="CPU Status", style="Header.TLabel").pack(anchor="w", pady=(0, 15))
        
        content = ttk.Frame(card, style="Panel.TFrame")
        content.pack(fill=tk.X)
        
        # PC
        self.var_pc = tk.StringVar(value="0x0")
        pc_frame = ttk.Frame(content, style="Panel.TFrame")
        pc_frame.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(pc_frame, text="PC", foreground="#666666", background=self.colors["panel_bg"]).pack(anchor="w")
        ttk.Label(pc_frame, textvariable=self.var_pc, style="Status.TLabel", foreground=self.colors["accent"]).pack(anchor="w")
        
        # CC
        self.var_cc = tk.StringVar(value="ZF=1 SF=0 OF=0")
        cc_frame = ttk.Frame(content, style="Panel.TFrame")
        cc_frame.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(cc_frame, text="Flags", foreground="#666666", background=self.colors["panel_bg"]).pack(anchor="w")
        ttk.Label(cc_frame, textvariable=self.var_cc, style="Status.TLabel", foreground=self.colors["fg"]).pack(anchor="w")

        # STAT
        self.var_stat = tk.StringVar(value="AOK")
        stat_frame = ttk.Frame(content, style="Panel.TFrame")
        stat_frame.pack(side=tk.LEFT)
        ttk.Label(stat_frame, text="Stat", foreground="#666666", background=self.colors["panel_bg"]).pack(anchor="w")
        self.lbl_stat = ttk.Label(stat_frame, textvariable=self.var_stat, style="Status.TLabel")
        self.lbl_stat.pack(anchor="w")

    def create_cache_card(self, parent):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=20)
        card.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(card, text="Cache", style="Header.TLabel").pack(anchor="w", pady=(0, 15))
        
        content = ttk.Frame(card, style="Panel.TFrame")
        content.pack(fill=tk.X)

        self.var_hits = tk.StringVar(value="0")
        f1 = ttk.Frame(content, style="Panel.TFrame")
        f1.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(f1, text="Hits", foreground="#666666", background=self.colors["panel_bg"]).pack(anchor="w")
        ttk.Label(f1, textvariable=self.var_hits, style="Value.TLabel").pack(anchor="w")

        self.var_miss = tk.StringVar(value="0")
        f2 = ttk.Frame(content, style="Panel.TFrame")
        f2.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(f2, text="Misses", foreground="#666666", background=self.colors["panel_bg"]).pack(anchor="w")
        ttk.Label(f2, textvariable=self.var_miss, style="Value.TLabel").pack(anchor="w")

        self.var_rate = tk.StringVar(value="0.0%")
        f3 = ttk.Frame(content, style="Panel.TFrame")
        f3.pack(side=tk.LEFT)
        ttk.Label(f3, text="Rate", foreground="#666666", background=self.colors["panel_bg"]).pack(anchor="w")
        ttk.Label(f3, textvariable=self.var_rate, style="Cache.TLabel").pack(anchor="w")

    def create_register_card(self, parent):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=20)
        card.pack(fill=tk.BOTH, expand=True)
        ttk.Label(card, text="Registers", style="Header.TLabel").pack(anchor="w", pady=(0, 15))
        
        grid_frame = ttk.Frame(card, style="Panel.TFrame")
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        regs = ["rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi", 
                "r8", "r9", "r10", "r11", "r12", "r13", "r14"]
        
        for i, rname in enumerate(regs):
            row = i
            lbl_name = ttk.Label(grid_frame, text=f"%{rname}", width=5, 
                               background=self.colors["panel_bg"], foreground="#666666", font=(self.font_code, 13))
            lbl_name.grid(row=row, column=0, sticky="w", pady=3)
            
            lbl_val = ttk.Label(grid_frame, text="0x0000000000000000", style="Value.TLabel")
            lbl_val.grid(row=row, column=1, sticky="e", padx=(15, 0), pady=3)
            
            self.reg_widgets[rname] = lbl_val

    def load_program(self):
        filename = filedialog.askopenfilename(filetypes=[("Y86 Object", "*.yo")])
        if not filename: return
        
        bin_path = "./cpu"
        if os.path.exists("./cpu.exe"):
            bin_path = "./cpu.exe"
        elif not os.path.exists(bin_path):
            if platform.system() == "Windows":
                bin_path = "cpu.exe" 
            
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                input_data = f.read()
                
            result = subprocess.run([bin_path, '-v'], input=input_data, text=True, capture_output=True, encoding='utf-8')
            
            if result.returncode != 0 and not result.stdout:
                raise Exception(f"Simulator crashed.\n{result.stderr}")

            raw_output = result.stdout
            start = raw_output.find('[')
            end = raw_output.rfind(']') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON output found.")
            self.states = json.loads(raw_output[start:end])
            
            self.parse_source_code(input_data)
            
            self.current_step = 0
            self.update_display()
            self.btn_next.config(state=tk.NORMAL)
            self.btn_prev.config(state=tk.DISABLED)
            self.lbl_progress.config(text=f"Loaded: {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def parse_source_code(self, source_content):
        self.pc_to_line = {}
        lines = source_content.splitlines()
        
        self.src_text.config(state=tk.NORMAL)
        self.src_text.delete(1.0, tk.END)
        self.src_text.insert(tk.END, source_content)
        self.src_text.config(state=tk.DISABLED)
        
        for i, line in enumerate(lines):
            match = re.match(r'\s*(0x[0-9a-fA-F]+):', line)
            if match:
                try:
                    address = int(match.group(1), 16)
                    if address not in self.pc_to_line: self.pc_to_line[address] = i + 1
                except ValueError: pass

    def next_step(self):
        if self.current_step < len(self.states) - 1:
            self.current_step += 1
            self.update_display()
            self.btn_prev.config(state=tk.NORMAL)
            if self.current_step == len(self.states) - 1: self.btn_next.config(state=tk.DISABLED)

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_display()
            self.btn_next.config(state=tk.NORMAL)
            if self.current_step == 0: self.btn_prev.config(state=tk.DISABLED)

    def update_display(self):
        state = self.states[self.current_step]
        prev_state = self.states[self.current_step - 1] if self.current_step > 0 else None
        
        self.lbl_progress.config(text=f"Cycle: {self.current_step + 1} / {len(self.states)}")
        
        current_pc = state['PC']
        self.var_pc.set(f"0x{current_pc:x}")
        
        cc = state['CC']
        self.var_cc.set(f"ZF={cc['ZF']} SF={cc['SF']} OF={cc['OF']}")
        
        stat_map = {1: "AOK", 2: "HLT", 3: "ADR", 4: "INS"}
        stat_val = stat_map.get(state['STAT'], str(state['STAT']))
        self.var_stat.set(stat_val)
        
        if state['STAT'] != 1:
            self.lbl_stat.configure(foreground=self.colors["stat_err"])
        else:
            self.lbl_stat.configure(foreground=self.colors["stat_ok"])

        # Cache Update
        if 'CACHE' in state:
            c = state['CACHE']
            self.var_hits.set(str(c['hits']))
            self.var_miss.set(str(c['misses']))
            self.var_rate.set(f"{c['rate']:.1f}%")

        # Source Highlight
        self.src_text.tag_remove("current_line", "1.0", tk.END)
        line_num = self.pc_to_line.get(current_pc)
        if line_num:
            self.src_text.tag_add("current_line", f"{line_num}.0", f"{line_num+1}.0")
            self.src_text.see(f"{line_num}.0")

        # Registers (Unsigned Hex Fix)
        reg_data = state['REG']
        prev_reg = prev_state['REG'] if prev_state else None
        
        for rname, val in reg_data.items():
            widget = self.reg_widgets.get(rname)
            if widget:
                # 核心修复：强制转为无符号 64 位显示
                unsigned_val = val & 0xFFFFFFFFFFFFFFFF
                hex_val = f"0x{unsigned_val:016x}"
                widget.config(text=hex_val)
                
                is_changed = prev_reg and prev_reg.get(rname) != val
                if is_changed:
                    widget.configure(foreground=self.colors["highlight"], font=(self.font_code, 13, "bold"))
                else:
                    widget.configure(foreground=self.colors["mem_fg"], font=(self.font_code, 13))

        # Memory (Treeview update with Unsigned Hex Fix)
        for item in self.mem_tree.get_children():
            self.mem_tree.delete(item)
        
        mem_data = state['MEM']
        sorted_addr = sorted([int(k) for k in mem_data.keys()])
        
        for addr in sorted_addr:
            val = mem_data[str(addr)]
            # 核心修复：强制转为无符号 64 位显示
            unsigned_val = val & 0xFFFFFFFFFFFFFFFF
            self.mem_tree.insert("", "end", values=(f"0x{addr:04x}", f"0x{unsigned_val:016x}"))

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    app = ModernY86Visualizer(root)
    root.mainloop()