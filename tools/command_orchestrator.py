"""
COMMAND ORCHESTRATOR
Wrapper for Factory Orchestrator to assert Command Control.
"""
import sys
import os
import time

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(__file__))

import factory_orchestrator

def main():
    print(f"\n{'#'*60}")
    print(f"⚔️ COMMAND ORCHESTRATOR: ASSUMING CONTROL")
    print(f"{'#'*60}")
    
    # Run the Factory
    factory_orchestrator.main()
    
    # Signal Completion
    print(f"\n{'#'*60}")
    print(f"✅ COMMAND CYCLE COMPLETE")
    print(f"{'#'*60}")
    
    try:
        import winsound
        winsound.Beep(1000, 200)
    except:
        pass

if __name__ == "__main__":
    main()
