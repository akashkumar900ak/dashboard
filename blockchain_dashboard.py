import requests
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

@dataclass
class WalletInfo:
    address: str
    balance: float
    token_balance: Optional[float] = None
    transaction_count: Optional[int] = None
    last_activity: Optional[str] = None
    usd_value: Optional[float] = None

class BlockchainQueryEngine:
    def __init__(self):
        # API Configuration
        self.etherscan_api_key = "FH7YYXWTZS8SCDHI4WITWYWNUSPT87KYY7"
        self.moralis_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImMwYmU5YjkxLWJhZWMtNDk3ZC04OWE2LWUwNmVhNGYzNWI5MCIsIm9yZ0lkIjoiNDUzNTkxIiwidXNlcklkIjoiNDY2NjgxIiwidHlwZUlkIjoiYjg0OGIzNGUtNzRiOS00ZDhiLWEyZjQtMTA2M2NjNzQyOGFjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NDk3MzQ2MTQsImV4cCI6NDkwNTQ5NDYxNH0.cdKiWcGh8ratJpYQAIXMCqzK42IZ_3h21bywg7wG8u4"
        self.alchemy_api_key = "eefqRWUjWK-GhAXCgyBlt"
        
        # Base URLs
        self.etherscan_base = "https://api.etherscan.io/api"
        self.moralis_base = "https://deep-index.moralis.io/api/v2.2"
        self.alchemy_base = f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
        
        # Headers for Moralis
        self.moralis_headers = {
            "X-API-Key": self.moralis_api_key,
            "Content-Type": "application/json"
        }
        
        # Common token contracts (can be expanded)
        self.token_contracts = {
            "usdt": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "usdc": "0xA0b86a33E6417c0Ed7ecf2aEe1A0BFE4E5F6F8a4",
            "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "uni": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
            "link": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
            "dai": "0x6B175474E89094C44Da98b954EedeAC495271d0F"
        }

    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language query into structured parameters"""
        query_lower = query.lower()
        
        # Extract number of results
        top_match = re.search(r'top\s+(\d+)', query_lower)
        limit = int(top_match.group(1)) if top_match else 50
        
        # Extract token name
        token_name = None
        for token, contract in self.token_contracts.items():
            if token in query_lower:
                token_name = token
                break
        
        # Extract value thresholds
        value_match = re.search(r'[\$>]\s*(\d+(?:,\d+)*(?:\.\d+)?)', query_lower)
        min_value = float(value_match.group(1).replace(',', '')) if value_match else None
        
        # Extract balance thresholds
        balance_match = re.search(r'balance[>\s]+(\d+(?:\.\d+)?)', query_lower)
        min_balance = float(balance_match.group(1)) if balance_match else None
        
        # Determine query type
        query_type = "token_holders"
        if "transaction" in query_lower or "volume" in query_lower:
            query_type = "high_volume_wallets"
        elif "whale" in query_lower or "large" in query_lower:
            query_type = "whale_wallets"
        elif "active" in query_lower:
            query_type = "active_wallets"
        
        return {
            "type": query_type,
            "limit": limit,
            "token": token_name,
            "min_value": min_value,
            "min_balance": min_balance,
            "original_query": query
        }

    def get_token_holders_etherscan(self, token_contract: str, limit: int = 100) -> List[WalletInfo]:
        """Get token holders using Etherscan API"""
        try:
            url = f"{self.etherscan_base}"
            params = {
                "module": "token",
                "action": "tokenholderlist",
                "contractaddress": token_contract,
                "page": 1,
                "offset": limit,
                "apikey": self.etherscan_api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            wallets = []
            if data.get("status") == "1" and data.get("result"):
                for holder in data["result"]:
                    wallet = WalletInfo(
                        address=holder["TokenHolderAddress"],
                        balance=float(holder["TokenHolderQuantity"]) / 10**18,  # Assuming 18 decimals
                        token_balance=float(holder["TokenHolderQuantity"]) / 10**18
                    )
                    wallets.append(wallet)
            
            return wallets
        except Exception as e:
            print(f"Error fetching token holders from Etherscan: {e}")
            return []

    def get_token_holders_moralis(self, token_contract: str, limit: int = 100) -> List[WalletInfo]:
        """Get token holders using Moralis API"""
        try:
            url = f"{self.moralis_base}/erc20/{token_contract}/owners"
            params = {
                "chain": "eth",
                "limit": limit,
                "order": "DESC"
            }
            
            response = requests.get(url, headers=self.moralis_headers, params=params)
            data = response.json()
            
            wallets = []
            if "result" in data:
                for holder in data["result"]:
                    balance_raw = int(holder.get("balance", "0"))
                    balance = balance_raw / 10**18  # Assuming 18 decimals
                    
                    wallet = WalletInfo(
                        address=holder["owner_address"],
                        balance=balance,
                        token_balance=balance
                    )
                    wallets.append(wallet)
            
            return wallets
        except Exception as e:
            print(f"Error fetching token holders from Moralis: {e}")
            return []

    def get_whale_wallets(self, min_balance: float = 1000) -> List[WalletInfo]:
        """Get whale wallets with high ETH balance"""
        try:
            # This is a simplified approach - in reality, you'd need to scan through blocks
            # or use more sophisticated methods to find whale wallets
            url = f"{self.etherscan_base}"
            
            # Get recent blocks and extract high-value transactions
            params = {
                "module": "proxy",
                "action": "eth_getBlockByNumber",
                "tag": "latest",
                "boolean": "true",
                "apikey": self.etherscan_api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            whale_addresses = set()
            if "result" in data and "transactions" in data["result"]:
                for tx in data["result"]["transactions"][:50]:  # Check recent transactions
                    value_wei = int(tx.get("value", "0x0"), 16)
                    value_eth = value_wei / 10**18
                    
                    if value_eth >= min_balance:
                        whale_addresses.add(tx["from"])
                        whale_addresses.add(tx["to"])
            
            # Get balance for each whale address
            wallets = []
            for address in list(whale_addresses)[:50]:  # Limit to avoid rate limits
                balance = self.get_eth_balance(address)
                if balance >= min_balance:
                    wallet = WalletInfo(
                        address=address,
                        balance=balance
                    )
                    wallets.append(wallet)
                time.sleep(0.2)  # Rate limiting
            
            return sorted(wallets, key=lambda x: x.balance, reverse=True)
        except Exception as e:
            print(f"Error fetching whale wallets: {e}")
            return []

    def get_eth_balance(self, address: str) -> float:
        """Get ETH balance for an address"""
        try:
            url = f"{self.etherscan_base}"
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest",
                "apikey": self.etherscan_api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "1":
                balance_wei = int(data["result"])
                return balance_wei / 10**18
            return 0.0
        except Exception as e:
            print(f"Error fetching ETH balance: {e}")
            return 0.0

    def get_high_volume_wallets(self, limit: int = 100, min_tx_count: int = 1000) -> List[WalletInfo]:
        """Get wallets with high transaction volume"""
        try:
            # This would typically require analyzing transaction history
            # For demo purposes, we'll get some active addresses from recent blocks
            url = f"{self.moralis_base}/block/latest"
            params = {"chain": "eth", "include": "internal_transactions"}
            
            response = requests.get(url, headers=self.moralis_headers, params=params)
            data = response.json()
            
            active_addresses = set()
            if "transactions" in data:
                for tx in data["transactions"]:
                    active_addresses.add(tx["from_address"])
                    active_addresses.add(tx["to_address"])
            
            # Get transaction count and balance for each address
            wallets = []
            for address in list(active_addresses)[:limit]:
                try:
                    tx_count = self.get_transaction_count(address)
                    if tx_count >= min_tx_count:
                        balance = self.get_eth_balance(address)
                        wallet = WalletInfo(
                            address=address,
                            balance=balance,
                            transaction_count=tx_count
                        )
                        wallets.append(wallet)
                    time.sleep(0.2)  # Rate limiting
                except Exception as e:
                    continue
            
            return sorted(wallets, key=lambda x: x.transaction_count or 0, reverse=True)
        except Exception as e:
            print(f"Error fetching high volume wallets: {e}")
            return []

    def get_transaction_count(self, address: str) -> int:
        """Get transaction count for an address"""
        try:
            url = f"{self.etherscan_base}"
            params = {
                "module": "proxy",
                "action": "eth_getTransactionCount",
                "address": address,
                "tag": "latest",
                "apikey": self.etherscan_api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if "result" in data:
                return int(data["result"], 16)
            return 0
        except Exception as e:
            print(f"Error fetching transaction count: {e}")
            return 0

    def process_query(self, query: str) -> List[WalletInfo]:
        """Main method to process natural language queries"""
        parsed = self.parse_query(query)
        
        print(f"Processing query: {query}")
        print(f"Parsed parameters: {parsed}")
        
        wallets = []
        
        if parsed["type"] == "token_holders" and parsed["token"]:
            token_contract = self.token_contracts.get(parsed["token"])
            if token_contract:
                print(f"Fetching holders for token: {parsed['token']}")
                # Try Moralis first, fallback to Etherscan
                wallets = self.get_token_holders_moralis(token_contract, parsed["limit"])
                if not wallets:
                    wallets = self.get_token_holders_etherscan(token_contract, parsed["limit"])
        
        elif parsed["type"] == "whale_wallets":
            min_balance = parsed.get("min_balance", 100)  # Default 100 ETH
            print(f"Fetching whale wallets with min balance: {min_balance} ETH")
            wallets = self.get_whale_wallets(min_balance)
        
        elif parsed["type"] == "high_volume_wallets":
            min_tx_count = 1000
            print(f"Fetching high volume wallets with min {min_tx_count} transactions")
            wallets = self.get_high_volume_wallets(parsed["limit"], min_tx_count)
        
        # Filter results based on additional criteria
        if parsed.get("min_value") and wallets:
            wallets = [w for w in wallets if (w.balance or 0) * 3000 >= parsed["min_value"]]  # Rough ETH price
        
        if parsed.get("min_balance") and wallets:
            wallets = [w for w in wallets if (w.balance or 0) >= parsed["min_balance"]]
        
        return wallets[:parsed["limit"]]

def main():
    # Initialize the blockchain query engine
    engine = BlockchainQueryEngine()
    
    # Example queries
    test_queries = [
        "Give me the top 50 wallets holding USDT",
        "Show me the top 20 whale wallets with more than 100 ETH",
        "Find the top 30 wallets holding UNI tokens",
        "Get me high volume wallets with more than 1000 transactions",
        "Top 25 USDC holders with balance > $10000"
    ]
    
    print("🔗 Smart Blockchain Query Dashboard")
    print("="*50)
    
    # Interactive mode
    while True:
        print("\nAvailable sample queries:")
        for i, query in enumerate(test_queries, 1):
            print(f"{i}. {query}")
        
        print("\nEnter your query (or 'quit' to exit):")
        user_input = input("> ").strip()
        
        if user_input.lower() == 'quit':
            break
        
        # Check if user selected a sample query
        if user_input.isdigit() and 1 <= int(user_input) <= len(test_queries):
            query = test_queries[int(user_input) - 1]
        else:
            query = user_input
        
        if not query:
            continue
        
        print(f"\n🔍 Processing: {query}")
        print("-" * 50)
        
        try:
            results = engine.process_query(query)
            
            if results:
                print(f"\n✅ Found {len(results)} wallets:")
                print("-" * 80)
                print(f"{'Rank':<5} {'Address':<45} {'Balance':<15} {'Token Balance':<15} {'Tx Count':<10}")
                print("-" * 80)
                
                for i, wallet in enumerate(results, 1):
                    address_short = f"{wallet.address[:6]}...{wallet.address[-4:]}"
                    balance_str = f"{wallet.balance:.4f}" if wallet.balance else "N/A"
                    token_balance_str = f"{wallet.token_balance:.4f}" if wallet.token_balance else "N/A"
                    tx_count_str = str(wallet.transaction_count) if wallet.transaction_count else "N/A"
                    
                    print(f"{i:<5} {wallet.address:<45} {balance_str:<15} {token_balance_str:<15} {tx_count_str:<10}")
                    
                    if i >= 20:  # Limit display to first 20 for readability
                        remaining = len(results) - 20
                        if remaining > 0:
                            print(f"... and {remaining} more wallets")
                        break
            else:
                print("❌ No results found. Try adjusting your query or check API limits.")
                
        except Exception as e:
            print(f"❌ Error processing query: {e}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    main()
