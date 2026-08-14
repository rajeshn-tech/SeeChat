import subprocess
import time
import sys

def run_auto_self_server():
    print("==================================================================")
    print("      SEECHAT AUTO-SELF-RUN DAEMON WATCHDOG (LIVE SERVICE)        ")
    print("==================================================================")
    print(" Status:          ACTIVE & MONITORING")
    print(" Auto-Restart:    ENABLED (Intelligent crash loop recovery)")
    print("==================================================================\n")
    
    consecutive_fast_crashes = 0
    
    while True:
        start_time = time.time()
        try:
            p = subprocess.Popen([sys.executable, "server.py"])
            p.wait()
        except KeyboardInterrupt:
            print("\n[WATCHDOG] Stopping SeeChat Service Daemon...")
            break
        except Exception as e:
            print(f"[WATCHDOG] Error: {e}")
        
        run_duration = time.time() - start_time
        if run_duration < 2.0:
            consecutive_fast_crashes += 1
        else:
            consecutive_fast_crashes = 0
            
        sleep_time = 5 if consecutive_fast_crashes >= 3 else 1
        if consecutive_fast_crashes >= 3:
            print(f"[WATCHDOG WARNING] Server exited rapidly ({consecutive_fast_crashes}x). Pausing {sleep_time}s before retrying to prevent CPU spin loop...")
        else:
            print("[WATCHDOG] Server stopped/restarted. Auto-restarting server in 1 second...")
            
        time.sleep(sleep_time)

if __name__ == "__main__":
    run_auto_self_server()
