#ifndef MEMORY_DB_H
#define MEMORY_DB_H

#include "config.h"

#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>

#ifdef PHASE0_SIMULATION
#  include <fstream>
#else
#  include <SD_MMC.h>
#endif

// ============================================================================
// MEMORY_DB_H — Long-term object database on SD card
// ============================================================================
// Stores object signatures (label + feature hash) so the robot can say
// "I've seen this before." Each entry is a fixed-size record written to
// /sdcard/data/objects/memory_db.bin.
//
// Think of this as the robot's "long-term memory." It persists across
// reboots and enables re-identification of previously encountered objects.

struct ObjectSignature {
    char       label[32];
    uint8_t    feature_hash[8];  // simple feature fingerprint
    uint32_t   first_seen_ms;
    uint32_t   last_seen_ms;
    uint16_t   sighting_count;
};

class MemoryDB {
public:
    MemoryDB();

    // Initialize: create directory, open or create the DB file.
    bool begin();

    // Look up a signature by label. Returns true if found.
    bool find(const std::string& label, ObjectSignature& out) const;

    // Add or update a signature for a label.
    void record(const std::string& label, const uint8_t* feature_hash, uint32_t timestamp_ms);

    // Check if we've seen this label before.
    bool hasSeen(const std::string& label) const;

    // Clear all stored object signatures.
    void clear();

    // Save all in-memory signatures to SD.
    void flush();

private:
#ifdef PHASE0_SIMULATION
    std::vector<ObjectSignature> memory_;
    bool loaded_ = false;
#else
    bool sd_ready_ = false;
#endif
    std::vector<ObjectSignature> cache_;
};

// Global memory DB instance.
extern MemoryDB memory_db;

#endif  // MEMORY_DB_H
