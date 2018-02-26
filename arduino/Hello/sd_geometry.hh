/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 *
 * Borrowed heavily from SdFat's examples:
 *   Copyright (c) 2011..2017 Bill Greiman
 *   https://github.com/greiman/SdFat
 */

/* Included directly by sd_path.cpp
 */

class SD_Geometry {
private:
  uint32_t cardSizeBlocks;    // Card size
  uint32_t cardCapacityMB;

  uint32_t sectorsPerTrack;   // Fake geometry
  uint32_t numberOfHeads;

  uint32_t sectorsPerCluster; // FAT information
  uint16_t reservedSectors;
  uint32_t fatStart;
  uint32_t fatSize;
  uint32_t dataStart;

  uint32_t relSector;         // MBR information
  uint32_t partSize;
  uint8_t  partType;

  bool     m_bFAT32;
  bool     m_bValid;

  cache_t m_cache;            // cache for SD block

public:
  bool valid () {
    return m_bValid;
  }

private:
  // return cylinder number for a logical block number
  uint16_t cylinder (uint32_t lbn) {
    return lbn / (numberOfHeads * sectorsPerTrack);
  }

  // return head number for a logical block number
  uint8_t head (uint32_t lbn) {
    return (lbn % (numberOfHeads * sectorsPerTrack)) / sectorsPerTrack;
  }

  // return sector number for a logical block number
  uint8_t sector (uint32_t lbn) {
    return (lbn % sectorsPerTrack) + 1;
  }

  // generate serial number from card size and micros since boot
  uint32_t generate_serial_number () {
    return (cardSizeBlocks << 8) + micros ();
  }

  void fake_geometry () { // set fake disk geometry
    sectorsPerTrack = cardCapacityMB <= 256 ? 32 : 63;

    if (cardCapacityMB <= 16) {
      numberOfHeads = 2;
    } else if (cardCapacityMB <= 32) {
      numberOfHeads = 4;
    } else if (cardCapacityMB <= 128) {
      numberOfHeads = 8;
    } else if (cardCapacityMB <= 504) {
      numberOfHeads = 16;
    } else if (cardCapacityMB <= 1008) {
      numberOfHeads = 32;
    } else if (cardCapacityMB <= 2016) {
      numberOfHeads = 64;
    } else if (cardCapacityMB <= 4032) {
      numberOfHeads = 128;
    } else {
      numberOfHeads = 255;
    }
  }

  void fat_parameters () {
    if (cardCapacityMB <= 6) { // oops, too small
      sectorsPerCluster = 0;
      m_bValid = false;
      return;
    }

    if (cardCapacityMB <= 16) {
      sectorsPerCluster = 2;
    } else if (cardCapacityMB <= 32) {
      sectorsPerCluster = 4;
    } else if (cardCapacityMB <= 64) {
      sectorsPerCluster = 8;
    } else if (cardCapacityMB <= 128) {
      sectorsPerCluster = 16;
    } else if (cardCapacityMB <= 1024) {
      sectorsPerCluster = 32;
    } else if (cardCapacityMB <= 32768) {
      sectorsPerCluster = 64;
    } else {
      // SDXC cards
      sectorsPerCluster = 128;
    }

    if (m_bFAT32) {
      uint16_t const BU32 = 8192;

      uint32_t nc;
      relSector = BU32;

      for (dataStart = 2 * BU32;; dataStart += BU32) {
	nc = (cardSizeBlocks - dataStart) / sectorsPerCluster;
	fatSize = (nc + 2 + 127) / 128;

	uint32_t r = relSector + 9 + 2 * fatSize;

	if (dataStart >= r) {
	  break;
	}
      }

      // error if too few clusters in FAT32 volume
      if (nc < 65525) {
	m_bValid = false;
      } else {
	reservedSectors = dataStart - relSector - 2 * fatSize;
	fatStart = relSector + reservedSectors;
	partSize = nc * sectorsPerCluster + dataStart - relSector;

	// type depends on address of end sector
	// max CHS has lbn = 16450560 = 1024*255*63
	if ((relSector + partSize) <= 16450560) {
	  // FAT32
	  partType = 0x0B;
	} else {
	  // FAT32 with INT 13
	  partType = 0x0C;
	}
      }
    } else {
      uint16_t const BU16 = 128;

      uint32_t nc;

      for (dataStart = 2 * BU16;; dataStart += BU16) {
	nc = (cardSizeBlocks - dataStart) / sectorsPerCluster;
	fatSize = (nc + 2 + 255) / 256;

	uint32_t r = BU16 + 1 + 2 * fatSize + 32;

	if (dataStart < r) {
	  continue;
	}
	relSector = dataStart - r + BU16;
	break;
      }

      // check valid cluster count for FAT16 volume
      if (nc < 4085 || nc >= 65525) {
	m_bValid = false;
      } else {
	reservedSectors = 1;
	fatStart = relSector + reservedSectors;
	partSize = nc * sectorsPerCluster + 2 * fatSize + reservedSectors + 32;

	if (partSize < 32680) {
	  partType = 0x01;
	} else if (partSize < 65536) {
	  partType = 0x04;
	} else {
	  partType = 0x06;
	}
      }
    }
  }

public:
  SD_Geometry (uint32_t block_count, bool bFAT32) :
    cardSizeBlocks(block_count),
    cardCapacityMB((block_count + 2047) / 2048),
    m_bFAT32(bFAT32),
    m_bValid(true)
  {
    fake_geometry ();
    fat_parameters ();
  }

  ~SD_Geometry () {
    // ...
  }

private:
  // write cached block to the card
  uint8_t cache_write (uint32_t lbn) {
    return sd.card()->writeBlock (lbn, m_cache.data);
  }

  // zero cache and optionally set the sector signature
  void cache_clear (bool bAddSig) {
    memset (&m_cache, 0, sizeof (m_cache));

    if (bAddSig) {
      m_cache.mbr.mbrSig0 = BOOTSIG0;
      m_cache.mbr.mbrSig1 = BOOTSIG1;
    }
  }

  // zero FAT and root dir area on SD
  bool clear_root (uint8_t address_src, uint32_t bgn, uint32_t count) {
    bool bOkay = true;

    cache_clear (false);

    for (uint32_t i = 0; i < count; i++) {
      if (!sd.card()->writeBlock (bgn + i, m_cache.data)) {
	Message response;
	response.text = "SD: Error while attempting to format: Clear FAT/DIR writeBlock failed";
	response.send (address_src);

	bOkay = false;
	break;
      }     
    }
    return bOkay;
  }

public:
  // format and write the Master Boot Record
  bool write_MBR (uint8_t address_src) {
    bool bOkay = true;

    uint16_t c = cylinder (relSector);

    if (c > 1023) {
      Message response;
      response.text = "SD: Error while attempting to format: MBR CHS";
      response.send (address_src);

      bOkay = false;
    } else {
      cache_clear (false);

      part_t * p = m_cache.mbr.part;

      p->boot = 0;
      p->beginCylinderHigh = c >> 8;
      p->beginCylinderLow = c & 0xFF;
      p->beginHead = head (relSector);
      p->beginSector = sector (relSector);
      p->type = partType;

      uint32_t endLbn = relSector + partSize - 1;

      c = cylinder (endLbn);

      if (c <= 1023) {
	p->endCylinderHigh = c >> 8;
	p->endCylinderLow = c & 0xFF;
	p->endHead = head (endLbn);
	p->endSector = sector (endLbn);
      } else {
	// Too big flag, c = 1023, h = 254, s = 63
	p->endCylinderHigh = 3;
	p->endCylinderLow = 255;
	p->endHead = 254;
	p->endSector = 63;
      }

      p->firstSector = relSector;
      p->totalSectors = partSize;

      if (!cache_write (0)) {
	Message response;
	response.text = "SD: Error while attempting to format: write MBR";
	response.send (address_src);

	bOkay = false;
      }
    }

    return bOkay;
  }

  bool write_FAT32 (uint8_t address_src) {
    bool bOkay = true;

    cache_clear (true);

    fat32_boot_t * pb = &m_cache.fbs32;

    pb->jump[0] = 0XEB;
    pb->jump[1] = 0X00;
    pb->jump[2] = 0X90;

    for (uint8_t i = 0; i < sizeof (pb->oemId); i++) {
      pb->oemId[i] = ' ';
    }

    pb->bytesPerSector = 512;
    pb->sectorsPerCluster = sectorsPerCluster;
    pb->reservedSectorCount = reservedSectors;
    pb->fatCount = 2;
    pb->mediaType = 0xF8;
    pb->sectorsPerTrack = sectorsPerTrack;
    pb->headCount = numberOfHeads;
    pb->hidddenSectors = relSector;
    pb->totalSectors32 = partSize;
    pb->sectorsPerFat32 = fatSize;
    pb->fat32RootCluster = 2;
    pb->fat32FSInfo = 1;
    pb->fat32BackBootBlock = 6;
    pb->driveNumber = 0x80;
    pb->bootSignature = EXTENDED_BOOT_SIG;
    pb->volumeSerialNumber = generate_serial_number ();

    memcpy (pb->volumeLabel, "NO NAME    ", 11 /* sizeof(pb->volumeLabel) */);
    memcpy (pb->fileSystemType, "FAT32   ", 8  /* sizeof(pb->fileSystemType) */);

    // write partition boot sector and backup
    if (!cache_write (relSector) || !cache_write (relSector + 6)) {
      Message response;
      response.text = "SD: Error while attempting to format: FAT32 write PBS failed";
      response.send (address_src);

      bOkay = false;
    } else {
      cache_clear (true);

      // write extra boot area and backup
      if (!cache_write (relSector + 2) || !cache_write (relSector + 8)) {
	Message response;
	response.text = "SD: Error while attempting to format: FAT32 PBS ext failed";
	response.send (address_src);

	bOkay = false;
      } else {
	fat32_fsinfo_t * pf = &m_cache.fsinfo;

	pf->leadSignature = FSINFO_LEAD_SIG;
	pf->structSignature = FSINFO_STRUCT_SIG;
	pf->freeCount = 0xFFFFFFFF;
	pf->nextFree = 0xFFFFFFFF;

	// write FSINFO sector and backup
	if (!cache_write (relSector + 1) || !cache_write (relSector + 7)) {
	  Message response;
	  response.text = "SD: Error while attempting to format: FAT32 FSINFO failed";
	  response.send (address_src);

	  bOkay = false;
	} else {
	  bOkay = clear_root (address_src, fatStart, 2 * fatSize + sectorsPerCluster);

	  if (bOkay) {
	    cache_clear (false);

	    m_cache.fat32[0] = 0x0FFFFFF8;
	    m_cache.fat32[1] = 0x0FFFFFFF;
	    m_cache.fat32[2] = 0x0FFFFFFF;

	    // write first block of FAT and backup for reserved clusters
	    if (!cache_write (fatStart) || !cache_write (fatStart + fatSize)) {
	      Message response;
	      response.text = "SD: Error while attempting to format: FAT32 reserve failed";
	      response.send (address_src);

	      bOkay = false;
	    }
	  }
	}
      }
    }
    return bOkay;
  }

  bool write_FAT16 (uint8_t address_src) {
    bool bOkay = true;

    cache_clear (true);

    fat_boot_t * pb = &m_cache.fbs;

    pb->jump[0] = 0XEB;
    pb->jump[1] = 0X00;
    pb->jump[2] = 0X90;

    for (uint8_t i = 0; i < sizeof (pb->oemId); i++) {
      pb->oemId[i] = ' ';
    }

    pb->bytesPerSector = 512;
    pb->sectorsPerCluster = sectorsPerCluster;
    pb->reservedSectorCount = reservedSectors;
    pb->fatCount = 2;
    pb->rootDirEntryCount = 512;
    pb->mediaType = 0xF8;
    pb->sectorsPerFat16 = fatSize;
    pb->sectorsPerTrack = sectorsPerTrack;
    pb->headCount = numberOfHeads;
    pb->hidddenSectors = relSector;
    pb->totalSectors32 = partSize;
    pb->driveNumber = 0x80;
    pb->bootSignature = EXTENDED_BOOT_SIG;
    pb->volumeSerialNumber = generate_serial_number ();

    memcpy (pb->volumeLabel, "NO NAME    ", 11 /* sizeof(pb->volumeLabel) */);
    memcpy (pb->fileSystemType, "FAT16   ", 8  /* sizeof(pb->fileSystemType) */);

    // write partition boot sector
    if (!cache_write (relSector)) {
      Message response;
      response.text = "SD: Error while attempting to format: FAT16 write PBS failed";
      response.send (address_src);

      bOkay = false;
    } else {
      // clear FAT and root directory
      bOkay = clear_root (address_src, fatStart, dataStart - fatStart);

      if (bOkay) {
	cache_clear (false);

	m_cache.fat16[0] = 0XFFF8;
	m_cache.fat16[1] = 0XFFFF;

	// write first block of FAT and backup for reserved clusters
	if (!cache_write (fatStart) || !cache_write (fatStart + fatSize)) {
	  Message response;
	  response.text = "SD: Error while attempting to format: FAT16 reserve failed";
	  response.send (address_src);

	  bOkay = false;
	}
      }
    }
    return bOkay;
  }

  static void format (uint8_t address_src) {
    Message response;

    if (!sd.card()->begin ()) {
      response.text = "SD: Unable to initialise card.";
      response.send (address_src);
    } else {
      bool bSDHC = (sd.card()->type () == SD_CARD_TYPE_SDHC);

      uint32_t block_count = sd.card()->cardSize (); // no. of 512-byte blocks

      SD_Geometry geometry (block_count, bSDHC);

      if (!geometry.valid ()) {
	response.text = "SD: Card capacity too low, or bad cluster count.";
	response.send (address_src);
      } else {
	if (geometry.write_MBR (address_src)) {
	  bool bOkay;

	  if (bSDHC) { // FAT32
	    bOkay = geometry.write_FAT32 (address_src);
	  } else { // FAT16
	    bOkay = geometry.write_FAT16 (address_src);
	  }
	  if (bOkay) {
	    response.text = "SD: Card formatted.";
	    response.send (address_src);
	  }
	}
      }
    }
  }

  static void erase (uint8_t address_src) {
    Message response;

    if (!sd.card()->begin ()) {
      response.text = "SD: Unable to initialise card.";
      response.send (address_src);
    } else {
      uint32_t block_count = sd.card()->cardSize (); // no. of 512-byte blocks

      uint32_t const ERASE_SIZE = 262144L; // 128MB
      uint32_t divisions = (block_count + ERASE_SIZE - 1) / ERASE_SIZE;

      uint32_t block_start = 0;
      uint32_t block_end;

      bool bOkay = true;

      while (divisions--) {
	if (divisions) {
	  block_end = block_start + ERASE_SIZE - 1;
	} else {
	  block_end = block_count - 1;
	}

	if (!sd.card()->erase (block_start, block_end)) {
	  response.text = "SD: Error attempting to erase card: ";
	  response.text += String (block_start) + " - " + String (block_end);
	  response.send (address_src);

	  bOkay = false;
	  break;
	}
	block_start += ERASE_SIZE;
      }
      if (bOkay) {
	response.text = "SD: Card erased.";
	response.send (address_src);
      }
    }
  }
};
