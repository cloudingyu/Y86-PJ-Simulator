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
        self.root.title("Y86-64 Simulator - Customized Font Edition")
        self.root.geometry("1300x750")
        
        # --- 字体配置 (核心修改) ---
        # 英文/代码/数据优先字体
        self.font_code = "Maple Mono"
        # 中文/UI/注释优先字体
        self.font_ui = "LXGW Wenkai Mono"
        
        # --- 1. 配色方案 (Dark Theme) ---
        self.colors = {
            "bg": "#1e1e1e",           # 整体背景
            "panel_bg": "#252526",     # 面板背景
            "fg": "#d4d4d4",           # 默认文字
            "accent": "#007acc",       # 强调色
            "accent_hover": "#0098ff", 
            "highlight": "#f44336",    # 数据变化高亮 (红)
            "line_hl": "#3a3d41",      # 源码行高亮 (深灰)
            "mem_bg": "#1e1e1e",       
            "mem_fg": "#9cdcfe",       # 内存数据蓝
            "comment": "#6a9955"       # 注释绿
        }
        
        # --- 2. 配置样式 ---
        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        
        self.configure_styles()
        self.root.configure(bg=self.colors["bg"])

        # --- 3. 数据状态 ---
        self.states = []
        self.current_step = 0
        self.reg_widgets = {} 
        self.pc_to_line = {} 
        
        # --- 4. 构建界面 ---
        self.setup_ui()

    def configure_styles(self):
        # 通用 Frame
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Panel.TFrame", background=self.colors["panel_bg"], relief="flat")
        
        # UI 标签：使用 LXGW Wenkai Mono
        self.style.configure("TLabel", 
            background=self.colors["bg"], 
            foreground=self.colors["fg"], 
            font=(self.font_ui, 11)
        )
        self.style.configure("Header.TLabel", 
            background=self.colors["panel_bg"], 
            foreground=self.colors["fg"], 
            font=(self.font_ui, 12, "bold")
        )
        
        # 数值标签：使用 Maple Mono
        self.style.configure("Value.TLabel", 
            background=self.colors["panel_bg"], 
            foreground="#569cd6", 
            font=(self.font_code, 11)
        )
        
        # 按钮样式：使用 LXGW Wenkai Mono
        self.style.configure("Accent.TButton", 
            background=self.colors["accent"], 
            foreground="white", 
            borderwidth=0,
            font=(self.font_ui, 11, "bold"),
            padding=(15, 8)
        )
        self.style.map("Accent.TButton",
            background=[('active', self.colors["accent_hover"]), ('disabled', '#3e3e42')],
            foreground=[('disabled', '#a0a0a0')]
        )
        
        # 状态栏数值：使用 Maple Mono
        self.style.configure("Status.TLabel", 
            background=self.colors["bg"], 
            foreground="#4ec9b0", 
            font=(self.font_code, 13, "bold")
        )

    def setup_ui(self):
        # === 顶部控制栏 ===
        control_bar = ttk.Frame(self.root, style="TFrame", padding=(10, 15))
        control_bar.pack(side=tk.TOP, fill=tk.X)
        
        btn_frame = ttk.Frame(control_bar, style="TFrame")
        btn_frame.pack(side=tk.LEFT)
        
        self.btn_load = ttk.Button(btn_frame, text="📂 加载程序 (Load)", style="Accent.TButton", command=self.load_program)
        self.btn_load.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_prev = ttk.Button(btn_frame, text="◀ 上一步", style="Accent.TButton", command=self.prev_step, state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT, padx=5)
        
        self.btn_next = ttk.Button(btn_frame, text="下一步 ▶", style="Accent.TButton", command=self.next_step, state=tk.DISABLED)
        self.btn_next.pack(side=tk.LEFT, padx=5)

        self.lbl_progress = ttk.Label(control_bar, text="就绪 (Ready)", font=(self.font_ui, 11))
        self.lbl_progress.pack(side=tk.RIGHT, padx=10)

        # === 主内容区 (三栏布局) ===
        main_pane = ttk.Frame(self.root, style="TFrame", padding=10)
        main_pane.pack(fill=tk.BOTH, expand=True)
        
        main_pane.columnconfigure(0, weight=1) # 寄存器
        main_pane.columnconfigure(1, weight=2) # 源代码
        main_pane.columnconfigure(2, weight=1) # 内存
        main_pane.rowconfigure(0, weight=1)

        # --- 第一栏：CPU 状态 ---
        left_panel = ttk.Frame(main_pane, style="TFrame")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.create_status_card(left_panel)
        self.create_register_card(left_panel)

        # --- 第二栏：源代码 ---
        mid_panel = ttk.Frame(main_pane, style="Panel.TFrame")
        mid_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        
        ttk.Label(mid_panel, text="源代码 (Source Code)", style="Header.TLabel", padding=10).pack(fill=tk.X)
        
        src_frame = ttk.Frame(mid_panel, style="Panel.TFrame")
        src_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 源代码区域：为了同时支持中英文显示良好，建议使用 LXGW Wenkai Mono
        # 或者如果你希望代码部分非常像代码，可以使用 Maple Mono (中文可能回退)
        # 这里为了满足"中文使用LXGW"的需求（源码里有中文注释），我配置为 LXGW Wenkai Mono
        self.src_text = tk.Text(src_frame,
            bg=self.colors["bg"], 
            fg=self.colors["fg"],
            insertbackground="white",
            font=(self.font_ui, 12), # 使用 LXGW 以确保注释显示完美
            bd=0,
            highlightthickness=0,
            state=tk.DISABLED,
            wrap=tk.NONE
        )
        self.src_text.tag_config("current_line", background=self.colors["line_hl"])
        
        src_scroll_y = ttk.Scrollbar(src_frame, orient="vertical", command=self.src_text.yview)
        src_scroll_x = ttk.Scrollbar(src_frame, orient="horizontal", command=self.src_text.xview)
        self.src_text.configure(yscrollcommand=src_scroll_y.set, xscrollcommand=src_scroll_x.set)
        
        src_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        src_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.src_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- 第三栏：内存 ---
        right_panel = ttk.Frame(main_pane, style="Panel.TFrame")
        right_panel.grid(row=0, column=2, sticky="nsew")
        
        ttk.Label(right_panel, text="内存视图 (Memory)", style="Header.TLabel", padding=10).pack(fill=tk.X)
        
        mem_frame = ttk.Frame(right_panel, style="Panel.TFrame")
        mem_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 内存数据纯粹是 Hex，使用 Maple Mono 效果最好
        self.mem_text = tk.Text(mem_frame, 
            bg=self.colors["mem_bg"], 
            fg=self.colors["mem_fg"],
            insertbackground="white",
            font=(self.font_code, 12), # Maple Mono
            bd=0,
            highlightthickness=0,
            state=tk.DISABLED
        )
        mem_scroll = ttk.Scrollbar(mem_frame, orient="vertical", command=self.mem_text.yview)
        self.mem_text.configure(yscrollcommand=mem_scroll.set)
        
        mem_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.mem_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_status_card(self, parent):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=15)
        card.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(card, text="处理器状态 (Status)", style="Header.TLabel").pack(anchor="w", pady=(0, 10))
        
        content = ttk.Frame(card, style="Panel.TFrame")
        content.pack(fill=tk.X)
        
        # PC
        self.var_pc = tk.StringVar(value="0x0")
        pc_frame = ttk.Frame(content, style="Panel.TFrame")
        pc_frame.pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(pc_frame, text="PC", foreground="#808080", background=self.colors["panel_bg"]).pack(anchor="w")
        ttk.Label(pc_frame, textvariable=self.var_pc, style="Status.TLabel", foreground=self.colors["accent"]).pack(anchor="w")
        
        # CC
        self.var_cc = tk.StringVar(value="Z=1 S=0 O=0")
        cc_frame = ttk.Frame(content, style="Panel.TFrame")
        cc_frame.pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(cc_frame, text="CC", foreground="#808080", background=self.colors["panel_bg"]).pack(anchor="w")
        ttk.Label(cc_frame, textvariable=self.var_cc, style="Status.TLabel").pack(anchor="w")

        # STAT
        self.var_stat = tk.StringVar(value="AOK")
        stat_frame = ttk.Frame(content, style="Panel.TFrame")
        stat_frame.pack(side=tk.LEFT)
        ttk.Label(stat_frame, text="STAT", foreground="#808080", background=self.colors["panel_bg"]).pack(anchor="w")
        self.lbl_stat = ttk.Label(stat_frame, textvariable=self.var_stat, style="Status.TLabel")
        self.lbl_stat.pack(anchor="w")

    def create_register_card(self, parent):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=15)
        card.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(card, text="通用寄存器 (Registers)", style="Header.TLabel").pack(anchor="w", pady=(0, 10))
        
        grid_frame = ttk.Frame(card, style="Panel.TFrame")
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        regs = ["rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi", 
                "r8", "r9", "r10", "r11", "r12", "r13", "r14"]
        
        for i, rname in enumerate(regs):
            row = i
            # 寄存器名使用 Maple Mono 对齐
            lbl_name = ttk.Label(grid_frame, text=f"%{rname}", width=5, 
                               background=self.colors["panel_bg"], foreground="#808080", font=(self.font_code, 12))
            lbl_name.grid(row=row, column=0, sticky="w", pady=2)
            
            # 寄存器值使用 Maple Mono
            lbl_val = ttk.Label(grid_frame, text="0x0000000000000000", style="Value.TLabel")
            lbl_val.grid(row=row, column=1, sticky="e", padx=(10, 0), pady=2)
            
            self.reg_widgets[rname] = lbl_val

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
                address_str = match.group(1)
                try:
                    address = int(address_str, 16)
                    if address not in self.pc_to_line:
                        self.pc_to_line[address] = i + 1
                except ValueError:
                    pass

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
                
            result = subprocess.run([bin_path], input=input_data, text=True, capture_output=True, encoding='utf-8')
            
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

    def next_step(self):
        if self.current_step < len(self.states) - 1:
            self.current_step += 1
            self.update_display()
            self.btn_prev.config(state=tk.NORMAL)
            if self.current_step == len(self.states) - 1:
                self.btn_next.config(state=tk.DISABLED)

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_display()
            self.btn_next.config(state=tk.NORMAL)
            if self.current_step == 0:
                self.btn_prev.config(state=tk.DISABLED)

    def update_display(self):
        state = self.states[self.current_step]
        prev_state = self.states[self.current_step - 1] if self.current_step > 0 else None
        
        self.lbl_progress.config(text=f"Cycle: {self.current_step + 1} / {len(self.states)}")
        
        current_pc = state['PC']
        self.var_pc.set(f"0x{current_pc:x}")
        
        cc = state['CC']
        self.var_cc.set(f"Z={cc['ZF']} S={cc['SF']} O={cc['OF']}")
        
        stat_map = {1: "AOK", 2: "HLT", 3: "ADR", 4: "INS"}
        stat_val = stat_map.get(state['STAT'], str(state['STAT']))
        self.var_stat.set(stat_val)
        
        if state['STAT'] != 1:
            self.lbl_stat.configure(foreground=self.colors["highlight"])
        else:
            self.lbl_stat.configure(foreground="#4ec9b0")

        # 源码高亮
        self.src_text.tag_remove("current_line", "1.0", tk.END)
        line_num = self.pc_to_line.get(current_pc)
        if line_num:
            self.src_text.tag_add("current_line", f"{line_num}.0", f"{line_num+1}.0")
            self.src_text.see(f"{line_num}.0")

        # 更新寄存器
        reg_data = state['REG']
        prev_reg = prev_state['REG'] if prev_state else None
        
        for rname, val in reg_data.items():
            widget = self.reg_widgets.get(rname)
            if widget:
                hex_val = f"0x{val:016x}"
                widget.config(text=hex_val)
                
                if prev_reg and prev_reg.get(rname) != val:
                    widget.configure(foreground=self.colors["highlight"], font=(self.font_code, 12, "bold"))
                else:
                    widget.configure(foreground="#569cd6", font=(self.font_code, 12))

        # 更新内存
        self.mem_text.config(state=tk.NORMAL)
        self.mem_text.delete(1.0, tk.END)
        
        mem_data = state['MEM']
        sorted_addr = sorted([int(k) for k in mem_data.keys()])
        
        for addr in sorted_addr:
            val = mem_data[str(addr)]
            line = f"0x{addr:04x}: 0x{val:016x}\n"
            self.mem_text.insert(tk.END, line)
            
        self.mem_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = ModernY86Visualizer(root)
    root.mainloop()