import sys
print("Python version:", sys.version)
 
# Check installed modules
help("modules")
 
# Quick version compare
if sys.version_info >= (3, 10):
    print("✅ You’re on a modern Python version!")
else:
    print("⚠️ Consider Upgrading Python.")