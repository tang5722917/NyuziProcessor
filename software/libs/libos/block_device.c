// 
// Copyright 2011-2015 Jeff Bush
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// 


#include "block_device.h"

static volatile unsigned int * const REGISTERS = (volatile unsigned int*) 0xffff0000;

static void set_cs(int asserted)
{
	REGISTERS[0x50 / 4] = asserted;
}

static int spi_transfer(int value)
{
	REGISTERS[0x44 / 4] = value & 0xff;
	while ((REGISTERS[0x4c / 4] & 1) == 0)
		;	// Wait for transfer to finish

	return REGISTERS[0x48 / 4];
}

static void wait_not_busy()
{
	while (spi_transfer(0xff) == 0xff)
		;
}

void init_block_device()
{
	set_cs(1);

	spi_transfer(0x56);	// set block length
	spi_transfer((BLOCK_SIZE >> 24) & 0xff);
	spi_transfer((BLOCK_SIZE >> 16) & 0xff);
	spi_transfer((BLOCK_SIZE >> 8) & 0xff);
	spi_transfer(BLOCK_SIZE & 0xff);
	spi_transfer(0x95);	// Checksum (ignored)

	set_cs(0);
}

void read_block_device(unsigned int block_address, void *ptr)
{
	set_cs(1);
	
	spi_transfer(0x57);	// READ block
	spi_transfer((block_address >> 24) & 0xff);
	spi_transfer((block_address >> 16) & 0xff);
	spi_transfer((block_address >> 8) & 0xff);
	spi_transfer(block_address & 0xff);
	spi_transfer(0x95);	// Checksum (ignored)

	wait_not_busy();
	for (int i = 0; i < BLOCK_SIZE; i++)
		((char*) ptr)[i] = spi_transfer(0xff);
	
	spi_transfer(0xff);	// checksum (ignored)
	
	set_cs(0);
}
