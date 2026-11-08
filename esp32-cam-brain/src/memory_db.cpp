#include "memory_db.h"

#ifdef PHASE0_SIMULATION
#  include <cstring>
#  include <ctime>
#  include <algorithm>
#else
#  include <Arduino.h>
#endif

MemoryDB::MemoryDB() {}

bool MemoryDB::begin() {
#ifdef PHASE0_SIMULATION
    loaded_ = true;
    std::printf("[MEM] Simulation memory DB initialized\n");
    return true;
#else
    if (!SD_MMC.begin(SD_MOUNT_POINT, true)) {
        std::printf("[MEM] SD mount failed\n");
        return false;
    }
    if (!SD_MMC.mkdir(OBJECTS_DIR)) {
        // May already exist.
    }
    sd_ready_ = true;
    std::printf("[MEM] Memory DB initialized on SD\n");
    return true;
#endif
}

bool MemoryDB::find(const std::string& label, ObjectSignature& out) const {
#ifdef PHASE0_SIMULATION
    for (const auto& sig : memory_) {
        if (std::string(sig.label) == label) {
            out = sig;
            return true;
        }
    }
    return false;
#else
    // Linear scan of SD file — fine for small DBs.
    (void)label; (void)out;
    return false;
#endif
}

void MemoryDB::record(const std::string& label,
                      const uint8_t* feature_hash,
                      uint32_t timestamp_ms) {
#ifdef PHASE0_SIMULATION
    ObjectSignature sig;
    std::memset(&sig, 0, sizeof(sig));
    std::strncpy(sig.label, label.c_str(), sizeof(sig.label) - 1);
    if (feature_hash) {
        std::memcpy(sig.feature_hash, feature_hash, 8);
    }
    sig.first_seen_ms = timestamp_ms;
    sig.last_seen_ms = timestamp_ms;
    sig.sighting_count = 1;

    // Update if exists, else append.
    bool found = false;
    for (auto& s : memory_) {
        if (std::string(s.label) == label) {
            s.last_seen_ms = timestamp_ms;
            s.sighting_count++;
            found = true;
            break;
        }
    }
    if (!found) memory_.push_back(sig);
#else
    (void)label; (void)feature_hash; (void)timestamp_ms;
#endif
}

bool MemoryDB::hasSeen(const std::string& label) const {
#ifdef PHASE0_SIMULATION
    for (const auto& sig : memory_) {
        if (std::string(sig.label) == label) return true;
    }
    return false;
#else
    (void)label;
    return false;
#endif
}

void MemoryDB::clear() {
#ifdef PHASE0_SIMULATION
    memory_.clear();
    std::printf("[MEM] Memory database cleared\n");
#else
    if (!sd_ready_) return;
    // Delete and recreate the DB file to clear all signatures.
    SD_MMC.remove(MEMORY_DB_PATH);
    cache_.clear();
    std::printf("[MEM] Memory database cleared from SD\n");
#endif
}

void MemoryDB::flush() {
#ifdef PHASE0_SIMULATION
    // In-memory simulation; nothing to flush to disk.
#else
    if (!sd_ready_) return;
    // Write cache to SD file.
#endif
}

MemoryDB memory_db;
