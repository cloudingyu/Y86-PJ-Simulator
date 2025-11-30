import json
import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import copy

class Y86Visualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Y86-64 Simulator Visualizer")
        self.root.geometry("800x600")

        # 数据存储
        self.states = []
        self.current_step = 0
        
        # 布局
        self.setup_ui()
        
    def setup_ui(self):
        # 1. 顶部控制栏
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(control_frame, text="Load .yo File", command=self.load_program).pack(side=tk.LEFT, padx=5)
        
        self.btn_prev = tk.Button(control_frame, text="<< Prev", command=self.prev_step, state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT, padx=5)
        
        self.btn_next = tk.Button(control_frame, text="Next >>", command=self.next_step, state=tk.DISABLED)
        self.btn_next.pack(side=tk.LEFT, padx=5)
        
        self.lbl_step = tk.Label(control_frame, text="Step: 0 / 0", font=("Arial", 12))
        self.lbl_step.pack(side=tk.LEFT, padx=20)

        # 2. 主要内容区 (左右分栏)
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：PC 和 寄存器
        left_frame = tk.LabelFrame(main_frame, text="CPU State", padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # PC & CC 显示
        self.var_pc = tk.StringVar(value="PC: 0")
        tk.Label(left_frame, textvariable=self.var_pc, font=("Consolas", 14, "bold"), fg="blue").grid(row=0, column=0, columnspan=2, sticky="w")
        
        self.var_cc = tk.StringVar(value="CC: ZF=1 SF=0 OF=0")
        tk.Label(left_frame, textvariable=self.var_cc, font=("Consolas", 12)).grid(row=1, column=0, columnspan=2, sticky="w")
        
        # 寄存器显示表格
        self.reg_labels = {}
        regs = ["rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi", 
                "r8", "r9", "r10", "r11", "r12", "r13", "r14"]
        
        for idx, rname in enumerate(regs):
            tk.Label(left_frame, text=f"%{rname}:", font=("Consolas", 11)).grid(row=idx+2, column=0, sticky="e", padx=5)
            val_lbl = tk.Label(left_frame, text="0", font=("Consolas", 11))
            val_lbl.grid(row=idx+2, column=1, sticky="w", padx=5)
            self.reg_labels[rname] = val_lbl

        # 右侧：内存显示 (只显示非零)
        right_frame = tk.LabelFrame(main_frame, text="Non-Zero Memory", padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.mem_text = tk.Text(right_frame, width=30, height=20, font=("Consolas", 10))
        self.mem_text.pack(fill=tk.BOTH, expand=True)

    def load_program(self):
        # 选择 .yo 文件
        filename = filedialog.askopenfilename(filetypes=[("Y86 Object", "*.yo")])
        if not filename: return
        
        # 调用你的 cpu.exe
        # 注意：这里假设 cpu.exe 在同一目录下，且能从 stdin 读取
        try:
            with open(filename, 'r') as f:
                input_data = f.read()
                
            # 运行模拟器
            result = subprocess.run(['./cpu.exe'], input=input_data, text=True, capture_output=True)
            
            # 解析 JSON 输出
            # 有时候输出里可能混杂非 JSON 字符，尝试只提取 JSON 部分
            raw_output = result.stdout
            start = raw_output.find('[')
            end = raw_output.rfind(']') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found in output")
                
            json_str = raw_output[start:end]
            self.states = json.loads(json_str)
            
            # 重置界面
            self.current_step = 0
            self.update_display()
            self.btn_next.config(state=tk.NORMAL)
            self.btn_prev.config(state=tk.DISABLED)
            
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to run simulator:\n{e}")

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
        
        # 1. Update Label
        self.lbl_step.config(text=f"Step: {self.current_step + 1} / {len(self.states)}")
        
        # 2. Update PC
        self.var_pc.set(f"PC: {state['PC']}")
        
        # 3. Update CC
        cc = state['CC']
        self.var_cc.set(f"CC: ZF={cc['ZF']} SF={cc['SF']} OF={cc['OF']}")
        
        # 4. Update Registers (Highligh Changes)
        reg_data = state['REG']
        prev_reg = prev_state['REG'] if prev_state else None
        
        for rname, val in reg_data.items():
            label = self.reg_labels.get(rname)
            if label:
                # 转换为16进制显示更专业
                hex_val = f"0x{val:016x}" # if val >= 0 else f"{val}"
                label.config(text=hex_val)
                
                # 如果值变了，标红；否则标黑
                if prev_reg and prev_reg.get(rname) != val:
                    label.config(fg="red", font=("Consolas", 11, "bold"))
                else:
                    label.config(fg="black", font=("Consolas", 11))

        # 5. Update Memory
        self.mem_text.delete(1.0, tk.END)
        mem_data = state['MEM']
        # 排序显示
        sorted_addr = sorted([int(k) for k in mem_data.keys()])
        for addr in sorted_addr:
            val = mem_data[str(addr)]
            self.mem_text.insert(tk.END, f"0x{addr:04x}: {val}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = Y86Visualizer(root)
    root.mainloop()