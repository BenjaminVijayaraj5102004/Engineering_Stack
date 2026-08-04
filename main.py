import Agents.config  # Initialize environment and LangSmith tracing
from Agents.pipeline import run_pipeline

def main():
    print("[INFO] Initializing LangGraph Agent System with LangSmith Tracing...")
    tracing_status = Agents.config.init_tracing()
    print(f"[STATUS] Tracing Status: Project '{tracing_status['project']}', Active Key Present: {tracing_status['has_key']}")
    print("[SUCCESS] Multi-agent pipeline initialized with @traceable functions.")

if __name__ == "__main__":
    main()
