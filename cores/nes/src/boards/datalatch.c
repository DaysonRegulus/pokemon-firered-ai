/* FCE Ultra - NES/Famicom Emulator
 *
 * Copyright notice for this file:
 *  Copyright (C) 2002 Xodnizel
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 */

#include "mapinc.h"
#include "../ines.h"

static uint8 latche, latcheinit, bus_conflict;
static uint16 addrreg0, addrreg1;
static uint8 *WRAM = NULL;
static uint32 WRAMSIZE;
static void (*WSync)(void);

static DECLFW(LatchWrite) {
//	FCEU_printf("bs %04x %02x\n",A,V);
	if (bus_conflict)
		latche = V & CartBR(A);
	else
		latche = V;
	WSync();
}

static void LatchPower(void) {
	latche = latcheinit;
	WSync();
	if (WRAM) {
		SetReadHandler(0x6000, 0xFFFF, CartBR);
		SetWriteHandler(0x6000, 0x7FFF, CartBW);
		FCEU_CheatAddRAM(WRAMSIZE >> 10, 0x6000, WRAM);
	} else {
		SetReadHandler(0x8000, 0xFFFF, CartBR);
	}
	SetWriteHandler(addrreg0, addrreg1, LatchWrite);
}

static void LatchClose(void) {
	if (WRAM)
		FCEU_gfree(WRAM);
	WRAM = NULL;
}

static void StateRestore(int version) {
	WSync();
}

static void Latch_Init(CartInfo *info, void (*proc)(void), uint8 init, uint16 adr0, uint16 adr1, uint8 wram, uint8 busc) {
	bus_conflict = busc;
	latcheinit = init;
	addrreg0 = adr0;
	addrreg1 = adr1;
	WSync = proc;
	info->Power = LatchPower;
	info->Close = LatchClose;
	GameStateRestore = StateRestore;
	if (wram) {
		WRAMSIZE = 8192;
		WRAM = (uint8*)FCEU_gmalloc(WRAMSIZE);
		SetupCartPRGMapping(0x10, WRAM, WRAMSIZE, 1);
		if (info->battery) {
			info->SaveGame[0] = WRAM;
			info->SaveGameLen[0] = WRAMSIZE;
		}
		AddExState(WRAM, WRAMSIZE, 0, "WRAM");
	}
	AddExState(&latche, 1, 0, "LATC");
	AddExState(&bus_conflict, 1, 0, "BUSC");
}

//------------------ Map 0 ---------------------------

#ifdef DEBUG_MAPPER
static DECLFW(NROMWrite) {
	FCEU_printf("bs %04x %02x\n", A, V);
	CartBW(A, V);
}
#endif

static void NROMPower(void) {
	setprg8r(0x10, 0x6000, 0);	// Famili BASIC (v3.0) need it (uses only 4KB), FP-BASIC uses 8KB
	setprg16(0x8000, 0);
	setprg16(0xC000, ~0);
	setchr8(0);

	SetReadHandler(0x6000, 0x7FFF, CartBR);
	SetWriteHandler(0x6000, 0x7FFF, CartBW);
	SetReadHandler(0x8000, 0xFFFF, CartBR);

	FCEU_CheatAddRAM(WRAMSIZE >> 10, 0x6000, WRAM);

	#ifdef DEBUG_MAPPER
	SetWriteHandler(0x4020, 0xFFFF, NROMWrite);
	#endif
}

void NROM_Init(CartInfo *info) {
	info->Power = NROMPower;
	info->Close = LatchClose;

	WRAMSIZE = 8192;
	WRAM = (uint8*)FCEU_gmalloc(WRAMSIZE);
	SetupCartPRGMapping(0x10, WRAM, WRAMSIZE, 1);
	if (info->battery) {
		info->SaveGame[0] = WRAM;
		info->SaveGameLen[0] = WRAMSIZE;
	}
	AddExState(WRAM, WRAMSIZE, 0, "WRAM");
}

//------------------ Map 2 ---------------------------

static void UNROMSync(void) {
//	static uint32 mirror_in_use = 0;
//	if (PRGsize[0] <= 128 * 1024) {
//		setprg16(0x8000, latche & 0x7);
//		if ((latche & 0xF8) == 0x08) mirror_in_use = 1;
//		if (mirror_in_use)
//			setmirror(((latche >> 3) & 1) ^ 1);	// Higway Star Hacked mapper to be redefined to another mapper
//	} else
	setprg16(0x8000, latche);
	setprg16(0xc000, ~0);
	setchr8(0);
}

void UNROM_Init(CartInfo *info) {
	Latch_Init(info, UNROMSync, 0, 0x8000, 0xFFFF, 0, 1);
}

//------------------ Map 3 ---------------------------

static void CNROMSync(void) {
	setchr8(latche);
	setprg32(0x8000, 0);
	setprg8r(0x10, 0x6000, 0);	// Hayauchy IGO uses 2Kb or RAM
}

void CNROM_Init(CartInfo *info) {
	//TODO: move these to extended database when implemented.
	int _busc, x;
	uint64 partialmd5 = 0;
	_busc = 1;
	for (x = 0; x < 8; x++)
		partialmd5 |= (uint64)info->MD5[15 - x] << (x * 8);
	if (partialmd5 == 0x117181328eb1ad23LL) //75 Bingo (Sachen-English) [U].unf
		_busc = 0;
	else
		switch (info->CRC32) {
		case 0xf283cf58: // Colorful Dragon (Asia) (PAL) (Unl).nes
		case 0x2915faf0: // Incantation (Asia) (Unl).nes
		case 0xebd0644d: // Dao Shuai (Asia) (Unl).nes
		case 0x8f154a0d: // Pu Ke Jing Ling (China) (Unl).nes
		case 0xd04a40e6: // Bingo 75 (Asia) (Unl).nes
			_busc = 0;
			break;
	}
	Latch_Init(info, CNROMSync, 0, 0x8000, 0xFFFF, 1, _busc);
}

//------------------ Map 7 ---------------------------

static void ANROMSync() {
	setprg32(0x8000, latche & 0xF);
	setmirror(MI_0 + ((latche >> 4) & 1));
	setchr8(0);
}

void ANROM_Init(CartInfo *info) {
	Latch_Init(info, ANROMSync, 0, 0x4020, 0xFFFF, 0, 0);
}

//------------------ Map 8 ---------------------------

static void M8Sync() {
	setprg16(0x8000, latche >> 3);
	setprg16(0xc000, 1);
	setchr8(latche & 3);
}

void Mapper8_Init(CartInfo *info) {
	Latch_Init(info, M8Sync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 11 ---------------------------

static void M11Sync(void) {
	setprg32(0x8000, latche & 0xF);
	setchr8(latche >> 4);
}

void Mapper11_Init(CartInfo *info) {
	Latch_Init(info, M11Sync, 0, 0x8000, 0xFFFF, 0, 0);
}

void Mapper144_Init(CartInfo *info) {
	Latch_Init(info, M11Sync, 0, 0x8001, 0xFFFF, 0, 0);
}

//------------------ Map 13 ---------------------------

static void CPROMSync(void) {
	setchr4(0x0000, 0);
	setchr4(0x1000, latche & 3);
	setprg32(0x8000, 0);
}

void CPROM_Init(CartInfo *info) {
	Latch_Init(info, CPROMSync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 38 ---------------------------

static void M38Sync(void) {
	setprg32(0x8000, latche & 3);
	setchr8(latche >> 2);
}

void Mapper38_Init(CartInfo *info) {
	Latch_Init(info, M38Sync, 0, 0x7000, 0x7FFF, 0, 0);
}

//------------------ Map 66 ---------------------------

static void MHROMSync(void) {
	setprg32(0x8000, latche >> 4);
	setchr8(latche & 0xF);
}

void MHROM_Init(CartInfo *info) {
	Latch_Init(info, MHROMSync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 70 ---------------------------

static void M70Sync() {
	setprg16(0x8000, latche >> 4);
	setprg16(0xc000, ~0);
	setchr8(latche & 0xf);
}

void Mapper70_Init(CartInfo *info) {
	Latch_Init(info, M70Sync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 78 ---------------------------
/* Should be two separate emulation functions for this "mapper".  Sigh.  URGE TO KILL RISING. */
static void M78Sync() {
	setprg16(0x8000, (latche & 7));
	setprg16(0xc000, ~0);
	setchr8(latche >> 4);
	setmirror(MI_0 + ((latche >> 3) & 1));
}

void Mapper78_Init(CartInfo *info) {
	Latch_Init(info, M78Sync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 86 ---------------------------

static void M86Sync(void) {
	setprg32(0x8000, (latche >> 4) & 3);
	setchr8((latche & 3) | ((latche >> 4) & 4));
}

void Mapper86_Init(CartInfo *info) {
	Latch_Init(info, M86Sync, ~0, 0x6000, 0x6FFF, 0, 0);
}

//------------------ Map 87 ---------------------------

static void M87Sync(void) {
	setprg32(0x8000, 0);
	setchr8(((latche >> 1) & 1) | ((latche << 1) & 2));
}

void Mapper87_Init(CartInfo *info) {
	Latch_Init(info, M87Sync, ~0, 0x6000, 0xFFFF, 0, 0);
}

//------------------ Map 89 ---------------------------

static void M89Sync(void) {
	setprg16(0x8000, (latche >> 4) & 7);
	setprg16(0xc000, ~0);
	setchr8((latche & 7) | ((latche >> 4) & 8));
	setmirror(MI_0 + ((latche >> 3) & 1));
}

void Mapper89_Init(CartInfo *info) {
	Latch_Init(info, M89Sync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 93 ---------------------------

static void SSUNROMSync(void) {
	setprg16(0x8000, latche >> 4);
	setprg16(0xc000, ~0);
	setchr8(0);
}

void SUNSOFT_UNROM_Init(CartInfo *info) {
	Latch_Init(info, SSUNROMSync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 94 ---------------------------

static void M94Sync(void) {
	setprg16(0x8000, latche >> 2);
	setprg16(0xc000, ~0);
	setchr8(0);
}

void Mapper94_Init(CartInfo *info) {
	Latch_Init(info, M94Sync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 97 ---------------------------

static void M97Sync(void) {
	setchr8(0);
	setprg16(0x8000, ~0);
	setprg16(0xc000, latche & 15);
	switch (latche >> 6) {
	case 0: break;
	case 1: setmirror(MI_H); break;
	case 2: setmirror(MI_V); break;
	case 3: break;
	}
	setchr8(((latche >> 1) & 1) | ((latche << 1) & 2));
}

void Mapper97_Init(CartInfo *info) {
	Latch_Init(info, M97Sync, ~0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 101 ---------------------------

static void M101Sync(void) {
	setprg32(0x8000, 0);
	setchr8(latche);
}

void Mapper101_Init(CartInfo *info) {
	Latch_Init(info, M101Sync, ~0, 0x6000, 0x7FFF, 0, 0);
}

//------------------ Map 107 ---------------------------

static void M107Sync(void) {
	setprg32(0x8000, (latche >> 1) & 3);
	setchr8(latche & 7);
}

void Mapper107_Init(CartInfo *info) {
	Latch_Init(info, M107Sync, ~0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 113 ---------------------------

static void M113Sync(void) {
	setprg32(0x8000, (latche >> 3) & 7);
	setchr8(((latche >> 3) & 8) | (latche & 7));
//	setmirror(latche>>7); // only for HES 6in1
}

void Mapper113_Init(CartInfo *info) {
	Latch_Init(info, M113Sync, 0, 0x4100, 0x7FFF, 0, 0);
}

//------------------ Map 140 ---------------------------

void Mapper140_Init(CartInfo *info) {
	Latch_Init(info, MHROMSync, 0, 0x6000, 0x7FFF, 0, 0);
}

//------------------ Map 152 ---------------------------

static void M152Sync() {
	setprg16(0x8000, (latche >> 4) & 7);
	setprg16(0xc000, ~0);
	setchr8(latche & 0xf);
	setmirror(MI_0 + ((latche >> 7) & 1));	/* Saint Seiya...hmm. */
}

void Mapper152_Init(CartInfo *info) {
	Latch_Init(info, M152Sync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 180 ---------------------------

static void M180Sync(void) {
	setprg16(0x8000, 0);
	setprg16(0xc000, latche);
	setchr8(0);
}

void Mapper180_Init(CartInfo *info) {
	Latch_Init(info, M180Sync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 184 ---------------------------

static void M184Sync(void) {
	setchr4(0x0000, latche);
	setchr4(0x1000, latche >> 4);
	setprg32(0x8000, 0);
}

void Mapper184_Init(CartInfo *info) {
	Latch_Init(info, M184Sync, 0, 0x6000, 0x7FFF, 0, 0);
}

//------------------ Map 203 ---------------------------

static void M203Sync(void) {
	setprg16(0x8000, (latche >> 2) & 3);
	setprg16(0xC000, (latche >> 2) & 3);
	setchr8(latche & 3);
}

void Mapper203_Init(CartInfo *info) {
	Latch_Init(info, M203Sync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ Map 240 ---------------------------

static void M240Sync(void) {
	setprg8r(0x10, 0x6000, 0);
	setprg32(0x8000, latche >> 4);
	setchr8(latche & 0xF);
}

void Mapper240_Init(CartInfo *info) {
	Latch_Init(info, M240Sync, 0, 0x4020, 0x5FFF, 1, 0);
}

//------------------ Map 241 ---------------------------
// Mapper 7 mostly, but with SRAM or maybe prot circuit
// figure out, which games do need 5xxx area reading

static void M241Sync(void) {
	setchr8(0);
	setprg8r(0x10, 0x6000, 0);
	if (latche & 0x80)
		setprg32(0x8000, latche | 8);	// no 241 actually, but why not afterall?
	else
		setprg32(0x8000, latche);
}

void Mapper241_Init(CartInfo *info) {
	Latch_Init(info, M241Sync, 0, 0x8000, 0xFFFF, 1, 0);
}

//------------------ A65AS ---------------------------

// actually, there is two cart in one... First have extra mirroring
// mode (one screen) and 32K bankswitching, second one have only
// 16 bankswitching mode and normal mirroring... But there is no any
// correlations between modes and they can be used in one mapper code.

static void BMCA65ASSync(void) {
	if (latche & 0x40)
		setprg32(0x8000, (latche >> 1) & 0x0F);
	else {
		setprg16(0x8000, ((latche & 0x30) >> 1) | (latche & 7));
		setprg16(0xC000, ((latche & 0x30) >> 1) | 7);
	}
	setchr8(0);
	if (latche & 0x80)
		setmirror(MI_0 + (((latche >> 5) & 1)));
	else
		setmirror(((latche >> 3) & 1) ^ 1);
}

void BMCA65AS_Init(CartInfo *info) {
	Latch_Init(info, BMCA65ASSync, 0, 0x8000, 0xFFFF, 0, 0);
}

//------------------ BMC-11160 ---------------------------
// Simple BMC discrete mapper by TXC

static void BMC11160Sync(void) {
	uint32 bank = (latche >> 4) & 7;
	setprg32(0x8000, bank);
	setchr8((bank << 2) | (latche & 3));
	setmirror((latche >> 7) & 1);
}

void BMC11160_Init(CartInfo *info) {
	Latch_Init(info, BMC11160Sync, 0, 0x8000, 0xFFFF, 0, 0);
}
