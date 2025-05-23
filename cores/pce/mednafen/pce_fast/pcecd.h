#ifndef __PCE_CDROM_H
#define __PCE_CDROM_H

#include "../include/blip/Blip_Buffer.h"

typedef struct
{
	float CDDA_Volume;	// Max 2.000...
	float ADPCM_Volume;	// Max 2.000...

	unsigned int CD_Speed;

	bool ADPCM_LPF;
} PCECD_Settings;

void PCECD_Run(uint32 in_timestamp);
void PCECD_ResetTS(void);

bool PCECD_Init(const PCECD_Settings *settings, void (*irqcb)(bool), double master_clock, unsigned int ocm, Blip_Buffer *soundbuf_l, Blip_Buffer *soundbuf_r) MDFN_COLD;
bool PCECD_SetSettings(const PCECD_Settings *settings) MDFN_COLD;
void PCECD_Close(void) MDFN_COLD;
void PCECD_Power(uint32 timestamp) MDFN_COLD;


uint8 PCECD_Read(uint32 timestamp, uint32);
void PCECD_Write(uint32 timestamp, uint32, uint8 data);

bool PCECD_IsBRAMEnabled(void);

int PCECD_StateAction(StateMem *sm, int load, int data_only);

#endif
