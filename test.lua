-- Pure math fallback to check bit N in byte
local function hasBit(value, bitIndex)
  return math.floor(value / (2 ^ bitIndex)) % 2 >= 1
end

local badgeNames = {
  "Boulder", "Cascade", "Thunder", "Rainbow",
  "Soul", "Marsh", "Volcano", "Earth"
}

local function printBadges()
  local badgeByte = emu:read8(0xD356)
  print("Badge Byte: 0x" .. string.format("%02X", badgeByte))
  for i = 0, 7 do
    local hasBadge = hasBit(badgeByte, i)
    print(badgeNames[i + 1] .. ": " .. (hasBadge and "Yes" or "No"))
  end
  print("---")
end

callbacks:add("frame", function()
  if emu:currentFrame() % 120 == 0 then
    printBadges()
  end
end)
