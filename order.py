import subprocess
import os
import time

def touch(filename):
	subprocess.run(["touch", os.path.join("sets", filename)])
	time.sleep(0.1)

special = [
	"animals",
	"lakehouse",
	"minecraft",
	"tress"
]

for x in special:
	touch(x + ".json")

files = os.listdir("sets")
for filename in files:
	if filename in [f"{x}.json" for x in special]: continue;
	touch(filename)

print("[finished reordering]")