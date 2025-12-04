#ifndef CPU_H
#define CPU_H

#include <vector>
#include <array>
#include <cstdint>
#include <string>

const int MEM_SIZE = 0x10000;

namespace ICode {
    const int HALT   = 0x0;
    const int NOP    = 0x1;
    const int RRMOVQ = 0x2;
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

namespace Reg {
    const int RAX = 0x0;
    const int RCX = 0x1;
    const int RDX = 0x2;
    const int RBX = 0x3;
    const int RSP = 0x4;
    const int RBP = 0x5;
    const int RSI = 0x6;
    const int RDI = 0x7;
    const int R8  = 0x8;
    const int R9  = 0x9;
    const int R10 = 0xA;
    const int R11 = 0xB;
    const int R12 = 0xC;
    const int R13 = 0xD;
    const int R14 = 0xE;
    const int NONE = 0xF;
}

namespace Stat {
    const int AOK = 1;
    const int HLT = 2;
    const int ADR = 3;
    const int INS = 4;
}

struct CacheLine {
    bool valid = false;
    unsigned long long tag = 0;
    uint8_t block[32]; 
};

class Simulator
{
public:
    Simulator();
    void loadProgram();
    void run();
    
    void setGuiMode(bool mode) { gui_mode = mode; }

    long long cache_hits = 0;
    long long cache_misses = 0;

private:
    long long PC = 0;
    
    std::vector<uint8_t> memory;
    std::array<long long, 15> reg;
    
    bool zf = true;
    bool sf = false;
    bool of = false;

    int stat = Stat::AOK;
    bool gui_mode = false;

    static const int CACHE_SETS = 16;
    static const int BLOCK_SIZE = 32;
    static const int BLOCK_BITS = 5; 
    std::array<CacheLine, CACHE_SETS> cache;

    int icode = 0;
    int ifun = 0;
    int rA = Reg::NONE;
    int rB = Reg::NONE;
    long long valC = 0;
    long long valP = 0;
    
    long long valA = 0;
    long long valB = 0;
    long long valE = 0;
    long long valM = 0;

    bool cnd = false;

    void fetch();
    void decode();
    void execute();
    void memory_access();
    void write_back();
    void pc_update();

    long long readLong(long long addr);
    void writeLong(long long addr, long long val);
    void printJsonState(bool isFirst);
    
    uint8_t readByteCached(long long addr);
    void writeByteCached(long long addr, uint8_t val);
    void loadBlockToCache(int set_index, unsigned long long tag);
};

#endif