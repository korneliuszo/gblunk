#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "bsp/board.h"
#include "tusb.h"
#include "usb_descriptors.h"
#include <stdio.h>
#include "tusb.h"
#include "hardware/pio.h"
#include "pio/pio_spi.h"
#include "pico/bootrom.h"
#include "hardware/clocks.h"

//--------------------------------------------------------------------+
// MACRO CONSTANT TYPEDEF PROTYPES
//--------------------------------------------------------------------+

//------------- prototypes -------------//

/*------------- MAIN -------------*/

pio_spi_inst_t spi = { .pio = pio0, .sm = 0, .sm_clk = 1 };

#define PIN_SCK 0
#define PIN_SIN 1
#define PIN_SOUT 2

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


void tud_cdc_line_coding_cb(uint8_t itf, cdc_line_coding_t const *p_line_coding) {
	if (p_line_coding->bit_rate == 0)
		return;
	uint64_t bit_rate = p_line_coding->bit_rate;
	if (bit_rate > 500000 / 10)
		bit_rate = 500000 / 10;
	float clker_div = clock_get_hz(clk_sys) / (bit_rate);
	pio_sm_set_clkdiv(spi.pio, spi.sm_clk, clker_div);
}

int main(void) {

	uint master_prog_offs = pio_add_program(spi.pio, &gb_sio_master_program);
	uint clocker_prog_offs = pio_add_program(spi.pio, &gb_sio_clocker_program);
	float clk_div = clock_get_hz(clk_sys) / (500000.0f * 4.0f);
	float clker_div = clock_get_hz(clk_sys) / (10000.0f);
	pio_gb_sio_core_init(spi.pio, spi.sm, master_prog_offs, clk_div, PIN_SCK,
	PIN_SOUT, PIN_SIN);
	pio_gb_sio_clocker_init(spi.pio, spi.sm_clk, clocker_prog_offs,clker_div);
	tusb_init();

	io_rw_8 *rxfifo = (io_rw_8*) &spi.pio->rxf[spi.sm];
	while (1) {
		tud_task(); // tinyusb device task
		while (!pio_sm_is_rx_fifo_empty(spi.pio, spi.sm)) {
				uint8_t rxchr = *rxfifo;
				tud_cdc_write_char(rxchr);
			}
			tud_cdc_write_flush();
		while(tud_cdc_available() && (!pio_sm_is_tx_fifo_full(spi.pio, spi.sm))) {
			uint8_t chr = tud_cdc_read_char();
			io_rw_8 *txfifo = (io_rw_8*) &spi.pio->txf[spi.sm];
			*txfifo = chr;
		}
	}

	return 0;
}
