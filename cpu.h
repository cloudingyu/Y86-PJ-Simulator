#ifndef CPU_H
#define CPU_H

#include <vector>
#include <array>
#include <cstdint>
#include <string>

// 定义内存大小 (64KB，足够容纳所有测试用例)
const int MEM_SIZE = 0x10000;

// Y86 指令编码
namespace ICode {
    const int HALT   = 0x0;
    const int NOP    = 0x1;
    const int RRMOVQ = 0x2; // 包含 CMOVXX
    const int IRMOVQ = 0x3;
    const int RMMOVQ = 0x4;
    const int MRMOVQ = 0x5;
    const int OPQ    = 0x6;
    const int JXX    = 0x7;
    const int CALL   = 0x8;
    const int RET    = 0x9;
    const int PUSHQ  = 0xA;
    const int POPQ   = 0xB;
}

// 寄存器 ID
namespace Reg {
    const int RAX = 0;
    const int RCX = 1;
    const int RDX = 2;
    const int RBX = 3;
    const int RSP = 4;
    const int RBP = 5;
    const int RSI = 6;
    const int RDI = 7;
    const int R8  = 8;
    const int R9  = 9;
    const int R10 = 10;
    const int R11 = 11;
    const int R12 = 12;
    const int R13 = 13;
    const int R14 = 14;
    const int NONE = 0xF;
}

// 状态码
namespace Stat {
    const int AOK = 1;
    const int HLT = 2;
    const int ADR = 3;
    const int INS = 4;
}

class Simulator
{
public:
    Simulator();
    void loadProgram();
    void run();

private:
    // --- 硬件状态 ---
    long long PC = 0;
    std::vector<unsigned char> memory;
    std::array<long long, 15> reg;
    
    // 条件码
    bool zf = true;
    bool sf = false;
    bool of = false;

    // 运行状态
    int stat = Stat::AOK;

    // --- 流水线/中间变量 ---
    int icode = 0;
    int ifun = 0;
    int rA = Reg::NONE;
    int rB = Reg::NONE;
    long long valC = 0; // 立即数
    long long valP = 0; // 下一条指令地址 (PC + 长度)
    
    long long valA = 0; // 寄存器 A 的值
    long long valB = 0; // 寄存器 B 的值
    long long valE = 0; // ALU 计算结果 / 有效地址
    long long valM = 0; // 内存读取结果

    bool cnd = false;   // 跳转/传送条件是否满足

    // --- 阶段函数 ---
    void fetch();
    void decode();
    void execute();
    void memory_access();
    void write_back();
    void pc_update();

    // --- 辅助工具 ---
    long long readLong(long long addr);
    void writeLong(long long addr, long long val);
    void printJsonState(bool isFirst);
};

#endif