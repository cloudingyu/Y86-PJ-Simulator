#include "cpu.h"
#include "json.hpp"
#include <iostream>
#include <string>
#include <sstream>
#include <iomanip>

using json = nlohmann::json;

Simulator::Simulator()
{
    PC = 0;
    memory.resize(MEM_SIZE, 0);
    reg.fill(0);
    stat = Stat::AOK;
}

uint8_t hexToByte(const std::string &hex)
{
    unsigned int val;
    std::stringstream ss;
    ss << std::hex << hex;
    ss >> val;
    return static_cast<uint8_t>(val);
}

void Simulator::loadProgram()
{
    std::string line;
    while (std::getline(std::cin, line))
    {
        size_t addrPos = line.find("0x");
        size_t colonPos = line.find(":");
        size_t pipePos = line.find("|");

        if (addrPos != std::string::npos && colonPos != std::string::npos)
        {
            std::string addrStr = line.substr(addrPos, colonPos - addrPos);
            long long addr = 0;
            std::stringstream ss;
            ss << std::hex << addrStr;
            ss >> addr;

            size_t dataEnd = (pipePos == std::string::npos) ? line.length() : pipePos;
            std::string dataStr = line.substr(colonPos + 1, dataEnd - (colonPos + 1));

            std::string cleanData;
            for (char c : dataStr)
            {
                if (!isspace(c))
                    cleanData += c;
            }

            for (size_t i = 0; i < cleanData.length(); i += 2)
            {
                if (i + 1 < cleanData.length())
                {
                    std::string byteStr = cleanData.substr(i, 2);
                    if (addr < MEM_SIZE)
                    {
                        memory[addr] = hexToByte(byteStr);
                        addr++;
                    }
                }
            }
        }
    }
}

void Simulator::loadBlockToCache(int set_index, unsigned long long tag)
{
    long long block_start_addr = (tag << (BLOCK_BITS + 4)) | (set_index << BLOCK_BITS);

    CacheLine &line = cache[set_index];
    for (int i = 0; i < BLOCK_SIZE; ++i)
    {
        long long mem_addr = block_start_addr + i;
        if (mem_addr < MEM_SIZE)
        {
            line.block[i] = memory[mem_addr];
        }
        else
        {
            line.block[i] = 0;
        }
    }
    line.tag = tag;
    line.valid = true;
}

uint8_t Simulator::readByteCached(long long addr)
{
    unsigned long long set_index = (addr >> BLOCK_BITS) & (CACHE_SETS - 1);
    unsigned long long tag = addr >> (BLOCK_BITS + 4);
    unsigned long long offset = addr & (BLOCK_SIZE - 1);

    CacheLine &line = cache[set_index];

    if (line.valid && line.tag == tag)
    {
        cache_hits++;
        return line.block[offset];
    }
    else
    {
        cache_misses++;
        loadBlockToCache(set_index, tag);
        return line.block[offset];
    }
}

void Simulator::writeByteCached(long long addr, uint8_t val)
{
    memory[addr] = val;

    unsigned long long set_index = (addr >> BLOCK_BITS) & (CACHE_SETS - 1);
    unsigned long long tag = addr >> (BLOCK_BITS + 4);
    unsigned long long offset = addr & (BLOCK_SIZE - 1);

    CacheLine &line = cache[set_index];

    if (line.valid && line.tag == tag)
    {
        cache_hits++;
        line.block[offset] = val;
    }
    else
    {
        cache_misses++;
        loadBlockToCache(set_index, tag);
    }
}

long long Simulator::readLong(long long addr)
{
    if (addr < 0 || addr + 8 > MEM_SIZE)
    {
        stat = Stat::ADR;
        return 0;
    }
    long long val = 0;
    for (int i = 0; i < 8; ++i)
    {
        uint8_t byte = readByteCached(addr + i);
        val |= (long long)byte << (i * 8);
    }
    return val;
}

void Simulator::writeLong(long long addr, long long val)
{
    if (addr < 0 || addr + 8 > MEM_SIZE)
    {
        stat = Stat::ADR;
        return;
    }
    for (int i = 0; i < 8; ++i)
    {
        uint8_t byte = (val >> (i * 8)) & 0xFF;
        writeByteCached(addr + i, byte);
    }
}

void Simulator::fetch()
{
    if (PC < 0 || PC >= MEM_SIZE)
    {
        stat = Stat::ADR;
        return;
    }
    uint8_t byte0 = memory[PC];
    icode = (byte0 >> 4) & 0xF;
    ifun = byte0 & 0xF;
    if (icode > 0xB)
    {
        stat = Stat::INS;
        return;
    }

    valP = PC + 1;
    bool need_regs = (icode == ICode::RRMOVQ || icode == ICode::OPQ ||
                      icode == ICode::PUSHQ || icode == ICode::POPQ ||
                      icode == ICode::IRMOVQ || icode == ICode::RMMOVQ ||
                      icode == ICode::MRMOVQ);
    if (need_regs)
    {
        uint8_t byte1 = memory[valP];
        rA = (byte1 >> 4) & 0xF;
        rB = byte1 & 0xF;
        valP += 1;
    }
    else
    {
        rA = Reg::NONE;
        rB = Reg::NONE;
    }

    bool need_valC = (icode == ICode::IRMOVQ || icode == ICode::RMMOVQ ||
                      icode == ICode::MRMOVQ || icode == ICode::JXX ||
                      icode == ICode::CALL);
    if (need_valC)
    {
        long long val = 0;
        for (int i = 0; i < 8; ++i)
            val |= (long long)memory[valP + i] << (i * 8);
        valC = val;
        valP += 8;
    }
}

void Simulator::decode()
{
    int srcA = Reg::NONE;
    if (icode == ICode::RRMOVQ || icode == ICode::RMMOVQ || icode == ICode::OPQ || icode == ICode::PUSHQ)
        srcA = rA;
    else if (icode == ICode::POPQ || icode == ICode::RET)
        srcA = Reg::RSP;
    valA = (srcA == Reg::NONE) ? 0 : reg[srcA];

    int srcB = Reg::NONE;
    if (icode == ICode::OPQ || icode == ICode::RMMOVQ || icode == ICode::MRMOVQ)
        srcB = rB;
    else if (icode == ICode::PUSHQ || icode == ICode::POPQ || icode == ICode::CALL || icode == ICode::RET)
        srcB = Reg::RSP;
    valB = (srcB == Reg::NONE) ? 0 : reg[srcB];
}

void Simulator::execute()
{
    if (icode == ICode::OPQ)
    {
        long long a = valA, b = valB;
        if (ifun == 0)
            valE = b + a;
        else if (ifun == 1)
            valE = b - a;
        else if (ifun == 2)
            valE = b & a;
        else if (ifun == 3)
            valE = b ^ a;
        zf = (valE == 0);
        sf = (valE < 0);
        if (ifun == 0)
            of = ((a > 0 && b > 0 && valE < 0) || (a < 0 && b < 0 && valE >= 0));
        else if (ifun == 1)
            of = ((b > 0 && a < 0 && valE < 0) || (b < 0 && a > 0 && valE >= 0));
        else
            of = false;
    }
    else if (icode == ICode::IRMOVQ)
        valE = valC;
    else if (icode == ICode::RRMOVQ)
        valE = valA;
    else if (icode == ICode::RMMOVQ || icode == ICode::MRMOVQ)
        valE = valB + valC;
    else if (icode == ICode::PUSHQ || icode == ICode::CALL)
        valE = valB - 8;
    else if (icode == ICode::POPQ || icode == ICode::RET)
        valE = valB + 8;

    if (icode == ICode::JXX || icode == ICode::RRMOVQ)
    {
        switch (ifun)
        {
        case 0:
            cnd = true;
            break;
        case 1:
            cnd = (sf ^ of) || zf;
            break;
        case 2:
            cnd = (sf ^ of);
            break;
        case 3:
            cnd = zf;
            break;
        case 4:
            cnd = !zf;
            break;
        case 5:
            cnd = !(sf ^ of);
            break;
        case 6:
            cnd = !(sf ^ of) && !zf;
            break;
        default:
            cnd = false;
        }
    }
    if (icode == ICode::HALT)
        stat = Stat::HLT;
}

void Simulator::memory_access()
{
    long long addr = 0;
    bool read = false, write = false;
    long long writeVal = 0;

    if (icode == ICode::RMMOVQ || icode == ICode::PUSHQ || icode == ICode::CALL)
    {
        write = true;
        addr = valE;
        if (icode == ICode::CALL)
            writeVal = valP;
        else
            writeVal = valA;
    }
    else if (icode == ICode::MRMOVQ)
    {
        read = true;
        addr = valE;
    }
    else if (icode == ICode::POPQ || icode == ICode::RET)
    {
        read = true;
        addr = valA;
    }

    if (read)
        valM = readLong(addr);
    if (write)
        writeLong(addr, writeVal);
}

void Simulator::write_back()
{
    int dstE = Reg::NONE;
    if (icode == ICode::RRMOVQ && cnd)
        dstE = rB;
    else if (icode == ICode::OPQ || icode == ICode::IRMOVQ)
        dstE = rB;
    else if (icode == ICode::PUSHQ || icode == ICode::POPQ || icode == ICode::CALL || icode == ICode::RET)
        dstE = Reg::RSP;
    if (dstE != Reg::NONE)
        reg[dstE] = valE;

    int dstM = Reg::NONE;
    if (icode == ICode::MRMOVQ || icode == ICode::POPQ)
        dstM = rA;
    if (dstM != Reg::NONE)
        reg[dstM] = valM;
}

void Simulator::pc_update()
{
    if (stat != Stat::AOK)
        return;
    if (icode == ICode::CALL)
        PC = valC;
    else if (icode == ICode::RET)
        PC = valM;
    else if (icode == ICode::JXX)
        PC = cnd ? valC : valP;
    else
        PC = valP;
}

void Simulator::printJsonState(bool isFirst)
{
    json j;
    j["PC"] = PC;
    j["STAT"] = stat;
    j["CC"]["ZF"] = zf ? 1 : 0;
    j["CC"]["SF"] = sf ? 1 : 0;
    j["CC"]["OF"] = of ? 1 : 0;

    if (gui_mode)
    {
        j["CACHE"]["hits"] = cache_hits;
        j["CACHE"]["misses"] = cache_misses;
        long long total = cache_hits + cache_misses;
        j["CACHE"]["total"] = total;
        j["CACHE"]["rate"] = (total > 0) ? (double)cache_hits / total * 100.0 : 0.0;
    }

    const char *rNames[] = {"rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi", "r8", "r9", "r10", "r11", "r12", "r13", "r14"};
    for (int i = 0; i < 15; ++i)
        j["REG"][rNames[i]] = reg[i];

    for (int i = 0; i < MEM_SIZE; i += 8)
    {
        long long val = 0;
        for (int b = 0; b < 8; ++b)
            val |= (long long)memory[i + b] << (b * 8);
        if (val != 0)
            j["MEM"][std::to_string(i)] = val;
    }

    if (!isFirst)
        std::cout << ",";
    std::cout << j << std::endl;
}

void Simulator::run()
{
    std::cout << "[" << std::endl;
    bool isFirst = true;
    while (stat == Stat::AOK)
    {
        fetch();
        if (stat != Stat::AOK)
        {
            printJsonState(isFirst);
            break;
        }
        decode();
        execute();
        memory_access();
        write_back();
        pc_update();
        printJsonState(isFirst);
        isFirst = false;
        if (PC < 0 || PC >= MEM_SIZE)
            break;
    }
    std::cout << "]" << std::endl;
}

int main(int argc, char *argv[])
{
    Simulator sim;

    if (argc > 1 && std::string(argv[1]) == "-v")
    {
        sim.setGuiMode(true);
    }

    sim.loadProgram();
    sim.run();

    return 0;
}