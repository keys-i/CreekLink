curl -s http://localhost:8000/health | jq

curl -X POST http://localhost:8000/uplink \
  -H "Content-Type: application/json" \
  --data-binary @creeklink_ingest/examples/ttn_uplink_example.json