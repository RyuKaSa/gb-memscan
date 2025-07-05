-----------------------------------------------------------------------
-- memory_dump_200.lua  ·  mGBA-compatible
-- Dumps 200 critical Pokémon Red/Blue RAM addresses (goldfish list)
-- to JSON once, then exits.  Result is saved alongside this script.
-----------------------------------------------------------------------

-----------------------------------------------------------------------
--  Pure math bit-check helper kept from reference code (unused here)
-----------------------------------------------------------------------
local function hasBit(v, i) return math.floor(v / 2 ^ i) % 2 >= 1 end

-----------------------------------------------------------------------
--  Address list (exactly 200 entries)  {0xADDR, "Label"} -------------
-----------------------------------------------------------------------
local ADDR = {
  -- World / map (10)
  {0xD35E,"Current Map Number"},
  {0xD367,"Map Tileset"},
  {0xD368,"Map Height (blocks)"},
  {0xD369,"Map Width (blocks)"},
  {0xD361,"Player Y-Position"},
  {0xD362,"Player X-Position"},
  {0xD363,"Player Y-Block"},
  {0xD364,"Player X-Block"},
  {0xD365,"Last Map Location"},
  {0xD35D,"Map Palette (Flash)"},
  -- Trainer name (5)
  {0xD158,"Trainer Name[1]"},{0xD159,"Trainer Name[2]"},
  {0xD15A,"Trainer Name[3]"},{0xD15B,"Trainer Name[4]"},
  {0xD15C,"Trainer Name[5]"},
  -- Party size (1)
  {0xD163,"Party Size"},
  -- Money (3)
  {0xD347,"Money[1]"},{0xD348,"Money[2]"},{0xD349,"Money[3]"},
  -- Casino chips (2)
  {0xD5A4,"Casino Chips[1]"},{0xD5A5,"Casino Chips[2]"},
  -- Rival name (8)
  {0xD34A,"Rival Name[1]"},{0xD34B,"Rival Name[2]"},
  {0xD34C,"Rival Name[3]"},{0xD34D,"Rival Name[4]"},
  {0xD34E,"Rival Name[5]"},{0xD34F,"Rival Name[6]"},
  {0xD350,"Rival Name[7]"},{0xD351,"Rival Name[8]"},
  -- Options & identity (5)
  {0xD355,"Game Options"},{0xD35B,"Audio Track"},
  {0xD35C,"Audio Bank"},{0xD359,"Player ID-hi"},{0xD35A,"Player ID-lo"},
  -- Pokémon 1 (18)
  {0xD16B,"PKM1 Species"},
  {0xD16C,"PKM1 HP lo"},{0xD16D,"PKM1 HP hi"},
  {0xD16E,"PKM1 TempLvl"},{0xD16F,"PKM1 Status"},
  {0xD170,"PKM1 Type1"},{0xD171,"PKM1 Type2"},
  {0xD173,"PKM1 Move1"},{0xD174,"PKM1 Move2"},
  {0xD175,"PKM1 Move3"},{0xD176,"PKM1 Move4"},
  {0xD188,"PKM1 PP1"},{0xD189,"PKM1 PP2"},
  {0xD18A,"PKM1 PP3"},{0xD18B,"PKM1 PP4"},
  {0xD18C,"PKM1 Level"},
  {0xD18D,"PKM1 MaxHP lo"},{0xD18E,"PKM1 MaxHP hi"},
  -- Pokémon 2 (18)
  {0xD197,"PKM2 Species"},
  {0xD198,"PKM2 HP lo"},{0xD199,"PKM2 HP hi"},
  {0xD19A,"PKM2 TempLvl"},{0xD19B,"PKM2 Status"},
  {0xD19C,"PKM2 Type1"},{0xD19D,"PKM2 Type2"},
  {0xD19F,"PKM2 Move1"},{0xD1A0,"PKM2 Move2"},
  {0xD1A1,"PKM2 Move3"},{0xD1A2,"PKM2 Move4"},
  {0xD1B4,"PKM2 PP1"},{0xD1B5,"PKM2 PP2"},
  {0xD1B6,"PKM2 PP3"},{0xD1B7,"PKM2 PP4"},
  {0xD1B8,"PKM2 Level"},
  {0xD1B9,"PKM2 MaxHP lo"},{0xD1BA,"PKM2 MaxHP hi"},
  -- Pokémon 3 (18)
  {0xD1C3,"PKM3 Species"},
  {0xD1C4,"PKM3 HP lo"},{0xD1C5,"PKM3 HP hi"},
  {0xD1C6,"PKM3 TempLvl"},{0xD1C7,"PKM3 Status"},
  {0xD1C8,"PKM3 Type1"},{0xD1C9,"PKM3 Type2"},
  {0xD1CB,"PKM3 Move1"},{0xD1CC,"PKM3 Move2"},
  {0xD1CD,"PKM3 Move3"},{0xD1CE,"PKM3 Move4"},
  {0xD1E0,"PKM3 PP1"},{0xD1E1,"PKM3 PP2"},
  {0xD1E2,"PKM3 PP3"},{0xD1E3,"PKM3 PP4"},
  {0xD1E4,"PKM3 Level"},
  {0xD1E5,"PKM3 MaxHP lo"},{0xD1E6,"PKM3 MaxHP hi"},
  -- Pokémon 4 (18)
  {0xD1EF,"PKM4 Species"},
  {0xD1F0,"PKM4 HP lo"},{0xD1F1,"PKM4 HP hi"},
  {0xD1F2,"PKM4 TempLvl"},{0xD1F3,"PKM4 Status"},
  {0xD1F4,"PKM4 Type1"},{0xD1F5,"PKM4 Type2"},
  {0xD1F7,"PKM4 Move1"},{0xD1F8,"PKM4 Move2"},
  {0xD1F9,"PKM4 Move3"},{0xD1FA,"PKM4 Move4"},
  {0xD20C,"PKM4 PP1"},{0xD20D,"PKM4 PP2"},
  {0xD20E,"PKM4 PP3"},{0xD20F,"PKM4 PP4"},
  {0xD210,"PKM4 Level"},
  {0xD211,"PKM4 MaxHP lo"},{0xD212,"PKM4 MaxHP hi"},
  -- Pokémon 5 (18)
  {0xD21B,"PKM5 Species"},
  {0xD21C,"PKM5 HP lo"},{0xD21D,"PKM5 HP hi"},
  {0xD21E,"PKM5 TempLvl"},{0xD21F,"PKM5 Status"},
  {0xD220,"PKM5 Type1"},{0xD221,"PKM5 Type2"},
  {0xD223,"PKM5 Move1"},{0xD224,"PKM5 Move2"},
  {0xD225,"PKM5 Move3"},{0xD226,"PKM5 Move4"},
  {0xD238,"PKM5 PP1"},{0xD239,"PKM5 PP2"},
  {0xD23A,"PKM5 PP3"},{0xD23B,"PKM5 PP4"},
  {0xD23C,"PKM5 Level"},
  {0xD23D,"PKM5 MaxHP lo"},{0xD23E,"PKM5 MaxHP hi"},
  -- Pokémon 6 (18)
  {0xD247,"PKM6 Species"},
  {0xD248,"PKM6 HP lo"},{0xD249,"PKM6 HP hi"},
  {0xD24A,"PKM6 TempLvl"},{0xD24B,"PKM6 Status"},
  {0xD24C,"PKM6 Type1"},{0xD24D,"PKM6 Type2"},
  {0xD24F,"PKM6 Move1"},{0xD250,"PKM6 Move2"},
  {0xD251,"PKM6 Move3"},{0xD252,"PKM6 Move4"},
  {0xD264,"PKM6 PP1"},{0xD265,"PKM6 PP2"},
  {0xD266,"PKM6 PP3"},{0xD267,"PKM6 PP4"},
  {0xD268,"PKM6 Level"},
  {0xD269,"PKM6 MaxHP lo"},{0xD26A,"PKM6 MaxHP hi"},
  -- Bag (21)
  {0xD31D,"Bag Count"},
  {0xD31E,"Bag1 ID"},{0xD31F,"Bag1 Qty"},
  {0xD320,"Bag2 ID"},{0xD321,"Bag2 Qty"},
  {0xD322,"Bag3 ID"},{0xD323,"Bag3 Qty"},
  {0xD324,"Bag4 ID"},{0xD325,"Bag4 Qty"},
  {0xD326,"Bag5 ID"},{0xD327,"Bag5 Qty"},
  {0xD328,"Bag6 ID"},{0xD329,"Bag6 Qty"},
  {0xD32A,"Bag7 ID"},{0xD32B,"Bag7 Qty"},
  {0xD32C,"Bag8 ID"},{0xD32D,"Bag8 Qty"},
  {0xD32E,"Bag9 ID"},{0xD32F,"Bag9 Qty"},
  {0xD330,"Bag10 ID"},{0xD331,"Bag10 Qty"},
  -- PC items (21)
  {0xD53A,"PC Count"},
  {0xD53B,"PC1 ID"},{0xD53C,"PC1 Qty"},
  {0xD53D,"PC2 ID"},{0xD53E,"PC2 Qty"},
  {0xD53F,"PC3 ID"},{0xD540,"PC3 Qty"},
  {0xD541,"PC4 ID"},{0xD542,"PC4 Qty"},
  {0xD543,"PC5 ID"},{0xD544,"PC5 Qty"},
  {0xD545,"PC6 ID"},{0xD546,"PC6 Qty"},
  {0xD547,"PC7 ID"},{0xD548,"PC7 Qty"},
  {0xD549,"PC8 ID"},{0xD54A,"PC8 Qty"},
  {0xD54B,"PC9 ID"},{0xD54C,"PC9 Qty"},
  {0xD54D,"PC10 ID"},{0xD54E,"PC10 Qty"},
  -- Badges & key flags (16)
  {0xD356,"Badges Bitfield"},
  {0xD5F3,"Have Town Map"},
  {0xD60D,"Have Oak's Parcel"},
  {0xD755,"Fought Brock"},
  {0xD75E,"Fought Misty"},
  {0xD773,"Fought Lt Surge"},
  {0xD77C,"Fought Erika"},
  {0xD792,"Fought Koga"},
  {0xD79A,"Fought Blaine"},
  {0xD7B3,"Fought Sabrina"},
  {0xD751,"Fought Giovanni"},
  {0xD7D4,"Defeated Zapdos"},
  {0xD7D8,"Snorlax Verm gone"},
  {0xD7E0,"Snorlax Cel gone"},
  {0xD7EE,"Defeated Moltres"},
  {0xD782,"Defeated Articuno"},
}

-----------------------------------------------------------------------
--  JSON helpers -------------------------------------------------------
-----------------------------------------------------------------------
local function esc(s)
  return s:gsub('[%z\1-\31\\"]', function(c)
    return string.format("\\u%04X", c:byte())
  end)
end

local function buildJSON()
  local parts = {}
  for i, rec in ipairs(ADDR) do
    local val = emu:read8(rec[1])
    parts[i] = string.format('[ "0x%04X", "%s", %d ]',
                             rec[1], esc(rec[2]), val)
  end
  return "[\n  " .. table.concat(parts, ",\n  ") .. "\n]\n"
end

-----------------------------------------------------------------------
--  Dump every second (≈60 frames) -----------------------------------
-----------------------------------------------------------------------
local frameCount = 0
local FPS        = 60

-- derive output path once
local path = debug.getinfo(1, 'S').source:sub(2)
local dir  = path:match("(.*/)")
local out  = (dir or "./") .. "memory_dump.json"

local function writeDump()
  local f = assert(io.open(out, "w"))
  f:write(buildJSON())
  f:close()
  print("memory_dump.json written at: " .. out)
end

callbacks:add("frame", function()
  frameCount = frameCount + 1
  if frameCount < FPS then
    return
  end
  frameCount = 0
  writeDump()
end)
