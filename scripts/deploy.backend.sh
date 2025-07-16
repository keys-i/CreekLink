cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Make sure DATABASE_URL is set to a running Timescale/Postgres
export DATABASE_URL="postgresql://creeklink:creeklink_password@localhost:5432/creeklink"

uvicorn creekingest.main:app --reload
