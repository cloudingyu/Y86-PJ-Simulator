# Y86-64 模拟器项目需求文档 (Requirements.md)

## 项目概述

本项目是CSAPP（Computer Systems: A Programmer's Perspective）第四章的配套课程项目，要求基于Y86-64指令集实现一个软件层面的模拟处理器。该模拟器需要能够执行Y86-64指令，并通过指定的测试用例验证正确性。

## 功能需求

### 核心功能
- 实现Y86-64指令集的完整模拟，支持所有Y86-64指令的执行。
- 模拟处理器应包含以下组件：
  - 程序计数器（PC）
  - 15个通用寄存器（%rax, %rbx, %rcx, %rdx, %rsi, %rdi, %rsp, %rbp, %r8-%r14）
  - 内存系统
  - 条件码（ZF, SF, OF）
  - 状态码（STAT）

### 处理器架构
模拟器可以采用单周期或多周期架构。单周期CPU执行一条指令分为以下阶段：
- **取指（Fetch）**：从内存中读取指令字节，使用PC作为内存地址。
- **译码（Decode）**：从寄存器中读取用于运算的数据。
- **执行（Execute）**：ALU执行运算，或计算内存引用有效地址，或调整栈指针，并设置条件码。
- **访存（Memory）**：可能将数据写入内存或从内存读取数据。
- **写回（Write back）**：将最多两个结果写入寄存器。
- **更新PC（PC update）**：将PC更新为下一条指令地址。

## 输入输出格式

### 输入格式
- 输入为Y86-64汇编指令序列，格式为十六进制字节码。
- 输入通过标准输入流（stdin）提供。
- 示例格式（prog1.yo）：
  ```
  0x000: 30f20a00000000000000 |   irmovq $10,%rdx
  0x00a: 30f00300000000000000 |   irmovq  $3,%rax
  0x014: 10                   |   nop
  0x015: 10                   |   nop
  0x016: 10                   |   nop
  0x017: 6020                 |   addq %rdx,%rax
  0x019: 00                   |   halt
  ```

### 输出格式
- 输出为JSON格式，每条指令执行完毕后输出当前状态。
- 输出通过标准输出流（stdout）提供。
- 必须严格遵循answer/目录下示例格式。
- 每个输出条目包含：
  - **CC**: 条件码（OF, SF, ZF），以整数表示（0或1）。
  - **MEM**: 非零内存值，键值对格式 {地址: 值}，地址和值均为十进制，八字节对齐，按小端法解释为十进制有符号整数。
  - **PC**: 程序计数器值，十进制。
  - **REG**: 所有15个寄存器的值，键值对格式 {寄存器名: 值}，值为十进制。
  - **STAT**: 状态码，整数表示（1表示正常，2表示异常等）。
- 输出顺序必须与指令执行顺序一致。
- 示例格式（prog1.json片段）：
  ```json
  [
      {
          "CC": {
              "OF": 0,
              "SF": 0,
              "ZF": 1
          },
          "MEM": {
              "0": 717360,
              "16": 6922050288173973504,
              "24": 32,
              "8": 16914579456
          },
          "PC": 10,
          "REG": {
              "r10": 0,
              "r11": 0,
              "r12": 0,
              "r13": 0,
              "r14": 0,
              "r8": 0,
              "r9": 0,
              "rax": 0,
              "rbp": 0,
              "rbx": 0,
              "rcx": 0,
              "rdi": 0,
              "rdx": 10,
              "rsi": 0,
              "rsp": 0
          },
          "STAT": 1
      }
  ]
  ```

## 实现要求

### 技术栈
- 编程语言不限，可以使用C、C++、Python等。
- 对于C/C++实现，可以参考nlohmann/json库处理JSON输出。
- 程序必须以可执行文件形式提供，或通过解释器运行。

### 架构要求
- 处理器架构不限，可以是单周期或多周期。
- 必须正确实现Y86-64指令集的所有指令。
- 内存访问必须正确处理字节序（小端法）。
- 所有数值计算和存储必须使用64位表示。

### 正确性要求
- 输入输出格式必须完全正确。
- 必须通过所有测试用例（test/目录下的.yo文件）。
- 模拟器行为必须与Y86-64规范一致。

## 测试要求

### 测试环境
- 测试脚本：test.py
- 测试命令：`python test.py --bin {cpu可执行文件路径}`
- 示例：
  - `./cpu`：`python test.py --bin ./cpu`
  - `python cpu.py`：`python test.py --bin "python cpu.py"`

### 测试文件
- 测试输入：test/目录下的.yo文件
- 期望输出：answer/目录下的.json文件
- 测试覆盖所有Y86-64指令和常见场景

### 测试脚本要求
- 将最终用于测试的命令写入test.sh文件。
- 命令格式应支持重定向输入输出：
  ```
  ./cpu < test/prog1.yo > answer/prog1.json
  python cpu.py < test/prog1.yo > answer/prog1.json
  ```

## 开发与提交要求

### 环境配置
- 可以在非Linux环境下开发。
- 根据所选技术栈自行安装必要环境。

### 代码组织
- 参考文件（cpu.h, cpu.cpp, cpu.py, Makefile）仅供参考，可以删除。
- 提交的代码必须包含能够通过测试的基础实现。
- 有兴趣的同学可以在基础功能完成后进行创新扩展。

### 提交内容
- 完整的模拟器代码。
- test.sh脚本，包含最终测试命令。
- PPT演示文稿。
- 按时提交并完成期末汇报。

## 附加说明

- 所有输出数值（地址、寄存器值、内存值）必须以十进制表示。
- 内存非零值指值为非零的内存位置。
- 程序必须能够处理所有测试用例，包括边界情况和异常情况。
- 鼓励在通过基础测试后进行创新，但必须确保基础代码的完整性。

## CSCI 370: Computer Architecture -> Y86指令集

### Instruction Format

| 指令 | 格式 |
| :--- | :--- |
| `halt` | `0 0` |
| `nop` | `1 0` |
| `rrmovq rA, rB` | `2 0 rA rB` |
| `cmovXX rA, rB` | `2 fn rA rB` |
| `irmovq V, rB` | `3 0 F rB V` |
| `rmmovq rA,D(rB)` | `4 0 rA rB D` |
| `mrmovq D(rB),rA` | `5 0 rA rB D` |
| `addq rA, rB` | `6 0 rA rB` |
| `subq rA, rB` | `6 1 rA rB` |
| `andq rA, rB` | `6 2 rA rB` |
| `xorq rA, rB` | `6 3 rA rB` |
| `jmp Dest` | `7 0 Dest` |
| `jXX Dest` | `7 fn Dest` |
| `call Dest` | `8 0 Dest` |
| `ret` | `9 0` |
| `pushq rA` | `A 0 rA F` |
| `popq rA` | `B 0 rA F` |

#### fn Codes

| 代码 | 条件 |
| :--- | :--- |
| `1` | le (小于等于) |
| `2` | l (小于) |
| `3` | e (等于) |
| `4` | ne (不等于) |
| `5` | ge (大于等于) |
| `6` | g (大于) |

### Registers

| ID | Enc | Usage | 类型 |
| :--- | :--- | :--- | :--- |
| `%rdi` | 7 | arg1 | caller-saved |
| `%rsi` | 6 | arg2 | caller-saved |
| `%rdx` | 2 | arg3 | caller-saved |
| `%rcx` | 1 | arg4 | caller-saved |
| `%r8` | 8 | arg5 | caller-saved |
| `%r9` | 9 | arg6 | caller-saved |
| `%rax` | 0 | return | caller-saved |
| `%r10` | A | general | callee-saved |
| `%r11` | B | general | callee-saved |
| `%rbx` | 3 | general | callee-saved |
| `%r12` | C | general | callee-saved |
| `%r13` | D | general | callee-saved |
| `%r14` | E | general | callee-saved |
| `%rsp` | 4 | stack ptr | callee-saved |
| `%rbp` | 5 | base ptr | callee-saved |
| `F` | F | no reg | - |

### Status Conditions

| 状态码 | 值 | 描述 |
| :--- | :--- | :--- |
| AOK | 1 | Normal |
| HLT | 2 | Halt Encountered |
| ADR | 3 | Bad Address |
| INS | 4 | Invalid Instruction |

### HCL Y86-64 Hardware Registers

| 阶段 | 寄存器 | 描述 |
| :--- | :--- | :--- |
| **Fetch** | `icode,ifun` | Read instruction byte |
| | `rA,rB` | Read register byte |
| | `valC` | Read constant word |
| | `valP` | Compute next PC |
| **Decode** | `valA,srcA` | Read operand A |
| | `valB,srcB` | Read operand B |
| **Execute** | `valE` | Perform ALU operation |
| | `cnd` | Set/Use Condition Code |
| **Memory** | `valM` | Memory Read/Write |
| **Writeback** | `dstE` | Write back ALU result |
| | `dstM` | Write back Mem result |
| **PC Update** | `PC` | Update PC |

---

### Assembly Translation Example

```c
/* find number of elements in null-terminated list */
long len(long* a) {
    long len;
    for (len = 0; a[len]; ++len)
        ;
    return len;
}
```

```asm
len:
    irmovq $1, %r8      # Constant 1
    irmovq $8, %r9      # Constant 8
    irmovq $0, %rax     # len = 0
    mrmovq (%rdi), %rdx # val = *a
    andq %rdx, %rdx     # Test val
    je Done             # If zero, goto Done

Loop:
    addq %r8, %rax      # len++
    addq %r9, %rdi      # a++
    mrmovq (%rdi), %rdx # val = *a
    andq %rdx, %rdx     # Test val
    jne Loop            # If !0, goto Loop

Done:
    ret
```

### Y86-64 Data Example

```asm
.align 8
Array:
    .quad 0x0000000000000001
    .quad 0x0000000000000002
    .quad 0x0000000000000003
    .quad 0x0000000000000004
```