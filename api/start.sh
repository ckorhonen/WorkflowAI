#!/bin/sh

set -e

# Function to handle termination signals
# It forwards the signal to all child processes
handle_signal() {
    echo "Received signal, forwarding to child processes."
    # Forward the signal to all child processes
    pkill -TERM -P $$
}

# Trap termination signals and call the handle_signal function
trap 'handle_signal' SIGINT SIGTERM

# Start taskiq worker as a background process
taskiq worker api.broker:broker --fs-discover --tasks-pattern "api/jobs/*_jobs.py" &
taskiq_pid=$!
echo "Taskiq worker started with PID $taskiq_pid"

# Start taskiq scheduler as a background process
taskiq scheduler api.scheduler:scheduler &
scheduler_pid=$!
echo "Taskiq scheduler started with PID $scheduler_pid"

# Start uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2 &
uvicorn_pid=$!
echo "Uvicorn started with PID $uvicorn_pid"

# Wait for all child processes to finish
# -> It does not actually wait for processes to be done but
# instead, returns as soon as the message has been propagated to all child processes.
# So we have to wait for the child processes to finish manually.
wait

exit_code=$?

echo "Waiting for uvicorn #$uvicorn_pid to end"
# Wait for the uvicorn to finsh
while kill -0 $uvicorn_pid 2> /dev/null; do
    sleep 0.1
done
echo "Uvicorn #$uvicorn_pid ended."

# Wait for the taskiq worker to finsh
echo "Waiting for taskiq worker #$taskiq_pid to end"
while kill -0 $taskiq_pid 2> /dev/null; do
    sleep 0.1
done
echo "TaskIQ worker #$taskiq_pid ended."

# Wait for the taskiq scheduler to finsh
echo "Waiting for taskiq scheduler #$scheduler_pid to end"
while kill -0 $scheduler_pid 2> /dev/null; do
    sleep 0.1
done
echo "TaskIQ scheduler #$scheduler_pid ended."

echo "All child processes have finished, sleeping for 1 second for good measure."

sleep 1
echo "Done sleeping, exiting."

# Exit with the exit code of the last process that finished
exit $exit_code
