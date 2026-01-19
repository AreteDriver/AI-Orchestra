#!/bin/bash
# Gorgon Launcher - starts API server and opens dashboard

cd /home/arete/projects/Gorgon
source .venv/bin/activate

# Start API server in background
uvicorn test_ai.api:app --host 127.0.0.1 --port 8000 &
API_PID=$!

# Wait for API to be ready
echo "Starting Gorgon API server..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "API server ready!"
        break
    fi
    sleep 0.5
done

# Start Streamlit dashboard
echo "Starting Gorgon Dashboard..."
streamlit run src/test_ai/dashboard/app.py --server.port 8501 --server.headless true &
DASH_PID=$!

# Wait for dashboard
for i in {1..30}; do
    if curl -s http://127.0.0.1:8501 > /dev/null 2>&1; then
        echo "Dashboard ready!"
        break
    fi
    sleep 0.5
done

# Open browser
xdg-open http://127.0.0.1:8501 2>/dev/null || open http://127.0.0.1:8501 2>/dev/null

echo "Gorgon is running!"
echo "  Dashboard: http://127.0.0.1:8501"
echo "  API: http://127.0.0.1:8000"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for interrupt
trap "kill $API_PID $DASH_PID 2>/dev/null; exit" INT TERM
wait
