
#include "osd.h"

t_config config;

void set_config_defaults(void)
{
  int i;

  /* sound options */
  config.psg_preamp     = 150;
  config.fm_preamp      = 100;
  config.hq_fm          = 0;
  config.hq_psg         = 0;
  config.filter         = 1;
  config.low_freq       = 200;
  config.high_freq      = 8000;
  config.lg             = 1.0;
  config.mg             = 1.0;
  config.hg             = 1.0;
  config.lp_range       = 0x9999; /* 0.6 in 16.16 fixed point */
  config.dac_bits       = 14;
  config.ym2413         = 2; /* = AUTO (0 = always OFF, 1 = always ON) */
  config.mono           = 0;

  /* system options */
  config.system         = 0; /* = AUTO (or SYSTEM_SG, SYSTEM_MARKIII, SYSTEM_SMS, SYSTEM_SMS2, SYSTEM_GG, SYSTEM_MD) */
  config.region_detect  = 0; /* = AUTO (1 = USA, 2 = EUROPE, 3 = JAPAN/NTSC, 4 = JAPAN/PAL) */
  config.vdp_mode       = 0; /* = AUTO (1 = NTSC, 2 = PAL) */
  config.master_clock   = 0; /* = AUTO (1 = NTSC, 2 = PAL) */
  config.force_dtack    = 0;
  config.addr_error     = 1;
  config.bios           = 0;
  config.lock_on        = 0; /* = OFF (can be TYPE_SK, TYPE_GG & TYPE_AR) */
  config.ntsc           = 0;
  config.lcd            = 0; /* 0.8 fixed point */

  /* display options */
  config.overscan = 0;       /* 3 = all borders (0 = no borders , 1 = vertical borders only, 2 = horizontal borders only) */
  config.gg_extra = 0;       /* 1 = show extended Game Gear screen (256x192) */
  config.render   = 0;       /* 1 = double resolution output (only when interlaced mode 2 is enabled) */

  /* controllers options */
  input.system[0]       = SYSTEM_GAMEPAD;
  input.system[1]       = SYSTEM_GAMEPAD;
  config.gun_cursor[0]  = 1;
  config.gun_cursor[1]  = 1;
  config.invert_mouse   = 0;
  for (i=0;i<MAX_INPUTS;i++)
  {
    /* autodetected control pad type */
    config.input[i].padtype = DEVICE_PAD2B | DEVICE_PAD3B | DEVICE_PAD6B;
  }
}
