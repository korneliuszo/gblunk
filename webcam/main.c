#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "bsp/board.h"
#include "tusb.h"
#include "usb_descriptors.h"
#include <stdio.h>
#include "hardware/pio.h"
#include "pio/pio_spi.h"
#include "pico/bootrom.h"
#include "hardware/clocks.h"
#include "hardware/sync.h"
#include "pico/stdlib.h"

//--------------------------------------------------------------------+
// MACRO CONSTANT TYPEDEF PROTYPES
//--------------------------------------------------------------------+

//------------- prototypes -------------//
enum  {
  BLINK_NOT_MOUNTED = 250,
  BLINK_MOUNTED = 1000,
  BLINK_SUSPENDED = 2500,
};

static uint32_t blink_interval_ms = BLINK_NOT_MOUNTED;

/*------------- MAIN -------------*/

pio_spi_inst_t spi = { .pio = pio0, .sm = 0, .sm_clk = 1 };

#define PIN_SCK 0
#define PIN_SIN 1
#define PIN_SOUT 2

static uint8_t regs[0x36];
static bool regs_updated;

bool tud_vendor_control_xfer_cb(uint8_t rhport, uint8_t stage,
		tusb_control_request_t const *request) {
	// nothing to with DATA & ACK stage
	if (stage != CONTROL_STAGE_SETUP)
		return true;

	switch (request->bmRequestType_bit.type) {
	case TUSB_REQ_TYPE_VENDOR:
		switch (request->bRequest) {
		case 0x00:
			reset_usb_boot(0, 0);
			return tud_control_xfer(rhport, request, NULL, 0);

		case 0x01:
		{
			bool ret = tud_control_xfer(rhport, request, regs, 0x36);
			regs[0]&=0xFE;
			regs_updated = true;
			return ret;
		}
		default:
			break;
		}
		break;

	default:
		break;
	}

	// stall unknown request
	return false;
}

void video_task(void);
void led_blinking_task(void);

int main(void) {
	board_init();

	uint master_prog_offs = pio_add_program(spi.pio, &gb_sio_master_program);
	uint clocker_prog_offs = pio_add_program(spi.pio, &gb_sio_clocker_program);
	float clk_div = clock_get_hz(clk_sys) / (500000.0f * 4.0f);
	float clker_div = clock_get_hz(clk_sys) / (30000.0f);
	pio_gb_sio_core_init(spi.pio, spi.sm, master_prog_offs, clk_div, PIN_SCK,
	PIN_SOUT, PIN_SIN);
	pio_gb_sio_clocker_init(spi.pio, spi.sm_clk, clocker_prog_offs,clker_div);
	tud_init(BOARD_DEVICE_RHPORT_NUM);

	while(1)
	{
	    tud_task(); // tinyusb device task
	    led_blinking_task();

	    video_task();
	}

	return 0;
}

void readgb(uint16_t addr, uint8_t * buff,int len)
{
	while(len)
	{
		int plen = MIN(len,256);
		uint8_t header[5] = {'R',plen,addr>>8,addr,0};
		pio_spi_write8_blocking(&spi,header,5);
		pio_spi_read8_blocking(&spi,buff,plen);
		buff+=plen;
		len-=plen;
		addr+=plen;
	}
}

void writegb(uint16_t addr, const uint8_t * buff,int len)
{
	int i=0;
	while(len)
	{
		int plen = MIN(len,256);
		uint8_t header[4] = {'W',plen,addr>>8,addr};
		pio_spi_write8_blocking(&spi,header,4);
		pio_spi_write8_blocking(&spi,&buff[i],plen);
		i+=plen;
		len-=plen;
		addr+=plen;
	}
}

static volatile int tx_busy = 0;

static uint8_t frame_buffer[FRAME_WIDTH * FRAME_HEIGHT * 16 / 8];
static uint8_t gbimage[(112*128)/4];

#if 1
static void fill_color_bar(uint8_t *buffer)
{
  /* EBU color bars
   * See also https://stackoverflow.com/questions/6939422 */
  static uint8_t const pal[4][2] = {
    /*  Y,   U/V */
    { 255, 0x80},
    { 127, 0x80},
    { 63, 0x80},
    { 0, 0x80},
  };
  uint8_t bank=0;
  writegb(0x4000, &bank,1);

  readgb(0xA100,gbimage,(112*128)/4);
  for(int y=0;y<112;y++)
	  for(int xt=0;xt<128;xt+=8)
	  {
		  int ytile = y/8*8;
          uint8_t lb=gbimage[ytile*32+(y&0x7)*2+2*xt];
          uint8_t hb=gbimage[ytile*32+(y&0x7)*2+2*xt+1];
          for(int x=0;x<8;x++)
          {
        	  int mux = (1<<(7-x));
        	  int palidx = !!(lb&mux) | ((!!(hb&mux))<<1);
        	  int px = FRAME_WIDTH * 2 * y + (x+xt)*2;
        	  buffer[px] = pal[palidx][0];
        	  buffer[px+1] = pal[palidx][1];
          }
	  }
}
#else
static void fill_color_bar(uint8_t *buffer)
{
  /* EBU color bars
   * See also https://stackoverflow.com/questions/6939422 */
  static uint8_t const bar_color[8][4] = {
    /*  Y,   U,   Y,   V */
    { 235, 128, 235, 128}, /* 100% White */
    { 219,  16, 219, 138}, /* Yellow */
    { 188, 154, 188,  16}, /* Cyan */
    { 173,  42, 173,  26}, /* Green */
    {  78, 214,  78, 230}, /* Magenta */
    {  63, 102,  63, 240}, /* Red */
    {  32, 240,  32, 118}, /* Blue */
    {  16, 128,  16, 128}, /* Black */
  };
  uint8_t *p;

  /* Generate the 1st line */
  uint8_t *end = &buffer[FRAME_WIDTH * 2];
  unsigned idx = (FRAME_WIDTH / 2 - 1) - (0 % (FRAME_WIDTH / 2));
  p = &buffer[idx * 4];
  for (unsigned i = 0; i < 8; ++i) {
    for (int j = 0; j < FRAME_WIDTH / (2 * 8); ++j) {
      memcpy(p, &bar_color[i], 4);
      p += 4;
      if (end <= p) {
        p = buffer;
      }
    }
  }
  /* Duplicate the 1st line to the others */
  p = &buffer[FRAME_WIDTH * 2];
  for (unsigned i = 1; i < FRAME_HEIGHT; ++i) {
    memcpy(p, buffer, FRAME_WIDTH * 2);
    p += FRAME_WIDTH * 2;
  }
}
#endif
void video_task(void)
{
  if (!tud_video_n_streaming(0, 0)) {
    tx_busy = 0;
    return;
  }

  if (tx_busy) return;

  {
	  uint8_t bank=0x10;
	  writegb(0x4000, &bank,1);
	  uint8_t a0000_reg;
	  readgb(0xA000,&a0000_reg,1);
	  if(a0000_reg & 0x01) return;
  }
  fill_color_bar(frame_buffer);
  {
	  uint8_t bank=0x10;
	  writegb(0x4000, &bank,1);
	  if(regs_updated)
	  {
		  writegb(0xA000,regs,0x36);
		  regs_updated = false;
	  }
	  uint8_t a0000_reg = regs[0]| 0x01;
	  writegb(0xA000,&a0000_reg,1);
  }
  tx_busy++;
  tud_video_n_frame_xfer(0, 0, (void*)frame_buffer, FRAME_WIDTH * FRAME_HEIGHT * 16/8);
}

void tud_video_frame_xfer_complete_cb(uint_fast8_t ctl_idx, uint_fast8_t stm_idx)
{
  (void)ctl_idx; (void)stm_idx;
  tx_busy--;
  if(tx_busy<0)
  {
	  __breakpoint();
	  while(1);
  }
  /* flip buffer */
}

int tud_video_commit_cb(uint_fast8_t ctl_idx, uint_fast8_t stm_idx,
			video_probe_and_commit_control_t const *parameters)
{
  (void)ctl_idx; (void)stm_idx;
  return VIDEO_ERROR_NONE;
}
//--------------------------------------------------------------------+
// BLINKING TASK
//--------------------------------------------------------------------+
void led_blinking_task(void)
{
  static uint32_t start_ms = 0;
  static bool led_state = false;

  // Blink every interval ms
  if ( board_millis() - start_ms < blink_interval_ms) return; // not enough time
  start_ms += blink_interval_ms;

  board_led_write(led_state);
  led_state = 1 - led_state; // toggle
}

