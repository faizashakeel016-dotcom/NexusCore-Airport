import streamlit as st
import time
import pandas as pd

# Page Configuration for Professional Look
st.set_page_config(page_title="NexusCore: ATC Sky-Scheduler", page_icon="✈️", layout="wide")

st.title("✈️ NexusCore Terminal: Advanced Air Traffic Control Scheduler")
st.markdown("### `System Core: Python-Streamlit RTOS Simulator` | **Hangar Capacity: 1024 Slots**")
st.write("---")

# Initialize Log File
LOG_FILE = "atc_flight_log.txt"

def write_to_log(text):
    with open(LOG_FILE, "a") as f:
        f.write(text + "\n")

# --- UI Side Panel: Input Flights Data ---
st.sidebar.header("🛫 Flight Dispatch Control")
num_flights = st.sidebar.number_input("Number of Flights in Airspace", min_value=1, max_value=10, value=3)

flights = []
st.sidebar.markdown("---")
for i in range(num_flights):
    st.sidebar.subheader(f"Flight status {i+1}")
    f_name = st.sidebar.text_input(f"Flight Number/Sign", value=f"PK-{301+i}", key=f"name_{i}")
    f_burst = st.sidebar.number_input(f"Runway Time Needed (Mins)", min_value=1, max_value=20, value=3+i, key=f"burst_{i}")
    f_ram = st.sidebar.number_input(f"Hangar/Gate Slots Required (Max 1024)", min_value=50, max_value=500, value=128*(i+1), key=f"ram_{i}")
    flights.append({
        "name": f_name,
        "burst_time": f_burst,
        "remaining_time": f_burst,
        "ram_required": f_ram,
        "wait_time": 0,
        "tat": 0
    })

# --- Main Dashboard Setup ---
algo_choice = st.selectbox("🎯 Choose Scheduling Protocol", [
    "Select Protocol", 
    "First-Come-First-Served (FCFS) - Standard Queue", 
    "Shortest Job First (SJF) - Fuel Optimization Mode", 
    "Round Robin (RR) - Equal Share Airspace (Quantum = 2m)"
])

# Status Metrics Placeholders
metrics_area = st.empty()
simulation_log = st.empty()

# --- Core Simulation Engine ---
if algo_choice != "Select Protocol" and st.button("🚀 Authorize Runway Clearances"):
    
    total_hangar_capacity = 1024
    write_to_log(f"\n=== ATC Execution Log: {algo_choice} ===")
    
    # 1. Scheduling Logic Modifications
    executed_flights = []
    
    if "FCFS" in algo_choice:
        executed_flights = list(flights) # No sorting needed
    elif "SJF" in algo_choice:
        executed_flights = sorted(flights, key=lambda x: x["burst_time"]) # Sort by smallest time
    elif "Round Robin" in algo_choice:
        executed_flights = [dict(f) for f in flights] # Temp copy for loop

    st.info(f"⚡ Runway Engine Engaged using {algo_choice} strategy...")
    
    # --- FCFS / SJF Simulation Loop ---
    if "Round Robin" not in algo_choice:
        current_time = 0
        total_wait = 0
        total_tat = 0
        
        for f in executed_flights:
            # Memory (Hangar Slot) Allocation Check
            if f["ram_required"] > total_hangar_capacity:
                st.error(f"⚠️ [ATC ALERT] {f['name']} rejected! Demands {f['ram_required']} slots, but Hangar has only {total_hangar_capacity} slots free.")
                write_to_log(f"Flight {f['name']} wave-off due to Hangar overload.")
                continue
                
            # Occupy Hangar
            total_hangar_capacity -= f["ram_required"]
            f["wait_time"] = current_time
            f["tat"] = f["wait_time"] + f["burst_time"]
            
            total_wait += f["wait_time"]
            total_tat += f["tat"]
            
            # Update Live Visuals
            metrics_area.markdown(f"### 📡 Current Status: **{f['name']} occupies Runway** | 🏢 Free Hangar Slots: `{total_hangar_capacity} / 1024`")
            simulation_log.warning(f"⏱️ Mins {current_time}: **{f['name']}** has landed and rolling on Runway. (Required: {f['burst_time']} mins)")
            write_to_log(f"Mins {current_time}: {f['name']} Landed | Runway Time: {f['burst_time']}m | Free Hangar: {total_hangar_capacity}")
            
            time.sleep(1.5) # Real-time simulation delay
            current_time += f["burst_time"]
            
            # Deallocate Hangar (Flight parked inside, gate slots freed after runway clear)
            total_hangar_capacity += f["ram_required"]
            st.success(f"✅ Mins {current_time}: **{f['name']}** cleared runway. Gate slots released.")

        # Display Final Metrics Table
        st.write("---")
        st.subheader("📊 Tower Analysis Report")
        df = pd.DataFrame(executed_flights)
        st.table(df[["name", "burst_time", "ram_required", "wait_time", "tat"]])
        
        avg_wait = total_wait / len(executed_flights)
        avg_tat = total_tat / len(executed_flights)
        
        col1, col2 = st.columns(2)
        col1.metric("Average Waiting Time", f"{avg_wait:.2f} mins")
        col2.metric("Average Turnaround Time (TAT)", f"{avg_tat:.2f} mins")
        
        write_to_log(f"SUMMARY -> Avg Wait: {avg_wait:.2f}m | Avg TAT: {avg_tat:.2f}m\n")
        st.info("💾 Flight data logged successfully in `atc_flight_log.txt`.")

    # --- Round Robin Simulation Loop ---
    else:
        current_time = 0
        quantum = 2
        total_wait = 0
        total_tat = 0
        done = False
        
        n = len(executed_flights)
        
        while not done:
            done = True
            for i in range(n):
                f = executed_flights[i]
                if f["remaining_time"] > 0:
                    done = False # Still tasks to do
                    
                    metrics_area.markdown(f"### 📡 Current Status: **{f['name']} on Shared Approach Loop**")
                    
                    if f["remaining_time"] > quantum:
                        simulation_log.info(f"⏱️ Mins {current_time}: **{f['name']}** allocated {quantum}m runway window... (Remaining: {f['remaining_time'] - quantum}m)")
                        write_to_log(f"Mins {current_time}: {f['name']} active window")
                        current_time += quantum
                        f["remaining_time"] -= quantum
                        time.sleep(1)
                    else:
                        simulation_log.success(f"✅ Mins {current_time}: **{f['name']}** used final {f['remaining_time']}m slot and completely landed!")
                        write_to_log(f"Mins {current_time}: {f['name']} final landing complete.")
                        current_time += f["remaining_time"]
                        f["wait_time"] = current_time - f["burst_time"]
                        f["tat"] = current_time
                        total_wait += f["wait_time"]
                        total_tat += f["tat"]
                        f["remaining_time"] = 0
                        time.sleep(1)
                        
        st.write("---")
        st.subheader("📊 Tower Analysis Report (Round Robin)")
        df = pd.DataFrame(executed_flights)
        st.table(df[["name", "burst_time", "ram_required", "wait_time", "tat"]])
        
        avg_wait = total_wait / n
        avg_tat = total_tat / n
        
        col1, col2 = st.columns(2)
        col1.metric("Average Waiting Time", f"{avg_wait:.2f} mins")
        col2.metric("Average Turnaround Time (TAT)", f"{avg_tat:.2f} mins")
        
        write_to_log(f"SUMMARY RR -> Avg Wait: {avg_wait:.2f}m | Avg TAT: {avg_tat:.2f}m\n")
        st.info("💾 Flight data logged successfully in `atc_flight_log.txt`.")
