import argparse
import sys
import os

# Ensure the app package is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.posteering_client import posteering_client

def simulate_credit(virtual_account: str, amount_kobo: int, narration: str = "test payment"):
    print(f"Simulating BankRail credit...")
    print(f"  Virtual Account: {virtual_account}")
    print(f"  Amount (kobo):   {amount_kobo} (₦{amount_kobo / 100:,.2f})")
    print(f"  Narration:       {narration}\n")
    
    path = "/api/v1/one/products/bankrail-gateway/passthrough/sandbox/simulate-credit"
    payload = {
        "virtualAccount": virtual_account,
        "amountKobo": amount_kobo,
        "narration": narration
    }
    
    try:
        response = posteering_client.post(path, json_data=payload)
        
        print(f"HTTP Status: {response.status_code}")
        
        try:
            print("Response JSON:")
            import json
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print("Response Text:")
            print(response.text)
            
        if response.ok:
            print("\n✅ Simulation successful! The Posteering webhook should fire shortly.")
        else:
            print("\n❌ Simulation failed.")
            
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate a BankRail credit payment in sandbox.")
    parser.add_argument("virtual_account", help="The 10-digit virtual account number to credit")
    parser.add_argument("amount", type=float, help="The amount to credit (in Naira). E.g. 16600 for N16,600")
    parser.add_argument("--narration", default="test payment", help="Optional narration text")
    
    args = parser.parse_args()
    
    # Convert Naira to Kobo
    amount_kobo = int(args.amount * 100)
    
    simulate_credit(args.virtual_account, amount_kobo, args.narration)
