import asyncio
import sys
sys.path.insert(0, ".")
from app.services.posteering_client import posteering_client

def simulate_credit(virtual_account: str, amount_kobo: int):
    path = "/api/v1/one/products/bankrail-gateway/passthrough/sandbox/simulate-credit"
    payload = {
        "virtualAccount": virtual_account,
        "amountKobo": amount_kobo,
        "narration": "test payment"
    }
    
    print(f"Simulating credit of {amount_kobo} kobo to {virtual_account}...")
    try:
        response = posteering_client.post(path, json_data=payload)
        print("Response status:", response.status_code)
        print("Response body:", response.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fire_credit.py <virtual_account> <amount_kobo>")
        sys.exit(1)
        
    virtual_acct = sys.argv[1]
    amt = int(sys.argv[2])
    simulate_credit(virtual_acct, amt)
